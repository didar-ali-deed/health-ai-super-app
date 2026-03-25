import base64
import logging
from io import BytesIO

import pyotp
import qrcode
import streamlit as st

from auth import handle_logout, push_notification
from database import delete_user, update_user_theme, save_2fa_secret, enable_2fa, disable_2fa


def render_profile() -> None:
    """Render the profile management expander."""
    with st.expander("Profile", expanded=False):
        _render_theme_toggle()
        st.divider()
        _render_2fa_section()
        st.divider()
        _render_delete_account()


def _render_theme_toggle() -> None:
    st.subheader("Appearance")
    current = st.session_state.get("theme", "light")
    label = "Switch to Dark Mode" if current == "light" else "Switch to Light Mode"
    if st.button(label, key="profile_theme_toggle"):
        new_theme = "dark" if current == "light" else "light"
        st.session_state.theme = new_theme
        try:
            update_user_theme(st.session_state.user_id, new_theme)
        except Exception as exc:
            logging.error("Theme update failed: %s", exc)
        st.rerun()


def _render_2fa_section() -> None:
    st.subheader("Two-Factor Authentication")
    if st.session_state.get("2fa_enabled", False):
        st.success("2FA is enabled on your account.")
        if st.button("Disable 2FA", key="disable_2fa"):
            try:
                disable_2fa(st.session_state.user_id)
                st.session_state["2fa_enabled"] = False
                st.session_state["2fa_secret"] = None
                push_notification("success", "2FA disabled.")
                logging.info("2FA disabled for user_id %s", st.session_state.user_id)
            except Exception as exc:
                st.error(f"Error disabling 2FA: {exc}")
            st.rerun()
        return

    if st.button("Set Up 2FA", key="setup_2fa"):
        secret = pyotp.random_base32()
        st.session_state["2fa_secret"] = secret
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            st.session_state.username, issuer_name="Health AI"
        )
        qr = qrcode.make(uri)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        st.image(
            f"data:image/png;base64,{qr_b64}",
            caption="Scan this QR code with your authenticator app",
            width=200,
        )

    if st.session_state.get("2fa_secret"):
        code = st.text_input(
            "Enter 6-digit code to verify and activate",
            key="verify_2fa_input",
            max_chars=6,
        )
        if st.button("Activate 2FA", key="activate_2fa"):
            totp = pyotp.TOTP(st.session_state["2fa_secret"])
            if totp.verify(code):
                save_2fa_secret(st.session_state.user_id, st.session_state["2fa_secret"])
                enable_2fa(st.session_state.user_id)
                st.session_state["2fa_enabled"] = True
                push_notification("success", "2FA enabled successfully!")
                logging.info("2FA enabled for user_id %s", st.session_state.user_id)
                st.rerun()
            else:
                st.error("Invalid code — please try again.")


def _render_delete_account() -> None:
    st.subheader("Danger Zone")
    with st.expander("Delete Account", expanded=False):
        st.warning(
            "This permanently deletes your account and all health records. "
            "This cannot be undone."
        )
        confirm = st.text_input(
            'Type your username to confirm', key="delete_confirm_input"
        )
        if st.button("Permanently Delete My Account", key="confirm_delete", type="primary"):
            if confirm != st.session_state.username:
                st.error("Username does not match.")
                return
            try:
                delete_user(st.session_state.user_id)
                push_notification("success", "Account deleted.")
                logging.info("User %s deleted account", st.session_state.username)
                handle_logout()
            except Exception as exc:
                st.error(f"Error deleting account: {exc}")
                logging.error("Account deletion error: %s", exc)
