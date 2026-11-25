from __future__ import annotations

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("MEDISCAN_DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = Path(os.getenv("MEDISCAN_UPLOAD_DIR", str(BASE_DIR / "uploads")))
DB_PATH = Path(os.getenv("MEDISCAN_DB_PATH", str(DATA_DIR / "mediscan.db")))
OCR_BINARY_PATH = BASE_DIR / "ocr_helper" / "mediscan-ocr"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-4-hydrogen").strip() or "gemini-4-hydrogen"

_SECRET_FILE = DATA_DIR / ".jwt_secret"


def _load_or_create_jwt_secret() -> str:
    env_secret = os.getenv("JWT_SECRET", "").strip()
    if env_secret and env_secret != "change-me-in-production-to-a-long-random-secret":
        return env_secret
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_text().strip()
    generated = secrets.token_urlsafe(48)
    _SECRET_FILE.write_text(generated)
    os.chmod(_SECRET_FILE, 0o600)
    return generated


JWT_SECRET: str = _load_or_create_jwt_secret()
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "15"))
MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024
DEFAULT_RETENTION_DAYS: int = int(os.getenv("DEFAULT_RETENTION_DAYS", "30"))

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
}

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
}

DOCUMENT_TYPES = [
    "blood_test",
    "urine_test",
    "prescription",
    "radiology",
    "discharge_summary",
    "clinical_notes",
    "other",
]

MEDICAL_DISCLAIMER = (
    "MediScan AI is an informational medical document literacy tool. "
    "It does not diagnose medical conditions, interpret imaging pixel data, "
    "prescribe medications, or replace qualified healthcare professionals. "
    "Always consult a licensed clinician for medical advice."
)
