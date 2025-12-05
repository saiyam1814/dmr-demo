import os
import requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

MODEL_API_URL = os.getenv("MODEL_API_URL", "http://localhost:12434/engines/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "ai/qwen3-coder")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, text: str = Form(...)):
    """
    Send the pasted text to Docker Model Runner and ask it to:
    - summarize the content
    - highlight breaking changes
    - list action items
    """
    url = MODEL_API_URL.rstrip("/") + "/chat/completions"

    prompt = f"""
You are a concise assistant for dev and platform teams.

The user will paste release notes, logs, or configuration text.

Please respond with:

1. A very short summary (2-3 bullet points).
2. Any potential BREAKING CHANGES (if none, say 'None spotted').
3. Action items for a DevOps / Platform engineer.

Here is the text:

{text}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful release-note explainer for engineers."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        content = f"Error calling model: {e}"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "original": text,
            "analysis": content,
        },
    )

