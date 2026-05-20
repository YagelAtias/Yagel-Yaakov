import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db import models
from app.security.auth import get_password_hash


DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "DemoPassword123!")


def get_or_create(db, model, defaults=None, **filters):
    row = db.query(model).filter_by(**filters).first()
    if row:
        return row

    row = model(**filters, **(defaults or {}))
    db.add(row)
    db.flush()
    return row


def ensure_user(db, org, email, full_name, role, permissions):
    user = get_or_create(
        db,
        models.User,
        email=email,
        defaults={
            "full_name": full_name,
            "hashed_password": get_password_hash(DEMO_PASSWORD),
            "role": role,
            "organization_id": org.id,
            "permissions": permissions,
        },
    )
    user.full_name = full_name
    user.hashed_password = get_password_hash(DEMO_PASSWORD)
    user.role = role
    user.organization_id = org.id
    user.permissions = permissions
    return user


def ensure_student(db, org, classroom, email, first_name, last_name, grade_level):
    student = get_or_create(
        db,
        models.Student,
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "hashed_password": get_password_hash(DEMO_PASSWORD),
            "grade_level": grade_level,
            "organization_id": org.id,
            "classroom_id": classroom.id,
        },
    )
    student.first_name = first_name
    student.last_name = last_name
    student.hashed_password = get_password_hash(DEMO_PASSWORD)
    student.grade_level = grade_level
    student.organization_id = org.id
    student.classroom_id = classroom.id
    return student


def add_student_to_course(student, course):
    if course not in student.courses:
        student.courses.append(course)


def seed_data():
    db = SessionLocal()
    now = datetime.utcnow()

    try:
        org = get_or_create(db, models.Organization, name="Yagel-Yaakov Yeshiva")

        ensure_user(
            db,
            org,
            "admin@yagel-yaakov.edu",
            "Yagel Atias",
            "admin",
            ["can_manage_leaves", "can_take_attendance"],
        )
        teacher = ensure_user(
            db,
            org,
            "teacher@yagel-yaakov.edu",
            "Rav Amit Cohen",
            "teacher",
            ["can_take_attendance", "can_manage_leaves"],
        )
        ensure_user(
            db,
            org,
            "counselor@yagel-yaakov.edu",
            "Miriam Ben-David",
            "counselor",
            ["can_manage_leaves"],
        )

        classroom = get_or_create(
            db,
            models.Classroom,
            name="Kitah Het 1",
            organization_id=org.id,
            defaults={"teacher_id": teacher.id},
        )
        classroom.teacher_id = teacher.id

        math = get_or_create(
            db,
            models.Course,
            name="Mathematics 4 Units",
            organization_id=org.id,
            defaults={"teacher_id": teacher.id},
        )
        gemara = get_or_create(
            db,
            models.Course,
            name="Gemara Advanced",
            organization_id=org.id,
            defaults={"teacher_id": teacher.id},
        )
        math.teacher_id = teacher.id
        gemara.teacher_id = teacher.id

        student = ensure_student(
            db,
            org,
            classroom,
            "student@yagel-yaakov.edu",
            "Daniel",
            "Levi",
            "Het",
        )

        classmates = [
            ("noam@yagel-yaakov.edu", "Noam", "Cohen"),
            ("eitan@yagel-yaakov.edu", "Eitan", "Mizrahi"),
            ("uri@yagel-yaakov.edu", "Uri", "Ben-Ari"),
            ("yonatan@yagel-yaakov.edu", "Yonatan", "Shalev"),
        ]
        students = [student]
        for email, first_name, last_name in classmates:
            students.append(ensure_student(db, org, classroom, email, first_name, last_name, "Het"))

        for s in students:
            add_student_to_course(s, math)
            add_student_to_course(s, gemara)

        db.flush()

        # Keep the live DistressEngine and leave-request demos clean.
        student_ids = [s.id for s in students]
        db.query(models.DormLeave).filter(models.DormLeave.student_id.in_(student_ids)).delete(synchronize_session=False)
        db.query(models.DistressLog).filter(models.DistressLog.student_id.in_(student_ids)).delete(synchronize_session=False)

        for course, subject, days in [
            (math, "Algebra checkpoint", 3),
            (gemara, "Gemara bekiut quiz", 6),
        ]:
            exam = db.query(models.Exam).filter(
                models.Exam.course_id == course.id,
                models.Exam.subject == subject,
            ).first()
            if not exam:
                db.add(models.Exam(
                    course_id=course.id,
                    subject=subject,
                    date_scheduled=now + timedelta(days=days),
                    description="Demo exam for the teacher dashboard",
                ))

        session = db.query(models.AttendanceSession).filter(
            models.AttendanceSession.course_id == math.id,
            models.AttendanceSession.period == 1,
        ).first()
        if not session:
            session = models.AttendanceSession(
                course_id=math.id,
                date=now,
                period=1,
                created_by=teacher.id,
            )
            db.add(session)
            db.flush()

        existing_records = {
            r.student_id
            for r in db.query(models.AttendanceRecord).filter(models.AttendanceRecord.session_id == session.id).all()
        }
        for s in students:
            if s.id not in existing_records:
                db.add(models.AttendanceRecord(
                    session_id=session.id,
                    student_id=s.id,
                    status="present",
                    marked_by=teacher.id,
                ))

        db.commit()
        print("Demo seed complete.")
        print("Admin: admin@yagel-yaakov.edu")
        print("Teacher: teacher@yagel-yaakov.edu")
        print("Student: student@yagel-yaakov.edu")
        print(f"Demo password: {DEMO_PASSWORD}")
        print("Leave requests and conversation history were cleared for demo students.")

    except Exception as e:
        print(f"Seed error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
