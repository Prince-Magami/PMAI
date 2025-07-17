import os
import re
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import cohere 

load_dotenv()

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

# Request model
class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

# Function to check if it's a valid email
def is_email(input_str: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str) is not None

# VirusTotal URL scanner
async def scan_link_with_virustotal(link: str):
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data=f"url={link}"
        )
        if response.status_code == 200:
            analysis_id = response.json()["data"]["id"]
            report = await client.get(
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers=headers
            )
            return report.json()
        return None

# VirusTotal email detection logic (simulate phishing checks)
async def scan_email(email: str):
    domain = email.split('@')[-1].lower()
    result = {
        "email": email,
        "trust_score": 100,
        "status": "Safe",
        "issues": [],
        "confidence": "HIGH",
        "recommendation": "No Action Needed ✅"
    }

    issues = []

    # Detect impersonation of known services
    impersonated_domains = ["paypal.com", "google.com", "apple.com", "facebook.com"]
    for legit in impersonated_domains:
        if legit != domain and legit.replace('.', '') in domain.replace('.', ''):
            issues.append(f"🧠 Impersonation of \"{legit}\"")
            result["trust_score"] -= 35

    if re.search(r"\d|paypa1|go0gle|faceb00k", domain):
        issues.append("🔍 Unusual spelling in domain name")
        result["trust_score"] -= 30

    if "tracking" in email or "mailer@" in email:
        issues.append("💬 Email header contains masked tracking")
        result["trust_score"] -= 20

    if result["trust_score"] < 60:
        result["status"] = "High-risk email (Possible phishing attempt)"
        result["confidence"] = "EXTREMELY HIGH"
        result["recommendation"] = "BLOCK & REPORT THIS EMAIL 🚫"

    result["issues"] = issues
    return result

# Format for email report
def format_email_report(scan):
    return f"""📧 EMAIL SCAN REPORT

✉️ Email: {scan['email']}

✅ Trust Score: {scan['trust_score']}% Safe {"✅" if scan['trust_score'] >= 60 else "❌"}
⚠️ Status: {scan['status']}

🧪 Detected Issues:
{''.join(f"- {issue}\n" for issue in scan['issues']) if scan['issues'] else "- None"}

📊 Confidence Level: {scan['confidence']}

🛡️ Recommendation: {scan['recommendation']}"""

# Format for link report
def format_link_report(scan):
    stats = scan.get("data", {}).get("attributes", {}).get("stats", {})
    harmless = stats.get("harmless", 0)
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    total = harmless + malicious + suspicious + stats.get("undetected", 0) + 1

    trust_score = round((harmless / total) * 100)

    result = f"""🔗 LINK SCAN REPORT

🌍 URL: {scan.get('meta', {}).get('url_info', {}).get('url', 'N/A')}

✅ Trust Score: {trust_score}% Safe {"✅" if trust_score >= 60 else "❌"}
⚠️ Status: {"Malicious or Suspicious" if trust_score < 60 else "Likely Safe"}

🧪 Reported:
- 🧨 Malicious: {malicious}
- 🚧 Suspicious: {suspicious}
- 🛡️ Harmless: {harmless}

📊 Confidence Level: {"HIGH" if trust_score >= 70 else "LOW"}

🛡️ Recommendation: {"AVOID THIS LINK 🚫" if trust_score < 60 else "Looks Safe ✅"}"""

    return result

# Main AI logic
@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    # === MODE: EMAIL/LINK SCANNER ===
    if mode == "email/link scanner":
        if is_email(prompt):
            result = await scan_email(prompt)
            return {"response": format_email_report(result)}
        elif prompt.startswith("http://") or prompt.startswith("https://"):
            scan = await scan_link_with_virustotal(prompt)
            if scan:
                return {"response": format_link_report(scan)}
            else:
                return {"response": "❌ Unable to scan link. Please try again later."}
        else:
            return {"response": "⚠️ Please enter a valid email or URL."}

    # === FALLBACK TO DEFAULT (COHERE AI) ===
    if not COHERE_API_KEY:
        return {"response": "Cohere API key not set."}

    cohere_url = "https://api.cohere.ai/v1/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(cohere_url, headers=headers, json={"message": prompt})
        if res.status_code == 200:
            output = res.json().get("text") or res.json().get("response")
            return {"response": output}
        else:
            return {"response": "❌ AI response failed. Please try again."}
