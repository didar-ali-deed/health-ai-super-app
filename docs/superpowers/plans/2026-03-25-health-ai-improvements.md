# Health AI Super App — Improvements & Deployment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `app.py` into focused modules, apply Clean Medical visual design, and add Hugging Face Spaces deployment files.

**Architecture:** `app.py` becomes a ~80-line orchestrator that calls `auth.py`, `dashboard.py`, and `profile.py`. `layout.py` gains `render_services()` and loses dead nav href code. `style.css` is rewritten with the Clean Medical design system (`#0052CC` primary, white cards, `#EBF3FF` hero gradient).

**Tech Stack:** Python 3.12, Streamlit 1.45.1, SQLite, cryptography (Fernet), pyotp, qrcode, Plotly, Poppins font.

**Spec:** `docs/superpowers/specs/2026-03-25-health-ai-improvements-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `auth.py` | `get_encryption_key()`, `init_session_state()`, `render_login_form()`, `handle_logout()` |
| Create | `dashboard.py` | `render_dashboard()` — prediction chart, metrics, records table, CSV download |
| Create | `profile.py` | `render_profile()` — theme toggle, 2FA setup, account deletion |
| Create | `tests/test_auth.py` | Unit tests for `get_encryption_key()` |
| Modify | `layout.py` | Add `render_services()`, remove dead nav hrefs from `render_header()` |
| Rewrite | `app.py` | Thin orchestrator: page config first, session init, timeout, layout, route |
| Rewrite | `style.css` | Clean Medical design tokens, all components restyled |
| Modify | `README.md` | Prepend HF Spaces YAML frontmatter |
| Create | `.gitattributes` | Git LFS tracking for model files |
| Modify | `CLAUDE.md` | Add HF Spaces deploy instructions |

**Unchanged:** `database.py`, `pages/`, `diabetes_analysis/`, `speech_analysis/`, `xray_analysis/`, `models/`

---

## Task 1: Create `auth.py`

Extract all authentication logic from `app.py`. This module provides a stable encryption key, session state initialisation, the login form, and the logout handler.

**Files:**
- Create: `auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_auth.py`:

```python
import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_get_encryption_key_returns_valid_fernet_key():
    """Key must be a valid Fernet key (32 url-safe base64 bytes)."""
    from cryptography.fernet import Fernet
    import auth
    key = auth.get_encryption_key()
    assert isinstance(key, str)
    # Should not raise — invalid keys raise ValueError
    Fernet(key.encode())


def test_get_encryption_key_is_stable_across_calls():
    """Calling get_encryption_key() twice returns the same key."""
    import auth
    assert auth.get_encryption_key() == auth.get_encryption_key()


def test_get_encryption_key_respects_env_var(monkeypatch):
    """When ENCRYPTION_KEY env var is set, it must be used."""
    from cryptography.fernet import Fernet
    import importlib
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", test_key)
    import auth as auth_module
    importlib.reload(auth_module)
    assert auth_module.get_encryption_key() == test_key


def test_session_defaults_keys():
    """init_session_state must define the required session keys."""
    import auth
    defaults = auth.SESSION_DEFAULTS
    required = {"logged_in", "username", "user_id", "redirect_to",
                "last_activity", "theme", "notifications",
                "2fa_secret", "2fa_enabled"}
    assert required.issubset(set(defaults.keys()))
```

- [ ] **Step 2: Run tests to confirm they all fail**

```bash
cd "C:\Users\Didar Ali\Desktop\Hello\health-ai-super-app"
python -m pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: Create `auth.py`**

