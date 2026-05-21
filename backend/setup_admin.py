import sys
import os

# Add the parent directory to the path so we can import 'app' modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.db import models
from app.security.auth import get_password_hash
from app.api.admin import generate_wrapped_dek

def setup_admin():
    print("Initializing Database...")
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Create the Organization
        org_name = "ישיבת יגל-יעקב"
        org = db.query(models.Organization).filter(models.Organization.name == org_name).first()
        if not org:
            org = models.Organization(name=org_name)
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created Organization: {org.name}")
        else:
            print(f"Organization '{org.name}' already exists.")

        # 2. Setup Admin User
        admin_email = "admin@yagel-yaakov.edu"
        admin_password = os.environ.get("ADMIN_PASSWORD", "AdminPassword123!")
        raw_master_dek = b"MASTER_SCHOOL_DEK_9999_SUPER_SECRET"
        wrapped_dek = generate_wrapped_dek(raw_master_dek, admin_password)
        
        user = db.query(models.User).filter(models.User.email == admin_email).first()
        if not user:
            print(f"Creating Admin User: {admin_email}...")
            
            new_admin = models.User(
                email=admin_email,
                full_name="יגל אטיאס",
                hashed_password=get_password_hash(admin_password),
                role="admin",
                organization_id=org.id,
                encrypted_dek=wrapped_dek,
                permissions=["can_manage_leaves", "can_take_attendance"]
            )
            
            db.add(new_admin)
            db.commit()
            print("\nSuccessfully created Admin User with KEK/DEK Lockbox!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}\n")
        else:
            print(f"Admin User '{admin_email}' already exists. Ensuring demo credentials and role...")
            user.hashed_password = get_password_hash(admin_password)
            user.role = "admin"
            user.organization_id = org.id
            user.encrypted_dek = wrapped_dek
            user.permissions = ["can_manage_leaves", "can_take_attendance"]
            db.commit()
            print("Admin User updated for demo login.")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_admin()
