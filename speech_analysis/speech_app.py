import streamlit as st
import numpy as np
import joblib
import tensorflow as tf
import librosa
import pandas as pd
from datetime import datetime
import json
import os
import logging
from layout import apply_custom_css, render_header, render_footer
from database import save_prediction, get_user_predictions

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cache model and scaler
@st.cache_resource
def load_model_and_scaler():
    try:
        model = tf.keras.models.load_model("models/parkinsons_model.keras")
        scaler = joblib.load("models/parkinsons_scaler.pkl")
        return model, scaler
    except FileNotFoundError:
        st.error("Parkinson’s model or scaler not found.")
        logging.error("Parkinson’s model or scaler file missing.")
        st.stop()

model, scaler = load_model_and_scaler()

# Feature extraction with validation
def extract_features(audio_file):
    try:
        y, sr = librosa.load(audio_file, sr=None)
        if len(y) < sr * 5:  # Require at least 5 seconds
            raise ValueError("Audio must be at least 5 seconds long")
        features = {
            "MDVP:Fo(Hz)": librosa.feature.spectral_centroid(y=y, sr=sr).mean(),
            "MDVP:Fhi(Hz)": librosa.feature.spectral_bandwidth(y=y, sr=sr).mean(),
            "MDVP:Flo(Hz)": librosa.feature.spectral_rolloff(y=y, sr=sr).mean(),
            "MDVP:Jitter(%)": librosa.feature.zero_crossing_rate(y).mean(),
            "MDVP:Jitter(Abs)": np.abs(librosa.feature.zero_crossing_rate(y)).mean(),
            "MDVP:RAP": librosa.feature.zero_crossing_rate(y).mean() / 2,
            "MDVP:PPQ": librosa.feature.zero_crossing_rate(y).mean() / 3,
            "Jitter:DDP": librosa.feature.zero_crossing_rate(y).mean() * 3,
            "MDVP:Shimmer": librosa.feature.rms(y=y).mean(),
            "MDVP:Shimmer(dB)": 20 * np.log10(librosa.feature.rms(y=y).mean()),
            "Shimmer:APQ3": librosa.feature.rms(y=y).mean() / 3,
            "Shimmer:APQ5": librosa.feature.rms(y=y).mean() / 5,
            "MDVP:APQ": librosa.feature.rms(y=y).mean() / 2,
            "Shimmer:DDA": librosa.feature.rms(y=y).mean() * 3,
            "NHR": librosa.feature.spectral_flatness(y=y).mean(),
            "HNR": librosa.feature.rms(y=y).mean() / librosa.feature.spectral_flatness(y=y).mean(),
            "RPDE": 0.0,  # Placeholder for advanced features
            "DFA": 0.0,
            "spread1": 0.0,
            "spread2": 0.0,
            "D2": 0.0,
            "PPE": 0.0
        }
        return pd.DataFrame([features])
    except Exception as e:
        st.error(f"Error processing audio: {e}")
        logging.error(f"Audio processing error: {e}")
        return None

# Initialize session state
def initialize_session_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "user_id": None,
        "redirect_to": "app.py",
        "theme": "light",
        "page_transition": False,
        "header_rendered": False,
        "footer_rendered": False,
        "reset": False,
        "show_details": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Streamlit app
