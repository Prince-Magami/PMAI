import os
import re
import httpx
import dns.resolver
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import urlparse, quote

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IPQS_API_KEY = os.getenv("IPQS_API_KEY")

# FastAPI setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

# Utils
def is_email(text: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", text) is not None

def is_url(text: str) -> bool:
    return re.match(r"^(https?:\/\/)?([\w\-]+\.)+[\w\-]+.*$", text) is not None

def extract_domain(url: str) -> str:
    parsed = urlparse(url if url.startswith("http") else f"http://{url}")
    return f"{parsed.scheme}://{parsed.netloc}"

def validate_email_mx(email: str) -> bool:
    domain = email.split('@')[-1].lower()
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        return False

# ✅ Debug-friendly IPQS functions
async def scan_link_with_ipqs(link: str):
    encoded_link = quote(link, safe='')
    url = f"https://ipqualityscore.com/api/json/url/{IPQS_API_KEY}/{encoded_link}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print("=== IPQS RAW URL SCAN RESPONSE ===")
        print(response.status_code)
        print(response.text)
        if response.status_code != 200:
            return None
        data = response.json()
        # ✅ Allow response even if success=False
        return data

async def scan_email_with_ipqs(email: str):
    encoded_email = quote(email, safe='')
    url = f"https://ipqualityscore.com/api/json/email/{IPQS_API_KEY}/{encoded_email}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print("=== IPQS RAW EMAIL SCAN RESPONSE ===")
        print(response.status_code)
        print(response.text)
        if response.status_code != 200:
            return None
        data = response.json()
        # ✅ Allow response even if success=False
        return data

# Formatters with fallback
def format_email_report(email: str, valid_mx: bool, ipqs_data: dict) -> str:
    fraud_score = ipqs_data.get("fraud_score", 0)
    valid = ipqs_data.get("valid", False)
    risk = "High Risk" if fraud_score >= 75 or not valid_mx or not valid else "Safe"
    color = "<span style='color:red'>" if risk == "High Risk" else "<span style='color:green'>"
    return f"{color}Status: {risk}</span>"

def format_link_report(scan: dict) -> str:
    risk_score = scan.get("risk_score", 0)
    trust_score = 100 - risk_score
    status = "Safe" if trust_score >= 80 else "Moderate Risk" if trust_score >= 50 else "Not Safe"
    color = "<span style='color:green'>" if status == "Safe" else "<span style='color:red'>"
    return f"{color}Status: {status}<br>Trust Score: {trust_score}%</span>"

# Main AI logic
@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    if mode == "email/link scanner":
        if is_email(prompt):
            ipqs_result = await scan_email_with_ipqs(prompt)
            valid_mx = validate_email_mx(prompt)
            if ipqs_result:
                return {"response": format_email_report(prompt, valid_mx, ipqs_result)}
            else:
                return {
                    "response": "<span style='color:red'>Scan failed or could not analyze this email. It may be too new, private, or malformed.</span>"
                }

        elif is_url(prompt):
            clean_url = extract_domain(prompt)
            scan_result = await scan_link_with_ipqs(clean_url)
            if scan_result:
                return {"response": format_link_report(scan_result)}
            else:
                return {
                    "response": "<span style='color:red'>Scan failed or could not analyze this link. It may be too new, private, or malformed.</span>"
                }

        else:
            return {"response": "Please enter a valid email or URL."}

    # Gemini fallback
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            headers=headers,
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            output = candidates[0]["content"]["parts"][0]["text"] if candidates else "No response from Gemini."
            return {"response": output}
        else:
            return {"response": "Gemini API failed. Please try again."}

# Alias route
@app.post("/api/chat")
async def alias_chat_route(req: dict):
    prompt = req.get("message", "").strip()
    mode = req.get("mode", "").strip().lower()
    lang = req.get("lang", "").strip().lower()

    if mode == "scan":
        mode = "email/link scanner"

    proxy_req = PromptRequest(prompt=prompt, mode=mode, language=lang)
    return await ask_ai(proxy_req)
