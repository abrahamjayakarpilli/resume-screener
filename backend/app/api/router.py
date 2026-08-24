import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import datetime
import json
import logging

from app.core.database import get_db
from app.models.models import (
    Job, JobRequirement, Resume, Candidate, Skill, CandidateSkill, 
    Experience, Education, Project, ScreeningRun, Match, MatchRequirement
)
from app.schemas.schemas import (
    JobCreate, JobResponse, ScreeningRunResponse, CandidateProfileResponse, 
    MatchResponse, CompareRequest, CompareResponse, CompareCandidateSummary
)
from app.services.parser_service import ParserService
from app.services.normalization_service import SkillNormalizationService
from app.services.llm_service import get_llm_provider
from app.services.matching_service import MatchingService
from app.services.scoring_service import ScoringService

router = APIRouter()
logger = logging.getLogger(__name__)

# LLM Parser helper for background tasks
llm_provider = get_llm_provider()
matching_service = MatchingService()

@router.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

# JOBS ENDPOINTS
@router.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Create a Job along with its structured requirements list"""
    job = Job(
        title=payload.title,
        description=payload.description,
        department=payload.department
    )
    db.add(job)
    db.flush()  # Generate job.id
    
    # If requirements are provided, save them
    if payload.requirements:
        for req in payload.requirements:
            db.add(JobRequirement(
                job_id=job.id,
                requirement_text=req.requirement_text,
                category=req.category,
                importance=req.importance
            ))
    else:
        # Fallback: Auto-generate requirements using LLM from job description text
        try:
            logger.info(f"Auto-analyzing requirements for job: {payload.title}")
            parsed_reqs = llm_provider.analyze_job(payload.description)
            for req in parsed_reqs:
                db.add(JobRequirement(
                    job_id=job.id,
                    requirement_text=req.get("requirement_text", ""),
                    category=req.get("category", "technical"),
                    importance=req.get("importance", "HIGH")
                ))
        except Exception as e:
            logger.error(f"Error auto-analyzing job requirements: {e}")
            # Fallback to single general requirement
            db.add(JobRequirement(
                job_id=job.id,
                requirement_text="Demonstrated engineering capability",
                category="other",
                importance="HIGH"
            ))
            
    db.commit()
    db.refresh(job)
    return job

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# SCREENING RUN BACKGROUND TASK
def process_screening_files(screening_run_id: int, files_data: List[dict], db_session_factory):
    db = db_session_factory()
    try:
        run = db.query(ScreeningRun).filter(ScreeningRun.id == screening_run_id).first()
        if not run:
            logger.error(f"Screening Run {screening_run_id} not found in background task.")
            return

        job = db.query(Job).filter(Job.id == run.job_id).first()
        if not job:
            logger.error(f"Job {run.job_id} not found in background task.")
            run.status = "failed"
            db.commit()
            return

        for f_data in files_data:
            filename = f_data["filename"]
            content = f_data["content"]
            
            # Deduplication: Hash file content to avoid redundant LLM parsing
            file_hash = hashlib.sha256(content).hexdigest()
            existing_resume = db.query(Resume).filter(Resume.file_hash == file_hash).first()

            candidate_db = None
            if existing_resume:
                logger.info(f"Resume file {filename} already exists. Reusing extracted candidate data.")
                candidate_db = existing_resume.candidate
            else:
                # 1. Extract text and normalize
                raw_text = ParserService.extract_text(content, filename)
                clean_text = ParserService.normalize_text(raw_text)
                
                # Save Resume record
                resume_db = Resume(
                    file_name=filename,
                    file_hash=file_hash,
                    raw_text=clean_text
                )
                db.add(resume_db)
                db.flush()

                # 2. Structured Profile Extraction
                logger.info(f"Extracting profile structured JSON via LLM for {filename}")
                profile_data = llm_provider.parse_resume(clean_text)
                
                # Check / Validate structure
                cand_name = profile_data.get("name", "Unknown Candidate")
                cand_email = profile_data.get("email")
                cand_phone = profile_data.get("phone")
                cand_summary = profile_data.get("summary")
                cand_exp_years = profile_data.get("experience_years", 0.0)
                cand_edu_summary = profile_data.get("education_summary")

                # Create Candidate
                candidate_db = Candidate(
                    resume_id=resume_db.id,
                    name=cand_name,
                    email=cand_email,
                    phone=cand_phone,
                    summary=cand_summary,
                    experience_years=cand_exp_years,
                    education_summary=cand_edu_summary
                )
                db.add(candidate_db)
                db.flush()

                # Save Skills with Normalization
                extracted_skills = profile_data.get("skills", [])
                for sk in extracted_skills:
                    sk_name = sk.get("name", "")
                    if not sk_name:
                        continue
                        
                    # Normalize skill
                    norm = SkillNormalizationService.normalize(sk_name)
                    # Check if Skill already exists in DB
                    skill_db = db.query(Skill).filter(Skill.name == norm["canonical_name"]).first()
                    if not skill_db:
                        skill_db = Skill(name=norm["canonical_name"], category=norm["category"])
                        db.add(skill_db)
                        db.flush()

                    db.add(CandidateSkill(
                        candidate_id=candidate_db.id,
                        skill_id=skill_db.id,
                        years_experience=sk.get("years_experience"),
                        evidence_text=sk.get("evidence_text")
                    ))

                # Save Experiences
                experiences = profile_data.get("experiences", [])
                for exp in experiences:
                    db.add(Experience(
                        candidate_id=candidate_db.id,
                        company=exp.get("company", "Unknown"),
                        role=exp.get("role", "Developer"),
                        start_date=exp.get("start_date"),
                        end_date=exp.get("end_date"),
                        description=exp.get("description"),
                        years=exp.get("years_calculated", 0.0)
                    ))

                # Save Educations
                educations = profile_data.get("educations", [])
                for edu in educations:
                    db.add(Education(
                        candidate_id=candidate_db.id,
                        degree=edu.get("degree", "Degree"),
                        institution=edu.get("institution", "University"),
                        field_of_study=edu.get("field_of_study"),
                        start_date=edu.get("start_date"),
                        end_date=edu.get("end_date")
                    ))

                # Save Projects
                projects = profile_data.get("projects", [])
                for proj in projects:
                    techs = ",".join(proj.get("technologies", []))
                    db.add(Project(
                        candidate_id=candidate_db.id,
                        title=proj.get("title", "Project"),
                        description=proj.get("description"),
                        technologies=techs
                    ))
                db.flush()

                # Calculate profile completeness
                from app.schemas.schemas import ExtractedResumeProfile
                profile_obj = ExtractedResumeProfile(**profile_data)
                candidate_db.completeness_score = ParserService.calculate_completeness(profile_obj)
                
                # Check chronological timeline warnings
                timeline_warnings = ScoringService.run_timeline_consistency_check(
                    candidate_db.experiences, candidate_db.educations
                )
                if timeline_warnings:
                    candidate_db.timeline_issues = json.dumps(timeline_warnings)
                db.flush()

            # 3. Create Match evaluation (semantic + evidence mapping)
            match_db = matching_service.match_candidate_to_job(db, candidate_db, job, run.id)

            # 4. Perform Scoring calculation
            scores, contributions = ScoringService.calculate_match_scores(db, match_db)
            
            # Apply scores to Match db record
            match_db.overall_score = scores["overall_score"]
            match_db.technical_score = scores["technical_score"]
            match_db.experience_score = scores["experience_score"]
            match_db.projects_score = scores["projects_score"]
            match_db.education_score = scores["education_score"]
            match_db.other_score = scores["other_score"]

            # Update MatchRequirements score contributions
            for mr in match_db.match_requirements:
                mr.score_contribution = contributions.get(mr.id, 0.0)

            # Recruiter recommendation status assignment based on score thresholds
            # 75-100: SHORTLIST, 55-74: REVIEW, 0-54: NOT RECOMMENDED
            if match_db.overall_score >= 75.0:
                match_db.recommendation = "SHORTLIST"
            elif match_db.overall_score >= 55.0:
                match_db.recommendation = "REVIEW"
            else:
                match_db.recommendation = "NOT RECOMMENDED"
            db.flush()

        run.status = "completed"
        run.completed_at = datetime.datetime.utcnow()
        db.commit()
        logger.info(f"Screening Run {screening_run_id} processed successfully.")

    except Exception as e:
        logger.error(f"Error processing screening run {screening_run_id}: {e}", exc_info=True)
        try:
            run = db.query(ScreeningRun).filter(ScreeningRun.id == screening_run_id).first()
            if run:
                run.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/jobs/{job_id}/screen", response_model=ScreeningRunResponse)
def screen_resumes(
    job_id: int, 
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload resumes and start screening run (processed asynchronously in background)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Limit file size check (max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    files_payload = []
    for f in files:
        # Read content to check size and pass to background worker
        content = f.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {f.filename} exceeds maximum size limit of 5MB.")
        
        files_payload.append({
            "filename": f.filename,
            "content": content
        })

    # Create Screening Run
    run_name = f"Screening Run {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run = ScreeningRun(
        job_id=job_id,
        name=run_name,
        status="processing"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Spawn background task
    from app.core.database import SessionLocal
    background_tasks.add_task(
        process_screening_files,
        run.id,
        files_payload,
        SessionLocal
    )

    return run

@router.get("/screening-runs", response_model=List[ScreeningRunResponse])
def list_screening_runs(db: Session = Depends(get_db)):
    return db.query(ScreeningRun).all()

@router.get("/screening-runs/{run_id}", response_model=ScreeningRunResponse)
def get_screening_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Screening run not found")
    return run


# CANDIDATE PROFILE DETAILS
@router.get("/candidates/{candidate_id}", response_model=CandidateProfileResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


# DETAILED MATCH DETAILS & DECISION INSIGHTS
@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

# DECISION SENSITIVITY ENDPOINT
@router.get("/matches/{match_id}/sensitivity")
def get_match_sensitivity(match_id: int, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    sensitivity = ScoringService.calculate_decision_sensitivity(db, match)
    return {
        "candidate_id": match.candidate_id,
        "current_score": match.overall_score,
        "potential_changes": sensitivity
    }


# COMPARATIVE CANDIDATE MATRIX
@router.post("/candidates/compare", response_model=CompareResponse)
def compare_candidates(payload: CompareRequest, db: Session = Depends(get_db)):
    """Compare 2-4 candidates side-by-side against a job's requirements"""
    candidate_ids = payload.candidate_ids
    if len(candidate_ids) < 2 or len(candidate_ids) > 4:
        raise HTTPException(status_code=400, detail="Comparison supports between 2 and 4 candidates.")
        
    candidates = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    if len(candidates) != len(candidate_ids):
        raise HTTPException(status_code=404, detail="One or more candidates not found")
        
    # Get matches for these candidates. We'll use the latest match.
    match_list = []
    for c in candidates:
        match = db.query(Match).filter(Match.candidate_id == c.id).order_by(Match.id.desc()).first()
        if not match:
            raise HTTPException(status_code=400, detail=f"Candidate {c.name} has not been screened yet.")
        match_list.append(match)

    # All candidates must have been screened against the same Job
    job_ids = {m.screening_run.job_id for m in match_list}
    if len(job_ids) > 1:
        raise HTTPException(status_code=400, detail="Candidates must be compared against the same job description.")
        
    job_id = list(job_ids)[0]
    job = db.query(Job).filter(Job.id == job_id).first()

    # Formulate candidate summaries
    summaries = []
    for m in match_list:
        cand = m.candidate
        
        # Identify strengths (requirements with MATCH status)
        strengths = [mr.requirement.requirement_text for mr in m.match_requirements if mr.status == "MATCH"]
        # Identify gaps (requirements with MISSING status)
        gaps = [mr.requirement.requirement_text for mr in m.match_requirements if mr.status == "MISSING"]
        
        # Build requirement status map for the candidate
        req_matches = []
        for mr in m.match_requirements:
            req_matches.append({
                "requirement_id": mr.requirement_id,
                "status": mr.status
            })

        summaries.append(CompareCandidateSummary(
            id=cand.id,
            name=cand.name,
            overall_score=m.overall_score,
            recommendation=m.recommendation,
            experience_years=cand.experience_years,
            strengths=strengths[:3],  # Top 3 strengths
            gaps=gaps[:3],            # Top 3 gaps
            req_matches=req_matches
        ))

    # Generate comparative justification summary
    summaries_sorted = sorted(summaries, key=lambda x: x.overall_score, reverse=True)
    best_candidate = summaries_sorted[0]
    second_candidate = summaries_sorted[1]
    
    justification = (
        f"{best_candidate.name} is ranked higher than the other candidates primarily because they satisfy "
        f"more critical technical requirements. They have demonstrated strong coverage of technical skills and "
        f"relevant experience. In comparison, {second_candidate.name} has minor skills gaps that reduce their "
        f"overall match alignment."
    )

    return CompareResponse(
        job_title=job.title,
        requirements=job.requirements,
        candidates=summaries,
        why_higher_justification=justification
    )
