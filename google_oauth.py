import os
import secrets
from urllib.parse import urlencode

import requests
import streamlit as st

from auth import get_or_create_google_user


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def is_google_oauth_configured():
    return all(os.getenv(key) for key in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"])


def get_google_login_url():
    st.session_state.oauth_state = secrets.token_urlsafe(24)
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "response_type": "code",
        "scope": "openid email profile",
        "state": st.session_state.oauth_state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def complete_google_login():
    if not is_google_oauth_configured():
        return None
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    if not code:
        return None
    expected_state = st.session_state.get("oauth_state")
    if expected_state and state != expected_state:
        st.error("Google sign-in failed because the OAuth state did not match.")
        return None

    token_response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if not token_response.ok:
        st.error("Google sign-in failed while exchanging the authorization code.")
        return None

    access_token = token_response.json().get("access_token")
    user_response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if not user_response.ok:
        st.error("Google sign-in failed while reading the Gmail profile.")
        return None

    profile = user_response.json()
    return get_or_create_google_user(profile.get("name", ""), profile["email"])
