# Decision Record: Deterministic Application-Controlled Scoring

## Status
Approved

## Context
Many recruitment tools delegate numerical scoring (e.g. "Overall Match: 87%") to the LLM. This leads to several failure modes:
1. The same candidate gets different scores on separate runs (non-deterministic).
2. The score calculation is opaque (black-box).
3. The recruiter cannot adjust priorities (e.g. making AWS critical instead of preferred) without changing the prompt.

## Alternatives Considered
1. **LLM Score Prediction**: Asking the LLM to output a float score out of 100 directly.
2. **Deterministic Rules Engine**: Standardizing job requirement matching status into variables and using an application-side weighted formula.

## Decision
We chose **Deterministic Application-Controlled Scoring** because:
- **Absolute Reproducibility**: Given the same resume and job requirements, the score is always exactly the same.
- **Configurable Weights**: Recruiters can customize weights (Technical, Experience, Projects, Education) dynamically.
- **Traceable Sub-Scores**: Displays a clear math breakdown (e.g. Tech Alignment: 36/40, Experience: 26/30), which makes the score fully explainable.
- **Decision Sensitivity Analysis**: Enables simulation (e.g. simulating how verifying AWS experience increases the score from 68 to 76) by recalculating the formula in code.
