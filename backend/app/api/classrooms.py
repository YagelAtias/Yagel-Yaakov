from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from ..db import database, models
from ..security.auth import require_role, get_password_hash

router = APIRouter()

# --- Pydantic Schemas ---
class ClassroomCreate(BaseModel):
    name: str # e.g. "Kitah Aleph 1"

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    grade_level: str
    classroom_id: int

class ExamCreate(BaseModel):
    subject: str
    date_scheduled: datetime
    description: Optional[str] = None

class ScheduleSlotCreate(BaseModel):
    day_of_week: int
    period: int
    subject: str
    teacher_name: Optional[str] = None

class CourseCreate(BaseModel):
    name: str  # e.g. "Math 4 Units - Group B"
    teacher_id: int  # Admin assigns which teacher teaches the course

class CourseUpdate(BaseModel):
    name: str
    teacher_id: Optional[int] = None

class CourseStudentAssignment(BaseModel):
    student_ids: List[int]  # List of student IDs to assign to the course

# --- Endpoints ---
@router.post("/classrooms")
def create_classroom(
    classroom: ClassroomCreate,
    db: Session = Depends(database.get_db),
    # Only teachers and higher can create classrooms
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Creates a new classroom and assigns the logged-in teacher as the homeroom teacher."""
    new_classroom = models.Classroom(
        name=classroom.name,
        organization_id=current_user.organization_id,
        teacher_id=current_user.id
    )
    db.add(new_classroom)
    db.commit()
    db.refresh(new_classroom)
    return {"status": "success", "classroom_id": new_classroom.id, "name": new_classroom.name}

@router.post("/students")
def register_student(
    student: StudentCreate,
    db: Session = Depends(database.get_db),
    # Teachers can register students into the system
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Registers a new student, hashes their password, and assigns them to a classroom."""
    # Verify the classroom belongs to the teacher's organization
    classroom = db.query(models.Classroom).filter(models.Classroom.id == student.classroom_id).first()
    if not classroom or classroom.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Invalid classroom ID or organization mismatch")

    # Check if email is already taken
    existing_student = db.query(models.Student).filter(models.Student.email == student.email).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Student email already registered")

    new_student = models.Student(
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        hashed_password=get_password_hash(student.password),
        grade_level=student.grade_level,
        organization_id=current_user.organization_id,
        classroom_id=student.classroom_id
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"status": "success", "student_id": new_student.id}

@router.post("/classrooms/{classroom_id}/exams")
def schedule_exam(
    classroom_id: int,
    exam: ExamCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher"]))
):
    """Schedules an upcoming exam for a specific classroom."""
    # Verify teacher actually owns this classroom
    classroom = db.query(models.Classroom).filter(
        models.Classroom.id == classroom_id,
        models.Classroom.teacher_id == current_user.id
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=403, detail="You are not authorized to schedule exams for this classroom.")
        
    new_exam = models.Exam(
        classroom_id=classroom_id,
        subject=exam.subject,
        date_scheduled=exam.date_scheduled,
        description=exam.description
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return {"status": "success", "exam_id": new_exam.id, "subject": new_exam.subject}

@router.post("/classrooms/{classroom_id}/schedule")
def add_schedule_slot(
    classroom_id: int,
    slot: ScheduleSlotCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "admin"]))
):
    """Adds a class schedule slot for a specific classroom."""
    # Verify teacher actually owns this classroom or is admin
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    
    if not classroom or (current_user.role != "admin" and classroom.teacher_id != current_user.id):
        raise HTTPException(status_code=403, detail="You are not authorized to edit this classroom's schedule.")
        
    new_slot = models.ScheduleSlot(
        classroom_id=classroom_id,
        day_of_week=slot.day_of_week,
        period=slot.period,
        subject=slot.subject,
        teacher_name=slot.teacher_name
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return {"status": "success", "slot_id": new_slot.id}

@router.get("/classrooms/{classroom_id}/schedule")
def get_classroom_schedule(
    classroom_id: int,
    db: Session = Depends(database.get_db)
):
    """Gets the weekly schedule for a classroom."""
    slots = db.query(models.ScheduleSlot).filter(models.ScheduleSlot.classroom_id == classroom_id).all()
    return {"status": "success", "schedule": slots}

# --- Course (Subject Class) Endpoints ---
@router.post("/courses")
def create_course(
    course: CourseCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"]))  # Only admin can create courses
):
    """Creates a new subject course/class. Admin assigns which teacher will teach it."""
    # Verify the teacher exists and belongs to the same organization
    teacher = db.query(models.User).filter(
        models.User.id == course.teacher_id,
        models.User.organization_id == current_user.organization_id
    ).first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or doesn't belong to your organization")

    new_course = models.Course(
        name=course.name,
        organization_id=current_user.organization_id,
        teacher_id=course.teacher_id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return {"status": "success", "course_id": new_course.id, "name": new_course.name, "teacher_id": new_course.teacher_id}

@router.get("/courses")
def get_courses(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Gets all courses belonging to the current teacher or all courses for admin/counselor."""
    if current_user.role in ["admin", "counselor"]:
        courses = db.query(models.Course).filter(
            models.Course.organization_id == current_user.organization_id
        ).all()
    else:
        courses = db.query(models.Course).filter(
            models.Course.teacher_id == current_user.id
        ).all()
    return {"status": "success", "courses": [{"id": c.id, "name": c.name, "teacher_id": c.teacher_id} for c in courses]}

@router.get("/courses/{course_id}")
def get_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Gets a specific course details."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify access: teacher must own the course OR be admin/counselor
    if current_user.role not in ["admin", "counselor"] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this course.")

    return {
        "status": "success",
        "course": {
            "id": course.id,
            "name": course.name,
            "teacher_id": course.teacher_id,
            "organization_id": course.organization_id
        }
    }

@router.put("/courses/{course_id}")
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"]))  # Only admin can edit courses
):
    """Updates a course name and/or teacher assignment."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify course belongs to admin's organization
    if course.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this course.")

    # Update name
    course.name = course_update.name

    # Update teacher if provided
    if course_update.teacher_id is not None:
        teacher = db.query(models.User).filter(
            models.User.id == course_update.teacher_id,
            models.User.organization_id == current_user.organization_id
        ).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found or doesn't belong to your organization")
        course.teacher_id = course_update.teacher_id

    db.commit()
    db.refresh(course)
    return {"status": "success", "course_id": course.id, "name": course.name, "teacher_id": course.teacher_id}

@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"]))  # Only admin can delete courses
):
    """Deletes a course."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify course belongs to admin's organization
    if course.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this course.")

    db.delete(course)
    db.commit()
    return {"status": "success", "message": "Course deleted successfully"}

# --- Course Exam Management ---
@router.post("/courses/{course_id}/exams")
def create_course_exam(
    course_id: int,
    exam: ExamCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "admin"]))
):
    """Creates an exam for a specific course. Teachers can only create exams for their own courses."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify teacher owns this course OR is admin
    if current_user.role != "admin" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to create exams for this course.")

    new_exam = models.Exam(
        course_id=course_id,
        subject=exam.subject,
        date_scheduled=exam.date_scheduled,
        description=exam.description
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return {"status": "success", "exam_id": new_exam.id, "subject": new_exam.subject}

@router.get("/courses/{course_id}/exams")
def get_course_exams(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Gets all exams for a specific course."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify access
    if current_user.role not in ["admin", "counselor"] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view exams for this course.")

    exams = db.query(models.Exam).filter(models.Exam.course_id == course_id).all()
    return {
        "status": "success",
        "exams": [
            {
                "id": e.id,
                "subject": e.subject,
                "date_scheduled": e.date_scheduled.isoformat(),
                "description": e.description
            }
            for e in exams
        ]
    }

@router.delete("/exams/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "admin"]))
):
    """Deletes an exam. Teachers can only delete exams from their own courses."""
    exam = db.query(models.Exam).filter(models.Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    course = db.query(models.Course).filter(models.Course.id == exam.course_id).first()

    # Verify teacher owns the course OR is admin
    if current_user.role != "admin" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this exam.")

    db.delete(exam)
    db.commit()
    return {"status": "success", "message": "Exam deleted successfully"}

# --- Course Student Assignment ---
@router.post("/courses/{course_id}/students")
def assign_students_to_course(
    course_id: int,
    assignment: CourseStudentAssignment,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["admin"]))  # Only admin can assign students
):
    """Assigns students to a course."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify course belongs to admin's organization
    if course.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="You are not authorized to modify this course.")

    # Clear existing students and add new ones
    course.students.clear()

    for student_id in assignment.student_ids:
        student = db.query(models.Student).filter(
            models.Student.id == student_id,
            models.Student.organization_id == current_user.organization_id
        ).first()

        if student:
            course.students.append(student)

    db.commit()
    return {"status": "success", "message": f"Assigned {len(assignment.student_ids)} students to course"}

@router.get("/courses/{course_id}/students")
def get_course_students(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Gets all students enrolled in a course."""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify access
    if current_user.role not in ["admin", "counselor"] and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to view students for this course.")

    return {
        "status": "success",
        "students": [
            {
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.email,
                "grade_level": s.grade_level
            }
            for s in course.students
        ]
    }

# --- Get all students (for admin to assign to courses) ---
@router.get("/students")
def get_all_students(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Gets all students in the organization."""
    students = db.query(models.Student).filter(
        models.Student.organization_id == current_user.organization_id
    ).all()

    return {
        "status": "success",
        "students": [
            {
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "email": s.email,
                "grade_level": s.grade_level,
                "classroom_id": s.classroom_id
            }
            for s in students
        ]
    }

