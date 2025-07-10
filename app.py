# app.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import cohere
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COHERE_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_KEY)

class Message(BaseModel):
    prompt: str
    mode: str
    lang: str

@app.post("/chat")
async def chat_router(data: Message):
    prompt = data.prompt
    mode = data.mode
    lang = data.lang

    if mode == "chat":
        return chat_response(prompt, lang)
    elif mode == "scan":
        return scan_url_response(prompt)
    elif mode == "edu":
        return academic_advice_response(prompt)
    elif mode == "cyber":
        return cybersecurity_tip_response(prompt)
    else:
        return {"response": "Invalid mode selected."}

def chat_response(prompt, lang):
    suffix = " (reply in Pidgin English)" if lang == "pidgin" else ""
    response = co.chat(message=prompt + suffix)
    return {"response": response.text}

def scan_url_response(input_text):
    # Example only: You should integrate a real scanning service
    virus_total_api_key = os.getenv("VIRUSTOTAL_API_KEY")
    headers = {"x-apikey": virus_total_api_key}

    if input_text.startswith("http"):
        url = f"https://www.virustotal.com/api/v3/urls"
        resp = requests.post(url, data={"url": input_text}, headers=headers).json()
        scan_id = resp.get("data", {}).get("id")

        if scan_id:
            report = requests.get(f"https://www.virustotal.com/api/v3/analyses/{scan_id}", headers=headers).json()
            stats = report.get("data", {}).get("attributes", {}).get("stats", {})
            return {"response": f"Scan Results: {stats}"}
    return {"response": "Invalid URL or scan failed."}

def academic_advice_response(prompt):
    # Simple placeholder advice
    links = "https://myschool.ng/classroom/"
    return {"response": f"To prepare well, practice past WAEC/NECO/JAMB questions here: {links}.\nTip: Set a timetable, revise topics weekly, and test yourself."}

def cybersecurity_tip_response(prompt):
    tips = [
        "Use strong, unique passwords for all accounts.",
        "Avoid clicking links in unknown emails.",
        "Keep your software up to date.",
        "Enable two-factor authentication."
    ]
    return {"response": tips[len(prompt) % len(tips)]}
