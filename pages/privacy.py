import streamlit as st
from layout import apply_custom_css, render_header, render_footer
from database import update_user_theme
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set page configuration
st.set_page_config(
    page_title="Privacy Policy | Didar AI/ML Solutions",
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
            <li><span aria-current='page'>Privacy Policy</span></li>
        </ol>
    </nav>
    """, unsafe_allow_html=True)

render_breadcrumbs()

# Sidebar for navigation and theme toggle
with st.sidebar:
    st.title("Navigation")
    pages = ["Home", "Diabetes Detection", "Parkinson's Detection", "Pneumonia Detection", "About", "Contact", "Privacy Policy", "Login"]
    selection = st.selectbox("Go to", pages, index=pages.index("Privacy Policy"), key="nav_select", help="Select a page to navigate")
    if st.button("Navigate", key="navigate_button", use_container_width=True):
        try:
            if selection != "Privacy Policy":
                page_map = {
                    "Home": "app.py",
                    "Diabetes Detection": "pages/diabetes.py",
                    "Parkinson's Detection": "pages/parkinsons.py",
                    "Pneumonia Detection": "pages/pneumonia.py",
                    "About": "pages/about.py",
                    "Contact": "pages/contact.py",
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

# Privacy policy configuration
privacy_config = {
    "last_updated": "June 1, 2025",
    "title": "Privacy Policy",
    "intro": (
        "At Didar AI/ML Solutions, we are committed to safeguarding your privacy. "
        "This Privacy Policy outlines how we collect, use, disclose, and protect your information "
        "when you use our application and services."
    ),
    "sections": [
        {
            "title": "Information We Collect",
            "content": [
                "<strong>Personal Information</strong>: Includes your name, email address, and contact details provided during registration or through our contact form.",
                "<strong>Health Data</strong>: Medical data you input for diagnostics (e.g., diabetes risk factors, voice recordings, or X-ray images), securely stored in our database.",
                "<strong>Usage Data</strong>: Information about your interactions with the app, such as pages visited, features used, and timestamps, to improve our services."
            ]
        },
        {
            "title": "How We Use Your Information",
            "content": [
                "To provide AI-driven health diagnostics and personalized health insights.",
                "To enhance and optimize the app’s functionality and user experience.",
                "To respond to your inquiries and provide customer support.",
                "To comply with legal obligations and ensure the security of our services."
            ]
        },
        {
            "title": "Data Security",
            "content": [
                "We implement industry-standard security measures, including encryption and secure authentication, to protect your data.",
                "While we strive to ensure data security, no system is entirely risk-free, and we cannot guarantee absolute security."
            ]
        },
        {
            "title": "Data Sharing",
            "content": [
                "We do not sell or share your personal information with third parties, except:",
                "<ul><li>With your explicit consent.</li><li>To comply with legal requirements or protect our rights.</li><li>With trusted service providers (e.g., cloud hosting) under strict confidentiality agreements.</li></ul>"
            ]
        },
        {
            "title": "Your Rights",
            "content": [
                "You may access, correct, or request deletion of your personal information.",
                "You can opt out of non-essential data collection by contacting us.",
                "For users in certain jurisdictions (e.g., GDPR regions), additional rights may apply, such as data portability."
            ]
        },
        {
            "title": "Contact Us",
            "content": [
                "For questions or concerns about this Privacy Policy, please reach out:",
                "📧 <a href='mailto:support@healthaisuperapp.com'>support@healthaisuperapp.com</a>",
                "📍 Peshawar, Pakistan"
            ]
        }
    ]
}

# Main content
st.markdown(f"""
<div class='privacy-container page-transition' role='article' aria-label='Privacy Policy' style='max-width: 800px; margin: 2rem auto;'>
    <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>{privacy_config['title']}</h1>
    <p style='text-align: center; font-size: 1.1rem; margin-bottom: 1rem;'>
        Last updated: {privacy_config['last_updated']}
    </p>
    <p class='subtitle' style='line-height: 1.6; margin-bottom: 2rem;'>
        {privacy_config['intro']}
    </p>
</div>
""", unsafe_allow_html=True)

# Render sections
for section in privacy_config["sections"]:
    st.markdown(f"""
    <div class='privacy-section page-transition' style='max-width: 800px; margin: 2rem auto; line-height: 1.6;'>
        <h2 style='margin-bottom: 1rem;'>{section['title']}</h2>
        {'<ul style="list-style-type: disc; padding-left: 1.5rem;">' + ''.join(f'<li>{item}</li>' for item in section['content']) + '</ul>' 
         if section['title'] not in ['Data Sharing', 'Contact Us'] 
         else ''.join(f'<div>{item}</div>' for item in section['content'])}
    </div>
    """, unsafe_allow_html=True)

# Contact CTA
st.markdown("""
<div class="contact-cta page-transition" style='text-align: center; margin: 2rem 0; max-width: 800px; margin-left: auto; margin-right: auto;'>
    <h3 style='margin-bottom: 0.75rem;'>Have Questions?</h3>
    <p style='margin-bottom: 1rem;'>Contact us for inquiries about our privacy practices.</p>
""", unsafe_allow_html=True)
if st.button("Contact Us", key="contact_cta", use_container_width=True):
    try:
        st.session_state.redirect_to = "pages/contact.py"
        st.session_state.page_transition = True
        st.switch_page("pages/contact.py")
        logging.info("Navigated to Contact page from Privacy")
    except Exception as e:
        st.error(f"Error navigating to Contact page: {e}")
        logging.error(f"Navigation error to Contact: {e}")
st.markdown("</div>", unsafe_allow_html=True)

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