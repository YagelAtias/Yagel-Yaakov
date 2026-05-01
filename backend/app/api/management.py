from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..db import database, models
from ..security.auth import require_role

router = APIRouter()

# --- Pydantic Schemas ---
class GradeCreate(BaseModel):
    subject: str
    score: float

class BagrutCreate(BaseModel):
    subject: str
    units: int
    final_score: Optional[float] = None
    is_completed: bool = False

class DormLeaveRequest(BaseModel):
    student_id: int
    leave_type: str # "mid_week", "shabbat_stay", "shabbat_home", "temporary"
    reason: Optional[str] = None
    destination: str
    departure_date: datetime
    return_date: datetime

# --- Endpoints ---

@router.post("/students/{student_id}/grades")
def submit_grade(
    student_id: int,
    grade: GradeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "admin"]))
):
    """Allows a teacher to submit a grade. This fuels the Global Risk Algorithm."""
    # Organization Firewall
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student or student.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Student not found in your organization")

    new_grade = models.Grade(
        student_id=student_id,
        subject=grade.subject,
        score=grade.score
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return {"status": "success", "grade_id": new_grade.id}


@router.post("/students/{student_id}/bagrut")
def update_bagrut(
    student_id: int,
    bagrut: BagrutCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Updates a student's Bagrut matriculation status (Subject, Yechidot, Final Score)."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student or student.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Student not found in your organization")

    new_bagrut = models.BagrutStatus(
        student_id=student_id,
        subject=bagrut.subject,
        units=bagrut.units,
        final_score=bagrut.final_score,
        is_completed=bagrut.is_completed
    )
    db.add(new_bagrut)
    db.commit()
    db.refresh(new_bagrut)
    return {"status": "success", "bagrut_id": new_bagrut.id}


@router.post("/dorms/request_leave")
def request_dorm_leave(
    leave_request: DormLeaveRequest,
    db: Session = Depends(database.get_db),
    # Both students and teachers can request a leave
    current_user: models.User = Depends(require_role(["student", "teacher", "counselor", "admin"]))
):
    """A student (or teacher) requests a weekend or temporary dorm leave."""
    # If the user is a student, they can only request leave for themselves
    if current_user.role == "student" and current_user.id != leave_request.student_id:
        raise HTTPException(status_code=403, detail="Students can only request leave for themselves.")
        
    new_leave = models.DormLeave(
        student_id=leave_request.student_id,
        leave_type=leave_request.leave_type,
        reason=leave_request.reason,
        destination=leave_request.destination,
        departure_date=leave_request.departure_date,
        return_date=leave_request.return_date,
        status="pending",
        is_approved=False
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return {"status": "success", "leave_id": new_leave.id}


@router.put("/dorms/{leave_id}/approve")
def approve_dorm_leave(
    leave_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """Allows a Madrich/Teacher to explicitly approve a dorm leave request."""
    leave = db.query(models.DormLeave).filter(models.DormLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    leave.is_approved = True
    leave.status = "approved"
    db.commit()
    return {"status": "success", "message": "Leave approved"}


@router.put("/dorms/{leave_id}/return")
def mark_dorm_return(
    leave_id: int,
    db: Session = Depends(database.get_db),
    # Students can mark themselves as returned, or a teacher/guard can do it for them
    current_user: models.User = Depends(require_role(["student", "teacher", "counselor", "admin"]))
):
    """Records the exact moment a student returns to the dorms from a temporary leave."""
    leave = db.query(models.DormLeave).filter(models.DormLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    if current_user.role == "student" and current_user.id != leave.student_id:
        raise HTTPException(status_code=403, detail="You can only mark your own return")

    leave.status = "returned"
    leave.actual_return_time = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Student has safely returned", "timestamp": leave.actual_return_time}
