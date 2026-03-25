import re
import time
from datetime import datetime, timedelta

import streamlit as st

from auth import init_session_state
from database import authenticate_user, create_reset_token, get_user_by_email, register_user
from layout import apply_custom_css, render_footer, render_header

st.set_page_config(
    page_title="Login - Health AI Super App",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state()

# Rate-limit keys not in SESSION_DEFAULTS — init independently
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0
if "last_attempt_time" not in st.session_state:
    st.session_state.last_attempt_time = None

apply_custom_css(st.session_state.theme)
render_header()

contact_config = {"admin_email": "didarali1129@gmail.com"}

if st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>You are logged in</h1>", unsafe_allow_html=True)
    st.write(f"Logged in as: {st.session_state.username}")
    if st.button("Go to Home", use_container_width=True):
        st.switch_page("app.py")
    render_footer()
    st.stop()

st.markdown("<h1 style='text-align:center;' role='heading' aria-level='1'>Account Access</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; max-width:600px; margin:1rem auto;'>Access our AI-driven health diagnostics by logging in, signing up, or resetting your password.</p>", unsafe_allow_html=True)

col_left, col_main, col_right = st.columns([1, 3, 1])
with col_main:
    tab_login, tab_signup, tab_forgot = st.tabs(["Login", "Sign Up", "Forgot Password"])

    MAX_ATTEMPTS = 3
    ATTEMPT_WINDOW = timedelta(minutes=5)
    if st.session_state.last_attempt_time and (datetime.now() - st.session_state.last_attempt_time) > ATTEMPT_WINDOW:
        st.session_state.login_attempts = 0
        st.session_state.last_attempt_time = None

    with tab_login:
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Your password", key="login_password")
            submit_button = st.form_submit_button("Login", use_container_width=True, disabled=(st.session_state.login_attempts >= MAX_ATTEMPTS))

            if submit_button:
                time.sleep(1)
                if st.session_state.login_attempts >= MAX_ATTEMPTS:
                    wait_secs = (ATTEMPT_WINDOW - (datetime.now() - st.session_state.last_attempt_time)).seconds
                    st.error(f"Too many login attempts. Please wait {wait_secs // 60} minutes.")
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
                            redirect_page = st.session_state.redirect_to
                            st.session_state.redirect_to = "app.py"
                            try:
                                st.switch_page(redirect_page)
                            except Exception:
                                st.switch_page("app.py")
                        else:
                            st.session_state.login_attempts += 1
                            st.session_state.last_attempt_time = datetime.now()
                            remaining = MAX_ATTEMPTS - st.session_state.login_attempts
                            st.error(f"Invalid username or password. {remaining} attempts remaining.")
                    except Exception as e:
                        st.error(f"Login error: {e}")

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            new_username = st.text_input("Username", placeholder="Choose a username (4+ chars)", key="signup_username")
            new_email = st.text_input("Email", placeholder="Your email address", key="signup_email")
            new_password = st.text_input("Password", type="password", placeholder="Create a password (8+ chars)", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm")
            captcha_checked = st.checkbox("I am not a robot", key="signup_captcha")
            submit_button = st.form_submit_button("Sign Up", use_container_width=True)

            if submit_button:
                time.sleep(1)
                if not all([new_username, new_email, new_password, confirm_password]):
                    st.error("All fields are required.")
                elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", new_email):
                    st.error("Please enter a valid email address.")
                elif not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", new_password):
                    st.error("Password must be 8+ chars with 1 uppercase, 1 number, 1 special character.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_username) < 4:
                    st.error("Username must be at least 4 characters.")
                elif not captcha_checked:
                    st.error("Please verify you are not a robot.")
                else:
                    try:
                        if register_user(new_username, new_password, new_email):
                            st.success("Account created successfully! Please log in.")
                        else:
                            st.error("Username or email already exists.")
                    except Exception as e:
                        st.error(f"Signup error: {e}")

    with tab_forgot:
        with st.form("reset_form", clear_on_submit=True):
            email = st.text_input("Email", placeholder="Your registered email", key="reset_email")
            captcha_checked = st.checkbox("I am not a robot", key="reset_captcha")
            submit_button = st.form_submit_button("Send Reset Link", use_container_width=True)

            if submit_button:
                time.sleep(1)
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
                            create_reset_token(user[0])
                            st.success(f"If an account exists for {email}, a reset link has been sent.")
                        else:
                            # Ambiguous to prevent email enumeration
                            st.success(f"If an account exists for {email}, a reset link has been sent.")
                    except Exception as e:
                        st.error(f"Password reset error: {e}")

render_footer()
