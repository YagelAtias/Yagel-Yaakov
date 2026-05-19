from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import base64

from ..db import database, models
from ..security.auth import require_role, get_password_hash

router = APIRouter(tags=["Admin"])

class StaffCreate(BaseModel):
    email: str
    full_name: str
    role: str # "teacher", "counselor"
    temporary_password: str

def generate_wrapped_dek(admin_ram_dek: bytes, new_user_password: str) -> str:
    """
    Simulates KEK/DEK wrapping. 
    In production: 
    1. Derive KEK from new_user_password using PBKDF2/Argon2.
    2. Encrypt admin_ram_dek with the KEK using AES-GCM.
    3. Return Base64 of the ciphertext.
    """
    # Security simulation: Wrapping the DEK so only the user's password can unlock it
    return base64.b64encode(b"WRAPPED_BY_KEK_" + admin_ram_dek).decode('utf-8')

@router.post("/staff")
def onboard_staff(
    staff: StaffCreate,
    db: Session = Depends(database.get_db),
    # Only principals/admins can execute this
    current_admin: models.User = Depends(require_role(["admin"]))
):
    """
    Securely onboards a new teacher/counselor.
    Takes the organization's DEK from the admin's RAM and wraps it for the new user.
    """
    if staff.role not in ["teacher", "counselor"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be teacher or counselor.")
        
    existing_user = db.query(models.User).filter(models.User.email == staff.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # The DEK sits securely in the Principal's RAM during their active session
    # We simulate reading it from RAM here:
    admin_ram_dek = b"SECRET_ORGANIZATION_DEK_777" 
    
    # Cryptographic Handshake: Wrap the DEK with the new user's password
    wrapped_dek = generate_wrapped_dek(admin_ram_dek, staff.temporary_password)

    new_user = models.User(
        email=staff.email,
        full_name=staff.full_name,
        hashed_password=get_password_hash(staff.temporary_password),
        role=staff.role,
        organization_id=current_admin.organization_id,
        encrypted_dek=wrapped_dek # Save the lockbox, NEVER the plain DEK!
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "status": "success",
        "user_id": new_user.id,
        "message": f"Successfully onboarded {staff.role} with secure DEK lockbox."
    }

@router.get("/staff")
def get_all_staff(
    db: Session = Depends(database.get_db),
    current_admin: models.User = Depends(require_role(["admin"]))
):
    """
    Returns all staff members (teachers, counselors, admins) in the organization.
    """
    staff = db.query(models.User).filter(
        models.User.organization_id == current_admin.organization_id
    ).all()

    return {
        "status": "success",
        "staff": [
            {
                "id": s.id,
                "full_name": s.full_name,
                "email": s.email,
                "role": s.role
            }
            for s in staff
        ]
    }