```python
import os
import logging
import base64
from datetime import datetime
from io import BytesIO

import streamlit as st
import pyotp
import qrcode
from cryptography.fernet import Fernet

from database import authenticate_user

# ---------------------------------------------------------------------------
# Encryption key — generated once at module load, stable for process lifetime
# ---------------------------------------------------------------------------
# Generated once when Python imports this module — stable for the lifetime
# of the process. Intentionally NOT stable across process restarts (e.g.
# after a file-save reload during dev). For a portfolio demo this is fine;
# in production, always set the ENCRYPTION_KEY env var.
_DEV_KEY: str = Fernet.generate_key().decode()


def get_encryption_key() -> str:
    """Return the Fernet encryption key.

    Uses ENCRYPTION_KEY env var when set (production / HF Spaces secret).
    Falls back to a per-process key for local dev — good enough for a demo.
    """
    return os.environ.get("ENCRYPTION_KEY", _DEV_KEY)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
SESSION_DEFAULTS: dict = {
    "logged_in": False,
    "username": "",
    "user_id": None,
    "redirect_to": "app.py",
    "last_activity": datetime.now(),
    "theme": "light",
    "notifications": [],
    "2fa_secret": None,
    "2fa_enabled": False,
}


def init_session_state() -> None:
    """Populate session_state with defaults for any key not already present."""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def push_notification(kind: str, message: str) -> None:
    """Queue a notification to be displayed on the next render."""
    st.session_state.notifications.append({"type": kind, "message": message})


def display_notifications() -> None:
    """Render and clear all queued notifications."""
    for notif in st.session_state.notifications:
        if notif["type"] == "success":
            st.success(notif["message"])
        elif notif["type"] == "warning":
            st.warning(notif["message"])
        elif notif["type"] == "error":
            st.error(notif["message"])
    st.session_state.notifications = []


# ---------------------------------------------------------------------------
# Login form
# ---------------------------------------------------------------------------
def render_login_form() -> None:
    """Render the inline login form shown on the home page to logged-out users."""
    st.warning("Log in or sign up to access advanced health solutions.")
    with st.form("quick_login", clear_on_submit=True):
        username = st.text_input(
            "Username", placeholder="Enter username", key="quick_username"
        )
        password = st.text_input(
            "Password", type="password", placeholder="Enter password", key="quick_password"
        )
        tfa_code = None
        if st.session_state.get("2fa_enabled", False):
            tfa_code = st.text_input(
                "2FA Code", placeholder="Enter 6-digit code", key="2fa_code_login"
            )

        col, _ = st.columns([1, 3])
        with col:
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            _handle_login(username, password, tfa_code)


def _handle_login(username: str, password: str, tfa_code: str | None) -> None:
    try:
        user = authenticate_user(username, password)
        if not user:
            st.error("Invalid username or password.")
            logging.warning("Failed login for %s", username)
            return

        if st.session_state.get("2fa_enabled") and tfa_code:
            totp = pyotp.TOTP(st.session_state["2fa_secret"])
            if not totp.verify(tfa_code):
                st.error("Invalid 2FA code.")
                logging.warning("Invalid 2FA for %s", username)
                return

        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_id = user[0]
        st.session_state.last_activity = datetime.now()
        st.session_state.theme = user[4] if user[4] else "light"
        push_notification("success", f"Welcome back, {username}!")
        logging.info("User %s logged in", username)

        redirect = st.session_state.redirect_to
        if redirect and redirect != "app.py":
            st.switch_page(redirect)
        else:
            st.rerun()
    except Exception as exc:
        st.error(f"Login error: {exc}")
        logging.error("Login error for %s: %s", username, exc)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
def render_logout_button() -> None:
    """Render the logout button shown to logged-in users on the home page."""
    st.success(f"Logged in as **{st.session_state.username}**")
    if st.button("Logout", key="logout_button", use_container_width=True):
        handle_logout()


def handle_logout() -> None:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.redirect_to = "app.py"
    push_notification("success", "Logged out successfully.")
    logging.info("User logged out")
    st.rerun()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add auth.py tests/test_auth.py
git commit -m "feat: extract auth.py with stable encryption key and session helpers"
```

---

## Task 2: Create `dashboard.py`

Extract the logged-in dashboard from `app.py`: prediction history chart, latest health metrics, the paginated records table with search/filter, and the CSV download.

The `@st.cache_data` function is defined at module level (not inside a try block) so it is registered once.

**Files:**
- Create: `dashboard.py`

- [ ] **Step 1: Create `dashboard.py`**

