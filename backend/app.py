import os
import re
import base64
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import cohere

load_dotenv()

app = FastAPI()

# Allow all CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

# Email check
def is_email(input_str: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str) is not None

# --- VirusTotal LINK SCAN ---
async def scan_link_with_virustotal(link: str):
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        # Submit the URL
        submit_response = await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data=f"url={link}"
        )

        if submit_response.status_code != 200:
            return None

        url_id = submit_response.json().get("data", {}).get("id")

        # Get full report using /urls/{id} (not /analyses)
        report_response = await client.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers
        )

        if report_response.status_code == 200:
            return report_response.json()
        return None

# --- Email SCAN logic ---
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

    # Impersonation check
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

# --- Email Report Format ---
def format_email_report(scan):
    return f"""📧 EMAIL SCAN REPORT

✉️ Email: {scan['email']}

✅ Trust Score: {scan['trust_score']}% Safe {"✅" if scan['trust_score'] >= 60 else "❌"}
⚠️ Status: {scan['status']}

🧪 Detected Issues:
{''.join(f"- {issue}\n" for issue in scan['issues']) if scan['issues'] else "- None"}

📊 Confidence Level: {scan['confidence']}

🛡️ Recommendation: {scan['recommendation']}"""

# --- Link Report Format ---
def format_link_report(scan):
    stats = scan.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    url_info = scan.get("data", {}).get("attributes", {})
    harmless = stats.get("harmless", 0)
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)
    total = harmless + malicious + suspicious + undetected + 1
    trust_score = round((harmless / total) * 100)

    url_display = url_info.get("url", "Unknown URL")

    if trust_score >= 80:
        status = "✅ Very Safe"
        level = "LOW"
        recommendation = "You can trust this link ✅"
    elif trust_score >= 50:
        status = "⚠️ Moderate Risk"
        level = "MEDIUM"
        recommendation = "Use with caution ⚠️"
    else:
        status = "❌ High Risk"
        level = "EXTREMELY HIGH"
        recommendation = "AVOID THIS LINK 🚫"

    return f"""🔗 LINK SCAN REPORT

🌐 URL: {url_display}

🛡️ Trust Score: {trust_score}% Safe {status}
⚠️ Status: {status}

🧪 Detected Issues:
- 🔴 Malicious: {malicious}
- 🟠 Suspicious: {suspicious}
- 🟢 Harmless: {harmless}
- ⚪ Undetected: {undetected}

📊 Confidence Level: {level}

🧠 Recommendation: {recommendation}"""

# === MAIN AI HANDLER ===
@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

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

    # === COHERE fallback ===
    if not COHERE_API_KEY:
        return {"response": "Cohere API key not set."}

    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.cohere.ai/v1/chat",
            headers=headers,
            json={"message": prompt}
        )
        if res.status_code == 200:
            output = res.json().get("text") or res.json().get("response")
            return {"response": output}
        else:
            return {"response": "❌ AI response failed. Please try again."}
