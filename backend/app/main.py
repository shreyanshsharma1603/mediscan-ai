from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import GEMINI_API_KEY, GEMINI_MODEL, MEDICAL_DISCLAIMER, SUPPORTED_LANGUAGES
from app.database import cleanup_expired_documents, init_db
from app.routers import auth, documents, insights


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    cleanup_expired_documents()
    yield


app = FastAPI(
    title="MediScan AI API",
    description="Multilingual Medical Document Intelligence Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(insights.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "MediScan AI Backend",
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL,
        "supported_languages": SUPPORTED_LANGUAGES,
        "disclaimer": MEDICAL_DISCLAIMER,
    }
