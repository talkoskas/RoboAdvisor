# fullstack/login_ui.py
import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx

from fullstack import auth_manager, user_management, utils
from fullstack.database_mongo import create_chat, get_chats_by_user

# init cookie mgr once per process
_cookie_manager = None
def cookie_manager():
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = stx.CookieManager()
    return _cookie_manager

def ensure_session_state_keys():
    defaults = {
        "authenticated": False,
        "username": None,
        "reset_password": False,
        "registration": False,
        "login_error": None,
        "cookie_checked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def check_auth_cookie():
    cm = cookie_manager()
    if not st.session_state.cookie_checked:
        st.session_state.cookie_checked = True
        token = cm.get("auth_token")
        if token:
            user = auth_manager.validate_auth_token(token)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user["username"]

def display_login():
    ensure_session_state_keys()
    check_auth_cookie()

    st.markdown('<div class="main-title">Hello There! Let\'s get to know each other ☺️</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me", value=True)
            submit = st.form_submit_button("Continue")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    res = auth_manager.authenticate_user(username, password)
                    if res["success"]:
                        st.session_state.authenticated = True
                        st.session_state.username = username

                        existing = get_chats_by_user(username)
                        if not existing:
                            # Only create if this user has zero chats
                            new_id = create_chat(username, [], None)
                            st.session_state.current_chat_id = str(new_id)
                            st.session_state.selected_chat_id = str(new_id)
                        else:
                            # Select newest existing chat
                            newest_id = str(existing[0]["_id"])
                            st.session_state.current_chat_id = newest_id
                            st.session_state.selected_chat_id = newest_id

                        st.session_state.chat_history = []
                        st.session_state.available_chats = sorted(
                            get_chats_by_user(username),
                            key=lambda m: m["last_updated"],
                            reverse=True
                        )
                        st.session_state.selected_chat_idx = 0
                        st.rerun()
                    else:
                        st.error(res["message"])

    st.markdown("Don't have an account?")
    if st.button("Sign Up"):
        st.session_state.registration = True
        st.rerun()

def display_registration():
    ensure_session_state_keys()

    st.title("Create account")
    with st.form("registration_form"):
        username = st.text_input("Username*", key="reg_username")
        email = st.text_input("Email address*", key="reg_email")
        password = st.text_input("Password*", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password*", type="password", key="reg_confirm_password")
        submit = st.form_submit_button("Create account")

        if submit:
            if not username or not email or not password or not confirm:
                st.error("Please fill in all fields")
            elif password != confirm:
                st.error("Passwords do not match")
            elif not utils.is_valid_email(email):
                st.error("Please enter a valid email address")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                res = user_management.register_user(username, email, password)
                if res["success"]:
                    st.success("Registration successful! Logging you in…")
                    st.session_state.registration = False
                    st.session_state.authenticated = True
                    st.session_state.username = username

                    new_id = create_chat(username, [], None)
                    st.session_state.current_chat_id = str(new_id)
                    st.session_state.chat_history = []
                    st.session_state.available_chats = sorted(
                        get_chats_by_user(username),
                        key=lambda m: m["last_updated"],
                        reverse=True
                    )
                    st.session_state.selected_chat_idx = 0

                    st.rerun()
                else:
                    st.error(res["message"])

    if st.button("Back to Login"):
        st.session_state.registration = False
        st.rerun()

def display_password_reset():
    ensure_session_state_keys()

    if "reset_email_sent" not in st.session_state:
        st.session_state.reset_email_sent = False

    if not st.session_state.reset_email_sent:
        st.title("Reset password")
        with st.form("reset_request_form"):
            email = st.text_input("Email address*", key="reset_email")
            submit = st.form_submit_button("Send reset link")
            if submit:
                if not email:
                    st.error("Please enter your email address")
                elif not utils.is_valid_email(email):
                    st.error("Please enter a valid email address")
                else:
                    res = user_management.request_password_reset(email)
                    if res["success"]:
                        st.session_state.reset_email_sent = True
                        st.success("Password reset instructions sent to your email")
                        st.rerun()
                    else:
                        st.error(res["message"])
        if st.button("Back to Login"):
            st.session_state.reset_password = False
            st.rerun()
    else:
        st.title("Create new password")
        with st.form("reset_password_form"):
            code = st.text_input("Reset code from email*", key="reset_code")
            new_password = st.text_input("New Password*", type="password", key="new_password")
            confirm = st.text_input("Confirm New Password*", type="password", key="confirm_new_password")
            submit = st.form_submit_button("Reset Password")
            if submit:
                if not code or not new_password or not confirm:
                    st.error("Please fill in all fields")
                elif new_password != confirm:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long")
                else:
                    res = user_management.reset_password(code, new_password)
                    if res["success"]:
                        st.success("Password has been reset. Please login.")
                        st.session_state.reset_password = False
                        st.session_state.reset_email_sent = False
                        st.rerun()
                    else:
                        st.error(res["message"])
