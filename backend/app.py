from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API (v1)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-pro")  # ✅ FIXED!

# Initialize FastAPI
app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# Prompt builder
def build_prompt(mode: str, lang: str, user_input: str):
    prompts = {
        "chat": "You are a smart, friendly assistant. Answer clearly and naturally.",
        "scan": "You are a cybersecurity analyst. Scan this link or email for threats (phishing, scam, malware). Give a verdict in plain language.",
        "edu": "You are an education advisor. Give study tips, exam help, and explanations.",
        "cyber": "You are a cybersecurity tutor. Explain terms and give safety tips in simple words.",
    }
    lang_line = "Use Nigerian Pidgin." if lang == "pidgin" else "Use simple, clear English."
    return f"{prompts.get(mode, 'You are an assistant.')}\n{lang_line}\nUser: {user_input}\nAI:"

# API Endpoint
@app.post("/api/chat")
async def chat_with_gemini(payload: ChatRequest):
    prompt = build_prompt(payload.mode, payload.lang, payload.message)
    try:
        response = model.generate_content(prompt)
        return JSONResponse({"reply": response.text.strip()})
    except Exception as e:
        print("Gemini API Error:", e)
        return JSONResponse({"reply": "⚠️ Gemini failed to respond. Check server logs."})

# Root
@app.get("/")
def root():
    return {"message": "PMAI Gemini API is running ✅"}
