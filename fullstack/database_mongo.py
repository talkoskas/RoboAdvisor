from datetime import datetime, timedelta
import time
from bson.objectid import ObjectId
from db import users_col, reset_tokens_col

def get_user_by_username(username):
    return users_col.find_one({"username": username})

def get_user_by_email(email):
    return users_col.find_one({"email": email})

def create_user(username, email, password_hash, provider="local"):
    if users_col.find_one({"username": username}):
        return {"success": False, "message": "Username already exists"}

    if users_col.find_one({"email": email}):
        return {"success": False, "message": "Email already registered"}

    user_data = {
        "username": username,
        "email": email,
        "password": password_hash,
        "provider": provider,
        "created_at": datetime.utcnow().isoformat()
    }

    users_col.insert_one(user_data)
    return {"success": True, "message": "User created successfully"}

def update_user_password(username, new_password_hash):
    result = users_col.update_one(
        {"username": username},
        {"$set": {"password": new_password_hash}}
    )

    if result.matched_count == 0:
        return {"success": False, "message": "User not found"}
    
    return {"success": True, "message": "Password updated successfully"}

def store_reset_token(email, token):
    expiration = time.time() + 3600  # 1 hour from now
    reset_tokens_col.update_one(
        {"email": email},
        {"$set": {"token": token, "expiration": expiration}},
        upsert=True
    )
    return {"success": True}

def validate_reset_token(token):
    token_data = reset_tokens_col.find_one({"token": token})
    if not token_data:
        return {"success": False, "message": "Invalid reset code"}

    if token_data["expiration"] < time.time():
        reset_tokens_col.delete_one({"_id": token_data["_id"]})
        return {"success": False, "message": "Reset code has expired"}

    return {"success": True, "email": token_data["email"]}

def invalidate_reset_token(token):
    reset_tokens_col.delete_one({"token": token})
    return {"success": True}
