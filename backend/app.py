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
        result = scan_with_virustotal(payload.message)
        return JSONResponse({"reply": result})

    # All other modes use Cohere
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
