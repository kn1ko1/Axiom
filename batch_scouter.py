import os
import csv
import time
import json
import argparse
from engine import AxiomEngine

# --- CONFIGURATION ---
RESUMES_DIR = "./resumes"
OUTPUT_FILE = "axiom_leaderboard.csv"
MAX_RETRIES = 5
RETRY_WAIT = 30  # seconds
THROTTLE = 2     # seconds between successful calls

def load_job_description(jd_path=None, default_jd=None):
    if jd_path:
        if not os.path.isfile(jd_path):
            raise ValueError(f"Job description path '{jd_path}' is not a file.")
        with open(jd_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    if default_jd:
        return default_jd
    raise ValueError("No job description provided.")

def analyze_resume(axiom, filename, job_description):
    path = os.path.join(RESUMES_DIR, filename)
    print(f"🔍 Analyzing: {filename}...", end=" ", flush=True)

    # Extract text
    text = axiom.extract_text(path)
    if "ERROR" in text:
        print("❌ Extraction Failed.")
        return {
            "name": filename,
            "score": 0,
            "rationale": "Extraction Failed."
        }

    # Get Verdict with Retries for Rate Limits
    retries = 0
    while retries < MAX_RETRIES:
        try:
            raw_response = axiom.quick_sweep(text, job_description)
            verdict = json.loads(raw_response)
            print(f"✅ Scored {verdict.get('score')}")
            time.sleep(THROTTLE)
            return {
                "name": filename,
                "score": verdict.get("score", 0),
                "rationale": verdict.get("rationale", "N/A")
            }
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                retries += 1
                print(f"🚩 Rate limit hit. Cooling down for {RETRY_WAIT}s... (Retry {retries}/{MAX_RETRIES})")
                time.sleep(RETRY_WAIT)
            else:
                print(f"❌ Failed: {str(e)}")
                break
    print(f"❌ Max retries exceeded for {filename}.")
    return {
        "name": filename,
        "score": 0,
        "rationale": "Max retries exceeded or unknown error."
    }

def run_scouter(job_description):
    axiom = AxiomEngine()
    results = []

    # 1. Gather all PDFs
    files = [f for f in os.listdir(RESUMES_DIR) if f.lower().endswith('.pdf')]
    print(f"🚀 Axiom Batch Scouter: Found {len(files)} resumes to audit.")

    for filename in files:
        result = analyze_resume(axiom, filename, job_description)
        results.append(result)

    # 2. Sort and Save (Leaderboard Logic)
    results.sort(key=lambda x: x['score'], reverse=True)

    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "score", "rationale"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n🏆 Batch Complete! Leaderboard saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Axiom Batch Scouter")
    parser.add_argument('--jd', type=str, help="Path to job description text file.")
    parser.add_argument('--jd-text', type=str, help="Job description as a string (overrides file).")
    args = parser.parse_args()

    job_description = load_job_description(args.jd, args.jd_text)
    run_scouter(job_description)
