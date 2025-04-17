import os
import json
import time
from datetime import datetime

# Path to the users.json file
USERS_FILE = "data/users.json"

def load_users():
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {"users": {}}
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_users(data):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_by_username(username):
    """Get a user by username"""
    data = load_users()
    return data["users"].get(username)

def get_user_by_email(email):
    """Get a user by email"""
    data = load_users()
    for user in data["users"].values():
        if user["email"] == email:
            return user
    return None

def create_user(username, email, password_hash, provider="local"):
    """Create a new user"""
    data = load_users()
    
    # Check if username already exists
    if username in data["users"]:
        return {"success": False, "message": "Username already exists"}
    
    # Check if email already exists
    for user in data["users"].values():
        if user["email"] == email:
            return {"success": False, "message": "Email already registered"}
    
    # Create new user
    data["users"][username] = {
        "username": username,
        "email": email,
        "password": password_hash,
        "provider": provider,
        "created_at": datetime.utcnow().isoformat()
    }
    
    save_users(data)
    return {"success": True, "message": "User created successfully"}

def update_user_password(username, new_password_hash):
    """Update a user's password"""
    data = load_users()
    
    if username not in data["users"]:
        return {"success": False, "message": "User not found"}
    
    data["users"][username]["password"] = new_password_hash
    save_users(data)
    return {"success": True, "message": "Password updated successfully"}

def store_reset_token(email, token):
    """Store a password reset token"""
    data = load_users()
    
    # Add expiration time (1 hour from now)
    expiration = time.time() + 3600
    
    # Store the token
    if "reset_tokens" not in data:
        data["reset_tokens"] = {}
    
    data["reset_tokens"][email] = {
        "token": token,
        "expiration": expiration
    }
    
    save_users(data)
    return {"success": True}

def validate_reset_token(token):
    """Validate a password reset token"""
    data = load_users()
    
    if "reset_tokens" not in data:
        return {"success": False, "message": "Invalid reset code"}
    
    # Find the token
    for email, token_data in data["reset_tokens"].items():
        if token_data["token"] == token:
            # Check if token has expired
            if token_data["expiration"] < time.time():
                # Remove expired token
                del data["reset_tokens"][email]
                save_users(data)
                return {"success": False, "message": "Reset code has expired"}
            
            return {"success": True, "email": email}
    
    return {"success": False, "message": "Invalid reset code"}

def invalidate_reset_token(token):
    """Invalidate a password reset token after use"""
    data = load_users()
    
    if "reset_tokens" not in data:
        return {"success": True}
    
    # Find and remove the token
    for email, token_data in data["reset_tokens"].items():
        if token_data["token"] == token:
            del data["reset_tokens"][email]
            save_users(data)
            break
    
    return {"success": True}
