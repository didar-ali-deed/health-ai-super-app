import base64
import logging
import os

import streamlit as st

st.set_page_config(
    page_title="About | Didar AI/ML Solutions",
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

# Breadcrumb
st.page_link("app.py", label="Home", icon=None)

st.markdown("""
<div class="page-hero">
    <h1>About Didar AI/ML Solutions</h1>
    <p class="subtitle">Transforming healthcare with AI-driven diagnostics for a healthier tomorrow.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='max-width:1200px;margin:2rem auto'>
    <h2 style='text-align:center;margin-bottom:2rem;'>Our Mission &amp; Vision</h2>
    <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.5rem;'>
        <div class="mission-card">
            <h3>Mission</h3>
            <p>Empower individuals and healthcare providers with precise AI diagnostics for early detection of critical conditions like Diabetes, Parkinson's, and Pneumonia.</p>
        </div>
        <div class="mission-card">
            <h3>Vision</h3>
            <p>Lead global healthcare innovation by making AI-powered diagnostics accessible, reliable, and impactful for all communities.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;margin:2rem 0 1rem;'>Meet the Founder</h2>", unsafe_allow_html=True)

photo_path = "static/didar_ali.jpg"
photo_fallback = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
if os.path.exists(photo_path):
    with open(photo_path, "rb") as img:
        photo_src = f"data:image/jpeg;base64,{base64.b64encode(img.read()).decode()}"
else:
    photo_src = photo_fallback

st.markdown(f"""
<div class="mission-card" style='display:flex;gap:2rem;align-items:center;max-width:900px;margin:0 auto;'>
    <img src="{photo_src}" alt="Didar Ali" style='width:160px;height:160px;object-fit:cover;border-radius:8px;' loading="lazy">
    <div>
        <h3>Didar Ali</h3>
        <p style='font-weight:500;margin-bottom:0.5rem;'>Founder &amp; AI Specialist</p>
        <p>Passionate innovator in AI and machine learning, committed to making early disease detection accessible to all.</p>
    </div>
</div>
""", unsafe_allow_html=True)

team_members = [
    {"name": "Dr. Ayesha Khan", "role": "Medical Advisor", "bio": "Expert in clinical diagnostics, ensuring our solutions meet medical standards."},
    {"name": "Sarah Ahmed", "role": "Data Scientist", "bio": "Specialises in machine learning models for health data analysis."},
    {"name": "Omar Farooq", "role": "Software Engineer", "bio": "Builds robust platforms to deliver our AI solutions seamlessly."},
]
st.markdown("<h2 style='text-align:center;margin:2rem 0 1rem;'>Our Team</h2>", unsafe_allow_html=True)
cols = st.columns(len(team_members))
for col, m in zip(cols, team_members):
    with col:
        st.markdown(f"""<div class="team-card"><h3>{m['name']}</h3><p style='font-weight:500;'>{m['role']}</p><p>{m['bio']}</p></div>""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;margin:2rem 0 1rem;'>Frequently Asked Questions</h2>", unsafe_allow_html=True)
faq_data = [
    {"question": "What is Didar AI/ML Solutions?", "answer": "A healthcare technology company using AI to provide accurate diagnostics."},
    {"question": "How accurate are your AI models?", "answer": "Our models achieve over 88-92% accuracy, validated against clinical datasets."},
    {"question": "How can I get started?", "answer": "Sign up or log in to access our diagnostic tools."},
    {"question": "Where are you based?", "answer": "Proudly based in Peshawar, Pakistan, serving a global audience."},
]
for faq in faq_data:
    with st.expander(faq["question"]):
        st.write(faq["answer"])

if st.button("Contact Us", key="about_contact_cta"):
    st.switch_page("pages/contact.py")

if st.session_state.logged_in:
    import datetime as _dt
    st.session_state.last_activity = _dt.datetime.now()

render_footer()
