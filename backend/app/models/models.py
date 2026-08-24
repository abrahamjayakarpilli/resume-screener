from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Table, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    screening_runs = relationship("ScreeningRun", back_populates="job", cascade="all, delete-orphan")

class JobRequirement(Base):
    __tablename__ = "job_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    requirement_text = Column(String, nullable=False)
    category = Column(String, nullable=False)  # technical, experience, education, other
    importance = Column(String, nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    score_weight = Column(Float, default=1.0)
    
    job = relationship("Job", back_populates="requirements")
    match_requirements = relationship("MatchRequirement", back_populates="requirement", cascade="all, delete-orphan")

class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    job = relationship("Job", back_populates="screening_runs")
    matches = relationship("Match", back_populates="screening_run", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    candidate = relationship("Candidate", back_populates="resume", uselist=False, cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    experience_years = Column(Float, default=0.0)
    education_summary = Column(Text, nullable=True)
    completeness_score = Column(Float, default=0.0)  # Profile Completeness
    timeline_issues = Column(Text, nullable=True)  # Warnings about date overlaps / gaps
    
    resume = relationship("Resume", back_populates="candidate")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="candidate", cascade="all, delete-orphan")

class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    start_date = Column(String, nullable=True)
    start_date_raw = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    end_date_raw = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    years = Column(Float, default=0.0)
    
    candidate = relationship("Candidate", back_populates="experiences")

class Education(Base):
    __tablename__ = "educations"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    degree = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    field_of_study = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    
    candidate = relationship("Candidate", back_populates="educations")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(String, nullable=True)  # Comma separated
    
    candidate = relationship("Candidate", back_populates="projects")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=True)  # Programming Language, Database, Framework, DevOps, Soft Skill
    
    candidate_skills = relationship("CandidateSkill", back_populates="skill", cascade="all, delete-orphan")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    years_experience = Column(Float, nullable=True)
    evidence_text = Column(Text, nullable=True)
    
    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    screening_run_id = Column(Integer, ForeignKey("screening_runs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    overall_score = Column(Float, nullable=False)
    recommendation = Column(String, nullable=False)  # SHORTLIST, REVIEW, NOT RECOMMENDED
    summary_justification = Column(Text, nullable=True)
    
    technical_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    projects_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    other_score = Column(Float, default=0.0)
    confidence = Column(String, default="MEDIUM")  # HIGH, MEDIUM, LOW
    
    screening_run = relationship("ScreeningRun", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")
    match_requirements = relationship("MatchRequirement", back_populates="match", cascade="all, delete-orphan")

class MatchRequirement(Base):
    __tablename__ = "match_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(String, nullable=False)  # MATCH, PARTIAL, MISSING, UNKNOWN
    evidence = Column(Text, nullable=True)
    source_section = Column(String, nullable=True)
    confidence = Column(String, nullable=True)  # HIGH, MEDIUM, LOW
    score_contribution = Column(Float, default=0.0)
    
    match = relationship("Match", back_populates="match_requirements")
    requirement = relationship("JobRequirement", back_populates="match_requirements")
