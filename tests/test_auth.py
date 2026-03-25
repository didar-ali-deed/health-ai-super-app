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
    Fernet(key.encode())  # raises ValueError if invalid


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
