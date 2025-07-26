import os
import re
import httpx
import dns.resolver
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Load API Keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

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

def validate_email_mx(email: str):
    domain = email.split('@')[-1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        return False

def format_email_report(email: str, valid_mx: bool, vt_data: dict):
    domain = email.split("@")[1]
    domain_info = vt_data.get("data", {}).get("attributes", {})
    malicious = domain_info.get("last_analysis_stats", {}).get("malicious", 0)

    risk = "High Risk" if malicious > 0 or not valid_mx else "Safe"
    color = "<span style='color:red'>" if risk == "High Risk" else "<span style='color:green'>"

    return f"""
{color}Email: {email}<br>
Status: {risk}<br>
Threats Detected: {malicious}</span>
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
    status = "Safe" if trust_score >= 80 else "Moderate Risk" if trust_score >= 50 else "Not Safe"
    color = "<span style='color:green'>" if status == "Safe" else "<span style='color:red'>"

    return f"""
{color}URL: {url_info.get('url', 'Unknown URL')}<br>
Status: {status}<br>
Trust Score: {trust_score}%</span>
"""

@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    if mode == "email/link scanner":
        if is_email(prompt):
            domain = prompt.split("@")[1]
            vt_domain_scan = await scan_link_with_virustotal(f"http://{domain}")
            valid_mx = validate_email_mx(prompt)
            if vt_domain_scan:
                return {"response": format_email_report(prompt, valid_mx, vt_domain_scan)}
            else:
                return {"response": "<span style='color:red'>Unable to scan email domain.</span>"}

        elif prompt.startswith("http://") or prompt.startswith("https://"):
            vt_link_scan = await scan_link_with_virustotal(prompt)
            if vt_link_scan:
                return {"response": format_link_report(vt_link_scan)}
            else:
                return {"response": "<span style='color:red'>Unable to scan link.</span>"}
        
        return {"response": "<span style='color:red'>Please enter a valid email or URL.</span>"}

    # GEMINI MODE (chat only, not used for scans)
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

