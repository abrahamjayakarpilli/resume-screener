import re
from io import BytesIO
from pypdf import PdfReader
from app.schemas.schemas import ExtractedResumeProfile

class ParserService:
    @staticmethod
    def extract_text(file_content: bytes, filename: str) -> str:
        """Extract text based on file format (PDF or text)"""
        if filename.endswith(".pdf"):
            try:
                reader = PdfReader(BytesIO(file_content))
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n".join(text_parts)
            except Exception as e:
                raise ValueError(f"Could not parse PDF file {filename}: {str(e)}")
        else:
            # Fallback to UTF-8 text file parsing
            try:
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    return file_content.decode("latin-1")
                except Exception:
                    raise ValueError(f"Could not parse text file {filename}. Ensure encoding is UTF-8 or Latin-1.")

    @staticmethod
    def normalize_text(text: str) -> str:
        """Standardize text by stripping whitespace, excess blank lines and standardizing spaces"""
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Standardize vertical spacing
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    @staticmethod
    def calculate_completeness(profile: ExtractedResumeProfile) -> float:
        """
        Deterministically calculate Candidate Profile Completeness:
        - Email present: 20%
        - Phone present: 20%
        - Summary present: 15%
        - Education records present: 15%
        - Experience records present: 15%
        - Projects list present: 15%
        """
        score = 0.0
        if profile.email:
            score += 20.0
        if profile.phone:
            score += 20.0
        if profile.summary:
            score += 15.0
        if len(profile.educations) > 0:
            score += 15.0
        if len(profile.experiences) > 0:
            score += 15.0
        if len(profile.projects) > 0:
            score += 15.0
        return score
