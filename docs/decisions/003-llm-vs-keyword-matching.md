# Decision Record: Semantic Matching vs. Keyword Matching

## Status
Approved

## Context
Traditional applicant tracking systems (ATS) rely on exact keyword matches (e.g. searching for "FastAPI" and rejecting a candidate who wrote "Fast API" or "built API endpoints using modern Python web frameworks"). This introduces high false-negative rates and encourages keyword-stuffing hacks.

## Alternatives Considered
1. **Fuzzy String Matching / TF-IDF**: Handles minor typos and keyword frequency scoring, but completely misses semantic intent, synonyms, and context.
2. **Pure LLM matching**: Sending a resume and a job description to an LLM and asking "Is this candidate a fit?" yields biased, arbitrary, and inconsistent scores with no traceable evidence.
3. **Structured Semantic Alignment**: The LLM maps candidate facts to job requirements, classifying status (`MATCH`, `PARTIAL`, `MISSING`, `UNKNOWN`) and providing exact quote evidence from the resume.

## Decision
We chose **Structured Semantic Alignment** because:
- **Synonym & Context Awareness**: Recognizes that "Amazon Web Services" means "AWS", and distinguishes a candidate who "wrote API endpoints" from a candidate who "managed API integrations".
- **Evidence-Driven Claims**: The system requires the LLM to extract direct quotes from the resume, creating an audit trail and preventing hallucinations.
- **Accurate Gaps Identification**: Distinguishes between `MISSING` (no evidence in the text) and `UNKNOWN` (ambiguous phrasing).
