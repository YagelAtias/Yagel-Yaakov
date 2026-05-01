from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

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
