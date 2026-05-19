import sys
import os
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.database import SessionLocal
from app.db import models

def seed_data():
    db = SessionLocal()
    try:
        org = db.query(models.Organization).first()
        if not org:
            print("No organization found. Run setup_admin.py first!")
            return

        # Find Admin (Yagel Atias) to assign as teacher
        admin_user = db.query(models.User).filter(models.User.email == "admin@yagel-yaakov.edu").first()

        # 1. Create Classrooms
        print("Creating Classrooms...")
        class1 = models.Classroom(name="כיתה ח' 1", organization_id=org.id, teacher_id=admin_user.id)
        db.add(class1)
        db.commit()

        # 2. Create Subject Courses (Taught by Admin)
        print("Creating Subject Courses...")
        math_course = models.Course(name="מתמטיקה 4 יח\"ל", organization_id=org.id, teacher_id=admin_user.id)
        gemara_course = models.Course(name="גמרא מורחב", organization_id=org.id, teacher_id=admin_user.id)
        db.add_all([math_course, gemara_course])
        db.commit()

        # 3. Create Only One Student (Daniel Levi) and Enroll him
        print("Creating Student...")
        daniel = models.Student(first_name="דניאל", last_name="לוי", grade_level="ח", organization_id=org.id, classroom_id=class1.id)
        
        # Enroll Daniel in courses
        daniel.courses.append(math_course)
        daniel.courses.append(gemara_course)
        
        db.add(daniel)
        db.commit()

        # 4. Create Exams (assigned to courses)
        print("Creating Exams...")
        db.add(models.Exam(course_id=math_course.id, subject="מבחן במתמטיקה", date_scheduled=datetime.utcnow() + timedelta(days=2)))
        db.add(models.Exam(course_id=gemara_course.id, subject="מבחן בגמרא", date_scheduled=datetime.utcnow() + timedelta(days=5)))
        
        # 5. Clear Old Leaves and Conversations
        print("Skipping Leave Requests and Conversations (Starting Clean)")

        db.commit()
        print("✅ Successfully seeded the database with live data!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