```python
import logging
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_patient_history, get_user_predictions

DB_PATH = "health_data.db"


@st.cache_data(ttl=300)
def _fetch_patient_page(user_id: int, page: int, page_size: int):
    """Fetch one page of patient records + total row count. Cached 5 minutes."""
    offset = (page - 1) * page_size
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM patients WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            conn,
            params=(user_id, page_size, offset),
        )
        total = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    return df, total


def render_dashboard() -> None:
    """Render the full logged-in dashboard: predictions, metrics, and records."""
    _render_summary()
    _render_records()


def _render_summary() -> None:
    with st.expander("Dashboard", expanded=True):
        try:
            predictions = get_user_predictions(st.session_state.user_id)
            if not predictions.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Predictions", len(predictions))
                    for ptype, count in predictions["prediction_type"].value_counts().items():
                        st.write(f"{ptype}: {count}")
                with col2:
                    fig = px.line(
                        predictions.sort_values("timestamp"),
                        x="timestamp",
                        y="probability",
                        color="prediction_type",
                        title="Prediction Confidence Over Time",
                        labels={"probability": "Confidence (%)", "timestamp": "Date"},
                        height=300,
                    )
                    st.plotly_chart(fig, use_container_width=True)

            history = get_patient_history(st.session_state.user_id)
            if not history.empty:
                latest = history.iloc[0]
                st.write("**Latest Health Metrics**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("BMI", f"{latest['bmi']:.2f}")
                with col2:
                    labels = ["Excellent", "Very Good", "Good", "Fair", "Poor"]
                    idx = int(latest["gen_health"]) - 1
                    st.metric("General Health", labels[idx] if 0 <= idx < 5 else "—")
        except Exception as exc:
            st.warning("Unable to load dashboard data.")
            logging.error("Dashboard error: %s", exc)


def _render_records() -> None:
    st.subheader("Your Health Records", anchor="health-records")

    with st.expander("Search & Filter Records", expanded=False):
        search_query = st.text_input("Search records", placeholder="Search across all fields")
        try:
            history_columns = list(get_patient_history(st.session_state.user_id).columns)
        except Exception:
            history_columns = []
        filter_col = st.selectbox("Filter by", ["All"] + history_columns, key="filter_column")
        sort_by = st.selectbox("Sort by", ["None"] + history_columns, key="sort_by")
        sort_order = st.radio("Sort order", ["Ascending", "Descending"], horizontal=True)

    page_size = st.slider("Records per page", 5, 50, 10, 5, key="page_size")
    page = st.number_input("Page", min_value=1, value=1, step=1, key="page_select")

    try:
        history, total_records = _fetch_patient_page(
            st.session_state.user_id, page, page_size
        )
        if history.empty:
            st.info("No health records available.")
            return

        # Apply in-memory search / filter / sort
        filtered = history.copy()
        if search_query:
            filtered = filtered[
                filtered.apply(lambda r: search_query.lower() in str(r).lower(), axis=1)
            ]
        if filter_col != "All":
            filtered = filtered[filtered[filter_col].notna()]
        if sort_by != "None":
            filtered = filtered.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))

        total_pages = max(1, (total_records + page_size - 1) // page_size)
        start = (page - 1) * page_size + 1
        end = min(page * page_size, total_records)
        st.caption(f"Showing {start}–{end} of {total_records} records · Page {page} of {total_pages}")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Date & Time",
                "probability": st.column_config.NumberColumn("Probability", format="%.2f"),
                "bmi": st.column_config.NumberColumn("BMI", format="%.2f"),
            },
        )

        st.download_button(
            label="Download Records as CSV",
            data=filtered.to_csv(index=False),
            file_name=f"health_records_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Error retrieving records: {exc}")
        logging.error("Health records error: %s", exc)
```

- [ ] **Step 2: Verify the module imports cleanly (no Streamlit runtime needed)**

```bash
python -c "import ast; ast.parse(open('dashboard.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add dashboard.py
git commit -m "feat: extract dashboard.py with module-level cache and clean pagination"
```

---

## Task 3: Create `profile.py`

Extract theme toggle, 2FA setup, and account deletion from `app.py`.

**Files:**
- Create: `profile.py`

- [ ] **Step 1: Create `profile.py`**

