import os

import requests
from dotenv import load_dotenv


load_dotenv()

MUSE_ENDPOINT_URL = os.getenv("MUSE_ENDPOINT_URL")
TOKEN_ID = os.getenv("MODAL_PROXY_TOKEN_ID")
TOKEN_SECRET = os.getenv("MODAL_PROXY_TOKEN_SECRET")


PLATFORM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
        "caption": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "title",
        "description",
        "hashtags",
        "keywords",
        "caption",
        "tags",
    ],
    "additionalProperties": False,
}


SOCIAL_MEDIA_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "social_media_seo",
        "schema": {
            "type": "object",
            "properties": {
                "YouTube": PLATFORM_SCHEMA,
                "Instagram": PLATFORM_SCHEMA,
                "Facebook": PLATFORM_SCHEMA,
                "LinkedIn": PLATFORM_SCHEMA,
                "Twitter": PLATFORM_SCHEMA,
                "Pinterest": PLATFORM_SCHEMA,
            },
            "required": [
                "YouTube",
                "Instagram",
                "Facebook",
                "LinkedIn",
                "Twitter",
                "Pinterest",
            ],
            "additionalProperties": False,
        },
    },
}


def ask_muse(system_prompt: str, user_prompt: str) -> str:
    if not MUSE_ENDPOINT_URL or not TOKEN_ID or not TOKEN_SECRET:
        raise RuntimeError(
            "Missing MUSE_ENDPOINT_URL or Modal token in .env"
        )

    headers = {
        "Modal-Key": TOKEN_ID,
        "Modal-Secret": TOKEN_SECRET,
        "Content-Type": "application/json",
    }

    payload = {
        "model": "muse-spark-1.3",
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": 8192,
        "reasoning_effort": "low",
        "response_format": SOCIAL_MEDIA_SCHEMA,
    }

    response = requests.post(
        MUSE_ENDPOINT_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()
    return result["choices"][0]["message"]["content"]
