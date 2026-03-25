import logging
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="Contact | Didar AI/ML Solutions",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import init_session_state
from database import db_pool
from layout import apply_custom_css, render_footer, render_header
from utils import check_session_timeout

load_dotenv()
init_session_state()
check_session_timeout()
apply_custom_css(st.session_state.theme)
render_header()

# Breadcrumb
st.page_link("app.py", label="Home", icon=None)

st.markdown("""
<div class="page-hero">
    <h1>Contact Us</h1>
    <p class="subtitle">We're here to answer your questions or discuss partnerships. Reach out today!</p>
</div>
""", unsafe_allow_html=True)

def _save_submission(name, email, subject, message):
    with db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO contact_submissions (name, email, subject, message) VALUES (?, ?, ?, ?)",
            (name, email, subject, message),
        )
        conn.commit()

st.markdown("<h2 style='text-align:center;margin-bottom:1.5rem;'>Send Us a Message</h2>", unsafe_allow_html=True)
with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Name", placeholder="Your full name")
    email = st.text_input("Email", placeholder="Your email address")
    subject = st.text_input("Subject", placeholder="Subject of your message")
    message = st.text_area("Message", placeholder="Your message or inquiry")
    captcha_answer = st.text_input("What is 2 + 3?", placeholder="Enter answer")
    submitted = st.form_submit_button("Send Message", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Name is required.")
        elif not email.strip() or not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            st.error("Please enter a valid email address.")
        elif not subject.strip():
            st.error("Subject is required.")
        elif not message.strip():
            st.error("Message is required.")
        elif captcha_answer.strip() != "5":
            st.error("Incorrect CAPTCHA answer.")
        else:
            try:
                _save_submission(name, email, subject, message)
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", 587))
                sender_email = os.getenv("SENDER_EMAIL")
                sender_password = os.getenv("SENDER_PASSWORD")
                receiver_email = os.getenv("RECEIVER_EMAIL", "support@healthaisuperapp.com")
                if sender_email and sender_password:
                    msg = MIMEMultipart()
                    msg["From"] = sender_email
                    msg["To"] = receiver_email
                    msg["Subject"] = subject
                    body = "Name: " + name + chr(10) + "Email: " + email + chr(10) + chr(10) + message
                    msg.attach(MIMEText(body, "plain"))
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, receiver_email, msg.as_string())
                st.success("Thank you for your message! We'll get back to you soon.")
                logging.info("Contact form submitted: Name=%s", name)
            except Exception as exc:
                st.error(f"Error submitting form: {exc}")
                logging.error("Contact form error: %s", exc)

st.markdown("""
<div style='max-width:1200px;margin:2rem auto;text-align:center;'>
    <h2 style='margin-bottom:1.5rem;'>Get in Touch</h2>
    <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.5rem;'>
        <div class="mission-card"><p style='font-weight:500;'>Email</p><p>support@healthaisuperapp.com</p></div>
        <div class="mission-card"><p style='font-weight:500;'>Location</p><p>Peshawar, Pakistan</p></div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.logged_in:
    st.session_state.last_activity = datetime.now()

render_footer()
