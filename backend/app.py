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
    mode = r