def run_speech_app():
    initialize_session_state()

    # Apply CSS
    try:
        apply_custom_css(st.session_state.theme)
    except Exception as e:
        st.error(f"Error applying CSS: {e}")
        logging.error(f"CSS application failed: {e}")

    # Check authentication
    if not st.session_state.logged_in:
        st.warning("Please log in to use the Parkinson’s Detection service.")
        st.session_state.redirect_to = "pages/parkinsons.py"
        if st.button("Log in", key="login_button", use_container_width=True):
            st.session_state.page_transition = True
            st.switch_page("pages/login.py")
        logging.info("Unauthenticated access attempt to Parkinson’s Detection")
        return

    # Render header only if not rendered by parkinsons.py
    if not st.session_state.header_rendered:
        try:
            render_header()
            st.session_state.header_rendered = True
        except Exception as e:
            st.error(f"Error rendering header: {e}")
            logging.error(f"Header rendering failed: {e}")

    # Main container
    with st.container():
        st.markdown(
            """
            <div class="page-transition" role="main" aria-label="Parkinson’s Detection Page">
                <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>Speech-Based Parkinson’s Detection</h1>
                <p style='text-align: center; font-size: 1.2rem; max-width: 700px; margin: 0 auto 2rem;'>Analyze voice samples to detect early signs of Parkinson’s disease using advanced AI.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Model metrics
        if os.path.exists("static/parkinsons_metrics.json"):
            try:
                with open("static/parkinsons_metrics.json") as f:
                    metrics = json.load(f)
                st.markdown(
                    f"""
                    <div class="card" style='text-align: center; margin-bottom: 2rem;'>
                        <p class="badge">Model Performance</p>
                        <p style='font-weight: 600; font-size: 1.1rem;'>Test Accuracy: {metrics['test_accuracy']:.2%}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning("Unable to load model metrics.")
                logging.error(f"Error loading parkinsons_metrics.json: {e}")

        # Input form
        with st.form("speech_form"):
            st.markdown('<div class="form-container" role="form" aria-label="Audio Upload Form">', unsafe_allow_html=True)
            st.markdown('<label class="form-label" for="audio_file">Upload Audio File</label>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Choose a WAV audio file...",
                type=["wav"],
                key="audio_file",
                label_visibility="hidden",
                help="Upload a clear WAV file (minimum 5 seconds)"
            )
            st.markdown('<div class="column-layout">', unsafe_allow_html=True)
            col_submit, col_reset = st.columns(2)
            with col_submit:
                submit = st.form_submit_button("Analyze", use_container_width=True)
            with col_reset:
                reset = st.form_submit_button("Reset", use_container_width=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        # Handle reset
        if reset:
            if st.button("Confirm Reset", key="confirm_reset", use_container_width=True):
                st.session_state.reset = True
                st.session_state.header_rendered = False
                st.session_state.footer_rendered = False
                st.session_state.show_details = False
                st.rerun()

        # Handle analysis
        if submit:
            if uploaded_file is None:
                st.error("Please upload a WAV audio file.")
                logging.warning("No audio file uploaded for analysis")
            else:
                st.audio(uploaded_file, format="audio/wav")
                with st.spinner("Analyzing audio..."):
                    features = extract_features(uploaded_file)
                    if features is not None:
                        try:
                            features_scaled = scaler.transform(features)
                            prediction = model.predict(features_scaled, verbose=0)[0][0]
                            probability = prediction * 100
                            outcome = "Parkinson’s Detected" if prediction > 0.5 else "No Parkinson’s"
                            confidence = probability if prediction > 0.5 else (1 - prediction) * 100
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            # Save prediction to database
                            try:
                                save_prediction(
                                    user_id=st.session_state.user_id,
                                    prediction_type="Parkinson’s",
                                    probability=probability,
                                    outcome=outcome,
                                    timestamp=timestamp
                                )
                                logging.info(f"Saved Parkinson’s prediction for user_id {st.session_state.user_id}")
                            except Exception as e:
                                st.warning("Failed to save prediction history.")
                                logging.error(f"Error saving prediction: {e}")

                            # Display result
                            result_color = "red" if prediction > 0.5 else "green"
                            st.markdown(
                                f"""
                                <div class="card page-transition" role="region" aria-label="Prediction Results">
                                    <p class="badge" style='background-color: {result_color};'>Prediction Result</p>
                                    <h2 style='text-align: center; font-size: 1.8rem; margin: 1rem 0;'>
                                        {outcome}
                                        <span class="tooltip" data-tooltip="Confidence level of the prediction">({confidence:.2f}%)</span>
                                    </h2>
                                    <p style='text-align: center; font-size: 0.9rem; color: #666;'>Completed at: {timestamp}</p>
                                    <div style='margin: 1rem 0;'>
                                        <p style='font-weight: 600; margin-bottom: 0.5rem;'>Confidence</p>
                                        <progress value="{confidence/100}" max="1" style='width: 100%; height: 10px;'></progress>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Toggle details
                            st.session_state.show_details = st.checkbox("Show Detailed Recommendations", value=st.session_state.show_details)
                            if st.session_state.show_details:
                                with st.expander("Recommendations", expanded=True):
                                    if prediction > 0.5:
                                        st.markdown(
                                            """
                                            **Recommendations:**
                                            - **Consult a Neurologist**: Schedule an appointment for a comprehensive evaluation.
                                            - **Monitor Symptoms**: Track speech and motor changes over time.
                                            - **Regular Check-ups**: Maintain routine health assessments.
                                            """
                                        )
                                    else:
                                        st.markdown(
                                            """
                                            **Recommendations:**
                                            - **Maintain Health**: Continue a balanced diet and exercise routine.
                                            - **Regular Monitoring**: Periodic voice analysis can help track changes.
                                            - **Stay Informed**: Learn about Parkinson’s risk factors.
                                            """
                                        )

                            logging.info(f"Parkinson’s prediction completed: {outcome}, Confidence {confidence:.2f}%")
                        except Exception as e:
                            st.error(f"Error during prediction: {e}")
                            logging.error(f"Prediction error: {e}")

        # Prediction history
        if st.session_state.logged_in and st.session_state.user_id:
            with st.expander("Recent Predictions", expanded=False):
                try:
                    history = get_user_predictions(st.session_state.user_id, prediction_type="Parkinson’s")
                    if not history.empty:
                        st.dataframe(
                            history[["timestamp", "outcome", "probability"]].sort_values(by="timestamp", ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "timestamp": "Date & Time",
                                "outcome": "Result",
                                "probability": st.column_config.NumberColumn("Confidence (%)", format="%.2f")
                            }
                        )
                    else:
                        st.info("No prediction history available.")
                except Exception as e:
                    st.warning("Unable to load prediction history.")
                    logging.error(f"Error loading prediction history: {e}")

    # Render footer only if not rendered by parkinsons.py
    if not st.session_state.footer_rendered:
        try:
            render_footer()
            st.session_state.footer_rendered = True
        except Exception as e:
            st.error(f"Error rendering footer: {e}")
            logging.error(f"Footer rendering failed: {e}")

if __name__ == "__main__":
    run_speech_app()