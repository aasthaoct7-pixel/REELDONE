# PURPOSE:
# This file initializes the ReelDone backend.
#
# WHAT THIS CODE DOES:
# 1. Creates a FastAPI application.
# 2. Configures basic CORS access.
# 3. Creates a health-check API endpoint.
# 4. Allows us to verify that the backend is running.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# PURPOSE:
# Create the main FastAPI application.

app = FastAPI(
    title="ReelDone API",
    description="AI-powered Creator Operating System",
    version="1.0.0"
)


# PURPOSE:
# Allow the frontend to communicate with the backend.
# Production origins will be restricted before deployment.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://reeldone.vercel.app",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# PURPOSE:
# Health-check endpoint.
# It confirms that the backend server is operational.

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "ReelDone",
        "message": "Backend is running successfully"
    }
# PURPOSE:
# Plug the /generate route (6-platform SEO) into the main application.
from backend.app.seo_routes import router as seo_router

app.include_router(seo_router)

from backend.app.facebook_routes import router as facebook_router
app.include_router(facebook_router)
