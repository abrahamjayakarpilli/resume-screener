from sqlalchemy.orm import Session
from app.models.models import Candidate, Job, Match, MatchRequirement, Skill, CandidateSkill
from app.services.llm_service import get_llm_provider
import logging

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.llm_provider = get_llm_provider()

    def match_candidate_to_job(self, db: Session, candidate: Candidate, job: Job, screening_run_id: int) -> Match:
        """
        Runs the semantic matching process. Maps the candidate's structured profile against
        the job requirements, queries the LLM for evidence, status, and confidence, and saves it.
        """
        # 1. Prepare job requirements payload
        requirements_data = []
        for req in job.requirements:
            requirements_data.append({
                "id": req.id,
                "requirement_text": req.requirement_text,
                "category": req.category,
                "importance": req.importance
            })

        # 2. Prepare candidate profile payload
        skills_data = []
        for cs in candidate.candidate_skills:
            skills_data.append({
                "name": cs.skill.name,
                "category": cs.skill.category,
                "years_experience": cs.years_experience,
                "evidence_text": cs.evidence_text
            })

        experiences_data = []
        for exp in candidate.experiences:
            experiences_data.append({
                "company": exp.company,
                "role": exp.role,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description,
                "years": exp.years
            })

        educations_data = []
        for edu in candidate.educations:
            educations_data.append({
                "degree": edu.degree,
                "institution": edu.institution,
                "field_of_study": edu.field_of_study,
                "start_date": edu.start_date,
                "end_date": edu.end_date
            })

        projects_data = []
        for proj in candidate.projects:
            projects_data.append({
                "title": proj.title,
                "description": proj.description,
                "technologies": proj.technologies.split(",") if proj.technologies else []
            })

        candidate_profile = {
            "name": candidate.name,
            "experience_years": candidate.experience_years,
            "summary": candidate.summary,
            "skills": skills_data,
            "experiences": experiences_data,
            "educations": educations_data,
            "projects": projects_data
        }

        # 3. Call LLM matching service
        logger.info(f"Running LLM semantic matching for candidate {candidate.name} against job {job.title}")
        match_result = self.llm_provider.match_candidate(requirements_data, candidate_profile)

        # 4. Create Match record (placeholders for scores, which will be updated by ScoringService)
        match_db = Match(
            screening_run_id=screening_run_id,
            candidate_id=candidate.id,
            overall_score=0.0,  # Calculated deterministically in ScoringService
            recommendation=match_result.get("recommendation", "REVIEW"),
            summary_justification=match_result.get("summary_justification", ""),
            confidence=match_result.get("confidence", "MEDIUM"),
            technical_score=0.0,
            experience_score=0.0,
            projects_score=0.0,
            education_score=0.0,
            other_score=0.0
        )
        db.add(match_db)
        db.flush()  # Generate match_db.id

        # 5. Save individual MatchRequirement evaluations
        req_evals = match_result.get("requirement_evaluations", [])
        # Create map from requirement_text to job requirement ID
        req_map = {r.requirement_text.lower(): r.id for r in job.requirements}
        
        for ev in req_evals:
            req_text = ev.get("requirement_text", "")
            req_id = req_map.get(req_text.lower())
            
            # If not direct match by text, try fuzzy or substring match
            if not req_id:
                for req in job.requirements:
                    if req.requirement_text.lower() in req_text.lower() or req_text.lower() in req.requirement_text.lower():
                        req_id = req.id
                        break
            
            # If still not found, default to first requirement or log warning
            if not req_id and job.requirements:
                req_id = job.requirements[0].id
                
            match_req = MatchRequirement(
                match_id=match_db.id,
                requirement_id=req_id,
                status=ev.get("status", "UNKNOWN"),
                evidence=ev.get("evidence", ""),
                source_section=ev.get("source_section"),
                confidence=ev.get("confidence", "MEDIUM"),
                score_contribution=0.0  # Assigned during scoring
            )
            db.add(match_req)
            
        db.commit()
        return match_db
