from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..db import database, models
from ..security.auth import get_current_user, require_role, require_permission
from ..services.push_service import PushNotificationService

router = APIRouter()

class LeaveRequest(BaseModel):
    leave_type: str
    reason: Optional[str] = None
    destination: str
    departure_date: datetime
    return_date: datetime

@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_leave(
    leave: LeaveRequest, 
    db: Session = Depends(database.get_db), 
    current_user = Depends(require_role(["student"]))
):
    new_leave = models.DormLeave(
        student_id=current_user.id,
        leave_type=leave.leave_type,
        reason=leave.reason,
        destination=leave.destination,
        departure_date=leave.departure_date,
        return_date=leave.return_date,
        status="pending",
        is_approved=False
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    
    student_name = f"{current_user.first_name} {current_user.last_name}"
    PushNotificationService.send_to_staff_with_permission(
        organization_id=current_user.organization_id,
        permission="can_manage_leaves",
        title="בקשת יציאה חדשה מהפנימייה",
        body=f"{student_name} הגיש בקשת יציאה. אנא היכנס למערכת כדי לאשר.",
        db_session=db
    )
    
    return {"message": "Leave submitted successfully", "leave_id": new_leave.id}

class LeaveStatusUpdate(BaseModel):
    status: str
    is_approved: bool

@router.put("/{leave_id}/status")
def update_leave_status(
    leave_id: int, 
    update: LeaveStatusUpdate, 
    db: Session = Depends(database.get_db), 
    current_user = Depends(require_permission("can_manage_leaves"))
):
    leave = db.query(models.DormLeave).filter(models.DormLeave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave.status = update.status
    leave.is_approved = update.is_approved
    db.commit()
    
    student_name = f"{leave.student.first_name} {leave.student.last_name}" if leave.student else "תלמיד"
    if update.status == "returned":
        PushNotificationService.send_to_staff_for_student(
            student_id=leave.student_id,
            title="חזר לפנימייה",
            body=f"{student_name} סומן כמי שחזר לפנימייה.",
            db_session=db
        )
    elif update.is_approved:
        PushNotificationService.send_to_staff_for_student(
            student_id=leave.student_id,
            title="יציאה אושרה",
            body=f"בקשת היציאה של {student_name} אל {leave.destination} אושרה.",
            db_session=db
        )
        
    return {"message": "Leave updated successfully"}
