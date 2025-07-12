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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pmai-brac-9swaa96oh-abubakar-magamis-projects.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

# ----------- Request Schema ----------- #
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# ----------- Util Functions ----------- #
def build_prompt(mode: str, lang: str, user_input: str):
    prompt_map = {
        "chat": "You are a friendly AI chatbot.",
        "scan": "You are a cybersecurity analyst. Scan the given link or email and explain the risk involved in clear terms.",
        "edu": "You are an academic advisor helping students understand their subjects and prepare for exams.",
        "cyber": "You are a cybersecurity assistant giving general cyber hygiene tips and answering related questions."
    }
    lang_note = "Respond only in Nigerian Pidgin." if lang == "pidgin" else "Respond in clear English."
    return f"""{prompt_map.get(mode, 'You are an AI.')}
{lang_note}
User: {user_input}
AI:"""

# ----------- Main AI Endpoint ----------- #
@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    user_input = payload.message
    mode = payload.mode
    lang = payload.lang

    # ------- Email/Link Scan Mode ------- #
    if mode == "scan":
        virus_total_key = os.getenv("VIRUSTOTAL_API_KEY")
        headers = {"x-apikey": virus_total_key}

        if user_input.startswith("http"):
            url_id = requests.utils.quote(user_input, safe='')
            vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            resp = requests.get(vt_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                categories = data.get("data", {}).get("attributes", {}).get("categories", {})
                total = sum(score.values())
                malicious = score.get("malicious", 0)
                harmless = score.get("harmless", 0)
                pct_malicious = round((malicious / total) * 100) if total else 0

                reply = f"Scanned URL: {user_input}\nMalicious: {malicious}\nHarmless: {harmless}\nThreat Score: {pct_malicious}%\nCategory: {', '.join(categories.values()) or 'Unknown'}\nVerdict: {'Avoid visiting this site.' if pct_malicious >= 40 else 'Link seems okay but be cautious.'}"
                return JSONResponse({"reply": reply})
            else:
                return JSONResponse({"reply": "Could not analyze the link. Please try again."})

        else:
            scan_prompt = build_prompt("scan", lang, user_input)
            result = cohere_client.chat(model="command-r-plus", message=user_input, preamble=scan_prompt)
            return JSONResponse({"reply": result.text.strip()})

    # ------- Education Mode (Show Tips or Respond) ------- #
    elif mode == "edu":
        edu_prompt = build_prompt("edu", lang, user_input)
        result = cohere_client.chat(model="command-r-plus", message=user_input, preamble=edu_prompt)
        return JSONResponse({"reply": result.text.strip()})

    # ------- Cyber Mode ------- #
    elif mode == "cyber":
        cyber_prompt = build_prompt("cyber", lang, user_input)
        result = cohere_client.chat(model="command-r-plus", message=user_input, preamble=cyber_prompt)
        return JSONResponse({"reply": result.text.strip()})

    # ------- Chat Mode (Default) ------- #
    else:
        default_prompt = build_prompt("chat", lang, user_input)
        result = cohere_client.chat(model="command-r-plus", message=user_input, preamble=default_prompt)
        return JSONResponse({"reply": result.text.strip()})

# ----------- Root Test ----------- #
@app.get("/")
def root():
    return {"message": "PMAI API is running."}
