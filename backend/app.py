from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cohere
import os
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# ✅ DEFINE THE APP FIRST
app = FastAPI()

# ✅ CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Setup Cohere
cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

# ✅ Pydantic Schema
class ChatRequest(BaseModel):
    message: str
    mode: str
    lang: str = "english"

# ✅ Prompt Builder
def build_prompt(mode: str, lang: str, user_input: str):
    prompt_map = {
        "chat": "You are a friendly AI chatbot.",
        "scan": "You are a cybersecurity analyst. Scan the given link or email and explain the risk involved in clear terms.",
        "edu": "You are an academic advisor helping students understand their subjects and prepare for exams.",
        "cyber": "You are a cybersecurity assistant giving general cyber hygiene tips and answering related questions."
    }
    lang_note = "Respond only in Nigerian Pidgin." if lang == "pidgin" else "Respond in clear English."
    return f"""{prompt_map.get(mode, 'You are an AI.')}\n{lang_note}\nUser: {user_input}\nAI:"""

# ✅ Main Chat Route
@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    prompt = build_prompt(payload.mode, payload.lang, payload.message)
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7,
        stop_sequences=["User:", "AI:"]
    )
    return JSONResponse({"reply": response.generations[0].text.strip()})

# ✅ Health Check
@app.get("/")
def root():
    return {"message": "PMAI API is running."}
