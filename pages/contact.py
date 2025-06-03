import streamlit as st
from layout import apply_custom_css, render_header, render_footer
from database import update_user_theme
from datetime import datetime, timedelta
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set page configuration
st.set_page_config(
    page_title="Contact | Didar AI/ML Solutions",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = "app.py"
if "last_activity" not in st.session_state:
    st.session_state.last_activity = datetime.now()
if "page_transition" not in st.session_state:
    st.session_state.page_transition = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# Session timeout (30 minutes)
SESSION_TIMEOUT = timedelta(minutes=30)
if st.session_state.logged_in and (datetime.now() - st.session_state.last_activity) > SESSION_TIMEOUT:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.redirect_to = "app.py"
    st.warning("Session timed out. Please log in again.")
    logging.info("Session timed out for user")

# Theme toggle with database sync
def toggle_theme():
    new_theme = "dark" if st.session_state.theme == "light" else "light"
    st.session_state.theme = new_theme
    if st.session_state.logged_in:
        try:
            update_user_theme(st.session_state.user_id, new_theme)
            logging.info(f"Theme updated to {new_theme} for user_id {st.session_state.user_id}")
        except Exception as e:
            logging.error(f"Failed to update theme in database: {e}")
    apply_custom_css(st.session_state.theme)

# Apply CSS and render header
try:
    apply_custom_css(st.session_state.theme)
    render_header()
except Exception as e:
    st.error(f"Error rendering header: {e}")
    logging.error(f"Header rendering failed: {e}")

# Page transition animation
if st.session_state.page_transition:
    st.markdown("""
    <style>
        .page-transition {
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)
    st.session_state.page_transition = False

# Breadcrumbs
def render_breadcrumbs():
    st.markdown("""
    <nav aria-label="Breadcrumb">
        <ol style='display: flex; gap: 0.5rem; list-style: none; margin: 1rem 0; font-size: 0.9rem;'>
            <li><a href='/' style='color: var(--primary-color); text-decoration: none;' aria-current='false'>Home</a></li>
            <li style='color: var(--text-color);'> > </li>
            <li><span aria-current='page'>Contact</span></li>
        </ol>
    </nav>
    """, unsafe_allow_html=True)

render_breadcrumbs()

# Sidebar for navigation and theme toggle
with st.sidebar:
    st.title("Navigation")
    pages = ["Home", "Diabetes Detection", "Parkinson's Detection", "Pneumonia Detection", "About", "Contact", "Privacy Policy", "Login"]
    selection = st.selectbox("Go to", pages, index=pages.index("Contact"), key="nav_select", help="Select a page to navigate")
    if st.button("Navigate", key="navigate_button", use_container_width=True):
        try:
            if selection != "Contact":
                page_map = {
                    "Home": "app.py",
                    "Diabetes Detection": "pages/diabetes.py",
                    "Parkinson's Detection": "pages/parkinsons.py",
                    "Pneumonia Detection": "pages/pneumonia.py",
                    "About": "pages/about.py",
                    "Privacy Policy": "pages/privacy.py",
                    "Login": "pages/login.py"
                }
                st.session_state.redirect_to = page_map[selection]
                st.session_state.page_transition = True
                if not st.session_state.logged_in and selection not in ["Home", "About", "Contact", "Privacy Policy"]:
                    st.switch_page("pages/login.py")
                else:
                    st.switch_page(page_map[selection])
            logging.info(f"Navigated to {selection}")
        except Exception as e:
            st.error(f"Error navigating to {selection}: {e}")
            logging.error(f"Navigation error to {selection}: {e}")

    st.markdown("---")
    st.title("Preferences")
    if st.button("Toggle Light/Dark Mode", key="theme_toggle", use_container_width=True):
        toggle_theme()
        st.rerun()

# Session timeout warning
if st.session_state.logged_in:
    time_left = SESSION_TIMEOUT - (datetime.now() - st.session_state.last_activity)
    if time_left < timedelta(minutes=5):
        st.warning(f"Session will expire in {int(time_left.total_seconds() // 60)} minutes. Interact to extend.")
        if st.button("Extend Session", key="extend_session"):
            st.session_state.last_activity = datetime.now()
            st.rerun()

# Contact Section with Hero
st.markdown("""
<div class="contact-section page-transition" role="region" aria-label="Contact Didar AI/ML Solutions">
    <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>Contact Us</h1>
    <p class="subtitle" style='text-align: center; font-size: 1.2rem; max-width: 800px; margin: 0 auto;'>We’re here to answer your questions or discuss partnerships. Reach out today!</p>
</div>
""", unsafe_allow_html=True)

# Contact Form
def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def save_contact_submission(name, email, subject, message):
    """Save contact form submission to database."""
    try:
        conn = sqlite3.connect('health_data.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute("INSERT INTO contact_submissions (name, email, subject, message) VALUES (?, ?, ?, ?)",
                  (name, email, subject, message))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error saving contact submission: {e}")
        raise Exception(f"Database error: {e}")
    finally:
        conn.close()

st.markdown("""
<div class="form-container page-transition" role="form" aria-label="Contact Form" style='max-width: 600px; margin: 2rem auto;'>
    <h2 style='text-align: center; margin-bottom: 1.5rem;'>Send Us a Message</h2>
""", unsafe_allow_html=True)

with st.form("contact_form", clear_on_submit=True):
    st.markdown('<label class="form-label" for="contact_name">Name</label>', unsafe_allow_html=True)
    name = st.text_input("Name", placeholder="Your full name", key="contact_name", label_visibility="hidden")
    st.markdown('<label class="form-label" for="contact_email">Email</label>', unsafe_allow_html=True)
    email = st.text_input("Email", placeholder="Your email address", key="contact_email", label_visibility="hidden")
    st.markdown('<label class="form-label" for="contact_subject">Subject</label>', unsafe_allow_html=True)
    subject = st.text_input("Subject", placeholder="Subject of your message", key="contact_subject", label_visibility="hidden")
    st.markdown('<label class="form-label" for="contact_message">Message</label>', unsafe_allow_html=True)
    message = st.text_area("Message", placeholder="Your message or inquiry", key="contact_message", label_visibility="hidden")
    # Simple CAPTCHA
    captcha_answer = st.text_input("What is 2 + 3?", placeholder="Enter answer", key="captcha")
    submit_button = st.form_submit_button("Send Message", use_container_width=True)

    if submit_button:
        try:
            # Validate inputs
            if not name.strip():
                st.error("Name is required.")
                logging.warning("Contact form submission failed: Name missing")
            elif not email.strip() or not validate_email(email):
                st.error("Please enter a valid email address.")
                logging.warning(f"Contact form submission failed: Invalid email {email}")
            elif not subject.strip():
                st.error("Subject is required.")
                logging.warning("Contact form submission failed: Subject missing")
            elif not message.strip():
                st.error("Message is required.")
                logging.warning("Contact form submission failed: Message missing")
            elif captcha_answer.strip() != "5":
                st.error("Incorrect CAPTCHA answer. Please try again.")
                logging.warning("Contact form submission failed: Incorrect CAPTCHA")
            else:
                # Save to database
                save_contact_submission(name, email, subject, message)

                # SMTP configuration from .env
                smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
                smtp_port = int(os.getenv("SMTP_PORT", 587))
                sender_email = os.getenv("SENDER_EMAIL")
                sender_password = os.getenv("SENDER_PASSWORD")
                receiver_email = os.getenv("RECEIVER_EMAIL", "support@healthaisuperapp.com")

                if not all([sender_email, sender_password]):
                    st.error("Email configuration missing. Please contact support directly.")
                    logging.error("Contact form submission failed: Missing SMTP credentials")
                else:
                    # Prepare email
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = receiver_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(f"Name: {name}\nEmail: {email}\n\n{message}", 'plain'))

                    # Send email
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, receiver_email, msg.as_string())

                    st.session_state.form_submitted = True
                    st.success("Thank you for your message! We’ll get back to you soon.")
                    logging.info(f"Contact form submitted and email sent: Name={name}, Email={email}, Subject={subject}")
        except smtplib.SMTPAuthenticationError:
            st.error("Invalid email credentials. Please check SMTP configuration.")
            logging.error("Contact form submission failed: SMTP authentication error")
        except smtplib.SMTPException as e:
            st.error(f"Failed to send email: {e}")
            logging.error(f"Contact form submission failed: SMTP error - {e}")
        except Exception as e:
            st.error(f"Error submitting form: {e}")
            logging.error(f"Contact form submission error: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# Display success message
if st.session_state.form_submitted:
    st.markdown("""
    <div class="success-message page-transition" style='text-align: center; margin: 1rem 0; max-width: 600px; margin-left: auto; margin-right: auto;'>
        <p>Your message has been sent successfully. Expect a response within 24-48 hours.</p>
    </div>
    """, unsafe_allow_html=True)

# Contact Information Section
st.markdown("""
<div class="contact-info-section page-transition" style='max-width: 1200px; margin: 2rem auto; text-align: center;'>
    <h2 style='margin-bottom: 1.5rem;'>Get in Touch</h2>
    <p style='margin-bottom: 1.5rem;'>Reach us directly via email or visit us at our office.</p>
    <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;'>
        <div class="contact-card service-card">
            <p style='font-weight: 500; margin-bottom: 0.5rem;'>Email</p>
            <p><a href="mailto:support@healthaisuperapp.com" class="cta-button" style='display: inline-block; padding: 0.5rem 1rem;'>support@healthaisuperapp.com</a></p>
        </div>
        <div class="contact-card service-card">
            <p style='font-weight: 500; margin-bottom: 0.5rem;'>Location</p>
            <p>Peshawar, Pakistan</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Update last activity
if st.session_state.logged_in:
    st.session_state.last_activity = datetime.now()

# Render footer
try:
    render_footer()
except Exception as e:
    st.error(f"Error rendering footer: {e}")
    logging.error(f"Footer rendering failed: {e}")

# JavaScript for accessibility and smooth scrolling
st.markdown("""
<script>
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    // Focus management for accessibility
    document.addEventListener('DOMContentLoaded', () => {
        const firstFocusable = document.querySelector('a, button, input, select, textarea');
        if (firstFocusable) firstFocusable.focus();
    });
</script>
""", unsafe_allow_html=True)