import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import logging
import os
from database import init_db, save_patient_data, get_patient_history, save_prediction, get_user_predictions
from layout import apply_custom_css, render_header, render_footer

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize database
init_db()

# Cache model and scaler
@st.cache_resource
def load_model_and_scaler():
    try:
        model = joblib.load("models/diabetes_model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        return model, scaler
    except FileNotFoundError:
        st.error("Model or scaler file not found.")
        logging.error("Model or scaler file missing.")
        st.stop()

model, scaler = load_model_and_scaler()

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

# Streamlit app logic
def run_diabetes_app():
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
            <div class="page-transition" role="main" aria-label="Diabetes Prediction Page">
                <h1 style='text-align: center; font-size: 2.5rem; margin-bottom: 1rem;'>Diabetes Risk Prediction</h1>
                <p style='text-align: center; font-size: 1.2rem; max-width: 700px; margin: 0 auto 2rem;'>Assess your diabetes risk using our advanced AI model.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Check authentication
        if not st.session_state.logged_in:
            st.warning("Please log in to use the Diabetes Risk Prediction service.")
            st.session_state.redirect_to = "pages/diabetes.py"
            if st.button("Log in", key="login_button", use_container_width=True):
                st.session_state.page_transition = True
                st.switch_page("pages/login.py")
            logging.info("Unauthenticated access attempt to Diabetes Prediction")
            return

        # Display feature importance
        if os.path.exists("static/diabetes_feature_importance.png"):
            st.markdown(
                """
                <div class="card" style='text-align: center; margin-bottom: 2rem;'>
                    <p class="badge">Feature Importance</p>
                    <img src="static/diabetes_feature_importance.png" alt="Feature Importance" style='width: 100%; border-radius: 8px;'>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Form for inputs
        with st.form("diabetes_form"):
            st.markdown('<div class="form-container" role="form" aria-label="Diabetes Prediction Form">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin-bottom: 1rem;">Patient Information</h3>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown('<label class="form-label">Age Range</label>', unsafe_allow_html=True)
                age = st.selectbox("", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                                  format_func=lambda x: f"{18 + (x-1)*5}-{22 + (x-1)*5}", key="age", label_visibility="hidden", help="Select age range")
                st.markdown('<label class="form-label">BMI</label>', unsafe_allow_html=True)
                bmi = st.number_input("", min_value=10.0, max_value=100.0, value=25.0, step=0.1, key="bmi", label_visibility="hidden", help="Body Mass Index")
                st.markdown('<label class="form-label">High Blood Pressure?</label>', unsafe_allow_html=True)
                high_bp = st.selectbox("", ("No", "Yes"), key="high_bp", label_visibility="hidden", help="Diagnosed with high BP?")
                st.markdown('<label class="form-label">High Cholesterol?</label>', unsafe_allow_html=True)
                high_chol = st.selectbox("", ("No", "Yes"), key="high_chol", label_visibility="hidden", help="Diagnosed with high cholesterol?")
                st.markdown('<label class="form-label">Cholesterol Check?</label>', unsafe_allow_html=True)
                chol_check = st.selectbox("", ("Yes", "No"), key="chol_check", label_visibility="hidden", help="Recent cholesterol test?")
                st.markdown('<label class="form-label">Smoker?</label>', unsafe_allow_html=True)
                smoker = st.selectbox("", ("No", "Yes"), key="smoker", label_visibility="hidden", help="Lifetime smoking history")
                st.markdown('<label class="form-label">Stroke History?</label>', unsafe_allow_html=True)
                stroke = st.selectbox("", ("No", "Yes"), key="stroke", label_visibility="hidden")

            with col2:
                st.markdown('<label class="form-label">Heart Disease?</label>', unsafe_allow_html=True)
                heart_disease = st.selectbox("", ("No", "Yes"), key="heart_disease", label_visibility="hidden", help="History of heart issues")
                st.markdown('<label class="form-label">Physical Activity?</label>', unsafe_allow_html=True)
                phys_activity = st.selectbox("", ("Yes", "No"), key="phys_activity", label_visibility="hidden", help="Recent exercise")
                st.markdown('<label class="form-label">Fruits Daily?</label>', unsafe_allow_html=True)
                fruits = st.selectbox("", ("Yes", "No"), key="fruits", label_visibility="hidden", help="Daily fruit consumption")
                st.markdown('<label class="form-label">Vegetables Daily?</label>', unsafe_allow_html=True)
                veggies = st.selectbox("", ("No", "Yes"), key="veggies", label_visibility="hidden", help="Daily vegetable consumption")
                st.markdown('<label class="form-label">Heavy Alcohol?</label>', unsafe_allow_html=True)
                hvy_alcohol = st.selectbox("", ("No", "Yes"), key="hvy_alcohol", label_visibility="hidden", help="Alcohol consumption")
                st.markdown('<label class="form-label">Healthcare Coverage?</label>', unsafe_allow_html=True)
                any_healthcare = st.selectbox("", ("Yes", "No"), key="any_healthcare", label_visibility="hidden", help="Insurance coverage")
                st.markdown('<label class="form-label">Unable to See Doctor?</label>', unsafe_allow_html=True)
                no_doc_cost = st.selectbox("", ("No", "Yes"), key="no_doc_cost", label_visibility="hidden")

            with col3:
                st.markdown('<label class="form-label">General Health</label>', unsafe_allow_html=True)
                gen_health = st.selectbox("", [1, 2, 3, 4, 5],
                                         format_func=lambda x: ["Excellent", "Very Good", "Good", "Fair", "Poor"][x-1],
                                         key="gen_health", label_visibility="hidden", help="Self-reported health")
                st.markdown('<label class="form-label">Mental Health Days</label>', unsafe_allow_html=True)
                ment_health = st.number_input("", min_value=0, max_value=30, value=0, key="ment_health", label_visibility="hidden")
                st.markdown('<label class="form-label">Physical Health Days</label>', unsafe_allow_html=True)
                phys_health = st.number_input("", min_value=0, max_value=30, value=0, key="phys_health", label_visibility="hidden")
                st.markdown('<label class="form-label">Difficulty Walking?</label>', unsafe_allow_html=True)
                diff_walk = st.selectbox("", ("No", "Yes"), key="diff_walk", label_visibility="hidden")
                st.markdown('<label class="form-label">Sex</label>', unsafe_allow_html=True)
                sex = st.selectbox("", ("Female", "Male"), key="sex", label_visibility="hidden")
                st.markdown('<label class="form-label">Education Level</label>', unsafe_allow_html=True)
                education = st.selectbox("", [1, 2, 3, 4, 5, 6],
                                        format_func=lambda x: ["Never attended", "Grades 1-8", "Grades 9-11", "High School", "Some College", "College+"][x-1],
                                        key="education", label_visibility="hidden")
                st.markdown('<label class="form-label">Income Level</label>', unsafe_allow_html=True)
                income = st.selectbox("", [1, 2, 3, 4, 5, 6, 7, 8],
                                     format_func=lambda x: ["<10k", "10-15k", "15-20k", "20-25k", "25-35k", "35-50k", "50-75k", "75k+"][x-1],
                                     key="income", label_visibility="hidden")

            st.markdown('<div class="column-layout">', unsafe_allow_html=True)
            col_submit, col_reset = st.columns(2)
            with col_submit:
                submit = st.form_submit_button("Predict", use_container_width=True)
            with col_reset:
                reset = st.form_submit_button("Reset", use_container_width=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        # Handle reset
        if reset:
            if st.button("Confirm Reset", key="confirm_reset", use_container_width=True):
                st.session_state.reset = True
                st.session_state.show_details = False
                st.rerun()

        # Handle submission
        if submit:
            if not all([age, bmi, high_bp, high_chol, chol_check, smoker, stroke, heart_disease, phys_activity,
                        fruits, veggies, hvy_alcohol, any_healthcare, no_doc_cost, gen_health, ment_health,
                        phys_health, diff_walk, sex, education, income]):
                st.error("Please fill all fields.")
                return
            if bmi < 10.0 or bmi > 100.0:
                st.error("BMI must be between 10 and 100.")
                return

            inputs = {
                "Age": age,
                "BMI": bmi,
                "HighBP": 1 if high_bp == "Yes" else 0,
                "HighChol": 1 if high_chol == "Yes" else 0,
                "CholCheck": 1 if chol_check == "Yes" else 0,
                "Smoker": 1 if smoker == "Yes" else 0,
                "Stroke": 1 if stroke == "Yes" else 0,
                "HeartDiseaseorAttack": 1 if heart_disease == "Yes" else 0,
                "PhysActivity": 1 if phys_activity == "Yes" else 0,
                "Fruits": 1 if fruits == "Yes" else 0,
                "Veggies": 1 if veggies == "Yes" else 0,
                "HvyAlcoholConsump": 1 if hvy_alcohol == "Yes" else 0,
                "AnyHealthcare": 1 if any_healthcare == "Yes" else 0,
                "NoDocbcCost": 1 if no_doc_cost == "Yes" else 0,
                "GenHlth": gen_health,
                "MentHlth": ment_health,
                "PhysHlth": phys_health,
                "DiffWalk": 1 if diff_walk == "Yes" else 0,
                "Sex": 1 if sex == "Male" else 0,
                "Education": education,
                "Income": income
            }

            feature_order = list(inputs.keys())
            input_data = pd.DataFrame([inputs])[feature_order]

            with st.spinner("Analyzing data..."):
                try:
                    input_data_scaled = scaler.transform(input_data)
                    prediction = model.predict(input_data_scaled)[0]
                    probability = model.predict_proba(input_data_scaled)[0][1] * 100
                    outcome = "High Diabetes Risk" if prediction == 1 else "No Diabetes"
                    confidence = probability if prediction == 1 else (1 - probability/100) * 100
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Save prediction to predictions table
                    try:
                        save_prediction(
                            user_id=st.session_state.user_id,
                            prediction_type="Diabetes",
                            probability=probability,
                            outcome=outcome,
                            timestamp=timestamp
                        )
                        logging.info(f"Saved Diabetes prediction for user_id {st.session_state.user_id}")
                    except Exception as e:
                        st.warning("Failed to save prediction history.")
                        logging.error(f"Error saving prediction: {e}")

                    # Save patient data to patients table
                    db_inputs = {
                        "age": inputs["Age"],
                        "bmi": inputs["BMI"],
                        "high_bp": inputs["HighBP"],
                        "high_chol": inputs["HighChol"],
                        "chol_check": inputs["CholCheck"],
                        "smoker": inputs["Smoker"],
                        "stroke": inputs["Stroke"],
                        "heart_disease": inputs["HeartDiseaseorAttack"],
                        "phys_activity": inputs["PhysActivity"],
                        "fruits": inputs["Fruits"],
                        "veggies": inputs["Veggies"],
                        "hvy_alcohol": inputs["HvyAlcoholConsump"],
                        "any_healthcare": inputs["AnyHealthcare"],
                        "no_doc_cost": inputs["NoDocbcCost"],
                        "gen_health": inputs["GenHlth"],
                        "ment_health": inputs["MentHlth"],
                        "phys_health": inputs["PhysHlth"],
                        "diff_walk": inputs["DiffWalk"],
                        "sex": inputs["Sex"],
                        "education": inputs["Education"],
                        "income": inputs["Income"],
                        "prediction": int(prediction),
                        "probability": float(probability/100)
                    }
                    try:
                        save_patient_data(st.session_state.user_id, **db_inputs)
                    except Exception as e:
                        st.warning("Failed to save patient data.")
                        logging.error(f"Error saving patient data: {e}")

                    # Display result
                    result_color = "red" if prediction == 1 else "green"
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
                            if prediction == 1:
                                st.markdown(
                                    """
                                    **Recommendations:**
                                    - **Consult a Healthcare Provider**: Schedule an appointment for further evaluation.
                                    - **Monitor Diet**: Reduce sugar and refined carbs, increase fiber intake.
                                    - **Exercise Regularly**: Aim for 150 minutes of moderate activity per week.
                                    - **Regular Check-ups**: Monitor blood glucose and cholesterol levels.
                                    """
                                )
                            else:
                                st.markdown(
                                    """
                                    **Recommendations:**
                                    - **Maintain Balanced Diet**: Continue eating fruits and vegetables daily.
                                    - **Regular Physical Activity**: Keep up with exercise routines.
                                    - **Monitor Health**: Check health metrics periodically.
                                    """
                                )

                    logging.info(f"Diabetes prediction completed: {outcome}, Confidence {confidence:.2f}%")
                except Exception as e:
                    st.error(f"Error during prediction: {e}")
                    logging.error(f"Prediction error: {e}")

        # Prediction history
        if st.session_state.logged_in and st.session_state.user_id:
            with st.expander("Recent Predictions", expanded=False):
                try:
                    history = get_user_predictions(st.session_state.user_id, prediction_type="Diabetes")
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

        # Patient history
        st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Your Patient History</h2>", unsafe_allow_html=True)
        try:
            history = get_patient_history(st.session_state.user_id)
            if not history.empty:
                st.dataframe(
                    history[["timestamp", "prediction", "probability"]].sort_values(by="timestamp", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": "Date & Time",
                        "prediction": st.column_config.TextColumn("Outcome", help="0 = No Diabetes, 1 = Diabetes Risk"),
                        "probability": st.column_config.NumberColumn("Probability", format="%.2f")
                    }
                )
            else:
                st.info("No patient history available.")
        except Exception as e:
            st.warning("Unable to load patient history.")
            logging.error(f"Error loading patient history: {e}")

    # Render footer
    if not st.session_state.footer_rendered:
        try:
            render_footer()
            st.session_state.footer_rendered = True
        except Exception as e:
            st.error(f"Error rendering footer: {e}")
            logging.error(f"Footer rendering failed: {e}")

if __name__ == "__main__":
    run_diabetes_app()