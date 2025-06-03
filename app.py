import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from layout import apply_custom_css, render_header, render_footer
from database import init_db, get_patient_history, authenticate_user, update_user_theme, get_user_predictions, delete_user
import logging
import os
import json
import base64
import streamlit.components.v1 as components
from cryptography.fernet import Fernet
import pyotp
import qrcode
from io import BytesIO
import sqlite3

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Initialize encryption
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher = Fernet(ENCRYPTION_KEY.encode())

# Initialize database
try:
    init_db()
    logging.info("Database initialized successfully")
except Exception as e:
    st.error(f"Failed to initialize database: {e}")
    logging.error(f"Database initialization failed: {e}")

# Initialize session state
def initialize_session_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "user_id": None,
        "redirect_to": "app.py",
        "last_activity": datetime.now(),
        "theme": "light",
        "page_transition": False,
        "header_rendered": False,
        "footer_rendered": False,
        "language": "en",
        "notifications": [],
        "2fa_secret": None,
        "2fa_enabled": False,
        "analytics": {"page_views": 0, "button_clicks": 0}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    st.session_state.analytics["page_views"] += 1

initialize_session_state()

# Session timeout
SESSION_TIMEOUT = timedelta(minutes=30)
if st.session_state.logged_in and (datetime.now() - st.session_state.last_activity) > SESSION_TIMEOUT:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.redirect_to = "app.py"
    st.session_state.notifications.append({"type": "warning", "message": "Session timed out. Please log in again."})
    logging.info("Session timed out for user")

