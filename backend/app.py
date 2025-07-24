import os
import re
import base64
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import cohere


load_dotenv()


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


COHERE_API_KEY = os.getenv("COHERE_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")


class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

def is_email(input_str: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str) is not None


async def scan_link_with_virustotal(link: str):
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Submit the URL for analysis
        submit_response = await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data=f"url={link}"
        )

        
        if submit_response.status_code != 200:
            print(f"Error submitting URL to VirusTotal: {submit_response.status_code} - {submit_response.text}")
            return None

     
        url_id = submit_response.json().get("data", {}).get("id")
        if not url_id:
            print("No URL ID found in VirusTotal submission response.")
            return None

        
        report_response = await client.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers
        )

    
        if report_response.status_code == 200:
            return report_response.json()
        else:
            print(f"Error retrieving VirusTotal report: {report_response.status_code} - {report_response.text}")
            return None


async def scan_email(email: str):
    domain = email.split('@')[-1].lower()
    result = {
        "email": email,
        "trust_score": 100,  
        "status": "Safe",
        "issues": [],
        "confidence": "HIGH",
        "recommendation": "No Action Needed"
    }

    issues = []


    impersonated_domains = ["paypal.com", "google.com", "apple.com", "facebook.com"]
    for legit in impersonated_domains:
        
        if legit != domain and legit.replace('.', '') in domain.replace('.', ''):
            issues.append(f"Impersonation of \"{legit}\"")
            result["trust_score"] -= 35  

    if re.search(r"\d|paypa1|go0gle|faceb00k", domain):
        issues.append("Unusual spelling in domain name")
        result["trust_score"] -= 30

  
    if "tracking" in email or "mailer@" in email:
        issues.append("Email header contains masked tracking")
        result["trust_score"] -= 20  

    
    if result["trust_score"] < 60:
        result["status"] = "High-risk email (Possible phishing attempt)"
        result["confidence"] = "EXTREMELY HIGH"
        result["recommendation"] = "BLOCK & REPORT THIS EMAIL"

    result["issues"] = issues 
    return result


def format_email_report(scan):
    return f""" EMAIL SCAN REPORT

Email: {scan['email']}

Trust Score: {scan['trust_score']}% Safe {"✅" if scan['trust_score'] >= 60 else "❌"}
Status: {scan['status']}

Detected Issues:
{''.join(f"- {issue}\\n" for issue in scan['issues']) if scan['issues'] else "- None"}

Confidence Level: {scan['confidence']}

Recommendation: {scan['recommendation']}"""


def format_link_report(scan):
    stats = scan.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    url_info = scan.get("data", {}).get("attributes", {})

    harmless = stats.get("harmless", 0)
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)

   
    total = harmless + malicious + suspicious + undetected
    if total == 0:
        trust_score = 0
    else:
        trust_score = round((harmless / total) * 100)

    url_display = url_info.get("url", "Unknown URL")

   
    status = ""
    confidence = ""
    recommendation = ""

    if trust_score >= 80:
        status = "Very Safe"
        confidence = "LOW"
        recommendation = "You can trust this link"
    elif trust_score >= 50:
        status = "Moderate Risk"
        confidence = "MEDIUM"
        recommendation = "Use with caution "
    else:
        status = "High Risk"
        confidence = "EXTREMELY HIGH"
        recommendation = "AVOID THIS LINK"

 
    html_report = f"""
    <h3>LINK SCAN REPORT</h3>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td><strong>URL:</strong></td>
            <td>{url_display}</td>
        </tr>
        <tr>
            <td><strong>Trust Score:</strong></td>
            <td>{trust_score}% Safe</td>
        </tr>
        <tr>
            <td><strong>Status:</strong></td>
            <td>{status}</td>
        </tr>
        <tr>
            <td><strong>Confidence Level:</strong></td>
            <td>{confidence}</td>
        </tr>
    </table>

    <h4>Detected Issues</h4>
    <ul>
        <li>Malicious: {malicious}</li>
        <li>Suspicious: {suspicious}</li>
        <li>Harmless: {harmless}</li>
        <li>Undetected: {undetected}</li>
    </ul>

    <p><strong>Recommendation:</strong> <span style="color:red; font-weight:bold;">{recommendation}</span></p>
    """
    return html_report

# MAIN AI HANDLER 
@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    #  "email/link scanner" mode
    if mode == "email/link scanner":
        if is_email(prompt):
            result = await scan_email(prompt)
            return {"response": format_email_report(result)}
        elif prompt.startswith("http://") or prompt.startswith("https://"):
            scan = await scan_link_with_virustotal(prompt)
            if scan:
                return {"response": format_link_report(scan)}
            else:
                return {"response": "Unable to scan link. Please try again later."}
        else:
            # If the prompt is neither a valid email nor a URL
            return {"response": "Please enter a valid email or URL."}

    # COHERE fallback 
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.cohere.ai/v1/chat",
            headers=headers,
            json={"message": prompt}
        )
        if res.status_code == 200:
            output = res.json().get("text") or res.json().get("response")
            return {"response": output}
        else:
            print(f"Cohere API error: {res.status_code} - {res.text}")
            return {"response": "AI response failed. Please try again."}
