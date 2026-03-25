import logging
from datetime import datetime, timedelta

import streamlit as st

from database import update_user_theme

SESSION_TIMEOUT = timedelta(minutes=30)


def check_session_timeout() -> None:
    """Log out user if 30-minute inactivity exceeded. Safe if not logged in."""
    if not st.session_state.get("logged_in"):
        return
    last = st.session_state.get("last_activity")
    if last is None:
        return
    if datetime.now() - last > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.redirect_to = "app.py"
        st.session_state.notifications = st.session_state.get("notifications", [])
        st.session_state.notifications.append({"type": "warning", "message": "Session timed out. Please log in again."})
        logging.info("Session timed out")
        st.rerun()


def toggle_theme(user_id) -> None:
    """Flip light/dark theme and persist to DB. Fails silently on DB error."""
    current = st.session_state.get("theme", "light")
    new_theme = "dark" if current == "light" else "light"
    st.session_state.theme = new_theme
    try:
        update_user_theme(user_id, new_theme)
    except Exception as exc:
        logging.error("Theme DB update failed: %s", exc)
    st.rerun()
