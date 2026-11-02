import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pathlib import Path

load_dotenv(override=True)
router = APIRouter(
    prefix="/auth/instagram",
    tags=["Instagram"]
)

META_APP_ID = (
    os.getenv("META_APP_ID")
    or os.getenv("FACEBOOK_APP_ID")
)

META_APP_SECRET = (
    os.getenv("META_APP_SECRET")
    or os.getenv("FACEBOOK_APP_SECRET")
)

INSTAGRAM_CONFIG_ID = os.getenv(
    "INSTAGRAM_CONFIG_ID"
)

INSTAGRAM_REDIRECT_URI = os.getenv(
    "INSTAGRAM_REDIRECT_URI"
)
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5500/"
)

GRAPH_URL = "https://graph.facebook.com/v26.0"

instagram_session = {
    "access_token": None,
    "account_id": None,
    "username": None,
}
@router.get("/callback")
def instagram_callback(code: str):

    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Meta app credentials are missing."
        )

    if not INSTAGRAM_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="Instagram redirect URI is missing."
        )

    token_response = requests.get(
        f"{GRAPH_URL}/oauth/access_token",
        params={
            "client_id": META_APP_ID,
            "client_secret": META_APP_SECRET,
            "redirect_uri": INSTAGRAM_REDIRECT_URI,
            "code": code,
        },
        timeout=30,
    )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Instagram token exchange failed: "
            + token_response.text[:400]
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=502,
            detail="Instagram access token was not returned."
        )

    instagram_session["access_token"] = access_token

    return RedirectResponse(
        FRONTEND_URL + "?ig=connected"
    )
@router.get("/login")
def instagram_login():

    if not META_APP_ID:
        raise HTTPException(
            status_code=500,
            detail="Meta App ID is missing."
        )

    if not INSTAGRAM_CONFIG_ID:
        raise HTTPException(
            status_code=500,
            detail="Instagram configuration ID is missing."
        )

    if not INSTAGRAM_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="Instagram redirect URI is missing."
        )

    login_url = (
        "https://www.facebook.com/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&config_id={INSTAGRAM_CONFIG_ID}"
        f"&redirect_uri={INSTAGRAM_REDIRECT_URI}"
        "&response_type=code"
        "&display=popup"
        "&prompt=login"
    )

    return RedirectResponse(login_url)
@router.get("/status")
def instagram_status():

    env_path = Path.cwd() / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    username = os.getenv("INSTAGRAM_USERNAME")

    connected = bool(access_token and account_id)

    return {
        "connected": connected,
        "account_id": account_id if connected else None,
        "username": username if connected else None,
    }
