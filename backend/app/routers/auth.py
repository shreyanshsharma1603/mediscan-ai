from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import DEFAULT_RETENTION_DAYS, SUPPORTED_LANGUAGES, UPLOAD_DIR
from app.database import db_session, utc_now_iso
from app.schemas import (
    AuthResponse,
    LoginRequest,
    PreferencesUpdateRequest,
    RegisterRequest,
    UserProfile,
)
from app.security import (
    EMAIL_REGEX,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if not req.consent_accepted:
        raise HTTPException(
            status_code=400,
            detail="Explicit user consent and acknowledgment of the medical disclaimer are required to register.",
        )

    lang = req.preferred_language if req.preferred_language in SUPPORTED_LANGUAGES else "en"
    user_id = str(uuid.uuid4())
    now = utc_now_iso()
    pw_hash = hash_password(req.password)

    with db_session() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

        conn.execute(
            """
            INSERT INTO users (
                id, email, full_name, password_hash, preferred_language,
                consent_accepted, consent_accepted_at, retention_days, created_at
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (user_id, email, req.full_name.strip(), pw_hash, lang, now, DEFAULT_RETENTION_DAYS, now),
        )
        row = conn.execute(
            "SELECT id, email, full_name, preferred_language, consent_accepted, consent_accepted_at, retention_days, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    user_dict = dict(row)
    user_dict["consent_accepted"] = bool(user_dict["consent_accepted"])
    token = create_access_token(user_id, email)
    return AuthResponse(access_token=token, user=UserProfile(**user_dict))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    email = req.email.strip().lower()
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_dict = {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "preferred_language": row["preferred_language"],
        "consent_accepted": bool(row["consent_accepted"]),
        "consent_accepted_at": row["consent_accepted_at"],
        "retention_days": row["retention_days"],
        "created_at": row["created_at"],
    }
    token = create_access_token(row["id"], row["email"])
    return AuthResponse(access_token=token, user=UserProfile(**user_dict))


@router.get("/me", response_model=UserProfile)
def me(current_user: dict = Depends(get_current_user)):
    current_user["consent_accepted"] = bool(current_user["consent_accepted"])
    return UserProfile(**current_user)


@router.patch("/preferences", response_model=UserProfile)
def update_preferences(
    req: PreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    new_lang = current_user["preferred_language"]
    if req.preferred_language is not None:
        if req.preferred_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail="Unsupported language code.")
        new_lang = req.preferred_language

    new_retention = current_user["retention_days"]
    if req.retention_days is not None:
        new_retention = req.retention_days

    with db_session() as conn:
        conn.execute(
            "UPDATE users SET preferred_language = ?, retention_days = ? WHERE id = ?",
            (new_lang, new_retention, current_user["id"]),
        )
        if req.retention_days is not None:
            new_exp = (datetime.now(timezone.utc) + timedelta(days=new_retention)).isoformat()
            conn.execute(
                "UPDATE medical_documents SET expires_at = ? WHERE user_id = ?",
                (new_exp, current_user["id"]),
            )
        row = conn.execute(
            "SELECT id, email, full_name, preferred_language, consent_accepted, consent_accepted_at, retention_days, created_at FROM users WHERE id = ?",
            (current_user["id"],),
        ).fetchone()

    user_dict = dict(row)
    user_dict["consent_accepted"] = bool(user_dict["consent_accepted"])
    return UserProfile(**user_dict)


@router.delete("/account")
def delete_account_and_data(current_user: dict = Depends(get_current_user)):
    """Permanent self-service deletion of user account and all stored medical documents."""
    user_dir = UPLOAD_DIR / current_user["id"]
    if user_dir.exists():
        shutil.rmtree(user_dir, ignore_errors=True)
    with db_session() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (current_user["id"],))
    return {"deleted": True, "message": "Account and all associated medical records permanently deleted."}
