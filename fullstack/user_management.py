import database_mongo as database
import auth_manager
import utils
import os
import streamlit as st

def register_user(username, email, password):
    """Register a new user"""
    print(f"Attempting to register user: {username} with email: {email}")
    
    # Validate inputs
    if not username or not email or not password:
        print("Registration failed: Missing required fields")
        return {"success": False, "message": "All fields are required"}
    
    if not utils.is_valid_email(email):
        print("Registration failed: Invalid email format")
        return {"success": False, "message": "Invalid email format"}
    
    if len(password) < 8:
        print("Registration failed: Password too short")
        return {"success": False, "message": "Password must be at least 8 characters long"}
    
    # Check if username is already taken
    existing_user = database.get_user_by_username(username)
    if existing_user:
        print(f"Registration failed: Username {username} already exists")
        return {"success": False, "message": "Username already exists"}
    
    # Check if email is already registered
    existing_email = database.get_user_by_email(email)
    if existing_email:
        print(f"Registration failed: Email {email} already registered")
        return {"success": False, "message": "Email is already registered"}
    
    # Hash the password
    password_hash = auth_manager.hash_password(password)
    
    # Create the user
    print("Attempting to create user in database...")
    result = database.create_user(username, email, password_hash)
    print(f"Database creation result: {result}")
    return result

def request_password_reset(email):
    """Request a password reset for a user"""
    # Check if email exists
    user = database.get_user_by_email(email)
    if not user:
        # For security reasons, don't reveal if email exists or not
        return {"success": True, "message": "If your email is registered, you will receive reset instructions"}
    
    # Generate a reset token
    reset_token = auth_manager.generate_password_reset_token()
    
    # Store the token
    database.store_reset_token(email, reset_token)
    
    # In a real application, send an email with the reset token
    # Here we'll just return it for testing purposes
    # utils.send_reset_email(email, reset_token)
    
    # For demo purposes, show the reset token in the console
    # In production, this would be sent via email and not displayed
    print(f"Password reset token for {email}: {reset_token}")
    
    return {"success": True, "message": "Reset instructions sent to your email"}

def reset_password(reset_token, new_password):
    """Reset a user's password using a reset token"""
    # Validate the token
    token_validation = database.validate_reset_token(reset_token)
    
    if not token_validation["success"]:
        return token_validation
    
    # Get the user by email
    email = token_validation["email"]
    user = database.get_user_by_email(email)
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    # Hash the new password
    new_password_hash = auth_manager.hash_password(new_password)
    
    # Update the user's password
    result = database.update_user_password(user["username"], new_password_hash)
    
    # Invalidate the reset token
    database.invalidate_reset_token(reset_token)
    
    return result

def social_login(email, provider):
    """Handle login or registration via social providers"""
    # Check if user exists
    user = database.get_user_by_email(email)
    
    if user:
        # User exists, check if they registered with this provider
        if user["provider"] == provider or user["provider"] == "local":
            # Allow login
            return {"success": True, "message": "Login successful", "username": user["username"]}
        else:
            # User registered with a different provider
            return {"success": False, "message": f"This email is already registered using {user['provider']}"}
    else:
        # User doesn't exist, create a new account
        # Generate a username from email
        base_username = email.split('@')[0]
        username = base_username
        
        # Check if username exists, append numbers if needed
        count = 1
        while database.get_user_by_username(username):
            username = f"{base_username}{count}"
            count += 1
        
        # Create random password for the account (it won't be used for login)
        random_password = utils.generate_random_password()
        password_hash = auth_manager.hash_password(random_password)
        
        # Create the user
        result = database.create_user(username, email, password_hash, provider=provider)
        
        if result["success"]:
            return {"success": True, "message": "Account created successfully", "username": username}
        else:
            return result
