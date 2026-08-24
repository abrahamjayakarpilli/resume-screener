import os

class Config:
    # Server configuration
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    
    # DB URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./talentlens.db")
    
    # LLM Settings
    MOCK_LLM: bool = os.getenv("MOCK_LLM", "true").lower() in ("true", "1", "yes")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Weight Configurations
    WEIGHT_TECH: float = float(os.getenv("SCORING_WEIGHT_TECH", 0.40))
    WEIGHT_EXP: float = float(os.getenv("SCORING_WEIGHT_EXP", 0.30))
    WEIGHT_PROJ: float = float(os.getenv("SCORING_WEIGHT_PROJ", 0.15))
    WEIGHT_EDU: float = float(os.getenv("SCORING_WEIGHT_EDU", 0.10))
    WEIGHT_OTHER: float = float(os.getenv("SCORING_WEIGHT_OTHER", 0.05))

    @classmethod
    def get_weights(cls):
        # Ensure weights are normalized to sum to 1.0
        total = cls.WEIGHT_TECH + cls.WEIGHT_EXP + cls.WEIGHT_PROJ + cls.WEIGHT_EDU + cls.WEIGHT_OTHER
        if abs(total - 1.0) > 1e-5:
            return {
                "tech": cls.WEIGHT_TECH / total,
                "exp": cls.WEIGHT_EXP / total,
                "proj": cls.WEIGHT_PROJ / total,
                "edu": cls.WEIGHT_EDU / total,
                "other": cls.WEIGHT_OTHER / total,
            }
        return {
            "tech": cls.WEIGHT_TECH,
            "exp": cls.WEIGHT_EXP,
            "proj": cls.WEIGHT_PROJ,
            "edu": cls.WEIGHT_EDU,
            "other": cls.WEIGHT_OTHER,
        }

settings = Config()
