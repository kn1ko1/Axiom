from engine import AxiomEngine

# 1. Setup the Engine
axiom = AxiomEngine()

# 2. Define a fake Job Description
sample_jd = "Senior Product Manager with experience in AI B2B tools and SaaS scaling."

# 3. Path to your test resume
# Note: You need to drop a PDF named 'test.pdf' into your resumes folder!
resume_path = "./resumes/test.pdf"

print("🚀 Axiom is analyzing...")

try:
    text = axiom.extract_text(resume_path)
    verdict = axiom.quick_sweep(text, sample_jd)
    print("\n--- THE VERDICT ---")
    print(verdict)
except FileNotFoundError:
    print("🚩 ERROR: No resume found. Please put a 'test.pdf' in the resumes folder.")
    