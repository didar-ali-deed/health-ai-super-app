# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

The app runs on port 8501 by default. There are no build, lint, or test scripts configured.

## Architecture Overview

This is a Python/Streamlit multi-page application providing three AI-powered medical diagnostics: diabetes, Parkinson's disease, and pneumonia detection.

**Routing:** Streamlit uses file-based routing. `app.py` is the home/dashboard. Pages in `pages/` map to routes:
- `pages/login.py` — authentication (login/signup/2FA)
- `pages/diabetes.py`, `pages/parkinsons.py`, `pages/pneumonia.py` — thin wrappers that call into the analysis modules

**Analysis modules** live in dedicated directories and are called from the page wrappers:
- `diabetes_analysis/diabetes_app.py` → `run_diabetes_app()` — tabular form input, XGBoost prediction
- `speech_analysis/speech_app.py` → `run_speech_app()` — audio file upload, Keras DNN prediction
- `xray_analysis/xray_app.py` → `run_pneumonia_app()` — image upload, TensorFlow CNN prediction

**Model files** are pre-trained and stored in `models/`:
- `diabetes_model.pkl` + `scaler.pkl` (XGBoost + StandardScaler)
- `parkinsons_model.keras` + `parkinsons_scaler.pkl` (Keras DNN)
- `pneumonia_model.keras` / `pneumonia_model.h5` (TensorFlow CNN)

**Shared infrastructure:**
- `database.py` — all SQLite operations (auth, predictions, patients). Database is `health_data.db` (gitignored). Tables: `users`, `patients`, `predictions`, `password_resets`.
- `layout.py` — `apply_custom_css()`, `render_header()`, `render_footer()` used across all pages
- `style.css` — global styling

## Session State

Key Streamlit session state keys used app-wide:
- `logged_in` (bool), `username` (str), `user_id` (int)
- `theme` ("light"/"dark")
- `last_activity` (datetime, 30-min timeout)
- `2fa_secret` (TOTP secret)

Authentication is Argon2-hashed passwords with optional TOTP 2FA. Password reset uses token-based expiry (1 hour).

## Configuration

`.streamlit/config.toml` sets port 8501, disables XSRF protection, and defines the theme (primary `#0052CC`).

The optional `ENCRYPTION_KEY` environment variable is used for Fernet encryption; it auto-generates if absent. Logs go to `app.log` and `database.log` (both gitignored).

## Deployment

Deployed on Streamlit Community Cloud via GitHub integration. `runtime.txt` pins Python 3.12.

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
