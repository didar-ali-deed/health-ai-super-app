import streamlit as st
from layout import apply_custom_css, render_header, render_footer
from database import authenticate_user, register_user, get_user_by_email, create_reset_token
import re
from datetime import datetime, timedelta
import time

# Set page configuration as the first Streamlit command
st.set_page_config(
    page_title="Login - Health AI Super App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize theme in session state if not set
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Apply custom CSS for forms
def apply_form_css(theme="light"):
    form_css = """
    <style>
        .form-container { max-width: 500px; margin: 2rem auto; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }
        .form-input { width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 10px; font-family: 'Inter', sans-serif; font-size: 1rem; transition: all 0.2s ease; }
        .form-input:focus { border-color: #0055ff; outline: none; box-shadow: 0 0 5px rgba(0, 85, 255, 0.5); }
        .form-label { font-weight: 500; margin-bottom: 0.5rem; display: block; }
        .submit-button { background-color: #0055ff; color: #fff; padding: 0.7rem 1.5rem; border: none; border-radius: 10px; font-weight: 500; cursor: pointer; transition: all 0.2s ease; width: 100%; }
        .submit-button:hover { background-color: #0033cc; transform: translateY(-2px); }
        .submit-button:disabled { background-color: #cccccc; cursor: not-allowed; }
        .tab-content { margin-top: 1rem; }
        .spinner { display: none; text-align: center; margin: 1rem 0; }
        .spinner.active { display: block; }
        .spinner::after { content: '⏳'; font-size: 1.5rem; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @media (max-width: 768px) {
            .form-container { margin: 1rem; padding: 1.5rem; }
            .form-input { font-size: 0.95rem; }
            .submit-button { padding: 0.6rem 1rem; }
        }
    """
    if theme == "dark":
        form_css += """
        .form-container { background-color: #2d3748; border-color: #4b5563; }
        .form-label { color: #e5e7eb; }
        .form-input { background-color: #1f2a44; color: #e5e7eb; border-color: #4b5563; }
        .form-input:focus { border-color: #3b82f6; box-shadow: 0 0 5px rgba(59, 130, 246, 0.5); }
        """
    else:
        form_css += """
        .form-container { background-color: #fff; }
        .form-label { color: #1f2a44; }
        .form-input { background-color: #fff; color: #1f2a44; }
        """
    form_css += "</style>"
    st.markdown(form_css, unsafe_allow_html=True)

# Apply layout and form CSS
try:
    theme = st.session_state.theme
    apply_custom_css(theme)
    apply_form_css(theme)
    render_header()
except Exception as e:
    st.error(f"Error rendering layout: {e}")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.last_activity = datetime.now()
    st.session_state.redirect_to = "app.py"
    st.session_state.login_attempts = 0
    st.session_state.last_attempt_time = None

# Session timeout (30 minutes)
SESSION_TIMEOUT = timedelta(minutes=30)
if st.session_state.logged_in and (datetime.now() - st.session_state.last_activity) > SESSION_TIMEOUT:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.redirect_to = "app.py"
    st.warning("Session timed out. Please log in again.")

# Contact configuration
contact_config = {
    "admin_email": "didarali1129@gmail.com"
}

# Handle logout and theme toggle if logged in
if st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>You are logged in</h1>", unsafe_allow_html=True)
    st.write(f"Logged in as: {st.session_state.username}")
    
    # Theme toggle
    col_theme, col_logout = st.columns([1, 1])
    with col_theme:
        theme_option = st.selectbox(
            "Theme",
            options=["light", "dark"],
            index=0 if st.session_state.theme == "light" else 1,
            key="theme_select"
        )
        if theme_option != st.session_state.theme:
            st.session_state.theme = theme_option
            st.rerun()
    
    with col_logout:
        if st.button("Logout", key="logout_button", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.redirect_to = "app.py"
            st.session_state.last_activity = datetime.now()
            st.session_state.login_attempts = 0
            st.success("Logged out successfully.")
            st.rerun()
    
    try:
        render_footer()
    except Exception as e:
        st.error(f"Error rendering footer: {e}")
    st.stop()

# Main content
st.markdown("<h1 style='text-align: center;' role='heading' aria-level='1'>Account Access</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; max-width: 600px; margin: 1rem auto; font-size: 1.05rem;'>Access our AI-driven health diagnostics by logging in, signing up, or resetting your password.</p>", unsafe_allow_html=True)

# Centered layout
col_left, col_main, col_right = st.columns([1, 3, 1])
with col_main:
    try:
        # Tabs for Login, Sign Up, Forgot Password
        tab_login, tab_signup, tab_forgot = st.tabs(["Login", "Sign Up", "Forgot Password"])

        # Rate limiting (3 attempts per 5 minutes)
        MAX_ATTEMPTS = 3
        ATTEMPT_WINDOW = timedelta(minutes=5)
        if st.session_state.last_attempt_time and (datetime.now() - st.session_state.last_attempt_time) > ATTEMPT_WINDOW:
            st.session_state.login_attempts = 0
            st.session_state.last_attempt_time = None

        # Login Tab
        with tab_login:
            st.markdown('<div class="form-container tab-content" role="form" aria-label="Login Form">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=True):
                st.markdown('<label class="form-label" for="login_username">Username</label>', unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Your username", key="login_username", label_visibility="hidden")
                
                st.markdown('<label class="form-label" for="login_password">Password</label>', unsafe_allow_html=True)
                password = st.text_input("Password", type="password", placeholder="Your password", key="login_password", label_visibility="hidden")
                
                submit_button = st.form_submit_button("Login", use_container_width=True, disabled=(st.session_state.login_attempts >= MAX_ATTEMPTS))

                if submit_button:
                    st.markdown('<div class="spinner active" aria-label="Processing login"></div>', unsafe_allow_html=True)
                    time.sleep(1)  # Simulate processing
                    
                    if st.session_state.login_attempts >= MAX_ATTEMPTS:
                        st.error(f"Too many login attempts. Please wait {(ATTEMPT_WINDOW - (datetime.now() - st.session_state.last_attempt_time)).seconds // 60} minutes or use 'Forgot Password'.")
                    elif not username.strip() or not password.strip():
                        st.error("Username and password are required.")
                    else:
                        try:
                            user = authenticate_user(username, password)
                            if user:
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_id = user[0]
                                st.session_state.last_activity = datetime.now()
                                st.session_state.login_attempts = 0
                                st.success(f"Welcome, {username}!")
                                redirect_page = st.session_state.redirect_to
                                st.session_state.redirect_to = "app.py"
                                try:
                                    st.switch_page(redirect_page)
                                except Exception:
                                    st.switch_page("app.py")
                            else:
                                st.session_state.login_attempts += 1
                                st.session_state.last_attempt_time = datetime.now()
                                st.error(f"Invalid username or password. {MAX_ATTEMPTS - st.session_state.login_attempts} attempts remaining.")
                        except Exception as e:
                            st.error(f"Login error: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Signup Tab
        with tab_signup:
            st.markdown('<div class="form-container tab-content" role="form" aria-label="Sign Up Form">', unsafe_allow_html=True)
            with st.form("signup_form", clear_on_submit=True):
                st.markdown('<label class="form-label" for="signup_username">Username</label>', unsafe_allow_html=True)
                new_username = st.text_input("Username", placeholder="Choose a username (4+ chars)", key="signup_username", label_visibility="hidden")
                
                st.markdown('<label class="form-label" for="signup_email">Email</label>', unsafe_allow_html=True)
                new_email = st.text_input("Email", placeholder="Your email address", key="signup_email", label_visibility="hidden")
                
                st.markdown('<label class="form-label" for="signup_password">Password</label>', unsafe_allow_html=True)
                new_password = st.text_input("Password", type="password", placeholder="Create a password (8+ chars)", key="signup_password", label_visibility="hidden")
                
                st.markdown('<label class="form-label" for="signup_confirm">Confirm Password</label>', unsafe_allow_html=True)
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm", label_visibility="hidden")
                
                # Simulated CAPTCHA
                captcha_checked = st.checkbox("I am not a robot", key="signup_captcha")
                
                submit_button = st.form_submit_button("Sign Up", use_container_width=True)

                if submit_button:
                    st.markdown('<div class="spinner active" aria-label="Processing signup"></div>', unsafe_allow_html=True)
                    time.sleep(1)  # Simulate processing
                    
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.error("All fields are required.")
                    elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", new_email):
                        st.error("Please enter a valid email address.")
                    elif not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", new_password):
                        st.error("Password must be at least 8 characters long, with 1 uppercase letter, 1 number, and 1 special character.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_username) < 4:
                        st.error("Username must be at least 4 characters long.")
                    elif not captcha_checked:
                        st.error("Please verify you are not a robot.")
                    else:
                        try:
                            if register_user(new_username, new_password, new_email):
                                st.session_state.last_activity = datetime.now()
                                st.success("Account created successfully! Please log in.")
                            else:
                                st.error("Username or email already exists.")
                        except Exception as e:
                            st.error(f"Signup error: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Forgot Password Tab
        with tab_forgot:
            st.markdown('<div class="form-container tab-content" role="form" aria-label="Forgot Password Form">', unsafe_allow_html=True)
            with st.form("reset_form", clear_on_submit=True):
                st.markdown('<label class="form-label" for="reset_email">Email</label>', unsafe_allow_html=True)
                email = st.text_input("Email", placeholder="Your registered email", key="reset_email", label_visibility="hidden")
                
                # Simulated CAPTCHA
                captcha_checked = st.checkbox("I am not a robot", key="reset_captcha")
                
                submit_button = st.form_submit_button("Send Reset Link", use_container_width=True)

                if submit_button:
                    st.markdown('<div class="spinner active" aria-label="Processing password reset"></div>', unsafe_allow_html=True)
                    time.sleep(1)  # Simulate processing
                    
                    if not email.strip():
                        st.error("Email is required.")
                    elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                        st.error("Invalid email address.")
                    elif not captcha_checked:
                        st.error("Please verify you are not a robot.")
                    else:
                        try:
                            user = get_user_by_email(email)
                            if user:
                                token = create_reset_token(user[0])
                                st.session_state.last_activity = datetime.now()
                                st.success(f"Password reset link sent to {email}! Check your inbox.")
                                st.info(f"Development mode: Use token '{token}' to reset your password. Contact {contact_config['admin_email']} for assistance.")
                            else:
                                st.error("No account found with this email.")
                        except Exception as e:
                            st.error(f"Password reset error: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error rendering login content: {e}")

# Render footer
try:
    render_footer()
except Exception as e:
    st.error(f"Error rendering footer: {e}")