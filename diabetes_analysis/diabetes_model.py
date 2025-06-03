import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# Load dataset
data = pd.read_csv("data/diabetes_data.csv")

# Select all relevant features
features = [
    "Age", "BMI", "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies", 
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth", 
    "MentHlth", "PhysHlth", "DiffWalk", "Sex", "Education", "Income"
]
X = data[features]
y = data["Diabetes_012"].apply(lambda x: 1 if x >= 1 else 0)  # Binary: diabetic/pre-diabetic vs. healthy

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train XGBoost model
model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=6,
    random_state=42,
    eval_metric='logloss'
)
model.fit(X_train_scaled, y_train)

# Save model and scaler
joblib.dump(model, "models/diabetes_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")

# Evaluate model
accuracy = model.score(X_test_scaled, y_test)
print(f"Model Accuracy: {accuracy:.2%}")