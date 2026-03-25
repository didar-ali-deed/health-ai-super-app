import logging
from datetime import datetime
import streamlit as st

# set_page_config MUST be the first Streamlit call
st.set_page_config(
    page_title="Health AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import display_notifications, init_session_state, render_login_form, render_logout_button
from utils import check_session_timeout
from database import init_db, cleanup_expired_tokens
from dashboard import render_dashboard
from layout import apply_custom_css, render_footer, render_header, render_services
from profile import render_profile

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

try:
    cleanup_expired_tokens()
except Exception as exc:
    logging.warning("Token cleanup failed (non-fatal): %s", exc)

init_session_state()

# --- Session timeout ----------------------------------------------------------
check_session_timeout()

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
