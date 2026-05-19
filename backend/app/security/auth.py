import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..db import models, database
from ..core.settings import get_settings

# Security configuration via centralized settings
settings = get_settings()
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# The URL where the frontend will send the username/password to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """Dependency that extracts the JWT token, validates it, and returns the User or Student object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type", "staff") # Default to staff for older tokens
        
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    if user_type == "student":
        user = db.query(models.Student).filter(models.Student.email == email).first()
        if user:
            # Attach a temporary role string so the require_role gatekeeper works seamlessly
            user.role = "student" 
    else:
        user = db.query(models.User).filter(models.User.email == email).first()
        
    if user is None:
        raise credentials_exception
    return user

def require_role(required_roles: list[str]):
    """
    Dependency generator for Role-Based Access Control (RBAC).
    Checks if the currently authenticated user's role is in the required_roles list.
    """
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    """
    Dependency generator for Permission-Based Access Control.
    Checks if the authenticated user's permissions JSON contains the required permission.
    """
    def permission_checker(current_user: models.User = Depends(get_current_user)):
        if getattr(current_user, "role", None) == "student":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students lack permissions")
        
        perms = getattr(current_user, "permissions", []) or []
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required privilege: {permission}"
            )
        return current_user
    return permission_checker
