# Interview Preparation Guide - TalentLens AI

This document contains detailed, engineering-first answers to core technical questions about the architecture, choices, and scaling paths of TalentLens AI.

---

### 1. Why did you build the scoring engine separately from the LLM?
* **Reproducibility**: LLM temperature and generation variances mean that sending the same resume twice can yield different scores. By moving scoring to deterministic Python code, the score remains 100% reproducible.
* **Explainability**: Recruiters need to see the exact formula and weight breakdown. It is simple to debug why a candidate got an 87 when we can show: `Tech (36/40) + Experience (26/30) + Projects (13/15) + Edu (9/10) + Other (3/5)`.
* **Configurability**: Recruiting priorities change. If a hiring manager decides AWS experience is now "Critical" instead of "Preferred," we adjust the DB model's requirement weights and re-run the calculation in milliseconds, without paying for expensive LLM API calls.
* **Simulative Insight**: It allows us to build features like **Decision Sensitivity Analysis** ("What would change the decision?") by running deterministic simulations of score changes.

### 2. How do you prevent hallucinations and validate LLM output?
* **Pydantic Validation**: All structured outputs are parsed using Pydantic schemas. If the model output misses a required field, returns invalid JSON, or changes data types, Pydantic throws a validation error.
* **Self-Correction & Retry**: If validation fails, the service catches the error, passes the validation traceback back to the LLM as a system correction instruction, and requests a corrected retry. If it fails a second time, it logs the error and gracefully skips the file rather than corrupting database records.
* **Bidirectional Evidence Mapping**: The matching prompt forces the LLM to supply the *exact text quote* from the resume as evidence for every match claim. This acts as an audit trail that recruiters can inspect, making it impossible for the AI to fabricate experiences without detection.

### 3. How would this scale to 100,000 resumes?
* **Asynchronous Queue**: Replace FastAPI's simple in-memory `BackgroundTasks` with a dedicated distributed task queue like **Celery** or **Arq**, backed by **Redis** as a broker.
* **Object Storage**: Store resume files in an S3 bucket or Google Cloud Storage, saving only the file URL and hash in the database.
* **Read Replicas**: Migrate SQLite to **PostgreSQL** with a master-replica configuration (since recruitment screening dashboards are heavily read-intensive).
* **Distributed Extraction**: Scale worker nodes horizontally to process PDF text extractions and LLM calls concurrently.

### 4. How would you reduce LLM token and API costs?
* **Text Pre-processing**: PDF structures contain duplicate styling headers, font mapping metadata, and page footers. The `ParserService` strips excessive spaces, consecutive newlines, and non-printable sequences, reducing prompt token size by 20-30%.
* **Ingestion Deduplication**: We hash file contents on upload. If a duplicate file is detected, we reuse the existing candidate profile and work history records from the DB, bypassing LLM parsing entirely.
* **Task Partitioning**: Resume parsing is the most expensive task. We do it *once* on upload. When matching the candidate against multiple different jobs later, we query the extracted candidate profile database fields directly rather than re-sending the raw resume text.
* **Model Tiering**: Use a small, cheap model (e.g. Gemini 1.5 Flash or GPT-4o-mini) for extraction and standard matching, and reserve larger models (Gemini 1.5 Pro) only for high-complexity candidate comparison analysis.

### 5. How do you handle scanned PDFs?
* **PDF Plumber fallback**: The current pipeline uses `pypdf` for extracting embedded text streams.
* **OCR Layer (Optical Character Recognition)**: For scanned PDFs (where text streams are empty), we introduce an OCR pre-processing layer using **Tesseract OCR** (via `pytesseract`) or **pdf2image**. If text extraction returns empty or less than 50 characters, we convert the PDF pages into image buffers and run OCR to extract clean text.

### 6. How do you handle conflicting information?
* **Timeline Checks**: We write custom overlapping date calculators. If the candidate claims 5 years of experience at Company A, but the dates show it was overlapping with full-time university study or another full-time role in a different location, the system highlights a warning: *"Timeline Conflict: Overlap of X months detected between Y and Z."*
* **Verification Flags**: Discrepancies do not auto-reject candidates. Instead, they are saved as non-judgmental warnings (`timeline_issues`), prompting the recruiter to verify the timeline during the initial phone screening.

### 7. How do you prevent demographic bias?
* **Blind Match Prompting**: Prompt instructions explicitly instruct the LLM to omit demographic metrics (photographs, gender, age, race, location, nationality) during structured extraction.
* **Feature Isolation**: While name, email, and phone are stored in the DB for recruiter dashboard displays, the matching engine only evaluates professional skills, experience tables, and degrees, ensuring complete structural blind matching.
