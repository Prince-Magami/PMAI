@app.post("/api/chat")
async def chat_with_ai(payload: ChatRequest):
    user_input = payload.message
    mode = payload.mode
    lang = payload.lang

    # VirusTotal scan if link
    if mode == "scan":
        virus_total_key = os.getenv("VIRUSTOTAL_API_KEY")
        headers = {"x-apikey": virus_total_key}

        if user_input.startswith("http"):
            url_id = requests.utils.quote(user_input, safe='')
            vt_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
            resp = requests.get(vt_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                categories = data.get("data", {}).get("attributes", {}).get("categories", {})
                total = sum(score.values())
                malicious = score.get("malicious", 0)
                harmless = score.get("harmless", 0)
                pct_malicious = round((malicious / total) * 100) if total else 0

                reply = f"Scanned URL: {user_input}\nMalicious: {malicious}\nHarmless: {harmless}\nThreat Score: {pct_malicious}%\nCategory: {', '.join(categories.values()) or 'Unknown'}\nVerdict: {'Avoid visiting this site.' if pct_malicious >= 40 else 'Link seems okay but be cautious.'}"
                return JSONResponse({"reply": reply})
            else:
                return JSONResponse({"reply": "Could not analyze the link. Please try again."})

        else:
            scan_prompt = build_prompt("scan", lang, user_input)
            response = co.generate(
                model="command-r-plus",
                prompt=scan_prompt,
                max_tokens=300,
                temperature=0.7,
                stop_sequences=["User:", "AI:"]
            )
            return JSONResponse({"reply": response.generations[0].text.strip()})

    elif mode == "edu":
        edu_prompt = build_prompt("edu", lang, user_input)
        response = co.generate(
            model="command-r-plus",
            prompt=edu_prompt,
            max_tokens=300,
            temperature=0.7,
            stop_sequences=["User:", "AI:"]
        )
        return JSONResponse({"reply": response.generations[0].text.strip()})

    elif mode == "cyber":
        cyber_prompt = build_prompt("cyber", lang, user_input)
        response = co.generate(
            model="command-r-plus",
            prompt=cyber_prompt,
            max_tokens=300,
            temperature=0.7,
            stop_sequences=["User:", "AI:"]
        )
        return JSONResponse({"reply": response.generations[0].text.strip()})

    else:
        default_prompt = build_prompt("chat", lang, user_input)
        response = co.generate(
            model="command-r-plus",
            prompt=default_prompt,
            max_tokens=300,
            temperature=0.7,
            stop_sequences=["User:", "AI:"]
        )
        return JSONResponse({"reply": response.generations[0].text.strip()})
