# app.py
# PMAI Backend (FastAPI) - Ultra Optimized

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx, os
import cohere

# ---------- INIT ----------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

co = cohere.Client(os.getenv("COHERE_API_KEY"))

# ---------- MODE ROUTING LOGIC ----------
class ChatInput(BaseModel):
    message: str
    mode: str
    lang: str

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chatpage(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def aboutpage(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.post("/api/chat")
async def chat_handler(data: ChatInput):
    prompt = build_prompt(data.mode, data.lang, data.message)

    if data.mode == "scan":
        async with httpx.AsyncClient() as client:
            headers = {"x-apikey": os.getenv("VIRUSTOTAL_API_KEY")}
            scan_url = f"https://www.virustotal.com/api/v3/urls"
            url_id = httpx.get("https://www.virustotal.com/api/v3/urls/" + data.message)
            response = await client.post(scan_url, data={"url": data.message}, headers=headers)
            result = response.json()
            stats = result.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            return JSONResponse({"reply": f"🔍 Link Scan Result: {stats}"})

    elif data.mode == "edu":
        return JSONResponse({"reply": f"🎓 Academic Assistant: For past questions visit https://myschool.ng or https://pass.ng"})

    elif data.mode == "cyber":
        tips = [
            "🔐 Use 2FA on all your accounts.",
            "🚫 Never reuse passwords.",
            "⚠️ Watch out for phishing emails.",
            "🔍 Regularly update software & apps."
        ]
        import random
        return JSONResponse({"reply": random.choice(tips)})

    else:
        response = co.chat(
            message=data.message,
            model="command-r-plus",
            preamble=prompt
        )
        return JSONResponse({"reply": response.text.strip()})

# ---------- PROMPT BUILDER ----------
def build_prompt(mode, lang, message):
    persona = {
        "chat": "Be helpful, clear, casual and creative.",
        "scan": "Act like a cybersecurity analyst. Give security verdicts for suspicious links.",
        "edu": "Be a smart academic assistant. Answer clearly.",
        "cyber": "Give cybersecurity tips in a friendly manner."
    }.get(mode, "Be helpful.")

    lang_note = "Use only Nigerian Pidgin." if lang == "pidgin" else "Use formal English."
    return f"{persona}\n{lang_note}\nUser: {message}\nAI:"
