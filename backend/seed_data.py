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

        # 1. Create Classrooms
        print("Creating Classrooms...")
        class1 = models.Classroom(name="כיתה ח' 1", organization_id=org.id)
        class2 = models.Classroom(name="כיתה ט' 3", organization_id=org.id)
        db.add_all([class1, class2])
        db.commit()

        # 2. Create Students
        print("Creating Students...")
        students = [
            models.Student(first_name="דניאל", last_name="לוי", grade_level="ח", organization_id=org.id, classroom_id=class1.id),
            models.Student(first_name="יוסף", last_name="כהן", grade_level="ח", organization_id=org.id, classroom_id=class1.id),
            models.Student(first_name="נועם", last_name="אברהם", grade_level="ט", organization_id=org.id, classroom_id=class2.id),
            models.Student(first_name="אריאל", last_name="שטרן", grade_level="ט", organization_id=org.id, classroom_id=class2.id)
        ]
        db.add_all(students)
        db.commit()

        # 3. Create Exams
        print("Creating Exams...")
        db.add(models.Exam(classroom_id=class1.id, subject="מבחן בגמרא", date_scheduled=datetime.utcnow() + timedelta(days=2)))
        db.add(models.Exam(classroom_id=class2.id, subject="מבחן בפיזיקה", date_scheduled=datetime.utcnow() + timedelta(days=5)))
        
        # 4. Create Leaves
        print("Creating Dorm Leaves...")
        db.add(models.DormLeave(student_id=students[0].id, leave_type="שבת הביתה", destination="ירושלים", departure_date=datetime.utcnow() + timedelta(days=3), return_date=datetime.utcnow() + timedelta(days=5), status="pending"))
        db.add(models.DormLeave(student_id=students[2].id, leave_type="אירוע משפחתי", destination="תל אביב", departure_date=datetime.utcnow() + timedelta(days=1), return_date=datetime.utcnow() + timedelta(days=1), status="pending"))

        # 5. Create Conversations (Distress Logs)
        print("Creating Conversation History...")
        for student in students:
            for i in range(3):
                date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                db.add(models.DistressLog(
                    student_id=student.id,
                    timestamp=date,
                    overall_score=random.uniform(0.1, 0.9),
                    has_critical_alert=(random.random() > 0.8),
                    encrypted_raw_text="ENCRYPTED_DUMMY_DATA"
                ))

        db.commit()
        print("✅ Successfully seeded the database with live data!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
