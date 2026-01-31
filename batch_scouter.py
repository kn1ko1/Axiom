import os
import time
import csv
from engine import AxiomEngine

RESUME_DIR = './resumes/'
LEADERBOARD = 'leaderboard.csv'
JD_PATH = 'job_description.txt'  # You can change this if needed
MAX_RETRIES = 5
BACKOFF_BASE = 5  # seconds

# Load job description
if not os.path.exists(JD_PATH):
    raise FileNotFoundError(f"Job description file '{JD_PATH}' not found.")
with open(JD_PATH, 'r', encoding='utf-8') as f:
    job_description = f.read().strip()

engine = AxiomEngine()
results = []

for filename in os.listdir(RESUME_DIR):
    if not filename.lower().endswith('.pdf'):
        continue
    pdf_path = os.path.join(RESUME_DIR, filename)
    print(f"Processing: {filename}")
    retries = 0
    while retries <= MAX_RETRIES:
        text = engine.extract_text(pdf_path)
        try:
            verdict = engine.quick_sweep(text, job_description)
            # Try to parse JSON result
            import json
            data = json.loads(verdict)
            score = data.get('score', 0)
            rationale = data.get('rationale', 'No rationale provided.')
            results.append({'filename': filename, 'score': score, 'rationale': rationale})
            break  # Success, move to next file
        except Exception as e:
            # Check for quota/rate limit error
            if 'RESOURCE_EXHAUSTED' in str(e) or 'quota' in str(e) or '429' in str(e):
                wait_time = BACKOFF_BASE * (2 ** retries)
                print(f"429/Quota error. Backing off for {wait_time}s (attempt {retries+1}/{MAX_RETRIES})...")
                time.sleep(wait_time)
                retries += 1
            else:
                print(f"Error processing {filename}: {e}")
                results.append({'filename': filename, 'score': 0, 'rationale': f'Error: {e}'})
                break
    else:
        print(f"Max retries exceeded for {filename}. Skipping.")
        results.append({'filename': filename, 'score': 0, 'rationale': 'Max retries exceeded.'})

# Sort leaderboard by score descending
results.sort(key=lambda x: x['score'], reverse=True)

with open(LEADERBOARD, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['filename', 'score', 'rationale'])
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"Leaderboard written to {LEADERBOARD}")
