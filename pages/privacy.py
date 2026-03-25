import streamlit as st

st.set_page_config(
    page_title="Privacy Policy | Didar AI/ML Solutions",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import init_session_state
from layout import apply_custom_css, render_footer, render_header
from utils import check_session_timeout

init_session_state()
check_session_timeout()
apply_custom_css(st.session_state.theme)
render_header()

st.page_link("app.py", label="Home", icon=None)

st.markdown("""
<div class="page-hero">
    <h1>Privacy Policy</h1>
    <p class="subtitle">Your privacy matters to us. Here's how we protect your data.</p>
</div>
""", unsafe_allow_html=True)

sections = [
    ("Data We Collect", "We collect usernames, email addresses, and health data you submit for analysis. We do not collect payment information."),
    ("How We Use Your Data", "Your data is used solely to provide AI-powered health diagnostics, improve our models, and maintain your account."),
    ("Data Security", "Passwords are hashed with Argon2. Data is stored in an encrypted SQLite database. We never sell your data to third parties."),
    ("Data Retention", "You may delete your account at any time. All associated data is permanently removed upon deletion."),
    ("Cookies", "We use Streamlit session cookies only for authentication. No third-party tracking cookies are used."),
    ("Contact", "For privacy inquiries, email us at support@healthaisuperapp.com."),
]
for title, body in sections:
    with st.expander(title):
        st.write(body)

render_footer()
