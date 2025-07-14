from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Request Schema
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# Prompt builder
def build_prompt(mode: str, lang: str, user_input: str):
    prompt_map = {
        "chat": "You are a friendly AI chatbot. Answer clearly and helpfully.",
        "scan": "You are a cybersecurity analyst. Scan the provided email or link for threats like phishing, malware, or scams. Explain results in simple language.",
        "edu": "You are an academic coach. Give useful study tips or explain any question clearly.",
        "cyber": "You are a cybersecurity assistant. Explain terms and give practical tips for staying safe online.",
    }
    lang_note = "Use Nigerian Pidgin for your reply." if lang == "pidgin" else "Use clear, simple English."
    return f"{prompt_map.get(mode, 'You are an AI.')}\n{lang_note}\nUser: {user_input}\nAI:"

# Main Chat Route
@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    prompt = build_prompt(payload.mode, payload.lang, payload.message)
    try:
        response = model.generate_content(prompt)
        return JSONResponse({"reply": response.text.strip()})
    except Exception as e:
        print("Error:", e)
        return JSONResponse({"reply": "⚠️ Gemini failed to respond. Check server logs."})

# Root Health Check
@app.get("/")
def root():
    return {"message": "PMAI Gemini API is running."}