```python
import base64
import logging
from io import BytesIO

import pyotp
import qrcode
import streamlit as st

from auth import handle_logout, push_notification
from database import delete_user, update_user_theme


def render_profile() -> None:
    """Render the profile management expander."""
    with st.expander("Profile", expanded=False):
        _render_theme_toggle()
        st.divider()
        _render_2fa_section()
        st.divider()
        _render_delete_account()


def _render_theme_toggle() -> None:
    st.subheader("Appearance")
    current = st.session_state.get("theme", "light")
    label = "Switch to Dark Mode" if current == "light" else "Switch to Light Mode"
    if st.button(label, key="profile_theme_toggle"):
        new_theme = "dark" if current == "light" else "light"
        st.session_state.theme = new_theme
        try:
            update_user_theme(st.session_state.user_id, new_theme)
        except Exception as exc:
            logging.error("Theme update failed: %s", exc)
        st.rerun()


def _render_2fa_section() -> None:
    st.subheader("Two-Factor Authentication")
    if st.session_state.get("2fa_enabled", False):
        st.success("2FA is enabled on your account.")
        return

    if st.button("Set Up 2FA", key="setup_2fa"):
        secret = pyotp.random_base32()
        st.session_state["2fa_secret"] = secret
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            st.session_state.username, issuer_name="Health AI"
        )
        qr = qrcode.make(uri)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        st.image(
            f"data:image/png;base64,{qr_b64}",
            caption="Scan this QR code with your authenticator app",
            width=200,
        )

    if st.session_state.get("2fa_secret"):
        code = st.text_input(
            "Enter 6-digit code to verify and activate",
            key="verify_2fa_input",
            max_chars=6,
        )
        if st.button("Activate 2FA", key="activate_2fa"):
            totp = pyotp.TOTP(st.session_state["2fa_secret"])
            if totp.verify(code):
                st.session_state["2fa_enabled"] = True
                push_notification("success", "2FA enabled successfully!")
                logging.info("2FA enabled for user_id %s", st.session_state.user_id)
                st.rerun()
            else:
                st.error("Invalid code — please try again.")


def _render_delete_account() -> None:
    st.subheader("Danger Zone")
    with st.expander("Delete Account", expanded=False):
        st.warning(
            "This permanently deletes your account and all health records. "
            "This cannot be undone."
        )
        confirm = st.text_input(
            'Type your username to confirm', key="delete_confirm_input"
        )
        if st.button("Permanently Delete My Account", key="confirm_delete", type="primary"):
            if confirm != st.session_state.username:
                st.error("Username does not match.")
                return
            try:
                delete_user(st.session_state.user_id)
                push_notification("success", "Account deleted.")
                logging.info("User %s deleted account", st.session_state.username)
                handle_logout()
            except Exception as exc:
                st.error(f"Error deleting account: {exc}")
                logging.error("Account deletion error: %s", exc)
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import ast; ast.parse(open('profile.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add profile.py
git commit -m "feat: extract profile.py with theme, 2FA, and account deletion"
```

---

## Task 4: Update `layout.py` — add `render_services()`, fix nav hrefs

Two changes: (1) add `render_services()` which renders the three service cards using `st.button` for navigation (not broken HTML hrefs); (2) remove the dead `href` attributes from `render_header()` nav links — they don't work in Streamlit but make the code misleading.

**Files:**
- Modify: `layout.py`

- [ ] **Step 1: Add `render_services()` to the bottom of `layout.py`**

Add this function at the end of `layout.py`:

```python
def render_services() -> None:
    """Render the three service cards with working Streamlit navigation."""
    import streamlit as st  # already imported at top — harmless re-reference

    SERVICES = [
        {
            "name": "Diabetes Detection",
            "icon": "🩺",
            "model": "XGBoost",
            "accuracy": "88%",
            "desc": "Assess diabetes risk with a high-precision XGBoost model trained on 21 clinical features.",
            "link": "pages/diabetes.py",
        },
        {
            "name": "Parkinson's Disease",
            "icon": "🎙️",
            "model": "Keras DNN",
            "accuracy": "91%",
            "desc": "Detect early Parkinson's signs through voice pattern analysis with a deep neural network.",
            "link": "pages/parkinsons.py",
        },
        {
            "name": "Pneumonia Detection",
            "icon": "🩻",
            "model": "TensorFlow CNN",
            "accuracy": "92%",
            "desc": "Identify pneumonia from chest X-ray images using a convolutional neural network.",
            "link": "pages/pneumonia.py",
        },
    ]

    st.markdown(
        "<h2 class='section-title' style='text-align:center;margin-bottom:2rem'>"
        "Our AI-Powered Health Solutions</h2>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, svc in zip(cols, SERVICES):
        with col:
            st.markdown(
                f"""
                <div class="service-card">
                    <div class="service-icon">{svc['icon']}</div>
                    <h3>{svc['name']}</h3>
                    <p class="service-meta">{svc['model']} · {svc['accuracy']} accuracy</p>
                    <p>{svc['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.get("logged_in"):
                if st.button(f"Analyse →", key=f"svc_{svc['link']}", use_container_width=True):
                    st.switch_page(svc["link"])
            else:
                if st.button("Log in to Access", key=f"svc_login_{svc['link']}", use_container_width=True):
                    st.session_state.redirect_to = svc["link"]
                    st.switch_page("pages/login.py")
```

- [ ] **Step 2: Remove dead href attributes from `render_header()` nav items**

In `layout.py`, the `nav_items` list (lines 33–47) contains path-style hrefs like `/diabetes` and `/about` that Streamlit's router never intercepts — clicking them does nothing useful. The fix is to **drop the `href` key entirely** so no misleading link target exists in the HTML. The nav bar is purely decorative; actual navigation happens through `st.switch_page()` calls in the service cards and sidebar.

