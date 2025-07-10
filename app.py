# app.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import cohere
import requests

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API Keys
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

co = cohere.Client(COHERE_API_KEY)

# ---------------- MODE HANDLERS ---------------- #

@app.post("/api/chat")
async def chat_handler(request: Request):
    data = await request.json()
    user_input = data.get("message")
    mode = data.get("mode", "chat")
    lang = data.get("lang", "english")

    # Mode switching logic
    if mode == "scan":
        return await handle_scan(user_input)
    elif mode == "edu":
        return await handle_edu(user_input)
    elif mode == "cyber":
        return await handle_cyber(user_input)
    else:
        return await handle_chatbox(user_input, lang)


# Chatbox mode (general AI chat)
async def handle_chatbox(user_input, lang):
    preamble = "Be a friendly and intelligent AI assistant."
    if lang == "pidgin":
        preamble += " Respond in Nigerian Pidgin."

    response = co.chat(
        model="command-r-plus",
        message=user_input,
        preamble=preamble
    )
    return {"reply": response.text.strip()}


# Cybersecurity tips mode
async def handle_cyber(user_input):
    prompt = f"Act like a cybersecurity coach. Explain in simple terms: {user_input}"
    response = co.chat(model="command-r-plus", message=user_input, preamble=prompt)
    return {"reply": response.text.strip()}


# Educational Assistant mode
async def handle_edu(user_input):
    prompt = f"Act like a smart academic tutor. Help with study advice, topics, and clarity: {user_input}"
    response = co.chat(model="command-r-plus", message=user_input, preamble=prompt)
    return {"reply": response.text.strip()}


# Email/Link Scanner using VirusTotal API
async def handle_scan(user_input):
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY
    }
    if "http" in user_input:
        url_id = requests.utils.quote(user_input, safe='')
        vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        r = requests.get(vt_url, headers=headers)
    else:
        r = requests.get(f"https://www.virustotal.com/api/v3/search?query={user_input}", headers=headers)

    if r.status_code == 200:
        data = r.json()
        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        summary = f"🔍 Scan Result:\n\n🛡️ Harmless: {stats.get('harmless', 0)}\n⚠️ Suspicious: {stats.get('suspicious', 0)}\n❌ Malicious: {stats.get('malicious', 0)}\n🧪 Undetected: {stats.get('undetected', 0)}"
        return {"reply": summary}
    else:
        return {"reply": "❌ Unable to scan. Please check the URL or input."}


# ---------------- ROOT ---------------- #

@app.get("/")
def index():
    return {"message": "PMAI AI server running..."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
