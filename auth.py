import os
import logging
from datetime import datetime

import streamlit as st
import pyotp
from cryptography.fernet import Fernet

from database import authenticate_user, get_2fa_info

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
    "last_activity": None,  # Sentinel — set to datetime.now() per-session in init_session_state
    "theme": "light",
    "notifications": [],
    "2fa_secret": None,
    "2fa_enabled": False,
}


def init_session_state() -> None:
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # Always set a live timestamp — never use the None sentinel or a frozen import-time value
    if st.session_state.last_activity is None:
        st.session_state.last_activity = datetime.now()


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
    st.info("Log in or sign up to access the AI health diagnostics.")
    with st.form("quick_login", clear_on_submit=True):
        username = st.text_input("Username", placeholder="Enter username", key="quick_username")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="quick_password")
        tfa_code = st.text_input("2FA Code (if enabled)", placeholder="Enter 6-digit code or leave blank", key="2fa_code_login")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")
        with col2:
            go_signup = st.form_submit_button("Sign Up", use_container_width=True)
        if submitted:
            _handle_login(username, password, tfa_code)
        if go_signup:
            st.switch_page("pages/login.py")


def _handle_login(username: str, password: str, tfa_code: str | None) -> None:
    try:
        user = authenticate_user(username, password)
        if not user:
            st.error("Invalid username or password.")
            logging.warning("Failed login for %s", username)
            return
        tfa_enabled, tfa_secret = get_2fa_info(user[0])
        if tfa_enabled:
            if not tfa_code:
                st.error("2FA code required.")
                return
            if not pyotp.TOTP(tfa_secret).verify(tfa_code):
                st.error("Invalid 2FA code.")
                logging.warning("Invalid 2FA for %s", username)
                return
        st.session_state["2fa_enabled"] = bool(tfa_enabled)
        st.session_state["2fa_secret"] = tfa_secret
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
