from app.db.database import SessionLocal
from app.db import models
from app.security.auth import verify_password

db = SessionLocal()
email = "admin@yagel-yaakov.edu"
password = "AdminPassword123!"

user = db.query(models.User).filter(models.User.email == email).first()
if user:
    print("User found!")
    is_valid = verify_password(password, user.hashed_password)
    print("Password valid:", is_valid)
else:
    print("User not found.")
