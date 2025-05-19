import bcrypt
import os
import jwt
from datetime import datetime, timedelta
import uuid
import database_mongo

# Secret key for JWT tokens
JWT_SECRET = os.getenv("JWT_SECRET", "default_secret_key_change_in_production")

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against a bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    user = database_mongo.get_user_by_username(username)
    
    if not user:
        return {"success": False, "message": "Invalid username or password"}
    
    if not verify_password(password, user["password"]):
        return {"success": False, "message": "Invalid username or password"}
    
    return {"success": True, "message": "Authentication successful", "user": user}

def generate_auth_token(username):
    """Generate a JWT token for authenticated users"""
    expiration = datetime.utcnow() + timedelta(days=30)
    payload = {
        "sub": username,
        "exp": expiration,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def validate_auth_token(token):
    """Validate a JWT authentication token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["sub"]
        user = database_mongo.get_user_by_username(username)
        return user
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def generate_password_reset_token():
    """Generate a random token for password reset"""
    return str(uuid.uuid4())
