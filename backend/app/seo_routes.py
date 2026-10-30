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

from app.muse_client import ask_muse

# A router groups related API endpoints; main.py plugs it into the app.
router = APIRouter()


# The shape of the data the frontend sends us.
class ScriptRequest(BaseModel):
    script: str


# Instructions that tell the model exactly what to return.
SYSTEM_PROMPT = """You are a social media SEO expert.
Return ONLY valid JSON with no extra text.
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
        answer = await ask_muse(SYSTEM_PROMPT, request.script)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Muse call failed: {error}")

    # The model may wrap JSON in extra text, so keep only the {...} part.
    start = answer.find("{")
    end = answer.rfind("}")
    if start == -1 or end == -1:
        raise HTTPException(status_code=502, detail="Model did not return JSON")

    # Turn the text into real data and send it back to the frontend.
    try:
        return json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Model JSON was invalid")
