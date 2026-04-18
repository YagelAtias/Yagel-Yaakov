from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import database, models
from ..security.auth import verify_password, get_password_hash, create_access_token, timedelta, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "teacher"
    organization_name: str

@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Get or create organization
    org = db.query(models.Organization).filter(models.Organization.name == user_data.organization_name).first()
    if not org:
        org = models.Organization(name=user_data.organization_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    hashed_pw = get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
        role=user_data.role,
        organization_id=org.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Standard OAuth2 Login endpoint.
    Frontend sends 'username' (which is the email) and 'password'.
    Returns a JWT Bearer token.
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "name": user.full_name,
        "organization_id": user.organization_id
    }
