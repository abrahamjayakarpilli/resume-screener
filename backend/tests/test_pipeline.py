import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add app directory to sys path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.parser_service import ParserService
from app.services.normalization_service import SkillNormalizationService
from app.services.scoring_service import ScoringService
from app.schemas.schemas import ExtractedResumeProfile, ExtractedSkill
from app.models.models import Experience, Education

client = TestClient(app)

# 1. Test Text Normalization
def test_text_normalization():
    dirty_text = "  Some    Python   developer\n\n\nwith   FastAPI  \t experience.  "
    clean = ParserService.normalize_text(dirty_text)
    assert clean == "Some Python developer\n\nwith FastAPI experience."

# 2. Test Profile Completeness calculation
def test_completeness_calculation():
    # Incomplete Profile
    incomplete = ExtractedResumeProfile(
        name="Charlie Brown",
        email=None,
        phone=None,
        summary="Tester",
        experience_years=1.0,
        education_summary=None,
        skills=[],
        experiences=[],
        educations=[],
        projects=[]
    )
    score = ParserService.calculate_completeness(incomplete)
    assert score == 15.0  # Just summary present

    # Complete Profile
    complete = ExtractedResumeProfile(
        name="John Doe",
        email="john@example.com",
        phone="555-555-5555",
        summary="Senior Developer",
        experience_years=5.0,
        education_summary="B.S. Computer Science",
        skills=[ExtractedSkill(name="Python")],
        experiences=[{"company": "Google", "role": "SWE", "years_calculated": 3.0}],
        educations=[{"degree": "B.S.", "institution": "GT"}],
        projects=[{"title": "Tool"}]
    )
    score2 = ParserService.calculate_completeness(complete)
    assert score2 == 100.0

# 3. Test Skill Normalization map
def test_skill_normalization():
    # Check JS canonical
    res_js = SkillNormalizationService.normalize("js")
    assert res_js["canonical_name"] == "JavaScript"
    assert res_js["category"] == "Programming Language"

    # Check postgres canonical
    res_pg = SkillNormalizationService.normalize("postgres")
    assert res_pg["canonical_name"] == "PostgreSQL"
    assert res_pg["category"] == "Database"

    # Check unknown technology fallback
    res_unknown = SkillNormalizationService.normalize("some-random-library")
    assert res_unknown["canonical_name"] == "Some-Random-Library"
    assert res_unknown["category"] == "Other Technology"

# 4. Test Timeline Overlap detector
def test_timeline_overlap_checks():
    # Valid non-overlapping experiences
    exp1 = Experience(role="SWE 1", company="A", start_date="2020-01", end_date="2021-12", years=2.0)
    exp2 = Experience(role="SWE 2", company="B", start_date="2022-01", end_date="2023-12", years=2.0)
    
    warnings = ScoringService.run_timeline_consistency_check([exp1, exp2], [])
    assert len(warnings) == 0

    # Overlapping experiences (> 1 month)
    exp_overlap1 = Experience(role="Role 1", company="Company X", start_date="2022-01", end_date="2023-06", years=1.5)
    exp_overlap2 = Experience(role="Role 2", company="Company Y", start_date="2023-01", end_date="2023-12", years=1.0)
    
    warnings2 = ScoringService.run_timeline_consistency_check([exp_overlap1, exp_overlap2], [])
    assert len(warnings2) == 1
    assert "overlap detected" in warnings2[0]

# 5. Test API Routes
def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_api_job_creation():
    payload = {
        "title": "QA Engineer",
        "description": "Requires deep understanding of software testing and python automation frameworks.",
        "requirements": [
            {"requirement_text": "Python", "category": "technical", "importance": "CRITICAL"},
            {"requirement_text": "Pytest", "category": "technical", "importance": "HIGH"}
        ]
    }
    res = client.post("/api/jobs", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "QA Engineer"
    assert len(data["requirements"]) == 2
