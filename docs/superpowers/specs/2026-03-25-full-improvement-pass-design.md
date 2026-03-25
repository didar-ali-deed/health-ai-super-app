# Health AI Super App — Full Improvement Pass Design

**Date:** 2026-03-25
**Status:** Draft
**Scope:** Fix critical bugs, DRY refactor, complete dark mode, style consolidation, HF Spaces deployment

---

## Problem Statement

The app has been refactored into clean modules but several cross-cutting issues remain:
1. **Critical logic bugs** — 2FA secret not persisted, sessions expire mid-analysis, reset token printed to UI
2. **Duplicated code** — Session init, timeout check, theme toggle, email regex copied 3-5x
3. **Incomplete dark mode** — Inline styles in about/contact/privacy pages ignore theme tokens
4. **Broken navigation** — Breadcrumbs and service-page CTAs use href attributes Streamlit ignores
5. **Style inconsistency** — 4 different heading sizes, inline form CSS overrides global styles, footer inverts in dark mode

---

## Architecture

### New File: `utils.py`

Shared helpers imported by all pages — replaces the 5x duplicated session/timeout/theme code.

Exports:
- `check_session_timeout()` — log out user if 30-min inactivity exceeded; call at top of every page
- `toggle_theme(user_id)` — flip light/dark and persist to DB

### Database Schema Changes (`database.py`)

Add two columns to `users` table:
- `tfa_secret TEXT DEFAULT NULL`
- `tfa_enabled INTEGER DEFAULT 0`

New functions:
- `save_2fa_secret(user_id, secret)` — stores TOTP secret
- `enable_2fa(user_id)` — sets tfa_enabled = 1
- `get_2fa_info(user_id)` — returns (tfa_enabled, tfa_secret)
- `disable_2fa(user_id)` — clears secret and flag

Add `contact_submissions` table to `init_db()` (currently created ad-hoc in contact.py).
Call `cleanup_expired_tokens()` at bottom of `init_db()`.
Consolidate email regex to single canonical version reused by all callers.

---

## Component Changes

### `auth.py` — Fix 2FA Login Verification

On `_handle_login()` success, load 2FA state from DB instead of session state:
```python
tfa_enabled, tfa_secret = get_2fa_info(user[0])
if tfa_enabled:
    if not tfa_code:
        st.error("2FA code required.")
        return
    if not pyotp.TOTP(tfa_secret).verify(tfa_code):
        st.error("Invalid 2FA code.")
        return
st.session_state["2fa_enabled"] = bool(tfa_enabled)
st.session_state["2fa_secret"] = tfa_secret
```

Always show the 2FA input field in `render_login_form()` so users with 2FA enabled can enter their code.

### `profile.py` — Persist 2FA to DB

On "Activate 2FA":
```python
if totp.verify(code):
    save_2fa_secret(st.session_state.user_id, secret)
    enable_2fa(st.session_state.user_id)
    st.session_state["2fa_enabled"] = True
```

Add "Disable 2FA" button that calls `disable_2fa(user_id)`.

### `style.css` — New Tokens and Classes

Add to `:root`:
- `--footer-bg: #0a1628` (always dark — footer is always navy, never inverts)
- `--heading-xl: clamp(1.75rem, 4vw, 2.75rem)`
- `--heading-lg: 1.6rem`
- `--heading-md: 1.25rem`
- `--btn-md-padding: 0.75rem 1.5rem`
- `--btn-sm-padding: 0.4rem 0.85rem`

Fix `.footer { background: var(--footer-bg); }` — replaces broken `var(--text-dark)`.

Add CSS classes for about/contact/privacy that currently use inline styles:
- `.page-hero` — centered page header with h1 and subtitle
- `.mission-card`, `.team-card` — card variants with dark mode support
- `.stat-highlight` — large colored stat numbers

### Pages — DRY Pattern

Replace duplicate session init + timeout + theme blocks in all pages with:
```python
from auth import init_session_state
from utils import check_session_timeout, toggle_theme

init_session_state()
check_session_timeout()
```

### Navigation Fixes

Breadcrumbs (`about.py`, `contact.py`, `privacy.py`) — Replace `<a href='/'>` with:
```python
if st.button("Home", key="breadcrumb_home"):
    st.switch_page("app.py")
```

Service page CTAs (`diabetes.py`, `parkinsons.py`, `pneumonia.py`) — Replace `href='/login'` with:
```python
if st.button("Log in to Access", type="primary"):
    st.switch_page("pages/login.py")
```

### Security Fixes

Password reset token — Remove `st.info(f"token: {token}")` from UI; log server-side only.

### Session Fixes

Add `st.session_state.last_activity = datetime.now()` at the end of each service page to prevent mid-analysis timeout.

Remove sidebar blocks from about/contact/privacy — sidebar is inconsistent with app.py's collapsed sidebar and breaks mobile.

---

## Data Flow

```
User visits service page
  init_session_state()
  check_session_timeout()          <- utils.py (single source)
  apply_custom_css(theme)
  auth guard -> st.switch_page()   <- fixed button, not broken href
  run_*_app()
  last_activity = datetime.now()   <- NEW: prevents timeout during analysis
```

```
2FA enable
  profile.py: verify TOTP
  save_2fa_secret(user_id, secret) <- NEW: persisted to DB
  enable_2fa(user_id)

2FA login
  _handle_login: authenticate_user()
  get_2fa_info(user_id)            <- NEW: reads from DB
  pyotp.TOTP(db_secret).verify()
```

---

## Error Handling

- `check_session_timeout()` safe if `last_activity` is None
- `toggle_theme()` fails silently on DB error (session state still updates)
- All new DB functions wrapped in try/except with logging

---

## Testing

Existing 4 tests must still pass.

New tests in `tests/test_utils.py`:
- `test_check_session_timeout_noop_when_logged_out()` — no crash or rerun
- `test_toggle_theme_changes_session_state()` — light->dark, dark->light

New tests in `tests/test_database.py`:
- `test_2fa_roundtrip()` — save_2fa_secret + get_2fa_info returns same values
- `test_enable_disable_2fa()` — enable then disable clears secret

---

## HF Spaces Deployment

README.md frontmatter and .gitattributes already configured from previous session.
Remaining steps documented in CLAUDE.md:
1. Create Space at huggingface.co -> Streamlit SDK -> link GitHub repo
2. Add ENCRYPTION_KEY secret in Space settings
3. Push main branch -> auto-deploys

---

## Files NOT Changed

- `app.py` — already clean orchestrator
- `dashboard.py` — no changes needed
- `auth.py:get_encryption_key()`, `init_session_state()`, `handle_logout()` — unchanged
- Analysis modules and models — untouched
- `.streamlit/config.toml`, `requirements.txt` — no new dependencies

---

## Implementation Order

1. `database.py` — 2FA columns + functions, contact table, email regex, cleanup call
2. `utils.py` — create with check_session_timeout(), toggle_theme()
3. `auth.py` — fix _handle_login() to read 2FA from DB; show 2FA field always
4. `profile.py` — persist 2FA on activate; add disable button
5. `style.css` — new tokens + page-hero/card classes; fix footer token
6. `pages/login.py` — remove duplicate session init; remove inline form CSS; remove token from UI
7. `pages/about.py`, `contact.py`, `privacy.py` — DRY refactor; fix breadcrumbs; remove sidebar; use CSS classes
8. `pages/diabetes.py`, `parkinsons.py`, `pneumonia.py` — fix CTA; add last_activity update
9. `tests/` — add new tests for utils.py and database.py 2FA functions
