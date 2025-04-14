import os
import requests
import json
import uuid
import streamlit as st

# OAuth credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")

# OAuth redirect URIs
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000")

def get_google_auth_url():
    """Get the Google OAuth authorization URL"""
    state = f"google-{str(uuid.uuid4())}"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "state": state,
        "prompt": "select_account"
    }
    
    # Convert params to URL query string
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    
    # Google OAuth endpoint
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{query_string}"
    return auth_url

def get_facebook_auth_url():
    """Get the Facebook OAuth authorization URL"""
    state = f"facebook-{str(uuid.uuid4())}"
    params = {
        "client_id": FACEBOOK_APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "email",
        "state": state
    }
    
    # Convert params to URL query string
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    
    # Facebook OAuth endpoint
    auth_url = f"https://www.facebook.com/v16.0/dialog/oauth?{query_string}"
    return auth_url

def get_microsoft_auth_url():
    """Get the Microsoft OAuth authorization URL"""
    state = f"microsoft-{str(uuid.uuid4())}"
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "response_mode": "query"
    }
    
    # Convert params to URL query string
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    
    # Microsoft OAuth endpoint
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{query_string}"
    return auth_url

def handle_google_callback(code):
    """Handle Google OAuth callback and get user info"""
    try:
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if "access_token" not in token_json:
            st.error("Failed to get access token from Google")
            return None
        
        # Use access token to get user info
        access_token = token_json["access_token"]
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        
        return user_info
    except Exception as e:
        st.error(f"Error in Google authentication: {str(e)}")
        return None

def handle_facebook_callback(code):
    """Handle Facebook OAuth callback and get user info"""
    try:
        # Exchange code for access token
        token_url = "https://graph.facebook.com/v16.0/oauth/access_token"
        token_params = {
            "client_id": FACEBOOK_APP_ID,
            "client_secret": FACEBOOK_APP_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code
        }
        
        token_response = requests.get(token_url, params=token_params)
        token_json = token_response.json()
        
        if "access_token" not in token_json:
            st.error("Failed to get access token from Facebook")
            return None
        
        # Use access token to get user info
        access_token = token_json["access_token"]
        user_info_url = "https://graph.facebook.com/me"
        params = {
            "fields": "id,name,email",
            "access_token": access_token
        }
        
        user_info_response = requests.get(user_info_url, params=params)
        user_info = user_info_response.json()
        
        return user_info
    except Exception as e:
        st.error(f"Error in Facebook authentication: {str(e)}")
        return None

def handle_microsoft_callback(code):
    """Handle Microsoft OAuth callback and get user info"""
    try:
        # Exchange code for access token
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        token_data = {
            "code": code,
            "client_id": MICROSOFT_CLIENT_ID,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": "openid email profile"
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if "access_token" not in token_json:
            st.error("Failed to get access token from Microsoft")
            return None
        
        # Use access token to get user info
        access_token = token_json["access_token"]
        user_info_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        
        return user_info
    except Exception as e:
        st.error(f"Error in Microsoft authentication: {str(e)}")
        return None
