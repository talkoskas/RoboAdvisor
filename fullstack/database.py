import os
import time
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json

# Set up database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define the models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed password
    provider = Column(String(20), default='local')  # 'local', 'google', 'facebook'
    created_at = Column(DateTime, default=datetime.utcnow)
    
class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), nullable=False)
    expiration = Column(Float, nullable=False)  # Unix timestamp
    
# Create tables if they don't exist
Base.metadata.create_all(engine)

def get_user_by_username(username):
    """Get a user by username"""
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            return {
                "username": user.username,
                "email": user.email,
                "password": user.password,
                "provider": user.provider,
                "created_at": user.created_at.isoformat()
            }
        return None
    finally:
        session.close()

def get_user_by_email(email):
    """Get a user by email"""
    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            return {
                "username": user.username,
                "email": user.email,
                "password": user.password,
                "provider": user.provider,
                "created_at": user.created_at.isoformat()
            }
        return None
    finally:
        session.close()

def create_user(username, email, password_hash, provider="local"):
    """Create a new user"""
    session = Session()
    try:
        # Check if username already exists
        existing_username = session.query(User).filter_by(username=username).first()
        if existing_username:
            return {"success": False, "message": "Username already exists"}
        
        # Check if email already exists
        existing_email = session.query(User).filter_by(email=email).first()
        if existing_email:
            return {"success": False, "message": "Email already registered"}
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=password_hash,
            provider=provider
        )
        
        session.add(new_user)
        session.commit()
        return {"success": True, "message": "User created successfully"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error creating user: {str(e)}"}
    finally:
        session.close()

def update_user_password(username, new_password_hash):
    """Update a user's password"""
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            return {"success": False, "message": "User not found"}
        
        user.password = new_password_hash
        session.commit()
        return {"success": True, "message": "Password updated successfully"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error updating password: {str(e)}"}
    finally:
        session.close()

def store_reset_token(email, token):
    """Store a password reset token"""
    session = Session()
    try:
        # Remove any existing tokens for this email
        session.query(PasswordResetToken).filter_by(email=email).delete()
        
        # Add expiration time (1 hour from now)
        expiration = time.time() + 3600
        
        # Create new token
        new_token = PasswordResetToken(
            token=token,
            email=email,
            expiration=expiration
        )
        
        session.add(new_token)
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error storing reset token: {str(e)}"}
    finally:
        session.close()

def validate_reset_token(token):
    """Validate a password reset token"""
    session = Session()
    try:
        token_record = session.query(PasswordResetToken).filter_by(token=token).first()
        
        if not token_record:
            return {"success": False, "message": "Invalid reset code"}
        
        # Check if token has expired
        if token_record.expiration < time.time():
            # Remove expired token
            session.delete(token_record)
            session.commit()
            return {"success": False, "message": "Reset code has expired"}
        
        return {"success": True, "email": token_record.email}
    except Exception as e:
        return {"success": False, "message": f"Error validating token: {str(e)}"}
    finally:
        session.close()

def invalidate_reset_token(token):
    """Invalidate a password reset token after use"""
    session = Session()
    try:
        token_record = session.query(PasswordResetToken).filter_by(token=token).first()
        
        if token_record:
            session.delete(token_record)
            session.commit()
        
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error invalidating token: {str(e)}"}
    finally:
        session.close()
