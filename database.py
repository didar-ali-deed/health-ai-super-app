import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import secrets
import re
import threading
import traceback
import shutil
from argon2 import PasswordHasher
import atexit
import os

# Configure logging
logging.basicConfig(
    filename='database.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

DB_PATH = "health_data.db"
BACKUP_PATH = "health_data_backup.db"
ph = PasswordHasher()
last_backup_time = None

# Connection pooling for thread-safe database access
class DatabaseConnection:
    def __init__(self):
        self.local = threading.local()

    def get_connection(self):
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        return self.local.connection

    def close(self):
        if hasattr(self.local, 'connection'):
            self.local.connection.close()
            del self.local.connection

db_pool = DatabaseConnection()

# Register cleanup at exit
atexit.register(db_pool.close)

def backup_database(force=False):
    """Create a backup of the SQLite database if needed."""
    global last_backup_time
    try:
        now = datetime.now()
        if force or last_backup_time is None or (now - last_backup_time) >= timedelta(days=1):
            shutil.copyfile(DB_PATH, BACKUP_PATH)
            last_backup_time = now
            logging.info("Database backup created successfully")
    except Exception as e:
        logging.error(f"Database backup failed: {str(e)}\n{traceback.format_exc()}")
        raise

def init_db():
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            # Create patients table
            c.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    age INTEGER CHECK(age >= 1 AND age <= 13),
                    bmi REAL CHECK(bmi >= 10 AND bmi <= 100),
                    high_bp INTEGER CHECK(high_bp IN (0, 1)),
                    high_chol INTEGER CHECK(high_chol IN (0, 1)),
                    chol_check INTEGER CHECK(chol_check IN (0, 1)),
                    smoker INTEGER CHECK(smoker IN (0, 1)),
                    stroke INTEGER CHECK(stroke IN (0, 1)),
                    heart_disease INTEGER CHECK(heart_disease IN (0, 1)),
                    phys_activity INTEGER CHECK(phys_activity IN (0, 1)),
                    fruits INTEGER CHECK(fruits IN (0, 1)),
                    veggies INTEGER CHECK(veggies IN (0, 1)),
                    hvy_alcohol INTEGER CHECK(hvy_alcohol IN (0, 1)),
                    any_healthcare INTEGER CHECK(any_healthcare IN (0, 1)),
                    no_doc_cost INTEGER CHECK(no_doc_cost IN (0, 1)),
                    gen_health INTEGER CHECK(gen_health >= 1 AND gen_health <= 5),
                    ment_health INTEGER CHECK(ment_health >= 0 AND ment_health <= 30),
                    phys_health INTEGER CHECK(phys_health >= 0 AND phys_health <= 30),
                    diff_walk INTEGER CHECK(diff_walk IN (0, 1)),
                    sex INTEGER CHECK(sex IN (0, 1)),
                    education INTEGER CHECK(education >= 1 AND education <= 6),
                    income INTEGER CHECK(income >= 1 AND income <= 8),
                    prediction INTEGER CHECK(prediction IN (0, 1)),
                    probability REAL CHECK(probability >= 0 AND probability <= 1),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Create predictions table
            c.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prediction_type TEXT NOT NULL,
                    probability REAL CHECK(probability >= 0 AND probability <= 100),
                    outcome TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Create users table
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'light',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create password_resets table
            c.execute('''
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Create indexes
            c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON patients(timestamp)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON patients(user_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp)')
            conn.commit()
            backup_database(force=True)
            logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}\n{traceback.format_exc()}")
        raise

def hash_password(password):
    return ph.hash(password)

def verify_password(password, hashed):
    try:
        return ph.verify(hashed, password)
    except:
        return False

def save_prediction(user_id, prediction_type, probability, outcome, timestamp):
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")
        if not isinstance(prediction_type, str) or not prediction_type:
            raise ValueError("Invalid prediction_type")
        if not isinstance(probability, (int, float)) or not (0 <= probability <= 100):
            raise ValueError("Probability must be between 0 and 100")
        if not isinstance(outcome, str) or not outcome.strip():
            raise ValueError("Outcome must be a non-empty string")
        if not isinstance(timestamp, str) or not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', timestamp):
            raise ValueError("Invalid timestamp format")
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO predictions (user_id, prediction_type, probability, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, prediction_type, float(probability), outcome, timestamp)
            )
            conn.commit()
            logging.info(f"Saved {prediction_type} prediction for user_id {user_id}")
    except Exception as e:
        logging.error(f"Error saving prediction: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_predictions(user_id, prediction_type=None):
    try:
        with db_pool.get_connection() as conn:
            query = "SELECT id, user_id, prediction_type, probability, outcome, timestamp FROM predictions WHERE user_id = ?"
            params = [user_id]
            if prediction_type:
                query += " AND prediction_type = ?"
                params.append(prediction_type)
            df = pd.read_sql_query(query, conn, params=params)
            df['probability'] = pd.to_numeric(df['probability'], errors='coerce')
            return df
    except Exception as e:
        logging.error(f"Error retrieving predictions: {str(e)}\n{traceback.format_exc()}")
        raise

def save_patient_data(user_id, **kwargs):
    try:
        if any(v is None for v in kwargs.values()):
            raise ValueError("All input fields must be provided")
        if any(isinstance(v, (int, float)) and v < 0 for v in kwargs.values()):
            raise ValueError("Input values must be non-negative")
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            columns = ', '.join(['user_id'] + list(kwargs.keys()))
            placeholders = ', '.join(['?'] * (len(kwargs) + 1))
            values = [user_id] + list(kwargs.values())
            c.execute(f'INSERT INTO patients ({columns}) VALUES ({placeholders})', values)
            conn.commit()
            logging.info(f"Patient data saved for user_id {user_id}")
    except Exception as e:
        logging.error(f"Error saving patient data: {str(e)}\n{traceback.format_exc()}")
        raise

def get_patient_history(user_id):
    try:
        with db_pool.get_connection() as conn:
            query = "SELECT * FROM patients WHERE user_id = ? ORDER BY timestamp DESC"
            return pd.read_sql_query(query, conn, params=(user_id,))
    except Exception as e:
        logging.error(f"Error retrieving patient history for user_id {user_id}: {str(e)}\n{traceback.format_exc()}")
        raise

def register_user(username, password, email):
    try:
        username = username.strip()
        email = email.strip().lower()
        if not username or not password or not email:
            raise ValueError("Username, password, and email are required")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            raise ValueError("Invalid email format")
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            password_hash = hash_password(password)
            c.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                      (username, password_hash, email))
            conn.commit()
            logging.info(f"User {username} registered successfully")
            return True
    except sqlite3.IntegrityError:
        logging.warning(f"Registration failed: Username or email already exists")
        return False
    except Exception as e:
        logging.error(f"Registration error: {str(e)}\n{traceback.format_exc()}")
        raise

def authenticate_user(username, password):
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
            user = c.fetchone()
            if user and verify_password(password, user[2]):
                logging.info(f"User {username} authenticated successfully")
                return user
            logging.warning(f"Authentication failed for {username}")
            return None
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_by_email(email):
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
            user = c.fetchone()
            return user
    except Exception as e:
        logging.error(f"Error retrieving user by email: {str(e)}\n{traceback.format_exc()}")
        raise

def create_reset_token(user_id):
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)",
                      (user_id, token, expires_at))
            conn.commit()
            logging.info(f"Reset token created for user_id {user_id}")
            return token
    except Exception as e:
        logging.error(f"Error creating reset token: {str(e)}\n{traceback.format_exc()}")
        raise

def get_reset_token(token):
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM password_resets WHERE token = ? AND expires_at > ?",
                      (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            return c.fetchone()
    except Exception as e:
        logging.error(f"Error retrieving reset token: {str(e)}\n{traceback.format_exc()}")
        raise

def cleanup_expired_tokens():
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM password_resets WHERE expires_at <= ?",
                      (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
            conn.commit()
            logging.info("Expired tokens cleaned up")
    except Exception as e:
        logging.error(f"Error cleaning up tokens: {str(e)}\n{traceback.format_exc()}")
        raise

def update_user_theme(user_id, theme):
    try:
        if theme not in ('light', 'dark'):
            raise ValueError("Theme must be 'light' or 'dark'")
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user_id))
            conn.commit()
            logging.info(f"Updated theme to {theme} for user_id {user_id}")
    except Exception as e:
        logging.error(f"Error updating user theme: {str(e)}\n{traceback.format_exc()}")
        raise

def delete_user(user_id):
    try:
        with db_pool.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM patients WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            backup_database()
            logging.info(f"User {user_id} and related data deleted successfully")
    except Exception as e:
        logging.error(f"Error deleting user {user_id}: {str(e)}\n{traceback.format_exc()}")
        raise