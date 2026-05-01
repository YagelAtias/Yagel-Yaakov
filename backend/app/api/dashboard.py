from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from ..db import database, models
from ..security.auth import require_role
from ..signals.global_risk import GlobalRiskEngine

router = APIRouter()

@router.get("/dashboard/teacher")
def get_teacher_dashboard(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_role(["teacher", "admin", "counselor"]))
):
    """
    The 'Mega-Endpoint' for the Mobile App.
    ARCHITECTURE REASONING:
    Mobile networks can be slow and phones have limited battery. Instead of forcing the React app 
    to make 10+ different API calls (fetch students, then fetch dorms, then fetch exams...), 
    this single endpoint acts as a funnel. It queries the database and packages the teacher's 
    entire necessary ecosystem state into one lightning-fast JSON response.
    """
    
    # 1. Fetch Classrooms owned by this teacher (or all if admin/counselor)
    if current_user.role in ["admin", "counselor"]:
        classrooms = db.query(models.Classroom).filter(models.Classroom.organization_id == current_user.organization_id).all()
    else:
        classrooms = db.query(models.Classroom).filter(models.Classroom.teacher_id == current_user.id).all()
        
    classroom_ids = [c.id for c in classrooms]
    
    # 2. Fetch Students in those classrooms
    students = db.query(models.Student).filter(models.Student.classroom_id.in_(classroom_ids)).all()
    student_ids = [s.id for s in students]
    
    # 3. Fetch Pending Dorm Leaves for these students
    pending_leaves = db.query(models.DormLeave).filter(
        models.DormLeave.student_id.in_(student_ids),
        models.DormLeave.status == "pending"
    ).all()
    
    # 4. Fetch Upcoming Exams
    upcoming_exams = db.query(models.Exam).filter(
        models.Exam.classroom_id.in_(classroom_ids),
        models.Exam.date_scheduled >= datetime.utcnow()
    ).all()
    
    # 5. Fetch Critical Risk Alerts (Calculate Risk for each student)
    risk_engine = GlobalRiskEngine(db)
    students_at_risk = []
    
    for student in students:
        risk_profile = risk_engine.calculate_student_risk(student.id)
        # If the student has a critical alert or high global risk, flag them on the dashboard immediately
        if risk_profile.get("has_recent_critical") or risk_profile.get("global_risk_score", 0) > 0.75:
            students_at_risk.append({
                "student_id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "risk_profile": risk_profile
            })
            
    # Package and send!
    return {
        "status": "success",
        "user_name": current_user.full_name,
        "classrooms_count": len(classrooms),
        "students_count": len(students),
        "pending_dorm_leaves": [
            {
                "leave_id": leave.id,
                "student_id": leave.student_id,
                "leave_type": leave.leave_type,
                "departure_date": leave.departure_date,
                "reason": leave.reason
            } for leave in pending_leaves
        ],
        "upcoming_exams": [
            {
                "exam_id": exam.id,
                "subject": exam.subject,
                "date_scheduled": exam.date_scheduled
            } for exam in upcoming_exams
        ],
        "critical_alerts": students_at_risk
    }
