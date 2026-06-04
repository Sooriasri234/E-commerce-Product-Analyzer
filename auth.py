import os
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from passlib.hash import pbkdf2_sha256

from database import create_google_user, create_user, get_user_by_email


JWT_SECRET = os.getenv("JWT_SECRET", "replace-this-secret-before-deployment")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "12"))


def _public_user(row) -> dict:
    return {"id": int(row["id"]), "name": row["name"], "email": row["email"], "provider": row["provider"]}


def register_user(name: str, email: str, password: str) -> dict:
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2:
        raise ValueError("Enter a valid full name.")
    if "@" not in clean_email or "." not in clean_email:
        raise ValueError("Enter a valid email address.")
    if not 4 <= len(password) <= 7:
        raise ValueError("Password must be 4 to 7 characters.")

    try:
        user_id = create_user(clean_name, clean_email, pbkdf2_sha256.hash(password), provider="local")
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with this email already exists.") from exc

    return {"id": user_id, "name": clean_name, "email": clean_email, "provider": "local"}


def authenticate_user(email: str, password: str) -> dict | None:
    row = get_user_by_email(email.strip().lower())
    if not row or not row["password_hash"]:
        return None
    if not pbkdf2_sha256.verify(password, row["password_hash"]):
        return None
    return _public_user(row)


def get_or_create_google_user(name: str, email: str) -> dict:
    clean_email = email.strip().lower()
    row = get_user_by_email(clean_email)
    if row:
        return _public_user(row)
    clean_name = name.strip() or clean_email.split("@")[0].replace(".", " ").title()
    user_id = create_google_user(clean_name, clean_email)
    return {"id": user_id, "name": clean_name, "email": clean_email, "provider": "google"}


def create_access_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "name": user["name"],
        "email": user["email"],
        "provider": user.get("provider", "local"),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        payload["sub"] = int(payload["sub"])
        return payload
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
