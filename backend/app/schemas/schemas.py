from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Job Requirement
class JobRequirementBase(BaseModel):
    requirement_text: str
    category: str = Field(..., description="Category of requirement: technical, experience, education, other")
    importance: str = Field(..., description="Importance level: CRITICAL, HIGH, MEDIUM, LOW")

class JobRequirementCreate(JobRequirementBase):
    pass

class JobRequirementResponse(JobRequirementBase):
    id: int
    job_id: int

    class Config:
        from_attributes = True

# Job
class JobBase(BaseModel):
    title: str
    description: str
    department: Optional[str] = None

class JobCreate(JobBase):
    requirements: List[JobRequirementCreate] = []

class JobResponse(JobBase):
    id: int
    created_at: datetime
    requirements: List[JobRequirementResponse] = []

    class Config:
        from_attributes = True

# Skills
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None

class CandidateSkillResponse(BaseModel):
    skill: SkillBase
    years_experience: Optional[float] = None
    evidence_text: Optional[str] = None

    class Config:
        from_attributes = True

# Experience
class ExperienceBase(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    start_date_raw: Optional[str] = None
    end_date: Optional[str] = None
    end_date_raw: Optional[str] = None
    description: Optional[str] = None
    years: float = 0.0

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceResponse(ExperienceBase):
    id: int
    class Config:
        from_attributes = True

# Education
class EducationBase(BaseModel):
    degree: str
    institution: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class EducationCreate(EducationBase):
    pass

class EducationResponse(EducationBase):
    id: int
    class Config:
        from_attributes = True

# Project
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    class Config:
        from_attributes = True

# Structured Resume Parser Outputs (LLM Extraction Schemas)
class ExtractedSkill(BaseModel):
    name: str
    category: Optional[str] = None
    years_experience: Optional[float] = None
    evidence_text: Optional[str] = None

class ExtractedExperience(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    years_calculated: float = 0.0

class ExtractedEducation(BaseModel):
    degree: str
    institution: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ExtractedProject(BaseModel):
    title: str
    description: Optional[str] = None
    technologies: List[str] = []

class ExtractedResumeProfile(BaseModel):
    name: str = Field(..., description="Full name of candidate")
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience_years: float = Field(0.0, description="Total professional years of experience")
    education_summary: Optional[str] = None
    skills: List[ExtractedSkill] = []
    experiences: List[ExtractedExperience] = []
    educations: List[ExtractedEducation] = []
    projects: List[ExtractedProject] = []

# Candidate Profile Response
class CandidateProfileResponse(BaseModel):
    id: int
    resume_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    experience_years: float
    education_summary: Optional[str] = None
    completeness_score: float
    timeline_issues: Optional[str] = None
    
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []
    projects: List[ProjectResponse] = []
    candidate_skills: List[CandidateSkillResponse] = []

    class Config:
        from_attributes = True

# Match Requirement details
class MatchRequirementResponse(BaseModel):
    id: int
    requirement: JobRequirementResponse
    status: str
    evidence: Optional[str] = None
    source_section: Optional[str] = None
    confidence: Optional[str] = None
    score_contribution: float

    class Config:
        from_attributes = True

# Match response
class MatchResponse(BaseModel):
    id: int
    screening_run_id: int
    candidate: CandidateProfileResponse
    overall_score: float
    recommendation: str
    summary_justification: Optional[str] = None
    technical_score: float
    experience_score: float
    projects_score: float
    education_score: float
    other_score: float
    confidence: str
    match_requirements: List[MatchRequirementResponse] = []

    class Config:
        from_attributes = True

# Screening Run
class ScreeningRunResponse(BaseModel):
    id: int
    job_id: int
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    matches: List[MatchResponse] = []

    class Config:
        from_attributes = True

# Comparison request
class CompareRequest(BaseModel):
    candidate_ids: List[int]

# Comparative Candidate Profile Card (for side-by-side matrices)
class CompareCandidateSummary(BaseModel):
    id: int
    name: str
    overall_score: float
    recommendation: str
    experience_years: float
    strengths: List[str]
    gaps: List[str]
    requirement_matches: List[dict]  # List of {"requirement_id": int, "status": str}

class CompareResponse(BaseModel):
    job_title: str
    requirements: List[JobRequirementResponse]
    candidates: List[CompareCandidateSummary]
    why_higher_justification: str
