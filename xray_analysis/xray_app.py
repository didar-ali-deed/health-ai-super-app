import streamlit as st
import tensorflow as tf
import numpy as np
import pandas as pd
from PIL import Image
from datetime import datetime
import json
import os
import logging
from io import BytesIO
import base64
from database import save_prediction, get_user_predictions
from layout import apply_custom_css, render_header, render_footer

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cache model
@st.cache_resource
def load_model():
    try:
        return tf.keras.models.load_model("models/pneumonia_model.keras")
    except Exception as e:
        st.error(f"Error loading model: {e}")
        logging.error(f"Pneumonia model failed to load: {e}")
        st.stop()

model = load_model()

# Image preprocessing
def preprocess_image(image):
    try:
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image = image.resize((150, 150))
        image_array = np.array(image) / 255.0
        if image_array.shape[-1] != 3:
            image_array = np.stack([image_array] * 3, axis=-1)
        return np.expand_dims(image_array, axis=0)
    except Exception as e:
        st.error(f"Error processing image: {e}")
        logging.error(f"Image preprocessing failed: {e}")
        return None

# Prediction function
def predict_pneumonia(image):
    processed_image = preprocess_image(image)
    if processed_image is None:
        return None
    try:
        probability = float(model.predict(processed_image, verbose=0)[0][0] * 100)
        return probability
    except Exception as e:
        st.error(f"Error during prediction: {e}")
        logging.error(f"Prediction error: {e}")
        return None

# Encode image to base64
def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

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
def run_pneumonia_app():
    initialize_session_state()

    # Apply CSS
    try:
        apply_custom_css(st.session_state.theme)
    except Exception as e:
        st.error(f"Error applying CSS: {e}")
        logging.error(f"CSS application failed: {e}")

    # Render header
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
            <div class="page-transition" role="main" aria-label="Pneumonia Detection Page">
                <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>Chest X-ray Pneumonia Detection</h1>
                <p style='text-align: center; font-size: 1.2rem; max-width: 700px; margin: 0 auto 2rem;'>Upload a chest X-ray to detect pneumonia using advanced AI.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Check authentication
        if not st.session_state.logged_in:
            st.warning("Please log in to use the Pneumonia Detection service.")
            st.session_state.redirect_to = "pages/pneumonia.py"
            if st.button("Log in", key="login_button", use_container_width=True):
                st.session_state.page_transition = True
                st.switch_page("pages/login.py")
            logging.info("Unauthenticated access attempt to Pneumonia Detection")
            return

        # Model metrics
        if os.path.exists("static/pneumonia_metrics.json"):
            try:
                with open("static/pneumonia_metrics.json") as f:
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
                logging.error(f"Error loading pneumonia_metrics.json: {e}")

        # Input form
        with st.form("pneumonia_form"):
            st.markdown('<div class="form-container" role="form" aria-label="X-ray Upload Form">', unsafe_allow_html=True)
            st.markdown('<label class="form-label">Upload X-ray Image</label>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "",
                type=["jpg", "jpeg", "png"],
                key="xray_file",
                label_visibility="hidden",
                help="Upload a chest X-ray image (JPG or PNG)"
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
                st.error("Please upload an X-ray image.")
                logging.warning("No X-ray image uploaded")
                return

            image = Image.open(uploaded_file)
            st.markdown(
                f"""
                <div class="card" style='margin: 1rem 0;'>
                    <img src="data:image/png;base64,{encode_image(image)}" alt="Uploaded X-ray" style='width: 100%; border-radius: 8px;'>
                    <p style='text-align: center; font-style: italic;'>Uploaded X-ray</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.spinner("Analyzing X-ray..."):
                probability = predict_pneumonia(image)
                if probability is not None:
                    outcome = "Pneumonia Detected" if probability > 50 else "No Pneumonia"
                    confidence = probability if probability > 50 else (100 - probability)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Save prediction
                    try:
                        save_prediction(
                            user_id=st.session_state.user_id,
                            prediction_type="Pneumonia",
                            probability=float(probability),
                            outcome=outcome,
                            timestamp=timestamp
                        )
                        logging.info(f"Saved Pneumonia prediction for user_id {st.session_state.user_id}")
                    except Exception as e:
                        st.warning("Failed to save prediction history.")
                        logging.error(f"Error saving prediction: {e}")

                    # Display result
                    result_color = "red" if probability > 50 else "green"
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

                    # Toggle recommendations
                    st.session_state.show_details = st.checkbox("Show Detailed Recommendations", value=st.session_state.show_details)
                    if st.session_state.show_details:
                        with st.expander("Recommendations", expanded=True):
                            if probability > 50:
                                st.markdown(
                                    """
                                    **Recommendations:**
                                    - **Consult a Doctor**: Seek immediate medical evaluation.
                                    - **Monitor Symptoms**: Watch for cough, fever, or breathing difficulties.
                                    - **Follow Medical Advice**: Adhere to prescribed treatments.
                                    """
                                )
                            else:
                                st.markdown(
                                    """
                                    **Recommendations:**
                                    - **Maintain Health**: Continue a healthy lifestyle.
                                    - **Regular Check-ups**: Schedule periodic health screenings.
                                    - **Stay Informed**: Monitor respiratory health.
                                    """
                                )

                    logging.info(f"Pneumonia prediction completed: {outcome}, Confidence {confidence:.2f}%")

        # Prediction history
        if st.session_state.logged_in and st.session_state.user_id:
            with st.expander("Recent Predictions", expanded=False):
                try:
                    history = get_user_predictions(st.session_state.user_id, prediction_type="Pneumonia")
                    if not history.empty:
                        # Ensure probability is numeric
                        history['probability'] = pd.to_numeric(history['probability'], errors='coerce')
                        st.dataframe(
                            history[["timestamp", "outcome", "probability"]].sort_values(by="timestamp", ascending=False),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "timestamp": "Date & Time",
                                "outcome": "Result",
                                "probability": st.column_config.NumberColumn(
                                    "Confidence (%)",
                                    format="%.2f",
                                    help="Prediction confidence as a percentage"
                                )
                            }
                        )
                    else:
                        st.info("No prediction history available.")
                except Exception as e:
                    st.warning("Unable to load prediction history.")
                    logging.error(f"Error loading prediction history: {e}")

    # Render footer
    if not st.session_state.footer_rendered:
        try:
            render_footer()
            st.session_state.footer_rendered = True
        except Exception as e:
            st.error(f"Error rendering footer: {e}")
            logging.error(f"Footer rendering failed: {e}")

if __name__ == "__main__":
    run_pneumonia_app()