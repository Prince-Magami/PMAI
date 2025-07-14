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

# Cohere
cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.Client(cohere_api_key)

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

# Main Chat Route
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
    
@app.get("/api/flashcards")
async def get_flashcards(mode: str):
    flashcard_prompt = {
        "edu": "Give 3 short academic study tips or motivation as separate lines.",
        "cyber": "Give 3 short cybersecurity tips or advice in simple layman's terms as separate lines."
    }

    prompt = flashcard_prompt.get(mode, "")
    if not prompt:
        return JSONResponse({"flashcards": []})

    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7,
            stop_sequences=["User:", "AI:"]
        )
        cards = response.generations[0].text.strip().split("\n")
        return JSONResponse({"flashcards": [c.strip("-• ") for c in cards if c.strip()]})
    except Exception as e:
        print("Flashcard error:", e)
        return JSONResponse({"flashcards": []})

# Health Check
@app.get("/")
def root():
    return {"message": "PMAI API is running."}
