# PURPOSE:
# Real Facebook login (OAuth) and publishing a video to a Facebook Page.
#
# WHAT THIS CODE DOES:
# 1. /auth/facebook/login       -> opens Facebook's real login popup.
# 2. /auth/facebook/callback    -> Facebook sends the user back here; we get tokens.
# 3. /auth/facebook/pages       -> lists the Pages the user manages (no secrets).
# 4. /auth/facebook/select-page -> the user picks which Page to post on.
# 5. /publish                   -> uploads the video + AI caption to that Page.

import os
import secrets
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

load_dotenv()

APP_ID = os.getenv("FACEBOOK_APP_ID")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
REDIRECT_URI = os.getenv(
    "FACEBOOK_REDIRECT_URI", "http://localhost:8000/auth/facebook/callback"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://reeldone.vercel.app")
VERSION = os.getenv("GRAPH_VERSION", "v24.0")
GRAPH = f"https://graph.facebook.com/{VERSION}"
SCOPES = "pages_show_list,pages_manage_posts,pages_read_engagement,public_profile"

router = APIRouter()

# Demo storage: in memory, one user. Tokens never go to the browser.
_pending_states = set()
_session = {"pages": [], "selected": None}


class PageChoice(BaseModel):
    page_id: str


async def _get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    # Call Facebook and return JSON. Errors never include our secret.
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(502, f"Facebook error: {response.text}")
    return response.json()


@router.get("/auth/facebook/login")
async def facebook_login():
    if not APP_ID or not APP_SECRET:
        raise HTTPException(500, "Missing FACEBOOK_APP_ID or FACEBOOK_APP_SECRET in .env")
    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": SCOPES,
        "response_type": "code",
    }
    url = f"https://www.facebook.com/{VERSION}/dialog/oauth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/auth/facebook/callback")
async def facebook_callback(code: str = "", state: str = "", error: str = ""):
    if error or not code:
        raise HTTPException(400, "Facebook login was cancelled or failed")
    if state not in _pending_states:
        raise HTTPException(400, "Invalid login state")
    _pending_states.discard(state)

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Swap the one-time code for a short-lived user token.
        short = await _get(client, f"{GRAPH}/oauth/access_token", {
            "client_id": APP_ID,
            "redirect_uri": REDIRECT_URI,
            "client_secret": APP_SECRET,
            "code": code,
        })
        # 2. Swap it for a long-lived token.
        long = await _get(client, f"{GRAPH}/oauth/access_token", {
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": short["access_token"],
        })
        # 3. Get the Pages this user manages (each comes with its own token).
        pages = await _get(client, f"{GRAPH}/me/accounts", {
            "access_token": long["access_token"],
            "fields": "id,name,access_token",
        })

    _session["pages"] = pages.get("data", [])
    _session["selected"] = None
    return RedirectResponse(f"{FRONTEND_URL}?fb=connected")


@router.get("/auth/facebook/pages")
async def list_pages():
    selected = _session["selected"]
    return {
        "connected": bool(_session["pages"]),
        "pages": [{"id": p["id"], "name": p["name"]} for p in _session["pages"]],
        "selected": selected["id"] if selected else None,
    }


@router.post("/auth/facebook/select-page")
async def select_page(choice: PageChoice):
    for page in _session["pages"]:
        if page["id"] == choice.page_id:
            _session["selected"] = page
            return {"selected": page["name"]}
    raise HTTPException(404, "Page not found")


@router.post("/publish")
async def publish(caption: str = Form(...), video: UploadFile = File(...)):
    page = _session["selected"]
    if not page:
        raise HTTPException(400, "Connect Facebook and select a Page first")

    content = await video.read()
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{GRAPH}/{page['id']}/videos",
            data={"description": caption, "access_token": page["access_token"]},
            files={"source": (video.filename, content, video.content_type or "video/mp4")},
        )
    if response.status_code >= 400:
        raise HTTPException(502, f"Facebook error: {response.text}")
    return {"status": "published", "page": page["name"], "facebook": response.json()}
