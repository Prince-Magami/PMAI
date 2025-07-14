from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import google.generativeai as genai

# ✅ Load env variables
load_dotenv()

# ✅ FastAPI App
app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# ✅ Pydantic Schema
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# ✅ Prompt Builder
def build_prompt(mode: str, lang: str, user_input: str):
    prefix_map = {
        "chat": "You are a friendly AI chatbot for general conversations and questions.",
        "scan": "You are a security analyst. Scan links and emails for phishing, malware, or fraud.",
        "edu": "You are an academic assistant. Give helpful study advice, explanations, and motivation.",
        "cyber": "You are a cybersecurity guide. Share tips on online safety in very simple language."
    }
    lang_note = "Respond only in Nigerian Pidgin." if lang == "pidgin" else "Respond in clear English."
    return f"""{prefix_map.get(mode, 'You are an AI.')}\n{lang_note}\nUser: {user_input}\nAI:"""

# ✅ AI Response Function
def ask_gemini(prompt: str):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini API Error:", e)
        return "❌ Error reaching AI model."

# ✅ Main Chat Endpoint
@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    user_input = payload.message
    mode = payload.mode
    lang = payload.lang

    # ✅ Special case: Link/Email Scanner using VirusTotal
    if mode == "scan":
        if user_input.startswith("http"):
            vt_key = os.getenv("VIRUSTOTAL_API_KEY")
            headers = {"x-apikey": vt_key}
            try:
                url_id = requests.utils.quote(user_input, safe='')
                vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
                resp = requests.get(vt_url, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    categories = data.get("data", {}).get("attributes", {}).get("categories", {})
                    total = sum(stats.values())
                    malicious = stats.get("malicious", 0)
                    harmless = stats.get("harmless", 0)
                    percent = round((malicious / total) * 100) if total else 0

                    verdict = "❗️Avoid visiting this link." if percent >= 40 else "✅ Link seems safe but always be cautious."
                    reply = (
                        f"🔗 Scanned URL: {user_input}\n"
                        f"🔴 Malicious: {malicious}\n🟢 Harmless: {harmless}\n"
                        f"⚠️ Threat Score: {percent}%\n"
                        f"📂 Category: {', '.join(categories.values()) or 'Unknown'}\n"
                        f"Verdict: {verdict}"
                    )
                    return JSONResponse({"reply": reply})
                else:
                    return JSONResponse({"reply": "⚠️ VirusTotal scan failed. Try again later."})
            except Exception as e:
                return JSONResponse({"reply": f"❌ Error scanning link: {str(e)}"})

        else:
            # It's an email-like text, so ask Gemini
            prompt = build_prompt("scan", lang, user_input)
            reply = ask_gemini(prompt)
            return JSONResponse({"reply": reply})

    # ✅ Default AI Modes
    prompt = build_prompt(mode, lang, user_input)
    reply = ask_gemini(prompt)
    return JSONResponse({"reply": reply})

# ✅ Root Health Check
@app.get("/")
def root():
    return {"message": "✅ PMAI backend with Gemini is running"}
