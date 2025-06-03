# 🧠 Health AI Super App

An end-to-end **AI-powered health diagnostics system** built with Python and Streamlit. It enables real-time prediction of **Diabetes**, **Parkinson’s Disease**, and **Pneumonia** using a combination of **XGBoost**, **Convolutional Neural Networks (CNN)**, and **Deep Neural Networks (DNN)**. Developed and deployed by a Machine Learning Engineer as a full-stack ML project.

---

## 🚀 Live Demo

## 🔗 [Try the App on Streamlit](https://health-ai-super-app-deed.streamlit.app/)

## 🎯 Project Features

- 🔐 **Secure Login System** – User authentication with prediction history tracking.
- 🩺 **Diabetes Detection** – Tabular data classified using XGBoost.
- 🧠 **Parkinson’s Detection** – Voice data processed via Librosa & DNN.
- 🫁 **Pneumonia Detection** – X-ray images analyzed with a CNN in TensorFlow.
- 🎨 **Modern UI** – Responsive layout, custom CSS, and page routing via Streamlit.

---

## 🛠️ Tech Stack

- **Languages**: Python
- **ML Libraries**:
  - [XGBoost](https://xgboost.readthedocs.io/en/latest/)
  - [TensorFlow](https://www.tensorflow.org/)
  - [Keras](https://keras.io/)
  - [Librosa](https://librosa.org/)
  - [OpenCV](https://opencv.org/)
- **Web Framework**: [Streamlit](https://streamlit.io/)
- **Database**: SQLite (`sqlite3`), `joblib` for model serialization
- **Environment Management**: Virtualenv

---

## 📁 Project Structure

```
health-ai-super-app/
├── app.py                   # Main entry point
├── layout.py                # UI layout + theming
├── style.css                # Custom styles
├── database.py              # Auth + SQLite logging
├── requirements.txt         # Dependency list
│
├── pages/                   # Streamlit multi-page navigation
│   ├── login.py
│   ├── about.py
│   ├── contact.py
│   ├── diabetes.py
│   ├── pneumonia.py
│   ├── parkinsons.py
│   └── privacy.py
│
├── diabetes_analysis/
│   ├── diabetes_app.py
│   └── diabetes_model.py
│
├── speech_analysis/
│   ├── speech_app.py
│   └── speech_model.py
│
├── xray_analysis/
│   ├── xray_app.py
│   └── xray_model.py
│
├── static/                  # Static assets (JSON logs, logo)
└── data/                    # Datasets (excluded via .gitignore)
```

---

## 🧪 Model Performance

| Condition   | Model            | Accuracy |
| ----------- | ---------------- | -------- |
| Diabetes    | XGBoost          | ~88%     |
| Parkinson’s | DNN (Keras)      | ~91%     |
| Pneumonia   | CNN (TensorFlow) | ~92%     |

---

## 🖥️ How to Run Locally

### ✅ 1. Clone the Repo

```bash
git clone https://github.com/didar-ali-deed/health-ai-super-app.git
cd health-ai-super-app
```

### ✅ 2. Create Virtual Environment & Install Requirements

```bash
python -m venv VENV
VENV\Scripts\activate       # Windows
# source VENV/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

### ✅ 3. Launch the App

```bash
streamlit run app.py
```

---

## 📌 Deployment

This project is deployed on Streamlit Cloud for public demo access.

You can deploy it yourself via:

- [Streamlit Community Cloud](https://streamlit.io/cloud)
- Docker
- Heroku (using gunicorn + streamlit)

---

## 🧑‍💻 Author

**Didar Ali**  
_Machine Learning Engineer | Python Developer_

- 🌐 GitHub: [https://github.com/didar-ali-deed](https://github.com/didar-ali-deed)
- 💼 LinkedIn: [https://linkedin.com/in/didar-ali-deed](https://linkedin.com/in/didar-ali-deed)
- 📫 Contact: youremail@example.com

---

## 📜 License

This project is open-source and available under the MIT License.
