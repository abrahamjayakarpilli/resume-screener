# TalentLens AI: Explainable Candidate Intelligence

TalentLens AI is an exceptional, production-grade candidate matching platform. It turns unstructured resumes and job descriptions into structured requirements and provides transparent, evidence-backed hiring recommendations. 

Unlike black-box AI screening systems that output arbitrary percentage matches, TalentLens AI calculates scores deterministically, traces every AI claim to direct quotes from the resume, highlights skill gaps, checks for timeline conflicts, and simulates decision sensitivity.

---

## 🚀 Key Differentiators

* **Explainable Match Intelligence**: Displays detailed requirement matrices detailing why a candidate received their score, mapping candidates to status ratings (`✓ MATCH`, `~ PARTIAL`, `× MISSING`, `? UNKNOWN`).
* **Bidirectional Evidence Mapping**: Traces every matching skill back to its source section and extracts the exact text quote from the resume, mitigating AI hallucination and enabling rapid verification.
* **Deterministic Application-Controlled Scoring**: The LLM acts as a semantic classifier, but the application calculates numerical scores using configurable importance weights (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Scores are 100% reproducible.
* **Decision Sensitivity Analysis ("What would change the decision?")**: Deterministically simulates score changes, showing how verifying a missing critical requirement increases the candidate's score.
* **Timeline Consistency Checker**: Deterministically calculates work and study dates to flag overlaps (> 1 month grace period) or concurrent degree programs, alerting recruiters non-judgmentally.
* **Algorithmic Fairness Safeguards**: Employs blind matching principles; personal information (names, emails, phones) is isolated, and prompts instruct the LLM to ignore age, gender, race, photos, and location.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.12, FastAPI, SQLAlchemy ORM, SQLite (local config) / PostgreSQL (production config), Pydantic v2.
* **Frontend**: Vanilla HTML5, Vanilla JavaScript (Single Page Application architecture), Vanilla CSS3 (Custom design tokens, grid spacing, CSS timeline, circular progress charts).
* **AI Engine**: Google Gemini API (standard model) / OpenAI API (fallback) / Offline Mock LLM Provider (active by default, requires zero API keys).

---

## 📁 Project Directory Structure

```
talentlens-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── router.py             # REST API endpoint handlers
│   │   ├── core/
│   │   │   ├── config.py             # Server & scoring weights config
│   │   │   └── database.py           # SQLAlchemy setup & session helper
│   │   ├── models/
│   │   │   └── models.py             # DB entities (Job, Candidate, Match...)
│   │   ├── prompts/
│   │   │   ├── resume_extraction.txt # Structured resume parser prompt
│   │   │   ├── job_analysis.txt      # Job requirement parser prompt
│   │   │   └── candidate_matching.txt# Requirement mapping prompt
│   │   ├── schemas/
│   │   │   └── schemas.py            # Pydantic validation models
│   │   ├── services/
│   │   │   ├── llm_service.py        # Gemini / OpenAI / Mock provider
│   │   │   ├── parser_service.py     # PDF text extraction & completeness
│   │   │   ├── normalization_service.py # Canonical skill mapper
│   │   │   ├── matching_service.py   # Semantic requirements aligner
│   │   │   └── scoring_service.py    # Weighted formula & timeline check
│   │   └── main.py                   # App entry & static assets mount
│   ├── tests/
│   │   └── test_pipeline.py          # Unit & Integration pytest suite
│   └── requirements.txt              # Backend dependencies
├── frontend/
│   ├── css/
│   │   └── styles.css                # B2B enterprise style design tokens
│   ├── js/
│   │   ├── api.js                    # Fetch wrapper client
│   │   ├── components.js             # HTML timelines & matrices builders
│   │   └── app.js                    # SPA state router & demo runner
│   └── index.html                    # Main semantic markup layout
├── docs/
│   ├── decisions/                    # Design Decision Records (DDR)
│   │   ├── 001-why-fastapi.md
│   │   ├── 002-why-sqlite.md
│   │   └── ... (003 - 006)
│   └── architecture.md               # Pipeline logic & data models
├── Dockerfile                        # Server containerization build
├── docker-compose.yml                # Docker orchestrator configuration
├── INTERVIEW.md                      # Scalability, cost, and design answers
└── README.md                         # Setup & walkthrough guide
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` to customize settings.

```env
# Server
PORT=8000
HOST=127.0.0.1

# Database
DATABASE_URL=sqlite:///./talentlens.db

# LLM Config
# Set MOCK_LLM to false and add keys to run live AI matching
MOCK_LLM=true
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Configurable Scoring Weights (must sum to 1.0)
SCORING_WEIGHT_TECH=0.40
SCORING_WEIGHT_EXP=0.30
SCORING_WEIGHT_PROJ=0.15
SCORING_WEIGHT_EDU=0.10
SCORING_WEIGHT_OTHER=0.05
```

---

## 🏃 Setup & Run Instructions

### Option 1: Local Installation (Fastest)

1. **Clone/Navigate** to the project directory:
   ```bash
   cd scratch/talentlens-ai
   ```
2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Start the FastAPI Application**:
   ```bash
   python backend/app/main.py
   ```
5. **Open Web Platform**:
   Navigate to [http://localhost:8000](http://localhost:8000) in your web browser. The FastAPI server serves the frontend SPA on the root path directly.

---

### Option 2: Run via Docker Compose

1. **Build and Run Containers**:
   ```bash
   docker-compose up --build
   ```
2. **Access application**:
   Open [http://localhost:8000](http://localhost:8000) on your browser.

---

### Run Test Suite
Verify parser normalization, scoring arithmetic, and API routes:
```bash
python -m pytest backend/tests/
```

---

## ⏱️ 2-Minute Demo Walkthrough

The platform has a **⚡ Run 2-Minute Demo Run** button on the dashboard sidebar that runs the entire pipeline locally:

1. **Click 'Run 2-Minute Demo Run'** on the quick actions panel.
2. The platform automatically:
   - Registers a **Senior Backend Developer** job description requiring Python, FastAPI, AWS, and PostgreSQL.
   - Extracts and structures the requirements with their priority levels.
   - Creates a **Screening Run** and uploads 5 high-fidelity synthetic resumes.
   - Normalizes skills, runs chronological checks, scores, and creates matches.
3. The platform navigates to the **Candidates** tab and ranks them:
   - **#1 John Doe (95%) - SHORTLIST**: Perfect match across all requirements.
   - **#2 Alice White (80%) - REVIEW**: Strong skills, but flags a timeline conflict (overlapping full-time roles).
   - **#3 Jane Smith (74%) - REVIEW**: High backend skills, but highlights an AWS skill gap.
   - **#4 Bob Jones (45%) - NOT RECOMMENDED**: Low experience, missing key technologies.
   - **#5 Charlie Brown (30%) - NOT RECOMMENDED**: Profile incompleteness issue (missing email/phone details).
4. **Inspect Jane Smith's Profile**:
   - Scroll to **Decision Sensitivity Analysis** to see: *"Verify 'AWS': +8.0 pts"*.
   - Review the **Job Requirements Matrix** to inspect the exact quote evidence mapped for Python and FastAPI, and the missing indicator for AWS.
5. **Select John Doe and Jane Smith** and click **⚖️ Compare Selected**:
   - Inspect the side-by-side criteria matrix comparing overall fit, recommendations, strengths, and technology statuses.
