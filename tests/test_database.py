"""Tests for 2FA database functions"""
import sqlite3
import tempfile
import os
import sys

# Patch DB_PATH to a temp file before importing database
import tempfile
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_tmp_path = _tmp.name
_tmp.close()

# Patch DB_PATH before import
import importlib
import database as db_mod
_orig_path = db_mod.DB_PATH
db_mod.DB_PATH = _tmp_path
# Re-create pool with new path
db_mod.db_pool = db_mod.DatabaseConnection()
db_mod.db_pool.local = type('L', (), {})()
db_mod.init_db()


def _create_user():
    with db_mod.db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            ("testuser2fa", "hash", "test2fa@example.com"),
        )
        conn.commit()
        c.execute("SELECT id FROM users WHERE username = ?", ("testuser2fa",))
        return c.fetchone()[0]


def test_2fa_roundtrip():
    """save_2fa_secret + get_2fa_info returns the same secret."""
    uid = _create_user()
    secret = "JBSWY3DPEHPK3PXP"
    db_mod.save_2fa_secret(uid, secret)
    enabled, stored = db_mod.get_2fa_info(uid)
    assert stored == secret, f"Expected {secret!r}, got {stored!r}"


def test_enable_disable_2fa():
    """enable_2fa sets flag; disable_2fa clears both flag and secret."""
    uid = _create_user()
    db_mod.save_2fa_secret(uid, "TESTSECRET")
    db_mod.enable_2fa(uid)
    enabled, secret = db_mod.get_2fa_info(uid)
    assert enabled == 1
    assert secret == "TESTSECRET"

    db_mod.disable_2fa(uid)
    enabled, secret = db_mod.get_2fa_info(uid)
    assert enabled == 0
    assert secret is None


def test_get_2fa_info_defaults():
    """get_2fa_info returns (0, None) for a user with no 2FA configured."""
    with db_mod.db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            ("freshuser", "hash", "fresh@example.com"),
        )
        conn.commit()
        c.execute("SELECT id FROM users WHERE username = ?", ("freshuser",))
        uid = c.fetchone()[0]
    enabled, secret = db_mod.get_2fa_info(uid)
    assert enabled == 0
    assert secret is None


def test_contact_submissions_table_exists():
    """contact_submissions table must exist after init_db()."""
    with db_mod.db_pool.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact_submissions'")
        row = c.fetchone()
    assert row is not None, "contact_submissions table not found"
