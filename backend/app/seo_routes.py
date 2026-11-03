# PURPOSE:
# Creates the /generate API: one script in, SEO for 6 platforms out.
#
# WHAT THIS CODE DOES:
# 1. Accepts a video script from the frontend.
# 2. Asks the Muse Spark model for SEO data for all 6 platforms in one call.
# 3. Converts the model's answer into clean JSON and returns it.

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.muse_client import ask_muse

# A router groups related API endpoints; main.py plugs it into the app.
router = APIRouter()


# The shape of the data the frontend sends us.
class ScriptRequest(BaseModel):
    script: str


# Instructions that tell the model exactly what to return.
SYSTEM_PROMPT = """You are a social media SEO expert.
Return ONLY valid JSON with no extra text and no markdown.
Never use real line breaks inside values; write \\n instead.
Create one entry for each of these platforms:
YouTube, Instagram, Facebook, LinkedIn, Twitter, Pinterest.
Each entry must have these keys:
"title", "description", "hashtags" (list), "keywords" (list),
"caption", "tags" (list).
Follow each platform's style and character limits."""


@router.post("/generate")
async def generate_seo(request: ScriptRequest):
    # Reject empty scripts early with a clear error message.
    if not request.script.strip():
        raise HTTPException(status_code=400, detail="Script is empty")

    # Ask the Muse model on Modal to write the SEO for every platform.
    try:
        answer = ask_muse(SYSTEM_PROMPT, request.script)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Muse call failed: {error}")

    # The model may wrap JSON in extra text, so keep only the {...} part.
    start = answer.find("{")
    end = answer.rfind("}")
    if start == -1 or end == -1:
        raise HTTPException(status_code=502, detail="Model did not return JSON")

    # strict=False allows line breaks inside text values.
    # If parsing still fails, show the real reason to help debugging.
    try:
        return json.loads(answer[start : end + 1], strict=False)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=502,
            detail=f"JSON parse error: {error} | answer length: {len(answer)} | last 150 chars: {answer[-150:]}",
        )
SCHEDULE_PROMPT = """
You are ReelDone's AI social media scheduling strategist.

Analyze the user's reel topic, niche and content.

Return ONLY valid JSON with no markdown and no extra text.

Return exactly these platforms:
Facebook, Instagram, YouTube, LinkedIn, Twitter, Pinterest.

For every platform return exactly 3 recommended posting times.

Use this structure:

{
  "Facebook": ["6:30 PM", "8:00 PM", "11:00 AM"],
  "Instagram": ["7:00 PM", "8:30 PM", "10:00 PM"],
  "YouTube": ["6:00 PM", "8:00 PM", "11:00 AM"],
  "LinkedIn": ["9:00 AM", "12:30 PM", "5:30 PM"],
  "Twitter": ["8:00 AM", "1:00 PM", "7:00 PM"],
  "Pinterest": ["8:00 PM", "9:30 PM", "11:00 AM"]
}

Choose times based on the topic, likely audience behaviour,
content niche and the style of each platform.
Times must be easy to read and use local time.
"""


@router.post("/schedule/suggestions")
async def schedule_suggestions(request: ScriptRequest):

    try:
       answer = ask_muse(
    SCHEDULE_PROMPT,
    request.script,
    use_schema=False
)

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Schedule AI failed: {error}"
        )

    start = answer.find("{")
    end = answer.rfind("}")

    if start == -1 or end == -1:
        raise HTTPException(
            status_code=502,
            detail="Schedule AI did not return JSON"
        )

    try:
        return json.loads(
            answer[start:end + 1],
            strict=False
        )

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Schedule JSON error: {error}"
        )
