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
    Unified OAuth2 Login endpoint.
    Frontend sends 'username' (which is the email) and 'password'.
    It checks if the credentials belong to a Teacher or a Student, and returns the appropriate JWT.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 1. Try to log in as a Teacher/Staff Member
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user and verify_password(form_data.password, user.hashed_password):
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role, "user_type": "staff"}, 
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "role": user.role, 
            "name": user.full_name,
            "organization_id": user.organization_id,
            "permissions": getattr(user, "permissions", []) or []
        }
        
    # 2. Try to log in as a Student
    student = db.query(models.Student).filter(models.Student.email == form_data.username).first()
    if student and student.hashed_password and verify_password(form_data.password, student.hashed_password):
        access_token = create_access_token(
            data={"sub": student.email, "role": "student", "user_type": "student"}, 
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "role": "student", 
            "name": f"{student.first_name} {student.last_name}",
            "organization_id": student.organization_id
        }

    # 3. Fail
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