Replace the entire `nav_items` list in `render_header()` with:

```python
    # href is intentionally absent — Streamlit does not handle anchor navigation.
    # Navigation is done via st.switch_page() in render_services() and the sidebar.
    nav_items = [
        {"name": "Home", "active": st.session_state.get("redirect_to", "") == "app.py"},
        {
            "name": "Services",
            "dropdown": [
                {"name": "Diabetes Detection"},
                {"name": "Parkinson's Detection"},
                {"name": "Pneumonia Detection"},
            ],
        },
        {"name": "About", "active": st.session_state.get("redirect_to", "").endswith("about.py")},
        {"name": "Contact", "active": st.session_state.get("redirect_to", "").endswith("contact.py")},
        {"name": "Privacy", "active": st.session_state.get("redirect_to", "").endswith("privacy.py")},
        {"name": "Log in / Sign up", "class": "cta-nav-btn", "active": False},
    ]
```

Also update the nav HTML builder loop below it to omit `href` when the key is absent:

```python
    nav_html = "<nav class='nav-menu' role='navigation'>"
    for item in nav_items:
        if "dropdown" in item:
            dropdown_links = "".join(
                f"<span class='dropdown-item'>{sub['name']}</span>"
                for sub in item["dropdown"]
            )
            nav_html += f"""
            <div class='dropdown'>
                <span class='nav-item' aria-haspopup='true'>{item['name']}</span>
                <div class='dropdown-content'>{dropdown_links}</div>
            </div>
            """
        else:
            active_class = "active" if item.get("active", False) else ""
            extra_class = item.get("class", "")
            nav_html += f"<span class='nav-item {extra_class} {active_class}'>{item['name']}</span>"
    nav_html += "</nav>"
```

- [ ] **Step 3: Verify syntax**

```bash
python -c "import ast; ast.parse(open('layout.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 4: Commit**

```bash
git add layout.py
git commit -m "feat: add render_services() to layout, remove dead nav hrefs"
```

---

## Task 5: Rewrite `app.py` as thin orchestrator

`app.py` becomes ~80 lines. `st.set_page_config()` is the very first call. Session init, timeout, notifications, layout, and routing all delegate to the new modules.

Removes: Spanish localization dict, `analytics.json` writes, `header_rendered` / `footer_rendered` flags, email update stub, inline `cached_patient_history`.

**Files:**
- Modify: `app.py` (full rewrite)

- [ ] **Step 1: Replace `app.py` entirely**

```python
import logging
from datetime import datetime, timedelta

import streamlit as st

# set_page_config MUST be the first Streamlit call
st.set_page_config(
    page_title="Health AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import display_notifications, init_session_state, render_login_form, render_logout_button
from dashboard import render_dashboard
from layout import apply_custom_css, render_footer, render_header, render_services
from profile import render_profile
from database import init_db

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)

# --- Database & session setup -------------------------------------------------
try:
    init_db()
except Exception as exc:
    st.error(f"Failed to initialise database: {exc}")
    logging.error("DB init failed: %s", exc)

init_session_state()

# --- Session timeout ----------------------------------------------------------
SESSION_TIMEOUT = timedelta(minutes=30)
if st.session_state.logged_in:
    elapsed = datetime.now() - st.session_state.last_activity
    if elapsed > SESSION_TIMEOUT:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.redirect_to = "app.py"
        from auth import push_notification
        push_notification("warning", "Session timed out. Please log in again.")
        logging.info("Session timed out")

# --- Layout -------------------------------------------------------------------
apply_custom_css(st.session_state.theme)
render_header()
display_notifications()

# --- Page content -------------------------------------------------------------
if st.session_state.logged_in:
    render_logout_button()
    render_services()
    render_dashboard()
    render_profile()
    # Update activity timestamp
    st.session_state.last_activity = datetime.now()
else:
    render_login_form()
    render_services()

