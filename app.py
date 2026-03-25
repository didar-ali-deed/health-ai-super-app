import logging
from datetime import datetime, timedelta

import streamlit as st

# set_page_config MUST be the first Streamlit call
st.set_page_config(
    page_title="Health AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import display_notifications, init_session_state, push_notification, render_login_form, render_logout_button
from dashboard import render_dashboard
from layout import apply_custom_css, render_footer, render_header, render_services
from profile import render_profile
from database import init_db

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)

# --- Database & session setup -------------------------------------------------
try:
    init_db()
except Exception as exc:
    st.error(f"Failed to initialise database: {exc}")
    logging.error("DB init failed: %s", exc)

init_session_state()

# --- Session timeout ----------------------------------------------------------
SESSION_TIMEOUT = timedelta(minutes=30)
if st.session_state.logged_in:
    elapsed = datetime.now() - st.session_state.last_activity
    if elapsed > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.redirect_to = "app.py"
        push_notification("warning", "Session timed out. Please log in again.")
        logging.info("Session timed out")

# --- Layout -------------------------------------------------------------------
apply_custom_css(st.session_state.theme)
render_header()
display_notifications()

# --- Page content -------------------------------------------------------------
if st.session_state.logged_in:
    render_logout_button()
    render_services()
    render_dashboard()
    render_profile()
    # Update activity timestamp
    st.session_state.last_activity = datetime.now()
else:
    render_login_form()
    render_services()

render_footer()
