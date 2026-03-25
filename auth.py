import os
import logging
import base64
from datetime import datetime
from io import BytesIO

import streamlit as st
import pyotp
import qrcode
from cryptography.fernet import Fernet

from database import authenticate_user

# Generated once when Python imports this module — stable for the lifetime
# of the process. Intentionally NOT stable across process restarts (e.g.
# after a file-save reload during dev). For a portfolio demo this is fine;
# in production, always set the ENCRYPTION_KEY env var.
_DEV_KEY: str = Fernet.generate_key().decode()


def get_encryption_key() -> str:
    """Return the Fernet encryption key.
    Uses ENCRYPTION_KEY env var when set (production / HF Spaces secret).
    Falls back to a per-process key for local dev — good enough for a demo.
    """
    return os.environ.get("ENCRYPTION_KEY", _DEV_KEY)


SESSION_DEFAULTS: dict = {
    "logged_in": False,
    "username": "",
    "user_id": None,
    "redirect_to": "app.py",
    "last_activity": datetime.now(),
    "theme": "light",
    "notifications": [],
    "2fa_secret": None,
    "2fa_enabled": False,
}


def init_session_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def push_notification(kind: str, message: str) -> None:
    st.session_state.notifications.append({"type": kind, "message": message})


def display_notifications() -> None:
    for notif in st.session_state.notifications:
        if notif["type"] == "success":
            st.success(notif["message"])
        elif notif["type"] == "warning":
            st.warning(notif["message"])
        elif notif["type"] == "error":
            st.error(notif["message"])
    st.session_state.notifications = []


def render_login_form() -> None:
    st.warning("Log in or sign up to access advanced health solutions.")
    with st.form("quick_login", clear_on_submit=True):
        username = st.text_input("Username", placeholder="Enter username", key="quick_username")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="quick_password")
        tfa_code = None
        if st.session_state.get("2fa_enabled", False):
            tfa_code = st.text_input("2FA Code", placeholder="Enter 6-digit code", key="2fa_code_login")
        col, _ = st.columns([1, 3])
        with col:
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            _handle_login(username, password, tfa_code)


def _handle_login(username: str, password: str, tfa_code) -> None:
    try:
        user = authenticate_user(username, password)
        if not user:
            st.error("Invalid username or password.")
            logging.warning("Failed login for %s", username)
            return
        if st.session_state.get("2fa_enabled") and tfa_code:
            totp = pyotp.TOTP(st.session_state["2fa_secret"])
            if not totp.verify(tfa_code):
                st.error("Invalid 2FA code.")
                logging.warning("Invalid 2FA for %s", username)
                return
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_id = user[0]
        st.session_state.last_activity = datetime.now()
        st.session_state.theme = user[4] if user[4] else "light"
        push_notification("success", f"Welcome back, {username}!")
        logging.info("User %s logged in", username)
        redirect = st.session_state.redirect_to
        if redirect and redirect != "app.py":
            st.switch_page(redirect)
        else:
            st.rerun()
    except Exception as exc:
        st.error(f"Login error: {exc}")
        logging.error("Login error for %s: %s", username, exc)


def render_logout_button() -> None:
    st.success(f"Logged in as **{st.session_state.username}**")
    if st.button("Logout", key="logout_button", use_container_width=True):
        handle_logout()


def handle_logout() -> None:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.redirect_to = "app.py"
    push_notification("success", "Logged out successfully.")
    logging.info("User logged out")
    st.rerun()
