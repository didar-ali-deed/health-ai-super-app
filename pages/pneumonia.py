import streamlit as st

# Set page config first
st.set_page_config(
    page_title="Pneumonia Detection - Health AI Super App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Imports after set_page_config
from xray_analysis.xray_app import run_pneumonia_app
from layout import apply_custom_css, render_header, render_footer

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = "app.py"

# Apply layout
apply_custom_css()
render_header()

# Check authentication
if not st.session_state.logged_in:
    st.warning("Please log in to use the Pneumonia Detection service.")
    st.session_state.redirect_to = "pages/pneumonia.py"
    st.markdown("<a href='/login' class='cta-button'>Log in</a>", unsafe_allow_html=True)
else:
    run_pneumonia_app()

# Render footer
render_footer()