from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ CORRECT model name
model = genai.GenerativeModel("gemini-pro")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

def build_prompt(mode: str, lang: str, user_input: str):
    prompts = {
        "chat": "You are a smart, friendly assistant. Answer clearly and naturally.",
        "scan": "You are a cybersecurity analyst. Scan this link or email for threats (phishing, scam, malware). Give a verdict in plain language.",
        "edu": "You are an education advisor. Give study tips, exam help, and explanations.",
        "cyber": "You are a cybersecurity tutor. Explain terms and give safety tips in simple words.",
    }
    lang_line = "Use Nigerian Pidgin." if lang == "pidgin" else "Use simple, clear English."
    return f"{prompts.get(mode, 'You are an assistant.')}\n{lang_line}\nUser: {user_input}\nAI:"

@app.post("/api/chat")
async def chat_with_gemini(payload: ChatRequest):
    prompt = build_prompt(payload.mode, payload.lang, payload.message)
    try:
        response = model.generate_content(prompt)
        return JSONResponse({"reply": response.text.strip()})
    except Exception as e:
        print("Gemini API Error:", e)
        return JSONResponse({"reply": "⚠️ Gemini failed to respond. Check server logs."})

@app.get("/")
def root():
    return {"message": "PMAI Gemini API is running ✅"}
