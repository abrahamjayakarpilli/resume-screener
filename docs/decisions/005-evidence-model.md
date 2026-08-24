# Decision Record: Bidirectional Resume Evidence Model

## Status
Approved

## Context
Recruiters do not trust AI recommendations blindly. If the system says "Matches AWS", the recruiter needs to know where and why this conclusion was drawn to verify it without manually searching through pages of text.

## Alternatives Considered
1. **Plain Highlights**: Storing a list of matched keywords.
2. **Text Citations**: Providing a simple textual justification from the LLM.
3. **Structured Evidence Engine**: Collecting:
   - Evaluated status (Match, Partial, Missing)
   - Exact quote from the resume
   - Source section (e.g. Experience -> Acme Corp)
   - Evidence confidence indicators (High, Medium, Low)

## Decision
We chose the **Structured Evidence Engine** because:
- **Zero Hallucination Validation**: Forcing the LLM to supply an exact quote from the resume text makes it easy to confirm that the candidate actually possesses the skill.
- **Location Mapping**: Storing the source section allows the front-end to render visual highlights (e.g. "Experience -> Tech Solutions") pointing the recruiter to the exact context of the claim.
- **Confidence Rating**: Rates confidence based on source quality (e.g. skills listed in work experience with dates get `HIGH` confidence, whereas skills listed in a loose summary get `MEDIUM` confidence).
