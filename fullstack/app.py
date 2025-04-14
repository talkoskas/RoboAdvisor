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
    # Custom CSS for styling elements similar to the image
    st.markdown("""
    <style>
    /* Main title styling */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #333 !important;
        margin-bottom: 2rem !important;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        padding: 0.8rem !important;
        font-size: 1rem !important;
        border-radius: 5px !important;
        border: 1px solid #ccc !important;
    }
    
    /* Continue button styling */
    .continue-btn button {
        background-color: #10B981 !important;
        color: white !important;
        padding: 0.8rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border-radius: 5px !important;
        border: none !important;
        width: 100% !important;
    }
    
    /* OR divider */
    .divider {
        display: flex;
        align-items: center;
        margin: 1.5rem 0;
        color: #888;
    }
    
    .divider-line {
        flex-grow: 1;
        height: 1px;
        background-color: #ddd;
    }
    
    .divider-text {
        padding: 0 1rem;
        font-size: 0.9rem;
    }
    
    /* Social login buttons */
    .social-btn {
        margin-bottom: 0.75rem !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
        color: #333 !important;
        border-radius: 5px !important;
        padding: 0.5rem 1rem !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        cursor: pointer !important;
    }
    
    .social-btn img {
        margin-right: 0.75rem;
        height: 24px;
        width: 24px;
    }
    
    /* Sign Up link */
    .signup-link {
        text-align: center;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .signup-link a {
        color: #10B981 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    /* Make container narrower */
    .login-container {
        max-width: 400px !important;
        margin: 0 auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display login error if any
    if st.session_state.login_error:
        st.error(st.session_state.login_error)
        st.session_state.login_error = None
    
    # Create the centered container for login
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Title
        st.title("Welcome back")
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            # Email input
            email = st.text_input("Email address*", key="login_email")
            
            # Password input
            password = st.text_input("Password", type="password", key="login_password")
            
            # Remember me checkbox (hidden by default, can be enabled)
            # Use CSS to hide the checkbox
            st.markdown('<style>.hide-checkbox { display: none; }</style>', unsafe_allow_html=True)
            with st.container():
                st.markdown('<div class="hide-checkbox">', unsafe_allow_html=True)
                remember_me = st.checkbox("Remember me", key="remember_me", value=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Submit button styled as green "Continue" button
            st.markdown('<div class="continue-btn">', unsafe_allow_html=True)
            submit = st.form_submit_button("Continue")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    # Try to authenticate with email as username
                    login_result = auth_manager.authenticate_user(email, password)
                    if login_result["success"]:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.username = email
                        
                        # Set auth cookie if remember me is checked
                        if remember_me:
                            expiry = datetime.now() + timedelta(days=30)
                            token = auth_manager.generate_auth_token(email)
                            cookie_manager.set("auth_token", token, expires_at=expiry)
                        
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.error(login_result["message"])
        
        # Sign Up link
        st.markdown('<div class="signup-link">Don\'t have an account? <a href="#" onclick="document.querySelector(\'[data-testid=\'stForm\'] button[kind=secondaryFormSubmit]\').click();">Sign Up</a></div>', unsafe_allow_html=True)
        
        # Register button (hidden, triggered by the Sign Up link)
        with st.container():
            # Use container with custom CSS to hide the button
            st.markdown('<style>.hide-button {display: none;}</style>', unsafe_allow_html=True)
            st.markdown('<div class="hide-button">', unsafe_allow_html=True)
            if st.button("Register", key="register_btn", type="secondary"):
                st.session_state.registration = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Forgot password link (hidden, can be enabled)
        with st.container():
            st.markdown('<div class="hide-button">', unsafe_allow_html=True)
            if st.button("Forgot password?", key="forgot_pwd", type="secondary", help="Reset your password"):
                st.session_state.reset_password = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # OR divider
        st.markdown('<div class="divider"><div class="divider-line"></div><div class="divider-text">OR</div><div class="divider-line"></div></div>', unsafe_allow_html=True)
        
        # Social login buttons
        # Google login
        google_btn_html = """
        <button class="social-btn" id="google-login">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" alt="Google">
            Continue with Google
        </button>
        <script>
            document.getElementById('google-login').addEventListener('click', function() {
                document.querySelector('[data-testid="stButton"] button[kind="secondary"]').click();
            });
        </script>
        """
        st.markdown(google_btn_html, unsafe_allow_html=True)
        
        # Hidden button for Google login
        with st.container():
            st.markdown('<div class="hide-button">', unsafe_allow_html=True)
            if st.button("Google Login", key="google_login", type="secondary"):
                auth_url = social_auth.get_google_auth_url()
                st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Microsoft login
        ms_btn_html = """
        <button class="social-btn" id="ms-login">
            <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" alt="Microsoft">
            Continue with Microsoft Account
        </button>
        <script>
            document.getElementById('ms-login').addEventListener('click', function() {
                document.querySelector('[data-testid="stButton"] button[kind="secondary"]:nth-of-type(2)').click();
            });
        </script>
        """
        st.markdown(ms_btn_html, unsafe_allow_html=True)
        
        # Hidden button for Microsoft login
        with st.container():
            st.markdown('<div class="hide-button">', unsafe_allow_html=True)
            if st.button("Microsoft Login", key="ms_login", type="secondary"):
                auth_url = social_auth.get_microsoft_auth_url()
                st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{auth_url}\'">', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close login-container

def display_registration():
    # Reuse the same CSS from login page
    st.markdown("""
    <style>
    /* Main title styling */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #333 !important;
        margin-bottom: 2rem !important;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        padding: 0.8rem !important;
        font-size: 1rem !important;
        border-radius: 5px !important;
        border: 1px solid #ccc !important;
    }
    
    /* Continue button styling */
    .continue-btn button {
        background-color: #10B981 !important;
        color: white !important;
        padding: 0.8rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border-radius: 5px !important;
        border: none !important;
        width: 100% !important;
    }
    
    /* Login link */
    .login-link {
        text-align: center;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .login-link a {
        color: #10B981 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    /* Make container narrower */
    .registration-container {
        max-width: 400px !important;
        margin: 0 auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the centered container for registration
    with st.container():
        st.markdown('<div class="registration-container">', unsafe_allow_html=True)
        
        # Title
        st.title("Create account")
        
        # Registration form
        with st.form("registration_form", clear_on_submit=False):
            # Username input
            username = st.text_input("Username*", key="reg_username")
            
            # Email input
            email = st.text_input("Email address*", key="reg_email")
            
            # Password input
            password = st.text_input("Password*", type="password", key="reg_password")
            
            # Confirm password
            confirm_password = st.text_input("Confirm Password*", type="password", key="reg_confirm_password")
            
            # Submit button styled as green "Create account" button
            st.markdown('<div class="continue-btn">', unsafe_allow_html=True)
            submit = st.form_submit_button("Create account")
            st.markdown('</div>', unsafe_allow_html=True)
            
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
        
        # Login link
        st.markdown('<div class="login-link">Already have an account? <a href="#" onclick="document.querySelector(\'[data-testid=\'stForm\'] button[kind=secondaryFormSubmit]\').click();">Sign In</a></div>', unsafe_allow_html=True)
        
        # Back button (hidden, triggered by the Sign In link)
        with st.container():
            st.markdown('<div class="hide-button">', unsafe_allow_html=True)
            if st.button("Back to Login", key="back_to_login", type="secondary"):
                st.session_state.registration = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)  # Close registration-container

def display_password_reset():
    # Reuse the same CSS from login page
    st.markdown("""
    <style>
    /* Main title styling */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        color: #333 !important;
        margin-bottom: 2rem !important;
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        padding: 0.8rem !important;
        font-size: 1rem !important;
        border-radius: 5px !important;
        border: 1px solid #ccc !important;
    }
    
    /* Continue button styling */
    .continue-btn button {
        background-color: #10B981 !important;
        color: white !important;
        padding: 0.8rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border-radius: 5px !important;
        border: none !important;
        width: 100% !important;
    }
    
    /* Login link */
    .login-link {
        text-align: center;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .login-link a {
        color: #10B981 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    /* Make container narrower */
    .reset-container {
        max-width: 400px !important;
        margin: 0 auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # First step: Request email
    if "reset_email_sent" not in st.session_state:
        st.session_state.reset_email_sent = False
        
    # Create the centered container for password reset
    with st.container():
        st.markdown('<div class="reset-container">', unsafe_allow_html=True)
        
        if not st.session_state.reset_email_sent:
            # Title
            st.title("Reset password")
            
            # Password reset request form
            with st.form("reset_request_form", clear_on_submit=False):
                # Email input
                email = st.text_input("Email address*", key="reset_email")
                
                # Submit button styled as green "Send reset link" button
                st.markdown('<div class="continue-btn">', unsafe_allow_html=True)
                submit = st.form_submit_button("Send reset link")
                st.markdown('</div>', unsafe_allow_html=True)
                
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
            
            # Login link
            st.markdown('<div class="login-link">Remember your password? <a href="#" onclick="document.querySelector(\'[data-testid=\'stForm\'] button[kind=secondaryFormSubmit]\').click();">Back to Sign In</a></div>', unsafe_allow_html=True)
            
            # Back button (hidden, triggered by the Sign In link)
            with st.container():
                st.markdown('<div class="hide-button">', unsafe_allow_html=True)
                if st.button("Back to Login", key="back_to_login", type="secondary"):
                    st.session_state.reset_password = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
        # Second step: Enter reset code and new password
        else:
            # Title
            st.title("Create new password")
            
            # Reset password form
            with st.form("reset_password_form", clear_on_submit=False):
                # Reset code input
                reset_code = st.text_input("Reset code from email*", key="reset_code")
                
                # New password input
                new_password = st.text_input("New Password*", type="password", key="new_password")
                
                # Confirm password
                confirm_password = st.text_input("Confirm New Password*", type="password", key="confirm_new_password")
                
                # Submit button styled as green "Reset Password" button
                st.markdown('<div class="continue-btn">', unsafe_allow_html=True)
                submit = st.form_submit_button("Reset Password")
                st.markdown('</div>', unsafe_allow_html=True)
                
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
            
            # Login link
            st.markdown('<div class="login-link">Remember your password? <a href="#" onclick="document.querySelector(\'[data-testid=\'stForm\'] button[kind=secondaryFormSubmit]\').click();">Back to Sign In</a></div>', unsafe_allow_html=True)
            
            # Back button (hidden, triggered by the Sign In link)
            with st.container():
                st.markdown('<div class="hide-button">', unsafe_allow_html=True)
                if st.button("Back to Login", key="back_to_login2", type="secondary"):
                    st.session_state.reset_password = False
                    st.session_state.reset_email_sent = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)  # Close reset-container

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
