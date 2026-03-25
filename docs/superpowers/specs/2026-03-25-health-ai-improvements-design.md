# Health AI Super App — Improvements & Deployment Design

**Date:** 2026-03-25
**Approach:** B — Refactor + Redesign + Deploy
**Status:** Approved

---

## Context

The Health AI Super App is a Streamlit-based portfolio project providing three AI diagnostic tools (diabetes, Parkinson's, pneumonia). The goal is to improve code quality, architecture, visual design, and deploy it live on Hugging Face Spaces — all in one pass.

**Target audience:** Portfolio / demo (not production users). Data persistence across redeploys is not required.

---

## 1. Architecture

### Problem

`app.py` is 625 lines doing too many unrelated things: session init, authentication, theme toggling, navigation, dashboard, health records with search/pagination, profile management, 2FA setup, account deletion, notifications, analytics, and header/footer rendering.

Additional bugs:
- `st.set_page_config()` is called after `apply_custom_css()`, which causes a Streamlit warning because `set_page_config` must be the first Streamlit call
- `ENCRYPTION_KEY` is set to `Fernet.generate_key().decode()` inline when the env var is absent — this generates a new key on every Python process start, making any Fernet-encrypted data unreadable across restarts
- Navigation links in `render_header()` use plain HTML `href` anchors (e.g. `/diabetes`) that do not work with Streamlit's routing — the app relies on `st.switch_page()` instead
- `cached_patient_history` is defined as a `@st.cache_data` function inside a `try` block that runs on every render, which re-registers the cache decorator unnecessarily

### Target structure

| File | Responsibility |
|---|---|
| `app.py` (~80 lines) | `set_page_config` (first), session init, timeout check, apply CSS, render header/footer, route to auth or dashboard |
| `auth.py` | `render_login_form()`, `handle_logout()`, session state helpers, stable encryption key loading |
| `dashboard.py` | `render_dashboard()` — prediction chart, health metrics summary, records table with search/filter/pagination, CSV download |
| `profile.py` | `render_profile()` — theme toggle, 2FA setup + QR display + verify, account deletion |
| `layout.py` (cleaned) | `apply_custom_css()`, `render_header()`, `render_footer()`, `render_services()` — no changes to logic, clean up dead nav href code |
| `database.py` | Unchanged |
| `diabetes_analysis/`, `speech_analysis/`, `xray_analysis/`, `models/` | Unchanged |

### What gets removed

- **Spanish localization** — only 2 fields translated, rest falls back silently; removed entirely to avoid inconsistent UI
- **Email update feature** — currently shows a `st.warning("not implemented")` which signals incompleteness to anyone reading the code; removed
- **`header_rendered` / `footer_rendered` session flags** — these flags were added to prevent double-rendering but are not needed once `app.py` is slim and renders layout once per run
- **`analytics.json` writes** — writing to a file on every page load causes errors on read-only/ephemeral deployments; removed

---

## 2. Visual Design — Clean Medical

### Design tokens

| Token | Value |
|---|---|
| Primary | `#0052CC` |
| Dark text | `#0A1628` |
| Secondary text | `#546e8a` |
| Hero background | `#EBF3FF` (gradient to `#f8faff`) |
| Page background | `#f8faff` |
| Card background | `white` |
| Card border | `#e0ecff` |
| Card shadow | `0 2px 8px rgba(0,82,204,0.06)` |
| Border radius (cards) | `8px` |
| Border radius (pills/buttons) | `20px` |
| Font | Poppins (already loaded via Google Fonts) |

### Key UI changes

**Navbar:** White background with a 2px blue-tinted bottom border. Logo uses the `🏥 HealthAI` wordmark. `Sign In` becomes a pill button. Nav links are clean text links (no dropdowns on mobile — collapsible hamburger kept).

**Hero section:** Light blue gradient background (`#EBF3FF → #f8faff`). Adds a small pill badge ("AI-POWERED DIAGNOSTICS") above the heading for visual hierarchy. CTA button becomes a pill with a blue drop shadow.

**Stats bar:** A three-column row below the hero showing model accuracy figures (88%, 91%, 92%) — adds immediate credibility without requiring login.

**Service cards:** White cards with `#e0ecff` border and subtle blue-tinted shadows. Each card shows the model type and accuracy below the title. CTA buttons are blue pills ("Analyse →").

**Dark mode:** Existing dark theme support is kept. Dark mode tokens are adjusted to match: dark navy background (`#0A1628`), cards `#111827`, accent `#3b82f6`.

**`style.css`** is rewritten from scratch with the new tokens. The existing Poppins import in `layout.py` is kept.

---

## 3. Deployment — Hugging Face Spaces

### Platform choice

Hugging Face Spaces (free tier): 2 vCPU / 16 GB RAM, auto-deploys from GitHub, public URL at `huggingface.co/spaces/<username>/health-ai-super-app`. Spaces sleep after 48h of inactivity on the free tier.

SQLite is used as-is. Data resets on Space restart — acceptable for a portfolio demo.

### Files to add or change

**`README.md`** — prepend HF Spaces YAML frontmatter:

```yaml
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

**`.gitattributes`** — add Git LFS tracking for model files (likely >10 MB):

```
models/*.pkl filter=lfs diff=lfs merge=lfs -text
models/*.keras filter=lfs diff=lfs merge=lfs -text
models/*.h5 filter=lfs diff=lfs merge=lfs -text
```

**`ENCRYPTION_KEY` secret** — set once in HF Space Settings → Repository secrets. Generate with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**`.streamlit/config.toml`** — kept as-is (CORS enabled, XSRF off, port 8501 is ignored by HF Spaces but harmless).

### Deployment steps (after code changes are merged)

1. Create a new Space at huggingface.co/new-space → Streamlit SDK → link to GitHub repo
2. Set `ENCRYPTION_KEY` in Space Settings → Repository secrets
3. Run `git lfs install`, stage `.gitattributes`, push
4. Push `main` branch — HF Spaces auto-builds and deploys

---

## 4. Out of scope

- Cloud database (SQLite resets are acceptable for portfolio)
- Email verification / password reset emails
- Demo mode / unauthenticated access to analysis tools
- Any changes to the three analysis modules or ML models
