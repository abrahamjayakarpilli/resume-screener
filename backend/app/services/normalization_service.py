from typing import Dict, Any

class SkillNormalizationService:
    # Strict canonical skill mapping
    CANONICAL_MAP = {
        "python": "Python",
        "py": "Python",
        
        "javascript": "JavaScript",
        "js": "JavaScript",
        "es6": "JavaScript",
        
        "typescript": "TypeScript",
        "ts": "TypeScript",
        
        "fastapi": "FastAPI",
        
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "pg": "PostgreSQL",
        
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        
        "docker": "Docker",
        
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        
        "aws": "AWS",
        "amazon web services": "AWS",
        
        "gcp": "GCP",
        "google cloud": "GCP",
        "azure": "Azure",
        
        "node": "Node.js",
        "nodejs": "Node.js",
        
        "react": "React",
        "reactjs": "React",
        "react.js": "React",
        
        "vue": "Vue.js",
        "vuejs": "Vue.js",
        
        "rest api": "REST APIs",
        "restful api": "REST APIs",
        "restful apis": "REST APIs",
        "rest apis": "REST APIs",
        
        "git": "Git",
        "github": "Git",
        
        "html": "HTML",
        "css": "CSS",
        "sass": "CSS",
        "tailwind": "Tailwind CSS",
        "tailwindcss": "Tailwind CSS"
    }

    # Default category mapping based on normalized skill names
    CATEGORY_MAP = {
        "Python": "Programming Language",
        "JavaScript": "Programming Language",
        "TypeScript": "Programming Language",
        "Go": "Programming Language",
        "Rust": "Programming Language",
        "Java": "Programming Language",
        "C++": "Programming Language",
        
        "FastAPI": "Backend Framework",
        "Django": "Backend Framework",
        "Flask": "Backend Framework",
        "Node.js": "Backend Framework",
        "Spring Boot": "Backend Framework",
        
        "React": "Frontend Framework",
        "Vue.js": "Frontend Framework",
        "Angular": "Frontend Framework",
        
        "PostgreSQL": "Database",
        "MySQL": "Database",
        "MongoDB": "Database",
        "Redis": "Database",
        "SQLite": "Database",
        
        "AWS": "Cloud Provider",
        "GCP": "Cloud Provider",
        "Azure": "Cloud Provider",
        
        "Docker": "DevOps / Infrastructure",
        "Kubernetes": "DevOps / Infrastructure",
        "Git": "Tools",
        "REST APIs": "Architecture Pattern",
        "Tailwind CSS": "UI Design"
    }

    @classmethod
    def normalize(cls, skill_name: str) -> Dict[str, Any]:
        """Normalize a skill string into canonical_name and category"""
        clean_name = skill_name.strip().lower()
        
        # Check canonical mapping
        canonical_name = cls.CANONICAL_MAP.get(clean_name)
        if not canonical_name:
            # Title-case fallback to preserve capitalization
            # e.g., "pandas" -> "Pandas"
            canonical_name = skill_name.strip().title()
        
        # Determine category
        category = cls.CATEGORY_MAP.get(canonical_name, "Other Technology")
        
        return {
            "canonical_name": canonical_name,
            "category": category
        }
