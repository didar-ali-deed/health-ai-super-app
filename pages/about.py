import streamlit as st
from layout import apply_custom_css, render_header, render_footer
from database import authenticate_user, update_user_theme
from datetime import datetime, timedelta
import logging
import os
import base64

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set page configuration
st.set_page_config(
    page_title="About | Didar AI/ML Solutions",
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
            <li><span aria-current='page'>About</span></li>
        </ol>
    </nav>
    """, unsafe_allow_html=True)

render_breadcrumbs()

# Sidebar for navigation and theme toggle
with st.sidebar:
    st.title("Navigation")
    pages = ["Home", "Diabetes Detection", "Parkinson's Detection", "Pneumonia Detection", "About", "Contact", "Privacy Policy", "Login"]
    selection = st.selectbox("Go to", pages, index=pages.index("About"), key="nav_select", help="Select a page to navigate")
    if st.button("Navigate", key="navigate_button", use_container_width=True):
        try:
            if selection != "About":
                page_map = {
                    "Home": "app.py",
                    "Diabetes Detection": "pages/diabetes.py",
                    "Parkinson's Detection": "pages/parkinsons.py",
                    "Pneumonia Detection": "pages/pneumonia.py",
                    "Contact": "pages/contact.py",
                    "Privacy Policy": "pages/privacy.py",
                    "Login": "pages/login.py"
                }
                st.session_state.redirect_to = page_map[selection]
                st.session_state.page_transition = True
                if not st.session_state.logged_in and selection not in ["Login", "About", "Contact", "Privacy Policy"]:
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

# About Section with Hero
st.markdown("""
<div class="about-section page-transition" role="region" aria-label="About Didar AI/ML Solutions">
    <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>About Didar AI/ML Solutions</h1>
    <p class="subtitle" style='text-align: center; font-size: 1.2rem; max-width: 800px; margin: 0 auto;'>Transforming healthcare with AI-driven diagnostics for a healthier tomorrow.</p>
</div>
""", unsafe_allow_html=True)

# Mission and Vision Section
st.markdown("""
<div class="mission-vision-section page-transition" style='max-width: 1200px; margin: 2rem auto;'>
    <h2 style='text-align: center; margin-bottom: 2rem;'>Our Mission & Vision</h2>
    <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;'>
        <div class="mission-card service-card">
            <h3 style='margin-bottom: 0.75rem;'>Mission</h3>
            <p>Empower individuals and healthcare providers with precise AI diagnostics for early detection of critical conditions like Diabetes, Parkinson's, and Pneumonia.</p>
        </div>
        <div class="vision-card service-card">
            <h3 style='margin-bottom: 0.75rem;'>Vision</h3>
            <p>Lead global healthcare innovation by making AI-powered diagnostics accessible, reliable, and impactful for all communities.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Founder Section
st.markdown("""
<div class="founder-section page-transition" style='max-width: 1200px; margin: 2rem auto;'>
    <h2 style='text-align: center; margin-bottom: 2rem;'>Meet the Founder</h2>
""", unsafe_allow_html=True)

# Load and display founder photo
photo_path = "static/didar_ali.jpg"
photo_fallback = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
photo_base64 = None
try:
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as image_file:
            photo_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        st.markdown(f"""
        <div class="founder-card service-card" style='display: flex; gap: 2rem; align-items: center;'>
            <img src="data:image/jpeg;base64,{photo_base64}" alt="Didar Ali, Founder" style='width: 200px; height: 200px; object-fit: cover; border-radius: 10px;' loading="lazy">
            <div>
                <h3 style='margin-bottom: 0.5rem;'>Didar Ali</h3>
                <p style='font-weight: 500; margin-bottom: 0.75rem;'>Founder & AI Specialist</p>
                <p>Didar Ali is a passionate innovator in AI and machine learning, leading Didar AI/ML Solutions to revolutionize healthcare diagnostics. With expertise in developing high-accuracy AI models, Didar is committed to making early disease detection accessible to all.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"Photo not found at {photo_path}. Using fallback image.")
        st.markdown(f"""
        <div class="founder-card service-card" style='display: flex; gap: 2rem; align-items: center;'>
            <img src="{photo_fallback}" alt="Didar Ali, Founder" style='width: 200px; height: 200px; object-fit: cover; border-radius: 10px;' loading="lazy">
            <div>
                <h3 style='margin-bottom: 0.5rem;'>Didar Ali</h3>
                <p style='font-weight: 500; margin-bottom: 0.75rem;'>Founder & AI Specialist</p>
                <p>Didar Ali is a passionate innovator in AI and machine learning, leading Didar AI/ML Solutions to revolutionize healthcare diagnostics. With expertise in developing high-accuracy AI models, Didar is committed to making early disease detection accessible to all.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading photo: {e}")
    logging.error(f"Photo loading failed: {e}")
    st.markdown("""
    <div class="founder-card service-card">
        <h3 style='margin-bottom: 0.5rem;'>Didar Ali</h3>
        <p style='font-weight: 500; margin-bottom: 0.75rem;'>Founder & AI Specialist</p>
        <p>Didar Ali is a passionate innovator in AI and machine learning, leading Didar AI/ML Solutions to revolutionize healthcare diagnostics. With expertise in developing high-accuracy AI models, Didar is committed to making early disease detection accessible to all.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Team Section
st.markdown("""
<div class="team-section page-transition" style='max-width: 1200px; margin: 2rem auto;'>
    <h2 style='text-align: center; margin-bottom: 2rem;'>Our Team</h2>
    <div class="team-grid" style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;'>
""", unsafe_allow_html=True)

team_members = [
    {"name": "Dr. Ayesha Khan", "role": "Medical Advisor", "bio": "Expert in clinical diagnostics, ensuring our solutions meet medical standards."},
    {"name": "Sarah Ahmed", "role": "Data Scientist", "bio": "Specializes in machine learning models for health data analysis."},
    {"name": "Omar Farooq", "role": "Software Engineer", "bio": "Builds robust platforms to deliver our AI solutions seamlessly."}
]
for member in team_members:
    st.markdown(f"""
        <div class="team-card service-card" role="article" aria-label="Team member {member['name']}">
            <h3 style='margin-bottom: 0.5rem;'>{member['name']}</h3>
            <p style='font-weight: 500; margin-bottom: 0.75rem;'>{member['role']}</p>
            <p>{member['bio']}</p>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

# Achievements Section
st.markdown("""
<div class="achievements-section page-transition" style='max-width: 1200px; margin: 2rem auto;'>
    <h2 style='text-align: center; margin-bottom: 2rem;'>Our Achievements</h2>
    <ul style='list-style-type: disc; padding-left: 1.5rem; max-width: 800px; margin: 0 auto;'>
        <li>Developed AI models with 95%+ accuracy for disease detection.</li>
        <li>Supported over 1,000 users in early health diagnostics.</li>
        <li>Recognized at the 2024 AI Healthcare Innovation Summit.</li>
        <li>Launched Didar AI/ML Solutions in Peshawar, Pakistan, in 2023.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# FAQ Section
st.subheader("Frequently Asked Questions", anchor="faq")
faq_data = [
    {"question": "What is Didar AI/ML Solutions?", "answer": "We are a healthcare technology company using AI to provide accurate diagnostics for conditions like Diabetes, Parkinson's, and Pneumonia."},
    {"question": "How accurate are your AI models?", "answer": "Our models achieve over 95% accuracy, validated against clinical datasets."},
    {"question": "How can I get started?", "answer": "Sign up or log in to access our diagnostic tools. Visit the homepage to get started."},
    {"question": "Where are you based?", "answer": "We are proudly based in Peshawar, Pakistan, serving a global audience."}
]
for faq in faq_data:
    with st.expander(faq["question"], expanded=False):
        st.write(faq["answer"])

# Contact Call-to-Action
st.markdown("""
<div class="contact-cta page-transition" style='text-align: center; margin: 2rem 0; max-width: 800px; margin-left: auto; margin-right: auto;'>
    <h3 style='margin-bottom: 0.75rem;'>Want to Learn More?</h3>
    <p style='margin-bottom: 1rem;'>Contact us for inquiries or partnerships.</p>
""", unsafe_allow_html=True)
if st.button("Contact Us", key="contact_cta", use_container_width=True):
    try:
        st.session_state.redirect_to = "pages/contact.py"
        st.session_state.page_transition = True
        st.switch_page("pages/contact.py")
        logging.info("Navigated to Contact page from About")
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