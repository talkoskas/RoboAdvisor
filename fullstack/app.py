import streamlit as st
import os
import extra_streamlit_components as stx
from datetime import datetime, timedelta

import auth_manager
import user_management
import social_auth
import utils

# Set page configuration
st.set_page_config(
    page_title="Stock Market AI Chatbot - Login",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "reset_password" not in st.session_state:
    st.session_state.reset_password = False
if "registration" not in st.session_state:
    st.session_state.registration = False
if "login_error" not in st.session_state:
    st.session_state.login_error = None

# Initialize cookie manager
cookie_manager = stx.CookieManager()

# Check if user is already authenticated via cookie
if not st.session_state.authenticated:
    auth_cookie = cookie_manager.get("auth_token")
    if auth_cookie:
        # Validate the auth cookie
        user = auth_manager.validate_auth_token(auth_cookie)
        if user:
            st.session_state.authenticated = True
            st.session_state.username = user["username"]

# Main app logic
def main():
    if st.session_state.authenticated:
        display_main_app()
    elif st.session_state.reset_password:
        display_password_reset()
    elif st.session_state.registration:
        display_registration()
    else:
        display_login()

def display_login():
    st.title("Stock Market AI Chatbot")
    st.subheader("Login")
    
    # Display login error if any
    if st.session_state.login_error:
        st.error(st.session_state.login_error)
        st.session_state.login_error = None
    
    # Create a more compact and smaller login form
    with st.form("login_form"):
        # Create a container with custom CSS for smaller inputs
        st.markdown("""
        <style>
        .small-input input {
            padding: 0.5rem;
            font-size: 0.9rem;
            max-width: 250px;
        }
        .stButton button {
            padding: 0.3rem 0.5rem;
            font-size: 0.8rem;
        }
        .social-buttons button {
            padding: 0.2rem 0.3rem;
            font-size: 0.75rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add the 'small-input' class to contain these inputs
        with st.container():
            st.markdown('<div class="small-input">', unsafe_allow_html=True)
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            st.markdown('</div>', unsafe_allow_html=True)
            
            remember_me = st.checkbox("Remember me", key="remember_me")
        
        # Make the buttons more compact
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Login")
        with col2:
            register = st.form_submit_button("Register")
            
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                login_result = auth_manager.authenticate_user(username, password)
                if login_result["success"]:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    
                    # Set auth cookie if remember me is checked
                    if remember_me:
                        expiry = datetime.now() + timedelta(days=30)
                        token = auth_manager.generate_auth_token(username)
                        cookie_manager.set("auth_token", token, expires_at=expiry)
                    
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error(login_result["message"])
        
        if register:
            st.session_state.registration = True
            st.rerun()
    
    # Password reset link - make it smaller
    if st.button("Forgot password?", key="forgot_pwd", type="secondary", help="Reset your password"):
        st.session_state.reset_password = True
        st.rerun()
    
    # Compact social login section
    st.markdown("<div class='social-buttons'><p style='font-size: 0.8rem; margin-bottom: 0.5rem;'>Quick login:</p></div>", unsafe_allow_html=True)
    
    # More compact social login buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Google", key="google_login", use_container_width=True):
            auth_url = social_auth.get_google_auth_url()
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)
    
    with col2:
        if st.button("Facebook", key="fb_login", use_container_width=True):
            auth_url = social_auth.get_facebook_auth_url()
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)

def display_registration():
    st.title("Register New Account")
    
    with st.form("registration_form"):
        # Apply the same CSS style for consistency
        st.markdown("""
        <style>
        .small-input input {
            padding: 0.5rem;
            font-size: 0.9rem;
            max-width: 250px;
        }
        .stButton button {
            padding: 0.3rem 0.5rem;
            font-size: 0.8rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create smaller form inputs
        with st.container():
            st.markdown('<div class="small-input">', unsafe_allow_html=True)
            username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # More compact buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Register")
        with col2:
            back = st.form_submit_button("Back to Login")
        
        if submit:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not utils.is_valid_email(email):
                st.error("Please enter a valid email address")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                registration_result = user_management.register_user(username, email, password)
                if registration_result["success"]:
                    st.success("Registration successful. You can now login.")
                    st.session_state.registration = False
                    st.rerun()
                else:
                    st.error(registration_result["message"])
        
        if back:
            st.session_state.registration = False
            st.rerun()

def display_password_reset():
    st.title("Reset Password")
    
    # First step: Request email
    if "reset_email_sent" not in st.session_state:
        st.session_state.reset_email_sent = False
    
    if not st.session_state.reset_email_sent:
        with st.form("reset_request_form"):
            # Apply consistent CSS styles
            st.markdown("""
            <style>
            .small-input input {
                padding: 0.5rem;
                font-size: 0.9rem;
                max-width: 250px;
            }
            .stButton button {
                padding: 0.3rem 0.5rem;
                font-size: 0.8rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Smaller input field
            with st.container():
                st.markdown('<div class="small-input">', unsafe_allow_html=True)
                email = st.text_input("Enter your email address", key="reset_email")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Compact buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Request Reset")
            with col2:
                back = st.form_submit_button("Back to Login")
            
            if submit:
                if not email:
                    st.error("Please enter your email address")
                elif not utils.is_valid_email(email):
                    st.error("Please enter a valid email address")
                else:
                    reset_result = user_management.request_password_reset(email)
                    if reset_result["success"]:
                        st.session_state.reset_email_sent = True
                        st.success("Password reset instructions have been sent to your email")
                        st.rerun()
                    else:
                        st.error(reset_result["message"])
            
            if back:
                st.session_state.reset_password = False
                st.rerun()
    # Second step: Enter reset code and new password
    else:
        with st.form("reset_password_form"):
            # Apply consistent CSS styles
            st.markdown("""
            <style>
            .small-input input {
                padding: 0.5rem;
                font-size: 0.9rem;
                max-width: 250px;
            }
            .stButton button {
                padding: 0.3rem 0.5rem;
                font-size: 0.8rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Smaller input fields
            with st.container():
                st.markdown('<div class="small-input">', unsafe_allow_html=True)
                reset_code = st.text_input("Enter reset code from email", key="reset_code")
                new_password = st.text_input("New Password", type="password", key="new_password")
                confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Compact buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Reset Password")
            with col2:
                back = st.form_submit_button("Back to Login")
            
            if submit:
                if not reset_code or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long")
                else:
                    reset_result = user_management.reset_password(reset_code, new_password)
                    if reset_result["success"]:
                        st.success("Password has been reset successfully. You can now login with your new password.")
                        st.session_state.reset_password = False
                        st.session_state.reset_email_sent = False
                        st.rerun()
                    else:
                        st.error(reset_result["message"])
            
            if back:
                st.session_state.reset_password = False
                st.session_state.reset_email_sent = False
                st.rerun()

def display_main_app():
    st.title(f"Welcome to Stock Market AI Chatbot, {st.session_state.username}!")
    
    # Logout button
    if st.button("Logout"):
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.username = None
        
        # Clear auth cookie
        cookie_manager.delete("auth_token")
        
        st.success("You have been logged out")
        st.rerun()
    
    # Here you would integrate with the existing AI chatbot application
    st.write("You are now logged in. The stock market AI chatbot would appear here.")
    
    # Placeholder for the chatbot UI
    st.markdown("---")
    st.subheader("Chat with the Stock Market AI")
    
    user_input = st.text_input("Ask a question about stocks:", key="user_query")
    if st.button("Send"):
        if user_input:
            # This would be replaced with actual chatbot functionality
            st.write(f"You asked: {user_input}")
            st.write("AI response would appear here based on your query.")
        else:
            st.warning("Please enter a question first.")

# Handle OAuth callbacks
params = st.query_params
if "code" in params and "state" in params:
    # Social login callback processing
    state = params["state"]
    code = params["code"]
    
    # Determine provider from state
    if state.startswith("google"):
        user_info = social_auth.handle_google_callback(code)
        if user_info and "email" in user_info:
            # Create/login user
            login_result = user_management.social_login(user_info["email"], "google")
            if login_result["success"]:
                st.session_state.authenticated = True
                st.session_state.username = login_result["username"]
                # Clear URL parameters
                params.clear()
                st.rerun()
            else:
                st.session_state.login_error = login_result["message"]
                params.clear()
                st.rerun()
    
    elif state.startswith("facebook"):
        user_info = social_auth.handle_facebook_callback(code)
        if user_info and "email" in user_info:
            # Create/login user
            login_result = user_management.social_login(user_info["email"], "facebook")
            if login_result["success"]:
                st.session_state.authenticated = True
                st.session_state.username = login_result["username"]
                # Clear URL parameters
                params.clear()
                st.rerun()
            else:
                st.session_state.login_error = login_result["message"]
                params.clear()
                st.rerun()

# Run the app
if __name__ == "__main__":
    main()
