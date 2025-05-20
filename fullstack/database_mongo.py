from datetime import datetime, timedelta
import time
from bson.objectid import ObjectId
from db import users_col, reset_tokens_col, users_chat_col

def get_user_by_username(username):
    return users_col.find_one({"username": username})

def get_user_by_email(email):
    return users_col.find_one({"email": email})

def create_user(username, email, password_hash, provider="local"):
    print(f"Checking if username {username} exists...")
    if users_col.find_one({"username": username}):
        print(f"Username {username} already exists")
        return {"success": False, "message": "Username already exists"}

    print(f"Checking if email {email} exists...")
    if users_col.find_one({"email": email}):
        print(f"Email {email} already registered")
        return {"success": False, "message": "Email already registered"}

    user_data = {
        "username": username,
        "email": email,
        "password": password_hash,
        "provider": provider,
        "created_at": datetime.utcnow().isoformat()
    }

    print("Attempting to insert user into database...")
    try:
        result = users_col.insert_one(user_data)
        print(f"Insert successful, document ID: {result.inserted_id}")
        return {"success": True, "message": "User created successfully"}
    except Exception as e:
        print(f"Error inserting user: {str(e)}")
        return {"success": False, "message": f"Database error: {str(e)}"}

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
def create_chat(username, chat_history, ts=None):
    """
    Create a new chat session for the given user.
    Returns the inserted document’s _id.
    """
    doc = {
        "username": username,
        "chat_history": chat_history,
        "last_updated": ts or datetime.utcnow()
    }
    result = users_chat_col.insert_one(doc)
    return result.inserted_id


def get_chats_by_user(username):
    """
    Fetch all chat sessions’ metadata for a user (no chat_history).
    Returns a list of docs with _id and last_updated.
    """
    cursor = users_chat_col.find(
        {"username": username},
        {"chat_history": 0}
    ).sort("last_updated", -1)
    return list(cursor)


def update_chat(chat_id, chat_history, ts=None):
    """
    Overwrite an existing session’s history and timestamp by its _id.
    Returns number of modified docs (0 or 1).
    """
    result = users_chat_col.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {
            "chat_history": chat_history,
            "last_updated": ts or datetime.utcnow()
        }}
    )
    return result.modified_count
def get_chat_by_id(chat_id):
    """
    Retrieve a single chat session document (with its full history) by _id.
    """
    return users_chat_col.find_one({"_id": ObjectId(chat_id)})

