import os
import re
import base64
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import cohere

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS middleware to allow all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Retrieve API keys from environment variables
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

# Pydantic model for incoming prompt requests
class PromptRequest(BaseModel):
    prompt: str
    mode: str
    language: str

# Helper function to check if a string is a valid email format
def is_email(input_str: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", input_str) is not None

# --- VirusTotal LINK SCAN ---
# Asynchronously scans a given link using the VirusTotal API
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

        # Check if the submission was successful
        if submit_response.status_code != 200:
            print(f"Error submitting URL to VirusTotal: {submit_response.status_code} - {submit_response.text}")
            return None

        # Extract the analysis ID from the submission response
        url_id = submit_response.json().get("data", {}).get("id")
        if not url_id:
            print("No URL ID found in VirusTotal submission response.")
            return None

        # Step 2: Retrieve the analysis report using the URL ID
        report_response = await client.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers
        )

        # Check if the report retrieval was successful
        if report_response.status_code == 200:
            return report_response.json()
        else:
            print(f"Error retrieving VirusTotal report: {report_response.status_code} - {report_response.text}")
            return None

# --- Email SCAN logic ---
# Scans an email address for potential phishing indicators
async def scan_email(email: str):
    domain = email.split('@')[-1].lower()
    result = {
        "email": email,
        "trust_score": 100,  # Initial trust score
        "status": "Safe",
        "issues": [],
        "confidence": "HIGH",
        "recommendation": "No Action Needed"
    }

    issues = []

    # Check for impersonation of common legitimate domains
    impersonated_domains = ["paypal.com", "google.com", "apple.com", "facebook.com"]
    for legit in impersonated_domains:
        # Check if a legitimate domain is "impersonated" by being part of the current domain
        if legit != domain and legit.replace('.', '') in domain.replace('.', ''):
            issues.append(f"Impersonation of \"{legit}\"")
            result["trust_score"] -= 35  # Deduct score for impersonation

    # Check for unusual spelling or numeric substitutions in the domain
    if re.search(r"\d|paypa1|go0gle|faceb00k", domain):
        issues.append("Unusual spelling in domain name")
        result["trust_score"] -= 30  # Deduct score for suspicious spelling

    # Check for masked tracking indicators in the email address
    if "tracking" in email or "mailer@" in email:
        issues.append("Email header contains masked tracking")
        result["trust_score"] -= 20  # Deduct score for tracking indicators

    # Adjust status, confidence, and recommendation based on the final trust score
    if result["trust_score"] < 60:
        result["status"] = "High-risk email (Possible phishing attempt)"
        result["confidence"] = "EXTREMELY HIGH"
        result["recommendation"] = "BLOCK & REPORT THIS EMAIL"

    result["issues"] = issues  # Update the issues list in the result
    return result

# --- Email Report Format ---
# Formats the email scan result into a human-readable text report
def format_email_report(scan):
    return f""" EMAIL SCAN REPORT

Email: {scan['email']}

Trust Score: {scan['trust_score']}% Safe {"✅" if scan['trust_score'] >= 60 else "❌"}
Status: {scan['status']}

Detected Issues:
{''.join(f"- {issue}\\n" for issue in scan['issues']) if scan['issues'] else "- None"}

Confidence Level: {scan['confidence']}

Recommendation: {scan['recommendation']}"""

# --- Link Report Format ---
# Formats the link scan result into an HTML report
def format_link_report(scan):
    # Extract analysis statistics and URL information from the scan result
    stats = scan.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    url_info = scan.get("data", {}).get("attributes", {})

    harmless = stats.get("harmless", 0)
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)

    # Calculate total scans and trust score
    total = harmless + malicious + suspicious + undetected
    if total == 0:
        trust_score = 0
    else:
        trust_score = round((harmless / total) * 100)

    url_display = url_info.get("url", "Unknown URL")

    # Determine status, confidence, and recommendation based on trust score
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

    # Construct the HTML report string using an f-string
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

# === MAIN AI HANDLER ===
# FastAPI endpoint to handle AI requests for email/link scanning or general AI chat
@app.post("/ask")
async def ask_ai(req: PromptRequest):
    prompt = req.prompt.strip()
    mode = req.mode.lower()

    # Handle "email/link scanner" mode
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

    # === COHERE fallback ===
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
        # Check if the Cohere API call was successful
        if res.status_code == 200:
            output = res.json().get("text") or res.json().get("response")
            return {"response": output}
        else:
            print(f"Cohere API error: {res.status_code} - {res.text}")
            return {"response": "AI response failed. Please try again."}
