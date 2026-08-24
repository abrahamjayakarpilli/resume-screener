import os
import json
import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base LLM Provider class
class LLMProvider:
    def analyze_job(self, job_description: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        raise NotImplementedError

    def match_candidate(self, job_requirements: List[Dict[str, Any]], candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

# Gemini Provider implementation
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _call_gemini(self, prompt: str) -> str:
        try:
            # Request JSON output constraint where supported
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Call failed: {e}")
            raise e

    def analyze_job(self, job_description: str) -> List[Dict[str, Any]]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "job_analysis.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{job_description}", job_description)
        result = self._call_gemini(prompt)
        return json.loads(result)

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "resume_extraction.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{resume_text}", resume_text)
        result = self._call_gemini(prompt)
        return json.loads(result)

    def match_candidate(self, job_requirements: List[Dict[str, Any]], candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "candidate_matching.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{job_requirements}", json.dumps(job_requirements, indent=2))
        prompt = prompt.replace("{candidate_profile}", json.dumps(candidate_profile, indent=2))
        result = self._call_gemini(prompt)
        return json.loads(result)

# OpenAI Provider implementation
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"

    def _call_openai(self, system_msg: str, user_msg: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        try:
            res = requests.post(self.url, headers=headers, json=data, timeout=30)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API Call failed: {e}")
            raise e

    def analyze_job(self, job_description: str) -> List[Dict[str, Any]]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "job_analysis.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        user_msg = f"Job description:\n{job_description}"
        result = self._call_openai(template, user_msg)
        return json.loads(result)

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "resume_extraction.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        user_msg = f"Resume Text:\n{resume_text}"
        result = self._call_openai(template, user_msg)
        return json.loads(result)

    def match_candidate(self, job_requirements: List[Dict[str, Any]], candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "candidate_matching.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        user_msg = f"Requirements:\n{json.dumps(job_requirements, indent=2)}\n\nProfile:\n{json.dumps(candidate_profile, indent=2)}"
        result = self._call_openai(template, user_msg)
        return json.loads(result)

# High-fidelity Offline Mock Provider
class MockLLMProvider(LLMProvider):
    def analyze_job(self, job_description: str) -> List[Dict[str, Any]]:
        # Deterministically extract mock requirements based on text presence
        # Looks for "Senior Backend Developer" or defaults
        return [
            {"requirement_text": "Python", "category": "technical", "importance": "CRITICAL"},
            {"requirement_text": "FastAPI", "category": "technical", "importance": "HIGH"},
            {"requirement_text": "PostgreSQL", "category": "technical", "importance": "MEDIUM"},
            {"requirement_text": "AWS", "category": "technical", "importance": "HIGH"},
            {"requirement_text": "Docker", "category": "technical", "importance": "LOW"},
            {"requirement_text": "3+ years of professional backend experience", "category": "experience", "importance": "CRITICAL"},
            {"requirement_text": "Bachelor's in Computer Science", "category": "education", "importance": "MEDIUM"}
        ]

    def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        # Return different mock parsed profiles depending on keywords in the text
        text_lower = resume_text.lower()
        if "john doe" in text_lower or "excellent" in text_lower:
            return {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 111-2222",
                "summary": "Experienced Full Stack Backend Engineer with strong history of maintaining Python servers, creating microservices, and deploying cloud architecture.",
                "experience_years": 4.5,
                "education_summary": "Bachelor of Science in Computer Science, Georgia Tech (2018-2022)",
                "skills": [
                    {"name": "Python", "category": "Programming Language", "years_experience": 4.0, "evidence_text": "Developed backend APIs using Python for 4+ years"},
                    {"name": "FastAPI", "category": "Backend Framework", "years_experience": 2.5, "evidence_text": "Built enterprise FastAPI applications"},
                    {"name": "PostgreSQL", "category": "Database", "years_experience": 3.0, "evidence_text": "Configured database schemas on PostgreSQL"},
                    {"name": "AWS", "category": "DevOps", "years_experience": 2.0, "evidence_text": "Managed deployments on AWS EC2 & RDS"},
                    {"name": "Docker", "category": "DevOps", "years_experience": 3.0, "evidence_text": "Dockerized microservices"}
                ],
                "experiences": [
                    {
                        "company": "Tech Solutions Corp",
                        "role": "Senior Software Engineer",
                        "start_date": "2023-01",
                        "end_date": "Present",
                        "description": "Architected Python FastAPI servers processing over 10M requests daily. Implemented AWS Cloud infrastructures including EC2 auto-scaling.",
                        "years_calculated": 3.6
                    },
                    {
                        "company": "Startup Labs",
                        "role": "Software Developer Intern",
                        "start_date": "2022-05",
                        "end_date": "2022-12",
                        "description": "Configured PostgreSQL databases and dockerized multi-tier web applications.",
                        "years_calculated": 0.6
                    }
                ],
                "educations": [
                    {
                        "degree": "Bachelor of Science",
                        "institution": "Georgia Institute of Technology",
                        "field_of_study": "Computer Science",
                        "start_date": "2018",
                        "end_date": "2022"
                    }
                ],
                "projects": [
                    {
                        "title": "Smart Inventory System",
                        "description": "Built automated stock forecasting using python, postgresql, and Docker containerization.",
                        "technologies": ["Python", "PostgreSQL", "Docker"]
                    }
                ]
            }
        elif "jane smith" in text_lower or "aws gap" in text_lower or "gap" in text_lower:
            return {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+1 (555) 222-3333",
                "summary": "Detail-oriented Software Developer specializing in Python backend technologies and lightweight FastAPI services. Passionate about PostgreSQL query tuning.",
                "experience_years": 3.2,
                "education_summary": "B.S. in Software Engineering, University of Washington (2019-2023)",
                "skills": [
                    {"name": "Python", "category": "Programming Language", "years_experience": 3.0, "evidence_text": "3 years of Python coding"},
                    {"name": "FastAPI", "category": "Backend Framework", "years_experience": 1.5, "evidence_text": "Engineered FastAPI web applications"},
                    {"name": "PostgreSQL", "category": "Database", "years_experience": 2.0, "evidence_text": "Structured tables and queries on Postgres"},
                    {"name": "Docker", "category": "DevOps", "years_experience": 1.0, "evidence_text": "Mentioned Docker in a backend project"}
                ],
                "experiences": [
                    {
                        "company": "Innovate Software Inc",
                        "role": "Backend Engineer",
                        "start_date": "2023-06",
                        "end_date": "Present",
                        "description": "Built backend services using FastAPI and PostgreSQL. Maintained Python microservices.",
                        "years_calculated": 3.2
                    }
                ],
                "educations": [
                    {
                        "degree": "B.S.",
                        "institution": "University of Washington",
                        "field_of_study": "Software Engineering",
                        "start_date": "2019",
                        "end_date": "2023"
                    }
                ],
                "projects": [
                    {
                        "title": "Collaborative Task Manager",
                        "description": "Developed database schemas on PostgreSQL, run inside Docker containers.",
                        "technologies": ["FastAPI", "PostgreSQL", "Docker"]
                    }
                ]
            }
        elif "bob jones" in text_lower or "weak" in text_lower:
            return {
                "name": "Bob Jones",
                "email": "bob.jones@example.com",
                "phone": "+1 (555) 333-4444",
                "summary": "Entry-level junior coder looking for opportunities in web design and scripting.",
                "experience_years": 1.2,
                "education_summary": "Associate Degree in Information Systems (2022-2024)",
                "skills": [
                    {"name": "Python", "category": "Programming Language", "years_experience": 1.0, "evidence_text": "Basic scripts in Python"}
                ],
                "experiences": [
                    {
                        "company": "Local Agency",
                        "role": "Junior IT Technician",
                        "start_date": "2024-01",
                        "end_date": "Present",
                        "description": "Automated simple office reports using Python scripting.",
                        "years_calculated": 1.2
                    }
                ],
                "educations": [
                    {
                        "degree": "Associate Degree",
                        "institution": "Community College",
                        "field_of_study": "Information Systems",
                        "start_date": "2022",
                        "end_date": "2024"
                    }
                ],
                "projects": []
            }
        elif "alice white" in text_lower or "timeline" in text_lower or "overlap" in text_lower:
            # Overlapping employment dates (timeline issue)
            return {
                "name": "Alice White",
                "email": "alice.white@example.com",
                "phone": "+1 (555) 444-5555",
                "summary": "Dynamic software developer with overlapping engagements at major IT consulting projects.",
                "experience_years": 3.5,
                "education_summary": "Bachelor in CS, Seattle University (2019-2023)",
                "skills": [
                    {"name": "Python", "category": "Programming Language", "years_experience": 3.0, "evidence_text": "Used Python backend"},
                    {"name": "FastAPI", "category": "Backend Framework", "years_experience": 2.0, "evidence_text": "Developed FastAPI microservices"},
                    {"name": "PostgreSQL", "category": "Database", "years_experience": 2.5, "evidence_text": "PostgreSQL administration"},
                    {"name": "AWS", "category": "DevOps", "years_experience": 1.5, "evidence_text": "AWS configuration"}
                ],
                "experiences": [
                    {
                        "company": "Apex Consulting Group",
                        "role": "Software Engineer (Full-Time)",
                        "start_date": "2023-01",
                        "end_date": "2024-06",
                        "description": "Engineered Python solutions and maintained databases.",
                        "years_calculated": 1.5
                    },
                    {
                        "company": "Global Systems Ltd",
                        "role": "Backend Architect (Full-Time)",
                        "start_date": "2023-06",
                        "end_date": "2024-12",
                        "description": "Developed FastAPI endpoints and configured AWS deployments.",
                        "years_calculated": 1.5
                    }
                ],
                "educations": [
                    {
                        "degree": "Bachelor",
                        "institution": "Seattle University",
                        "field_of_study": "Computer Science",
                        "start_date": "2019",
                        "end_date": "2023"
                    }
                ],
                "projects": []
            }
        else:
            # Charlie Brown: incomplete/missing details (resume completeness issue)
            return {
                "name": "Charlie Brown",
                "email": None,
                "phone": None,
                "summary": "Software script enthusiast. Works with Python backend code.",
                "experience_years": 2.0,
                "education_summary": "Studied Computer Engineering",
                "skills": [
                    {"name": "Python", "category": "Programming Language", "years_experience": 2.0, "evidence_text": "Python coder"}
                ],
                "experiences": [
                    {
                        "company": "Beta Labs",
                        "role": "Developer",
                        "start_date": None,
                        "end_date": None,
                        "description": "Coded python services.",
                        "years_calculated": 2.0
                    }
                ],
                "educations": [],
                "projects": []
            }

    def match_candidate(self, job_requirements: List[Dict[str, Any]], candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        # Formulate detailed evaluations matching the mock candidate's skills
        candidate_name = candidate_profile["name"]
        evals = []
        
        # Determine status mapping helper
        def get_eval(req_text, status, evidence, source, confidence):
            return {
                "requirement_text": req_text,
                "status": status,
                "evidence": evidence,
                "source_section": source,
                "confidence": confidence
            }

        if candidate_name == "John Doe":
            evals = [
                get_eval("Python", "MATCH", "Developed backend APIs using Python for 4+ years", "Skills list", "HIGH"),
                get_eval("FastAPI", "MATCH", "Architected Python FastAPI servers processing over 10M requests daily.", "Experience -> Tech Solutions Corp", "HIGH"),
                get_eval("PostgreSQL", "MATCH", "Configured database schemas on PostgreSQL", "Skills list", "HIGH"),
                get_eval("AWS", "MATCH", "Implemented AWS Cloud infrastructures including EC2 auto-scaling.", "Experience -> Tech Solutions Corp", "HIGH"),
                get_eval("Docker", "MATCH", "Dockerized microservices", "Skills list", "HIGH"),
                get_eval("3+ years of professional backend experience", "MATCH", "Has 4.5 years of total professional experience.", "Candidate profile", "HIGH"),
                get_eval("Bachelor's in Computer Science", "MATCH", "Bachelor of Science in Computer Science, Georgia Institute of Technology", "Education -> Georgia Tech", "HIGH")
            ]
            recommendation = "SHORTLIST"
            justification = "The candidate is an exceptional match. They satisfy all critical and high-priority requirements (Python, FastAPI, AWS, and 3+ years experience) with strong evidence from Tech Solutions Corp."
            confidence = "HIGH"
            
        elif candidate_name == "Jane Smith":
            evals = [
                get_eval("Python", "MATCH", "3 years of Python coding", "Skills list", "HIGH"),
                get_eval("FastAPI", "MATCH", "Built backend services using FastAPI and PostgreSQL.", "Experience -> Innovate Software Inc", "HIGH"),
                get_eval("PostgreSQL", "MATCH", "Structured tables and queries on Postgres", "Skills list", "HIGH"),
                get_eval("AWS", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("Docker", "PARTIAL", "Developed database schemas on PostgreSQL, run inside Docker containers.", "Projects -> Collaborative Task Manager", "MEDIUM"),
                get_eval("3+ years of professional backend experience", "MATCH", "Has 3.2 years of professional experience.", "Candidate profile", "HIGH"),
                get_eval("Bachelor's in Computer Science", "MATCH", "B.S. in Software Engineering, University of Washington", "Education -> UW", "HIGH")
            ]
            recommendation = "REVIEW"
            justification = "The candidate is a strong fit for core backend skills (Python, FastAPI, Postgres) and has enough experience. However, there is a complete absence of evidence for AWS (High Importance) and only partial/project Docker exposure."
            confidence = "HIGH"
            
        elif candidate_name == "Bob Jones":
            evals = [
                get_eval("Python", "MATCH", "Basic scripts in Python", "Skills list", "MEDIUM"),
                get_eval("FastAPI", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("PostgreSQL", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("AWS", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("Docker", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("3+ years of professional backend experience", "MISSING", "Only has 1.2 years of IT technician work.", "Experience -> Local Agency", "HIGH"),
                get_eval("Bachelor's in Computer Science", "MISSING", "Only possesses an Associate Degree in Information Systems.", "Education -> Community College", "HIGH")
            ]
            recommendation = "NOT RECOMMENDED"
            justification = "The candidate does not meet the core technical or experience requirements. They lack experience with FastAPI, PostgreSQL, AWS, and Docker, and have only 1.2 years of general IT experience."
            confidence = "HIGH"
            
        elif candidate_name == "Alice White":
            evals = [
                get_eval("Python", "MATCH", "Used Python backend", "Skills list", "HIGH"),
                get_eval("FastAPI", "MATCH", "Developed FastAPI microservices", "Skills list", "HIGH"),
                get_eval("PostgreSQL", "MATCH", "PostgreSQL administration", "Skills list", "HIGH"),
                get_eval("AWS", "MATCH", "Developed FastAPI endpoints and configured AWS deployments.", "Experience -> Global Systems Ltd", "HIGH"),
                get_eval("Docker", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("3+ years of professional backend experience", "MATCH", "Has 3.5 years of experience.", "Candidate profile", "HIGH"),
                get_eval("Bachelor's in Computer Science", "MATCH", "Bachelor in CS, Seattle University", "Education -> Seattle University", "HIGH")
            ]
            recommendation = "REVIEW"
            justification = "Highly capable candidate satisfying Python, FastAPI, AWS, and experience requirements. However, timeline flags must be checked as their full-time roles at Apex and Global Systems overlap significantly during 2023-2024."
            confidence = "HIGH"
            
        else: # Charlie Brown
            evals = [
                get_eval("Python", "MATCH", "Python coder", "Skills list", "MEDIUM"),
                get_eval("FastAPI", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("PostgreSQL", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("AWS", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("Docker", "MISSING", "No evidence found in the submitted resume.", None, "LOW"),
                get_eval("3+ years of professional backend experience", "MISSING", "Only has 2.0 years of experience.", "Experience -> Beta Labs", "HIGH"),
                get_eval("Bachelor's in Computer Science", "MISSING", "Studied Computer Engineering (No degree indicated)", "Education", "MEDIUM")
            ]
            recommendation = "NOT RECOMMENDED"
            justification = "Incomplete profile. Email and phone number are missing. Critical requirements (FastAPI, AWS, 3+ years experience) are absent."
            confidence = "MEDIUM"

        return {
            "recommendation": recommendation,
            "summary_justification": justification,
            "confidence": confidence,
            "requirement_evaluations": evals
        }

# Factory function to instantiate provider based on environment
def get_llm_provider() -> LLMProvider:
    if os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes"):
        logger.info("Initializing high-fidelity Mock LLM Provider.")
        return MockLLMProvider()
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        logger.info("Initializing active Google Gemini LLM Provider.")
        return GeminiProvider(api_key=gemini_key)
        
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        logger.info("Initializing active OpenAI LLM Provider.")
        return OpenAIProvider(api_key=openai_key)

    logger.warning("No LLM API keys configured. Falling back to Mock LLM Provider.")
    return MockLLMProvider()
