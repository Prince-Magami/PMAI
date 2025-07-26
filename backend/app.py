import os
import re
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Load API Keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

def is_email(input_str: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str) is not None

async def scan_link_with_virustotal(link: str):
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        submit_response = await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data=f"url={link}"
        )

        if submit_response.status_code != 200:
            return None

        url_id = submit_response.json().get("data", {}).get("id")
        if not url_id:
            return None

        report_response = await client.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers
        )
        return report_response.json() if report_response.status_code == 200 else None

async def validate_email_with_hunter(email: str):
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json() if response.status_code == 200 else None

def format_email_report(email: str, hunter_data: dict, vt_data: dict):
    score = hunter_data.get("data", {}).get("score", "Unknown")
    result = hunter_data.get("data", {}).get("result", "Unknown")
    domain = email.split("@")[1]
    domain_info = vt_data.get("data", {}).get("attributes", {})
    malicious = domain_info.get("last_analysis_stats", {}).get("malicious", 0)

    risk = "High Risk" if malicious > 0 or result == "undeliverable" else "Safe"

    return f"""
EMAIL SCAN REPORT
------------------
Email: {email}

Hunter Verification: {result.upper()}
Score: {score}/100
VirusTotal Domain Threats: {malicious}

Status: {risk}
Recommendation: {'Do not trust this email' if risk == 'High Risk' else 'No issues detected'}
"""

def format_link_report(scan):
    stats = scan.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    url_info = scan.get("data", {}).get("attributes", {})
    harmless = stats.get("harmless", 0)
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)
    total = harmless + malicious + suspicious + undetected
    trust_score = round((harmless / total) * 100) if total > 0 else 0
    url_display = url_info.get("url", "Unknown URL")
    status = "Very Safe" if trust_score >= 80 else "Moderate Risk" if trust_score >= 50 else "High Risk"
    recommendation = "Use with caution" if trust_score >= 50 else "Avoid this link"

    return f"""
LINK SCAN REPORT
-----------------
URL: {url_display}
Trust Score: {trust_score}%
Malicious: {malicious}, Suspicious: {suspicious}, Harmless: {harmless}, Undetected: {undetected}

Status: {status}
Recommendation: {recommendation}
"""

@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    if mode == "email/link scanner":
        if is_email(prompt):
            domain = prompt.split("@")[1]
            vt_domain_scan = await scan_link_with_virustotal(f"http://{domain}")
            hunter_result = await validate_email_with_hunter(prompt)

            if vt_domain_scan and hunter_result:
                return {"response": format_email_report(prompt, hunter_result, vt_domain_scan)}
            else:
                return {"response": "Unable to scan email at the moment."}

        elif prompt.startswith("http://") or prompt.startswith("https://"):
            scan = await scan_link_with_virustotal(prompt)
            if scan:
                return {"response": format_link_report(scan)}
            else:
                return {"response": "Unable to scan link. Please try again later."}
        else:
            return {"response": "Please enter a valid email or URL."}

    # GEMINI chat mode
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            headers=headers,
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            output = candidates[0]["content"]["parts"][0]["text"] if candidates else "No response from Gemini."
            return {"response": output}
        else:
            return {"response": "Gemini API failed. Please try again."}