render_footer()
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import ast; ast.parse(open('app.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 3: Run the app locally and confirm home page loads without errors**

```bash
streamlit run app.py
```

Open http://localhost:8501. Confirm:
- No Streamlit warning about `set_page_config`
- Header renders
- Login form visible when logged out
- Service cards render
- No Python exceptions in terminal

To test the logged-in path, you need a user account. If the database is fresh (no existing users), sign up first via the Login page (`pages/login.py`) before continuing. Use any test username/password — the DB is local and ephemeral.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "refactor: slim app.py to ~80-line orchestrator, fix set_page_config order"
```

---

## Task 6: Rewrite `style.css` — Clean Medical design

Full rewrite of `style.css` using the Clean Medical design tokens. All existing teal/black tokens are replaced with the blue system. Hero becomes a gradient from `#EBF3FF` to `#f8faff`. Service cards get white + `#e0ecff` border + blue shadow. Buttons become pills with `border-radius: 20px`.

**Files:**
- Modify: `style.css` (full rewrite)

- [ ] **Step 1: Verify how dark mode is toggled before writing the CSS**

The new CSS uses `[data-theme="dark"]` selectors on `<body>`. Check whether `apply_custom_css()` in `layout.py` actually sets that attribute:

```bash
grep -n "data-theme\|setAttribute\|theme" layout.py
```

If `apply_custom_css()` does **not** inject a `data-theme` attribute onto `<body>`, add the following injection at the end of `apply_custom_css()`, after the CSS `<style>` block is written:

```python
    # Set data-theme attribute on <body> so CSS [data-theme="dark"] selectors work
    theme_attr = theme if theme in ("light", "dark") else "light"
    st.markdown(
        f"<script>document.body.setAttribute('data-theme', '{theme_attr}');</script>",
        unsafe_allow_html=True,
    )
```

This must be done **before** rewriting `style.css` — otherwise dark mode silently stops working after the CSS change.

- [ ] **Step 2: Replace `style.css` entirely**

```css
/* ============================================================
   Health AI — Clean Medical Design System
   Primary: #0052CC  |  Dark text: #0A1628  |  BG: #f8faff
   ============================================================ */

/* Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* CSS Custom Properties */
:root {
  --primary:        #0052CC;
  --primary-dark:   #003d99;
  --primary-light:  #EBF3FF;
  --text-dark:      #0A1628;
  --text-mid:       #546e8a;
  --text-light:     #8fa8c8;
  --bg-page:        #f8faff;
  --bg-card:        #ffffff;
  --border-card:    #e0ecff;
  --shadow-card:    0 2px 8px rgba(0, 82, 204, 0.06);
  --shadow-hover:   0 6px 20px rgba(0, 82, 204, 0.14);
  --radius-card:    8px;
  --radius-pill:    20px;
  --font:           'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
  --transition:     all 0.2s ease;
}

/* Dark mode */
[data-theme="dark"] {
  --primary:       #3b82f6;
  --primary-dark:  #2563eb;
  --primary-light: #1e3a5f;
  --text-dark:     #e2e8f0;
  --text-mid:      #94a3b8;
  --text-light:    #64748b;
  --bg-page:       #0A1628;
  --bg-card:       #111827;
  --border-card:   #1e3a5f;
  --shadow-card:   0 2px 8px rgba(0, 0, 0, 0.4);
  --shadow-hover:  0 6px 20px rgba(0, 0, 0, 0.5);
}

/* Base */
html, body {
  min-height: 100vh;
  font-family: var(--font);
  background-color: var(--bg-page);
  color: var(--text-dark);
  line-height: 1.65;
  scroll-behavior: smooth;
}

/* ── Header ───────────────────────────────────────────────── */
.header {
  background: var(--bg-card);
  border-bottom: 2px solid var(--border-card);
  padding: 0.75rem 2rem;
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 82, 204, 0.05);
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--primary);
  letter-spacing: -0.3px;
}

.logo { width: 36px; }

.nav-menu { display: flex; gap: 0.25rem; align-items: center; }

.nav-item {
  color: var(--text-mid);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.4rem 0.85rem;
  border-radius: 6px;
  transition: var(--transition);
}

.nav-item:hover, .nav-item:focus {
  color: var(--primary);
  background: var(--primary-light);
}

.nav-item.active { color: var(--primary); font-weight: 600; }

.cta-nav-btn {
  background: var(--primary);
  color: #fff !important;
  border-radius: var(--radius-pill);
  padding: 0.4rem 1.1rem !important;
  font-weight: 600;
  margin-left: 0.5rem;
}

.cta-nav-btn:hover {
  background: var(--primary-dark) !important;
  color: #fff !important;
}

/* Dropdown */
.dropdown { position: relative; }

.dropdown-content {
  display: none;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 200px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-hover);
  z-index: 1001;
  overflow: hidden;
}

.dropdown:hover .dropdown-content,
.dropdown:focus-within .dropdown-content { display: block; }

.dropdown-content a {
  display: block;
  padding: 0.65rem 1rem;
  color: var(--text-dark);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: var(--transition);
}

.dropdown-content a:hover { background: var(--primary-light); color: var(--primary); }

/* Hamburger */
.hamburger {
  display: none;
  cursor: pointer;
  font-size: 1.4rem;
  background: none;
  border: none;
  color: var(--text-dark);
  padding: 0.4rem;
}

/* ── Hero ─────────────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg-page) 100%);
  text-align: center;
  padding: 5rem 2rem 3.5rem;
  margin-bottom: 0;
}

.hero-badge {
  display: inline-block;
  background: rgba(0, 82, 204, 0.1);
  color: var(--primary);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 0.25rem 0.8rem;
  border-radius: var(--radius-pill);
  margin-bottom: 1rem;
}

.hero h1 {
  font-size: clamp(1.75rem, 4vw, 2.75rem);
  font-weight: 800;
  color: var(--text-dark);
  line-height: 1.2;
  margin-bottom: 1rem;
}

.hero .subtitle {
  font-size: 1.05rem;
  color: var(--text-mid);
  max-width: 560px;
  margin: 0 auto 2rem;
}

/* ── Stats bar ────────────────────────────────────────────── */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  background: var(--bg-card);
  border-top: 1px solid var(--border-card);
  border-bottom: 1px solid var(--border-card);
  margin-bottom: 3rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  border-right: 1px solid var(--border-card);
}

.stat-item:last-child { border-right: none; }
.stat-number { font-size: 1.6rem; font-weight: 800; color: var(--primary); }
.stat-label  { font-size: 0.78rem; color: var(--text-mid); margin-top: 0.1rem; }

/* ── CTA Button ───────────────────────────────────────────── */
.cta-button {
  display: inline-block;
  background: var(--primary);
  color: #fff;
  padding: 0.75rem 2rem;
  border-radius: var(--radius-pill);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  box-shadow: 0 4px 14px rgba(0, 82, 204, 0.3);
  transition: var(--transition);
}

.cta-button:hover, .cta-button:focus {
  background: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(0, 82, 204, 0.4);
}

/* ── Section title ────────────────────────────────────────── */
.section-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-dark);
}

/* ── Service cards ────────────────────────────────────────── */
.services-section { max-width: 1100px; margin: 0 auto 3rem; padding: 0 1rem; }
.services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }

.service-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  padding: 2rem 1.5rem;
  text-align: center;
  box-shadow: var(--shadow-card);
  transition: var(--transition);
}

.service-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }

.service-icon { font-size: 2.25rem; margin-bottom: 0.75rem; }

.service-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 0.35rem;
}

.service-meta {
  font-size: 0.78rem;
  color: var(--primary);
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.service-card p { font-size: 0.88rem; color: var(--text-mid); margin-bottom: 1.25rem; }

/* ── Cards (dashboard, forms) ─────────────────────────────── */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
  margin-bottom: 1.5rem;
}

/* ── Forms ────────────────────────────────────────────────── */
.form-container {
  max-width: 520px;
  margin: 2rem auto;
  padding: 2rem;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.form-label {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-dark);
  display: block;
  margin-bottom: 0.4rem;
}

.form-input {
  width: 100%;
  padding: 0.7rem 1rem;
  border: 1px solid var(--border-card);
  border-radius: 6px;
  font-family: var(--font);
  font-size: 0.95rem;
  transition: var(--transition);
  background: var(--bg-card);
  color: var(--text-dark);
}

.form-input:focus {
  border-color: var(--primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 82, 204, 0.12);
}

.submit-button {
  background: var(--primary);
  color: #fff;
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: var(--radius-pill);
  font-family: var(--font);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
}

.submit-button:hover, .submit-button:focus {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

/* ── Footer ───────────────────────────────────────────────── */
.footer {
  background: var(--text-dark);
  color: rgba(255,255,255,0.85);
  padding: 2.5rem 1.5rem;
  text-align: center;
  margin-top: 4rem;
}

.footer-content { max-width: 900px; margin: 0 auto; }

.footer-links {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}

.footer-link {
  color: rgba(255,255,255,0.75);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: var(--transition);
}

.footer-link:hover { color: #fff; }

.social-links { display: flex; gap: 1.25rem; justify-content: center; margin: 1rem 0; }

.social-link {
  color: rgba(255,255,255,0.7);
  font-size: 1.35rem;
  text-decoration: none;
  transition: var(--transition);
}

.social-link:hover { color: #fff; transform: scale(1.15); }

.copyright { font-size: 0.82rem; opacity: 0.6; margin-top: 1rem; }

/* ── Privacy ──────────────────────────────────────────────── */
.privacy-container {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  padding: 2rem;
  box-shadow: var(--shadow-card);
}

/* ── Accessibility ────────────────────────────────────────── */
:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; transform: none !important; }
}

/* ── Responsive ───────────────────────────────────────────── */
@media (max-width: 768px) {
  .header { padding: 0.75rem 1rem; }

  .nav-menu {
    display: none;
    flex-direction: column;
    width: 100%;
    background: var(--bg-card);
    position: absolute;
    top: 100%;
    left: 0;
    padding: 1rem;
    box-shadow: var(--shadow-hover);
    border-top: 1px solid var(--border-card);
  }

  .nav-menu.active { display: flex; }
  .nav-item { width: 100%; text-align: center; padding: 0.65rem; }
  .hamburger { display: block; }
  .logo { width: 30px; }
  .hero { padding: 3.5rem 1.25rem 2.5rem; }
  .stats-bar { grid-template-columns: 1fr; }
  .stat-item { border-right: none; border-bottom: 1px solid var(--border-card); }
  .stat-item:last-child { border-bottom: none; }
  .form-container { margin: 1rem; padding: 1.25rem; }
  .footer-links { flex-direction: column; gap: 0.75rem; }
}
```

- [ ] **Step 3: Restart the app and visually verify the design**

```bash
streamlit run app.py
```

Check:
- Header is white with blue bottom border and `🏥 Health AI` wordmark
- Hero section has a light blue gradient background
- Service cards are white with blue border and subtle shadow
- Footer is dark navy
- Toggle theme to dark in the Profile panel — dark navy background should apply

- [ ] **Step 4: Commit**

```bash
git add style.css layout.py
git commit -m "design: rewrite style.css with Clean Medical design system, fix dark mode attribute"
```

---

## Task 7: Add deployment files

Add HF Spaces frontmatter to `README.md`, create `.gitattributes` for Git LFS, and update `CLAUDE.md` with deploy steps.

**Files:**
- Modify: `README.md`
- Create: `.gitattributes`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Prepend HF Spaces frontmatter to `README.md`**

Open `README.md` and insert the following block as the very first lines (before the existing `# 🧠 Health AI Super App` heading):

```
---
title: Health AI Super App
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.45.1
app_file: app.py
pinned: false
---

```

- [ ] **Step 2: Create `.gitattributes` for Git LFS**

Create `.gitattributes` in the project root:

```
models/*.pkl filter=lfs diff=lfs merge=lfs -text
models/*.keras filter=lfs diff=lfs merge=lfs -text
models/*.h5 filter=lfs diff=lfs merge=lfs -text
```

- [ ] **Step 3: Update `CLAUDE.md` — add Deployment section**

Append the following to `CLAUDE.md`:

```markdown
## Deploying to Hugging Face Spaces

The app is configured for HF Spaces (Streamlit SDK). `README.md` already contains the required YAML frontmatter.

**One-time setup:**
1. Create a new Space at huggingface.co/new-space → Streamlit SDK → link to your GitHub repo
2. In Space Settings → Repository secrets, add `ENCRYPTION_KEY`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. Set up Git LFS for model files:
   ```bash
   git lfs install
   git add .gitattributes
   git commit -m "chore: add git lfs tracking for model files"
   git push
   ```
4. Push `main` — HF Spaces auto-builds and deploys.

**Notes:**
- SQLite resets on Space restart (acceptable for portfolio demo)
- Spaces sleep after 48h of inactivity on the free tier
- Model files in `models/` are tracked via Git LFS (see `.gitattributes`)
```

- [ ] **Step 4: Commit all deployment files**

```bash
git add README.md .gitattributes CLAUDE.md
git commit -m "chore: add HF Spaces config, Git LFS tracking, deploy instructions"
```

---

## Final verification

- [ ] Run the full test suite

```bash
python -m pytest tests/ -v
```

Expected: 4 passed (all `test_auth.py` tests)

- [ ] Run the app and do a full end-to-end smoke test

```bash
streamlit run app.py
```

1. Open http://localhost:8501
2. Verify home page loads with Clean Medical design (no Streamlit warnings in terminal)
3. Log in with a test account
4. Verify service cards render and "Analyse →" buttons navigate correctly
5. Verify dashboard shows charts and records table
6. Open Profile expander, confirm theme toggle and 2FA setup work
7. Log out — confirm login form returns

- [ ] **Final commit if any loose ends were fixed, then merge to main**

```bash
git log --oneline -8
git checkout main
git merge feature/code-improvements --no-ff -m "feat: refactor, redesign, and HF Spaces deployment config"
```
