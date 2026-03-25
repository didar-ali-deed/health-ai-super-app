import streamlit as st

st.set_page_config(
    page_title="Pneumonia Detection - Health AI Super App",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import init_session_state
from xray_analysis.xray_app import run_pneumonia_app
from layout import apply_custom_css, render_footer, render_header
from utils import check_session_timeout

init_session_state()
check_session_timeout()
apply_custom_css(st.session_state.get("theme", "light"))
render_header()

if not st.session_state.logged_in:
    st.warning("Please log in to use the Pneumonia Detection service.")
    st.session_state.redirect_to = "pages/pneumonia.py"
    if st.button("Log in to Access", type="primary"):
        st.switch_page("pages/login.py")
else:
    run_pneumonia_app()
    # Keep session alive during analysis
    import datetime as _dt
    st.session_state.last_activity = _dt.datetime.now()

render_footer()
