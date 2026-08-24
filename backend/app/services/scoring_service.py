import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.models import Match, MatchRequirement, Candidate, JobRequirement, Experience, Education
from app.core.config import settings

class ScoringService:
    @staticmethod
    def calculate_match_scores(db: Session, match: Match) -> Tuple[Dict[str, float], Dict[int, float]]:
        """
        Calculates all sub-scores and overall score for a Match.
        Returns a dict of scores and a dict of requirement score contributions.
        """
        # Load requirements
        match_reqs = match.match_requirements
        
        # 1. Technical Score (technical category requirements)
        tech_reqs = [mr for mr in match_reqs if mr.requirement.category == "technical"]
        tech_score = ScoringService._calculate_weighted_category_score(tech_reqs)
        
        # 2. Experience Score (experience category requirements)
        exp_reqs = [mr for mr in match_reqs if mr.requirement.category == "experience"]
        # Determine candidate's total years and requirement years
        cand_years = match.candidate.experience_years
        req_years = ScoringService._parse_required_experience_years(match.candidate.experiences, exp_reqs)
        
        if req_years > 0:
            exp_score = min(1.0, cand_years / req_years) * 100.0
        else:
            # Fallback: if candidate has >= 3 years, give 100. If less, scale it
            exp_score = min(1.0, cand_years / 3.0) * 100.0
            
        # 3. Projects Score (evaluate technical matches that have evidence in projects section)
        project_evidence_count = 0
        total_evals = 0
        for mr in match_reqs:
            if mr.status in ("MATCH", "PARTIAL"):
                total_evals += 1
                if mr.source_section and "project" in mr.source_section.lower():
                    project_evidence_count += 1
        
        if total_evals > 0:
            projects_score = (project_evidence_count / total_evals) * 100.0
            # If candidate has projects listed, give a boost
            if len(match.candidate.projects) > 0:
                projects_score = min(100.0, projects_score + 20.0)
        else:
            projects_score = 100.0 if len(match.candidate.projects) > 0 else 0.0

        # 4. Education Score (education category requirements)
        edu_reqs = [mr for mr in match_reqs if mr.requirement.category == "education"]
        edu_score = ScoringService._calculate_weighted_category_score(edu_reqs)

        # 5. Other Score (other category requirements)
        other_reqs = [mr for mr in match_reqs if mr.requirement.category == "other"]
        other_score = ScoringService._calculate_weighted_category_score(other_reqs)

        # Calculate contributions
        contributions = {}
        importance_weights = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
        status_scores = {"MATCH": 1.0, "PARTIAL": 0.5, "MISSING": 0.0, "UNKNOWN": 0.0}
        
        for mr in match_reqs:
            imp_w = importance_weights.get(mr.requirement.importance, 0.5)
            stat_s = status_scores.get(mr.status, 0.0)
            contributions[mr.id] = imp_w * stat_s

        # Fetch configured weights
        weights = settings.get_weights()
        overall_score = (
            weights["tech"] * tech_score +
            weights["exp"] * exp_score +
            weights["proj"] * projects_score +
            weights["edu"] * edu_score +
            weights["other"] * other_score
        )

        scores = {
            "technical_score": round(tech_score, 1),
            "experience_score": round(exp_score, 1),
            "projects_score": round(projects_score, 1),
            "education_score": round(edu_score, 1),
            "other_score": round(other_score, 1),
            "overall_score": round(overall_score, 1)
        }
        
        return scores, contributions

    @staticmethod
    def _calculate_weighted_category_score(match_reqs: List[MatchRequirement]) -> float:
        if not match_reqs:
            return 100.0  # Perfect score if no requirements in this category
            
        importance_weights = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
        status_scores = {"MATCH": 1.0, "PARTIAL": 0.5, "MISSING": 0.0, "UNKNOWN": 0.0}
        
        weighted_sum = 0.0
        max_weighted_sum = 0.0
        
        for mr in match_reqs:
            weight = importance_weights.get(mr.requirement.importance, 0.5)
            score = status_scores.get(mr.status, 0.0)
            weighted_sum += weight * score
            max_weighted_sum += weight
            
        if max_weighted_sum == 0.0:
            return 0.0
        return (weighted_sum / max_weighted_sum) * 100.0

    @staticmethod
    def _parse_required_experience_years(experiences: List[Experience], exp_reqs: List[MatchRequirement]) -> float:
        """Parse required experience years from the job description experience text (e.g. '3+ years' -> 3.0)"""
        years_found = []
        for er in exp_reqs:
            text = er.requirement.requirement_text
            match = re.search(r"(\d+)\+?\s*years?", text, re.IGNORECASE)
            if match:
                years_found.append(float(match.group(1)))
        
        if years_found:
            return max(years_found)
        return 0.0

    @staticmethod
    def calculate_decision_sensitivity(db: Session, match: Match) -> List[Dict[str, Any]]:
        """
        Determines the potential score increases if missing requirements are satisfied.
        Calculates hypothetical score changes.
        """
        sensitivity_reports = []
        missing_reqs = [mr for mr in match.match_requirements if mr.status in ("MISSING", "PARTIAL")]
        
        if not missing_reqs:
            return []

        # Current scores
        weights = settings.get_weights()
        
        importance_weights = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
        status_scores = {"MATCH": 1.0, "PARTIAL": 0.5, "MISSING": 0.0, "UNKNOWN": 0.0}

        for mr in missing_reqs:
            # We simulate: what if this requirement is status='MATCH'
            category = mr.requirement.category
            
            # Simulate category score
            cat_reqs = [r for r in match.match_requirements if r.requirement.category == category]
            
            weighted_sum = 0.0
            max_weighted_sum = 0.0
            for r in cat_reqs:
                weight = importance_weights.get(r.requirement.importance, 0.5)
                # Check status
                status = "MATCH" if r.id == mr.id else r.status
                score = status_scores.get(status, 0.0)
                weighted_sum += weight * score
                max_weighted_sum += weight
                
            sim_cat_score = (weighted_sum / max_weighted_sum) * 100.0 if max_weighted_sum > 0 else 100.0
            
            # Load other scores
            current_tech = match.technical_score
            current_exp = match.experience_score
            current_proj = match.projects_score
            current_edu = match.education_score
            current_other = match.other_score
            
            # Replace simulated category
            if category == "technical":
                sim_tech = sim_cat_score
            else:
                sim_tech = current_tech
                
            if category == "experience":
                sim_exp = sim_cat_score
            else:
                sim_exp = current_exp
                
            if category == "education":
                sim_edu = sim_cat_score
            else:
                sim_edu = current_edu
                
            if category == "other":
                sim_other = sim_cat_score
            else:
                sim_other = current_other
                
            sim_overall = (
                weights["tech"] * sim_tech +
                weights["exp"] * sim_exp +
                weights["proj"] * current_proj +
                weights["edu"] * sim_edu +
                weights["other"] * sim_other
            )
            
            delta = round(sim_overall - match.overall_score, 1)
            
            if delta > 0:
                sensitivity_reports.append({
                    "requirement_id": mr.requirement.id,
                    "requirement_text": mr.requirement.requirement_text,
                    "importance": mr.requirement.importance,
                    "current_status": mr.status,
                    "score_delta": delta,
                    "potential_score": round(sim_overall, 1)
                })
                
        # Sort by impact
        sensitivity_reports.sort(key=lambda x: x["score_delta"], reverse=True)
        return sensitivity_reports

    @staticmethod
    def run_timeline_consistency_check(experiences: List[Experience], educations: List[Education]) -> List[str]:
        """
        Deterministic timeline analysis. Checks for date overlaps > 1 month (grace period).
        Returns a list of warning messages.
        """
        warnings = []
        import datetime

        # Helper to parse dates into datetime objects
        def parse_date(date_str: str, default_end=False) -> Optional[datetime.date]:
            if not date_str:
                return None
            date_clean = date_str.strip().lower()
            if "present" in date_clean or "current" in date_clean:
                return datetime.date.today()
            
            # Try YYYY-MM
            match_ym = re.match(r"^(\d{4})-(\d{1,2})", date_clean)
            if match_ym:
                year = int(match_ym.group(1))
                month = int(match_ym.group(2))
                return datetime.date(year, month, 1)
            
            # Try YYYY
            match_y = re.match(r"^(\d{4})", date_clean)
            if match_y:
                year = int(match_y.group(1))
                # End date default to end of year, start to start of year
                month = 12 if default_end else 1
                return datetime.date(year, month, 1)
                
            return None

        parsed_exps = []
        for exp in experiences:
            start = parse_date(exp.start_date)
            end = parse_date(exp.end_date, default_end=True)
            if start and end:
                parsed_exps.append((exp, start, end))

        # Check job-to-job overlaps
        for i in range(len(parsed_exps)):
            for j in range(i + 1, len(parsed_exps)):
                exp1, s1, e1 = parsed_exps[i]
                exp2, s2, e2 = parsed_exps[j]
                
                # Check overlap: (start1 < end2) and (start2 < end1)
                if s1 < e2 and s2 < e1:
                    # Calculate overlap size
                    overlap_start = max(s1, s2)
                    overlap_end = min(e1, e2)
                    overlap_days = (overlap_end - overlap_start).days
                    
                    # Grace period: > 30 days
                    if overlap_days > 30:
                        overlap_months = round(overlap_days / 30.4, 1)
                        warnings.append(
                            f"Employment overlap detected: '{exp1.role}' at {exp1.company} and "
                            f"'{exp2.role}' at {exp2.company} ({overlap_months} months overlap)."
                        )

        # Check education overlaps with full-time jobs
        parsed_edus = []
        for edu in educations:
            start = parse_date(edu.start_date)
            end = parse_date(edu.end_date, default_end=True)
            if start and end:
                parsed_edus.append((edu, start, end))

        for edu, es, ee in parsed_edus:
            for exp, xs, xe in parsed_exps:
                # Check overlap
                if es < xe and xs < ee:
                    overlap_start = max(es, xs)
                    overlap_end = min(ee, xe)
                    overlap_days = (overlap_end - overlap_start).days
                    
                    if overlap_days > 120:  # Flag long overlaps (e.g. concurrent full time study and work)
                        overlap_months = round(overlap_days / 30.4, 1)
                        # We only flag if it looks like full-time overlap, but write warning non-judgmentally
                        warnings.append(
                            f"Concurrent study and employment: '{edu.degree}' at {edu.institution} and "
                            f"'{exp.role}' at {exp.company} ({overlap_months} months overlap)."
                        )

        return warnings
