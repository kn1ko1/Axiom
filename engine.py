import pdfplumber
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types # New import for structured config

load_dotenv()

class AxiomEngine:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # Switch back to 2.0-flash but ensure the ID is exactly this:
        self.model_id = 'gemini-2.0-flash'

    def extract_text(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                content = [page.extract_text() for page in pdf.pages[:2]]
                text = " ".join(filter(None, content)).strip()
                
                if not text:
                    return "ERROR: PDF is empty or unreadable (likely an image-based scan)."
                return text
        except Exception as e:
            return f"ERROR: {str(e)}"

    def quick_sweep(self, resume_text, jd):
        if resume_text.startswith("ERROR"):
            return json.dumps({"score": 0, "rationale": resume_text})

        # FORCE JSON MODE using the 2026 SDK config
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0 # Set to 0.0 for maximum consistency
        )

        prompt = f"""
Act as a cynical FCDO Lead Investigator. Audit the candidate against the provided Job Description (JD) below.

SCORING RULES:
1. Technical DNA (ITIL, RCA, Incident Mgmt) is 80% of the score.
2. If Technical DNA is strong but Residency/Citizenship is UNKNOWN, do NOT fail them. Use the 'investigation_required' field.

Output ONLY JSON:
{{
    "score": 1-100,
    "rationale": "One blunt sentence.",
    "investigation_required": "List specific missing eligibility data (e.g. 'Verify British Citizenship') or 'None'.",
    "technical_match": "High/Medium/Low"
}}

JD: {jd}
RESUME: {resume_text}
"""
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
        )
        return response.text

if __name__ == "__main__":
    print("Axiom Engine 2.1 Ready.")
    