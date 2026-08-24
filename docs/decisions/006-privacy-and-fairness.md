# Decision Record: Privacy and Algorithmic Fairness Controls

## Status
Approved

## Context
Algorithmic screening can easily perpetuate bias (e.g. name-based bias, gender gaps, ageism) if LLMs are exposed to biographical, demographic, or visual data in resumes. 

## Alternatives Considered
1. **Unfiltered Screening**: Sending full resume text including names, graduation years, locations, and personal photos to the LLM.
2. **Deterministic Pre-Filtering**: Stripping dates and names in Python code before sending to the LLM.
3. **Structured Bias Mitigation Prompts + Blind Matching Architecture**:
   - The LLM prompt explicitly commands the model to ignore protected characteristics (gender, race, age, location, photographs, name-based bias).
   - In the matching engine, candidate evaluation is conducted strictly against professional attributes (skills, experience years, education level).

## Decision
We chose **Structured Bias Mitigation Prompts + Blind Matching Architecture** because:
- **Fair Evaluation**: Instructions strictly exclude demographic identifiers from the matching context.
- **Biographical Integrity**: While the system extracts names for the recruiter dashboard, the matching engine only evaluates the structured experience, education, and skill records.
- **Timeline Checks**: Standardized timeline checks analyze *intervals* (e.g. overlaps) rather than absolute age or graduation years, preventing age-related bias.
