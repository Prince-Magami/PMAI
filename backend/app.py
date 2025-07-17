from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cohere
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cohere setup
cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

# VirusTotal setup
virustotal_api_key = os.getenv("VIRUSTOTAL_API_KEY")
vt_headers = {
    "x-apikey": virustotal_api_key
}

# Pydantic Schema
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# Prompt Builder
def build_prompt(mode: str, lang: str, user_input: str):
    prompt_map = {
        "chat": "You are a friendly AI chatbot.",
        "scan": "You are a cybersecurity analyst. Scan the given link or email and explain the risk involved in clear terms.",
        "edu": "You are an academic advisor helping students understand their subjects and prepare for exams.",
        "cyber": "You are a cybersecurity assistant giving general cyber hygiene tips and answering related questions."
    }
    lang_note = "Respond only in Nigerian Pidgin." if lang == "pidgin" else "Respond in clear English."
    return f"""{prompt_map.get(mode, 'You are an AI.')}\n{lang_note}\nUser: {user_input}\nAI:"""

# VirusTotal Logic
def scan_with_virustotal(user_input: str):
    if user_input.startswith("http"):
        url_id = requests.utils.quote(user_input, safe='')
        url_report = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        response = requests.get(url_report, headers=vt_headers)
        if response.status_code == 200:
            data = response.json()
            stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            harmless = stats.get("harmless", 0)
            suspicious = stats.get("suspicious", 0)
            total = malicious + harmless + suspicious
            trust = round((harmless / total) * 100) if total > 0 else 0
            return f"**Link Scan Report**:\n- Harmless: {harmless}\n- Malicious: {malicious}\n- Suspicious: {suspicious}\n- Trust Score: {trust}%"
        else:
            return "Unable to scan the link at the moment. Please try again later."
    
    else:
        response = requests.get(f"https://www.virustotal.com/api/v3/search?query={user_input}", headers=vt_headers)
        if response.status_code == 200:
            results = response.json().get("data", [])
            if results:
                danger_tags = set()
                for item in results:
                    tags = item.get("attributes", {}).get("tags", [])
                    danger_tags.update(tags)
                if danger_tags:
                    return f"**Email Scan Report**:\n- Possible Risks Detected: {', '.join(danger_tags)}\n- ⚠This email may be used in phishing or other attacks."
                else:
                    return "**Email Scan Report**:\n- No major threats detected from this email."
            else:
                return "**Email Scan Report**:\n- No records found. Likely safe."
        else:
            return "Unable to scan the email. Please check the format or try again later."

# Main Chat Route
@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    if payload.mode == "scan":
        user_input = payload.message.strip()
        vt_api_key = os.getenv("VT_API_KEY")
        headers = {"x-apikey": vt_api_key}
    
        if "@" in user_input:
            scan_type = "email"
            domain = user_input.split("@")[-1]
            vt_url = f"https://www.virustotal.com/api/v3/domains/{domain}"
        else:
            scan_type = "url"
            # Clean URL
            if not user_input.startswith("http"):
                user_input = "http://" + user_input
            vt_url = f"https://www.virustotal.com/api/v3/urls"
        
        try:
            if scan_type == "url":
                # Submit URL for analysis
                submit_resp = requests.post(vt_url, headers=headers, data={"url": user_input})
                scan_id = submit_resp.json()["data"]["id"]
                vt_url = f"https://www.virustotal.com/api/v3/analyses/{scan_id}"
                report_resp = requests.get(vt_url, headers=headers)
            else:
                # Email domain reputation
                report_resp = requests.get(vt_url, headers=headers)
            
            report_data = report_resp.json()
            
            # Parse Report
            if scan_type == "url":
                stats = report_data["data"]["attributes"]["stats"]
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless = stats.get("harmless", 0)
                undetected = stats.get("undetected", 0)
                
                total = malicious + suspicious + harmless + undetected
                trust_score = int((harmless / total) * 100) if total > 0 else 0
                
                report = f"""
URL SCAN REPORT

Link: {payload.message}

Trust Score: {trust_score}% Safe {"✅" if trust_score > 80 else "❌"}
Status: {"High Risk" if trust_score < 40 else "Moderate Risk" if trust_score < 80 else "Low Risk"}

Detected Issues:
- {malicious} flagged as malicious
- {suspicious} flagged as suspicious
- {harmless} marked harmless
- {undetected} unknown by engines

Confidence Level: {"EXTREMELY HIGH" if malicious else "MEDIUM"}

Recommendation: {"AVOID OR REPORT THIS LINK" if trust_score < 50 else "Use with Caution "}
""".strip()
            else:
                # EMAIL scan (domain reputation)
                reputation = report_data["data"]["attributes"].get("reputation", 0)
                categories = report_data["data"]["attributes"].get("categories", {})
                trust_score = 50 + reputation * 10
                risk = "High-risk email (Possible phishing attempt)" if trust_score < 50 else "Suspicious Email" if trust_score < 80 else "Likely Safe"

                report = f"""
EMAIL SCAN REPORT

Email: {payload.message}

Trust Score: {trust_score}% Safe {"" if trust_score >= 80 else ""}
Status: {risk}

Detected Issues:
- Domain reputation score: {reputation}
- Categories: {', '.join(categories.values()) if categories else "None detected"}

Confidence Level: {"EXTREMELY HIGH" if trust_score < 30 else "HIGH" if trust_score < 60 else "MEDIUM"}

Recommendation: {"BLOCK & REPORT THIS EMAIL" if trust_score < 50 else "Verify before trusting"}
""".strip()
            return JSONResponse({"reply": report})

        except Exception as e:
            
            fallback_prompt = build_prompt("scan", payload.lang, payload.message)
            response = co.generate(
                model="command-r-plus",
                prompt=fallback_prompt,
                max_tokens=300,
                temperature=0.7,
                stop_sequences=["User:", "AI:"]
            )
            return JSONResponse({"reply": f"VirusTotal scan failed. Here's AI fallback:\n\n{response.generations[0].text.strip()}"})
    
    else:
        # Other modes use Cohere
        prompt = build_prompt(payload.mode, payload.lang, payload.message)
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=300,
            temperature=0.7,
            stop_sequences=["User:", "AI:"]
        )
        return JSONResponse({"reply": response.generations[0].text.strip()})


# Health Check
@app.get("/")
def root():
    return {"message": "PMAI API is running."}
