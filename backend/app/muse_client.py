# PURPOSE:
# Sends requests to the Muse Spark Open model hosted on Modal.
#
# WHAT THIS CODE DOES:
# 1. Reads the endpoint URL and secret tokens from environment variables.
# 2. Sends a chat request (system prompt + user prompt) to the Muse model.
# 3. Returns the text answer written by the model.

import os

import httpx
from dotenv import load_dotenv

# Load secret values from the .env file (never uploaded to GitHub).
load_dotenv()

# The Modal endpoint URL and proxy tokens come from environment variables.
MUSE_ENDPOINT_URL = os.getenv("MUSE_ENDPOINT_URL")
TOKEN_ID = os.getenv("MODAL_PROXY_TOKEN_ID")
TOKEN_SECRET = os.getenv("MODAL_PROXY_TOKEN_SECRET")

# The exact name of the open model we call on Modal.
MODEL_NAME = "meta-models/Muse-Spark-Open-816B-A42B"


async def ask_muse(system_prompt: str, user_prompt: str) -> str:
    # Stop early with a clear message if a secret value is missing.
    if not (MUSE_ENDPOINT_URL and TOKEN_ID and TOKEN_SECRET):
        raise RuntimeError("Missing MUSE_ENDPOINT_URL or Modal token in .env")

    # Modal expects the token id and secret joined by a dot.
    headers = {
        "Content-Type": "application/json",
"Authorization": f"Bearer {TOKEN_ID}.{TOKEN_SECRET}",
        "Modal-Key": TOKEN_ID,
"Modal-Secret": TOKEN_SECRET,
    }

    # The chat request: model name, instructions, and the user's task.
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    # Send the request and wait for the model (it can take several seconds).
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(MUSE_ENDPOINT_URL, headers=headers, json=payload)
        response.raise_for_status()

    # Return only the text of the model's first answer.
    return response.json()["choices"][0]["message"]["content"]


    # Return only the text of the model's first answer.
    return response.json()["choices"][0]["message"]["content"]