# Set page configuration
st.set_page_config(
    page_title="Didar AI/ML Solutions",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Localization
LANGUAGES = {
    "en": {
        "title": "Empowering Healthcare with AI-Driven Diagnostics",
        "subtitle": "Precision diagnostics for Diabetes, Parkinson's, and Pneumonia.",
        "cta_text": "Get Started Now",
        "services_title": "Our AI-Powered Health Solutions",
        "login": "Login",
        "logout": "Logout",
        "records": "Your Health Records",
        "search_placeholder": "Search records",
        "download_csv": "Download Records as CSV",
        "theme_toggle": "Toggle Theme",
        "profile": "Profile",
        "delete_account": "Delete Account",
        "2fa_setup": "Setup 2FA",
        "2fa_verify": "Verify 2FA Code"
    },
    "es": {
        "title": "Potenciando la atención médica con diagnósticos impulsados por IA",
        "subtitle": "Diagnósticos precisos para diabetes, Parkinson y neumonía.",
        "cta_text": "Comience ahora",
        "services_title": "Nuestras soluciones de salud impulsadas por IA",
        "login": "Iniciar sesión",
        "logout": "Cerrar sesión",
        "records": "Sus registros de salud",
        "search_placeholder": "Buscar registros",
        "download_csv": "Descargar registros como CSV",
        "theme_toggle": "Cambiar tema",
        "profile": "Perfil",
        "delete_account": "Eliminar cuenta",
        "2fa_setup": "Configurar 2FA",
        "2fa_verify": "Verificar código 2FA"
    }
}

# Theme toggle
def toggle_theme():
    new_theme = "dark" if st.session_state.theme == "light" else "light"
    st.session_state.theme = new_theme
    if st.session_state.logged_in:
        try:
            update_user_theme(st.session_state.user_id, new_theme)
            logging.info(f"Theme updated to {new_theme} for user_id {st.session_state.user_id}")
        except Exception as e:
            logging.error(f"Failed to update theme: {e}")
    apply_custom_css(st.session_state.theme)

# Apply CSS and render header
try:
    apply_custom_css(st.session_state.theme)
    if not st.session_state.header_rendered:
        render_header()
        st.session_state.header_rendered = True
except Exception as e:
    st.error(f"Error rendering header: {e}")
    logging.error(f"Header rendering failed: {e}")

# Page transition
if st.session_state.get("page_transition", False):
    st.markdown("""
    <style>
        .page-transition { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    """, unsafe_allow_html=True)
    st.session_state.page_transition = False

# Notifications
def display_notifications():
    for notif in st.session_state.notifications:
        if notif["type"] == "success":
            st.success(notif["message"])
        elif notif["type"] == "warning":
            st.warning(notif["message"])
        elif notif["type"] == "error":
            st.error(notif["message"])
    st.session_state.notifications = []

display_notifications()

# Breadcrumbs
def render_breadcrumbs():
    st.markdown("""
    <nav aria-label="Breadcrumb" class="page-transition">
        <ol style='display: flex; gap: 0.5rem; list-style: none; margin: 1rem 0; font-size: 0.9rem;'>
            <li><a href='/' style='color: var(--primary-color); text-decoration: none;' aria-current='page'>Home</a></li>
        </ol>
    </nav>
    """, unsafe_allow_html=True)

render_breadcrumbs()

# Hero Section
lang = LANGUAGES[st.session_state.language]
hero_config = {
    "title": lang["title"],
    "subtitle": lang["subtitle"],
    "cta_text": lang["cta_text"],
    "cta_link": "/login"
}
st.markdown(
    f"""
    <div class="hero page-transition" role="banner" aria-labelledby="hero-title">
        <h1 id="hero-title" style='font-size: 3rem; margin-bottom: 1.5rem;'>{hero_config['title']}</h1>
        <p class="subtitle" style='font-size: 1.3rem; max-width: 700px; margin: 0 auto 2rem;'>{hero_config['subtitle']}</p>
        <a href="{hero_config['cta_link']}" class="cta-button" aria-label="{hero_config['cta_text']}">{hero_config['cta_text']}</a>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    pages = ["Home", "Diabetes Detection", "Parkinson's Disease Detection", "Pneumonia Detection", "About", "Contact", "Privacy", "Login"]
    selection = st.selectbox("Select Page", pages, key="nav_select", help="Navigate to a page")
    if st.button("Go", key="navigate_button", use_container_width=True):
        st.session_state.analytics["button_clicks"] += 1
        try:
            if selection != "Home":
                page_map = {
                    "Diabetes Detection": "pages/diabetes.py",
                    "Parkinson's Disease Detection": "pages/parkinsons.py",
                    "Pneumonia Detection": "pages/pneumonia.py",
                    "About": "pages/about.py",
                    "Contact": "pages/contact.py",
                    "Privacy": "pages/privacy.py",
                    "Login": "pages/login.py"
                }
                if selection in page_map:
                    st.session_state.redirect_to = page_map[selection]
                    st.session_state.page_transition = True
                    if not st.session_state.logged_in and selection not in ["About", "Contact", "Privacy", "Login"]:
                        st.session_state.redirect_to = page_map[selection]
                        st.switch_page("pages/login.py")
                    else:
                        st.switch_page(page_map[selection])
                    logging.info(f"Navigated to {selection}")
                else:
                    st.error(f"Page {selection} not found.")
                    logging.error(f"Invalid page selection: {selection}")
        except Exception as e:
            st.error(f"Error navigating to {selection}: {e}")
            logging.error(f"Navigation error to {selection}: {e}")

    st.markdown("---")
    st.title("Preferences")
    st.selectbox("Language", ["English", "Spanish"], key="lang_select", on_change=lambda: st.session_state.update({"language": "es" if st.session_state.lang_select == "Spanish" else "en"}))
    if st.button(lang["theme_toggle"], key="theme_toggle", use_container_width=True):
        st.session_state.analytics["button_clicks"] += 1
        toggle_theme()
        st.rerun()

# Session timeout warning
if st.session_state.logged_in:
    time_left = SESSION_TIMEOUT - (datetime.now() - st.session_state.last_activity)
    if time_left < timedelta(minutes=5):
        st.markdown(
            f"""
            <div role="alert" aria-live="assertive">
                <p>Session expires in {int(time_left.total_seconds() // 60)} minutes. Interact to extend.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Extend Session", key="extend_session"):
            st.session_state.analytics["button_clicks"] += 1
            st.session_state.last_activity = datetime.now()
            st.rerun()

# Authentication
if not st.session_state.logged_in:
    st.warning(f"Log in or sign up to access advanced health solutions.")
    with st.form("quick_login", clear_on_submit=True):
        st.markdown('<div class="form-container" role="form" aria-label="Quick Login Form">', unsafe_allow_html=True)
        st.markdown('<label class="form-label" for="quick_username">Username</label>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter username", key="quick_username", label_visibility="hidden")
        st.markdown('<label class="form-label" for="quick_password">Password</label>', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", placeholder="Enter password", key="quick_password", label_visibility="hidden")
        if st.session_state.get("2fa_enabled", False):
            st.markdown('<label class="form-label" for="2fa_code">2FA Code</label>', unsafe_allow_html=True)
            tfa_code = st.text_input("2FA Code", placeholder="Enter 6-digit code", key="2fa_code", label_visibility="hidden")
        else:
            tfa_code = None
        col_submit, _ = st.columns([1, 3])
        with col_submit:
            if st.form_submit_button(lang["login"], use_container_width=True):
                st.session_state.analytics["button_clicks"] += 1
                try:
                    user = authenticate_user(username, password)
                    if user:
                        if st.session_state.get("2fa_enabled") and tfa_code:
                            totp = pyotp.TOTP(st.session_state["2fa_secret"])
                            if not totp.verify(tfa_code):
                                st.error("Invalid 2FA code.")
                                logging.warning(f"Invalid 2FA for {username}")
                                
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = user[0]
                        st.session_state.last_activity = datetime.now()
                        st.session_state.theme = user[4] if user[4] else "light"
                        st.session_state.notifications.append({"type": "success", "message": f"Welcome back, {username}!"})
                        logging.info(f"User {username} logged in")
                        apply_custom_css(st.session_state.theme)
                        if st.session_state.redirect_to != "app.py":
                            st.session_state.page_transition = True
                            st.switch_page(st.session_state.redirect_to)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        logging.warning(f"Failed login for {username}")
                except Exception as e:
                    st.error(f"Login error: {e}")
                    logging.error(f"Login error for {username}: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success(f"Logged in as {st.session_state.username}")
    if st.button(lang["logout"], key="logout_button", use_container_width=True):
        st.session_state.analytics["button_clicks"] += 1
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.redirect_to = "app.py"
        st.session_state.page_transition = True
        st.session_state.header_rendered = False
        st.session_state.footer_rendered = False
        st.session_state.notifications.append({"type": "success", "message": "Logged out successfully."})
        logging.info(f"User {st.session_state.username} logged out")
        st.rerun()

# Services Section
services_data = {
    "Diabetes Detection": {
        "label": "Diabetes Prediction",
        "desc": "Assess diabetes risk with high-precision machine learning models.",
        "link": "pages/diabetes.py",
        "icon": "🩺"
    },
    "Parkinson's Disease Detection": {
        "label": "Parkinson’s Speech Analysis",
        "desc": "Detect early signs of Parkinson’s through voice pattern analysis.",
        "link": "pages/parkinsons.py",
        "icon": "🎙️"
    },
    "Pneumonia Detection": {
        "label": "Pneumonia X-Ray Analysis",
        "desc": "Identify pneumonia using advanced X-ray image analysis.",
        "link": "pages/pneumonia.py",
        "icon": "🩻"
    }
}
st.markdown(
    f"""
    <div class="services-section page-transition" role="region" aria-labelledby="services-title">
        <h2 id="services-title" class="section-title" style='text-align: center; margin-bottom: 2.5rem; font-size: 2rem;'>{lang["services_title"]}</h2>
        <div class="services-grid">
    """,
    unsafe_allow_html=True
)
for service, data in services_data.items():
    st.markdown(
        f"""
        <div class="service-card" role="article" aria-label="{data['label']}" data-tooltip="{data['desc']}">
            <div style='font-size: 2.5rem; margin-bottom: 1rem;'>{data['icon']}</div>
            <h3 style='margin-bottom: 1rem; font-size: 1.5rem;'>{service}</h3>
            <p style='margin-bottom: 1.5rem;'>{data['desc']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    button_key = f"service_{service.lower().replace(' ', '_')}"
    if not st.session_state.logged_in:
        if st.button("Log in to Access", key=f"login_{button_key}", use_container_width=True):
            st.session_state.analytics["button_clicks"] += 1
            st.session_state.redirect_to = data["link"]
            st.session_state.page_transition = True
            st.switch_page("pages/login.py")
    else:
        if st.button(f"Explore {service}", key=button_key, use_container_width=True):
            st.session_state.analytics["button_clicks"] += 1
            try:
                st.session_state.redirect_to = data["link"]
                st.session_state.page_transition = True
                st.switch_page(data["link"])
                logging.info(f"User accessed {service}")
            except Exception as e:
                st.error(f"Error navigating to {service}: {e}")
                logging.error(f"Navigation error to {service}: {e}")
st.markdown("</div></div>", unsafe_allow_html=True)

# Dashboard and Records
if st.session_state.logged_in:
    st.subheader(lang["records"], anchor="health-records")
    with st.expander("Dashboard", expanded=True):
        try:
            predictions = get_user_predictions(st.session_state.user_id)
            if not predictions.empty:
                st.markdown('<div class="card" role="region" aria-label="Prediction Summary">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Predictions", len(predictions))
                    pred_types = predictions["prediction_type"].value_counts()
                    st.write("Predictions by Type:")
                    for ptype, count in pred_types.items():
                        st.write(f"{ptype}: {count}")
                with col2:
                    fig = px.line(
                        predictions.sort_values("timestamp"),
                        x="timestamp",
                        y="probability",
                        color="prediction_type",
                        title="Prediction Confidence",
                        labels={"probability": "Confidence (%)", "timestamp": "Date"},
                        height=300
                    )
                    st.plotly_chart(fig)
                st.markdown('</div>', unsafe_allow_html=True)
            history = get_patient_history(st.session_state.user_id)
            if not history.empty:
                st.markdown('<div class="card" role="region" aria-label="Health Metrics">', unsafe_allow_html=True)
                st.write("Latest Health Metrics:")
                latest = history.iloc[0]
                st.write(f"BMI: {latest['bmi']:.2f}")
                st.write(f"General Health: {['Excellent', 'Very Good', 'Good', 'Fair', 'Poor'][latest['gen_health']-1]}")
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning("Unable to load dashboard data.")
            logging.error(f"Dashboard error: {e}")

    with st.expander("Search & Filter Records", expanded=False):
        st.markdown('<div class="form-container" role="form" aria-label="Health Records Filter">', unsafe_allow_html=True)
        search_query = st.text_input(
            lang["search_placeholder"],
            key="search_input",
            placeholder=lang["search_placeholder"],
            help="Search across all fields"
        )
        try:
            history_columns = list(get_patient_history(st.session_state.user_id).columns)
            filter_column = st.selectbox("Filter by", options=["All"] + history_columns, key="filter_column")
            sort_by = st.selectbox("Sort by", options=["None"] + history_columns, key="sort_by")
        except Exception as e:
            st.warning("No health records available for filtering/sorting.")
            filter_column = "All"
            sort_by = "None"
        sort_order = st.radio("Sort order", options=["Ascending", "Descending"], key="sort_order", horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Real-time search
        components.html(
            f"""
            <script>
                const searchInput = document.querySelector('input[aria-label="{lang['search_placeholder']}"]');
                searchInput.addEventListener('input', () => {{
                    const rows = document.querySelectorAll('.stDataFrame tr');
                    const query = searchInput.value.toLowerCase();
                    rows.forEach(row => {{
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(query) ? '' : 'none';
                    }});
                }});
            </script>
            """,
            height=0
        )

    page_size = st.slider("Records per page", min_value=5, max_value=50, value=10, step=5, key="page_size")
    page = st.number_input("Page", min_value=1, value=1, step=1, key="page_select", help="Navigate to a page")

    try:
        @st.cache_data(ttl=300)
        def cached_patient_history(user_id, _timestamp, page, page_size):
            query = """
                SELECT * FROM patients
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            offset = (page - 1) * page_size
            with sqlite3.connect("health_data.db") as conn:
                df = pd.read_sql_query(query, conn, params=(user_id, page_size, offset))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM patients WHERE user_id = ?", (user_id,))
                total_count = cursor.fetchone()[0]
            return df, total_count

        history, total_records = cached_patient_history(st.session_state.user_id, datetime.now().timestamp(), page, page_size)
        if not history.empty:
            filtered_history = history.copy()
            if search_query:
                filtered_history = filtered_history[filtered_history.apply(
                    lambda row: search_query.lower() in str(row).lower(), axis=1
                )]
            if filter_column != "All":
                filtered_history = filtered_history[filtered_history[filter_column].notna()]
            if sort_by != "None":
                filtered_history = filtered_history.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))

            total_pages = (total_records + page_size - 1) // page_size
            page = min(page, total_pages) if total_pages > 0 else 1
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            if total_records > 0:
                st.markdown(
                    f"""
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <span>Showing {start_idx + 1}-{min(end_idx, total_records)} of {total_records} records</span>
                        <span>Page {page} of {total_pages}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.dataframe(
                    filtered_history,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": "Date & Time",
                        "probability": st.column_config.NumberColumn("Probability", format="%.2f"),
                        "bmi": st.column_config.NumberColumn("BMI", format="%.2f")
                    }
                )

                csv = filtered_history.to_csv(index=False)
                st.download_button(
                    label=lang["download_csv"],
                    data=csv,
                    file_name=f"health_records_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_csv",
                    use_container_width=True
                )
            else:
                st.info("No matching records found.")
        else:
            st.info("No health records available.")
        logging.info(f"Health records displayed for user_id {st.session_state.user_id}")
    except Exception as e:
        st.error(f"Error retrieving records: {e}")
        logging.error(f"Error retrieving health records: {e}")

    # Profile Management
    with st.expander(lang["profile"], expanded=False):
        st.markdown('<div class="form-container" role="form" aria-label="Profile Management">', unsafe_allow_html=True)
        new_email = st.text_input("Update Email", value="", placeholder="New email address")
        if st.button("Update Email", key="update_email"):
            st.session_state.analytics["button_clicks"] += 1
            st.warning("Email update not implemented yet.")
        if not st.session_state.get("2fa_enabled"):
            if st.button(lang["2fa_setup"], key="setup_2fa"):
                st.session_state.analytics["button_clicks"] += 1
                secret = pyotp.random_base32()
                st.session_state["2fa_secret"] = secret
                totp = pyotp.TOTP(secret)
                uri = totp.provisioning_uri(st.session_state.username, issuer_name="Didar AI/ML Solutions")
                qr = qrcode.make(uri)
                buffered = BytesIO()
                qr.save(buffered, format="PNG")
                qr_base64 = base64.b64encode(buffered.getvalue()).decode()
                st.image(f"data:image/png;base64,{qr_base64}", caption="Scan with Authenticator App")
                tfa_code = st.text_input("Enter 6-digit Code to Verify", key="verify_2fa_code")
                if st.button(lang["2fa_verify"], key="verify_2fa"):
                    st.session_state.analytics["button_clicks"] += 1
                    if totp.verify(tfa_code):
                        st.session_state["2fa_enabled"] = True
                        st.success("2FA enabled successfully!")
                        logging.info(f"2FA enabled for user_id {st.session_state.user_id}")
                    else:
                        st.error("Invalid 2FA code.")
                        logging.warning(f"Invalid 2FA verification for user_id {st.session_state.user_id}")
        if st.button(lang["delete_account"], key="delete_account"):
            st.session_state.analytics["button_clicks"] += 1
            if st.button("Confirm Account Deletion", key="confirm_delete"):
                try:
                    delete_user(st.session_state.user_id)
                    st.session_state.logged_in = False
                    st.session_state.username = ""
                    st.session_state.user_id = None
                    st.session_state.redirect_to = "app.py"
                    st.session_state.notifications.append({"type": "success", "message": "Account deleted successfully."})
                    logging.info(f"User {st.session_state.user_id} deleted account")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting account: {e}")
                    logging.error(f"Account deletion error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# Update last activity
if st.session_state.logged_in:
    st.session_state.last_activity = datetime.now()

# Render footer
try:
    if not st.session_state.footer_rendered:
        render_footer()
        st.session_state.footer_rendered = True
except Exception as e:
    st.error(f"Error rendering footer: {e}")
    logging.error(f"Footer rendering failed: {e}")

# JavaScript for accessibility
st.markdown(
    """
    <script>
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
        // Focus management
        document.addEventListener('DOMContentLoaded', () => {
            const firstFocusable = document.querySelector('a, button, input, select, textarea');
            if (firstFocusable) firstFocusable.focus();
        });
        // ARIA live region updates
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('role', 'status');
        liveRegion.style.position = 'absolute';
        liveRegion.style.left = '-9999px';
        document.body.appendChild(liveRegion);
        function announce(message) {
            liveRegion.textContent = message;
        }
    </script>
    """,
    unsafe_allow_html=True
)

# Save analytics
try:
    with open("analytics.json", "w") as f:
        json.dump(st.session_state.analytics, f)
except Exception as e:
    logging.error(f"Error saving analytics: {e}")