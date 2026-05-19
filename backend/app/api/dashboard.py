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
    Teacher dashboard in one call.
    Reason: phones and mobile networks work better with fewer requests. Instead of many small
    calls (students, dorms, exams, etc.), this endpoint collect the data a teacher needs and
    return it in one JSON. Faster to load, lighter on battery and data.
    """
    
    # 1. Fetch Classrooms and Courses owned by this teacher (or all if admin/counselor)
    if current_user.role in ["admin", "counselor"]:
        classrooms = db.query(models.Classroom).filter(models.Classroom.organization_id == current_user.organization_id).all()
        courses = db.query(models.Course).filter(models.Course.organization_id == current_user.organization_id).all()
    else:
        classrooms = db.query(models.Classroom).filter(models.Classroom.teacher_id == current_user.id).all()
        courses = db.query(models.Course).filter(models.Course.teacher_id == current_user.id).all()
        
    classroom_ids = [c.id for c in classrooms]
    course_ids = [c.id for c in courses]
    
    # 2. Fetch Students in those classrooms or courses
    students = db.query(models.Student).filter(
        models.Student.classroom_id.in_(classroom_ids) |
        models.Student.courses.any(models.Course.id.in_(course_ids))
    ).all()
    student_ids = [s.id for s in students]
    
    # 3. Fetch Pending Dorm Leaves for these students
    pending_leaves = db.query(models.DormLeave).filter(
        models.DormLeave.student_id.in_(student_ids),
        models.DormLeave.status == "pending"
    ).all()
    
    # 4. Fetch Upcoming Exams
    if current_user.role in ["admin", "counselor"]:
        upcoming_exams = db.query(models.Exam).filter(
            models.Exam.date_scheduled >= datetime.utcnow()
        ).all()
    else:
        if not course_ids:
            upcoming_exams = []
        else:
            upcoming_exams = db.query(models.Exam).filter(
                models.Exam.course_id.in_(course_ids),
                models.Exam.date_scheduled >= datetime.utcnow()
            ).all()
    
    # 5. Fetch critical risk alerts (calculate risk per student)
    risk_engine = GlobalRiskEngine(db)
    students_at_risk = []
    
    for student in students:
        risk_profile = risk_engine.calculate_student_risk(student.id)
        # If a student has a recent critical alert or a high risk score, flag them on the dashboard
        if risk_profile.get("has_recent_critical") or risk_profile.get("global_risk_score", 0) > 0.6:
            students_at_risk.append({
                "student_id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "risk_profile": risk_profile
            })
            
    # Build student entries and include a short view of recent conversations
    class_map = {c.id: c.name for c in classrooms}
    students_data = []
    
    for student in students:
        class_name = class_map.get(student.classroom_id, "ללא שיוך")
        
        # Get their recent conversations/logs
        logs = db.query(models.DistressLog).filter(
            models.DistressLog.student_id == student.id
        ).order_by(models.DistressLog.timestamp.desc()).limit(5).all()
        
        # Calculate the risk profile for the clinical view
        risk_profile = risk_engine.calculate_student_risk(student.id)
        
        # Figure out current location based on active leave
        current_time = datetime.utcnow()
        active_leave = db.query(models.DormLeave).filter(
            models.DormLeave.student_id == student.id,
            models.DormLeave.is_approved == True,
            models.DormLeave.status != "returned",
            models.DormLeave.departure_date <= current_time,
            models.DormLeave.return_date >= current_time
        ).first()
        
        active_leave_data = None
        if active_leave:
            current_location = "לא נמצא"
            active_leave_data = {
                "leave_id": active_leave.id,
                "destination": active_leave.destination,
                "reason": active_leave.reason,
                "departure_date": active_leave.departure_date,
                "return_date": active_leave.return_date,
                "leave_type": active_leave.leave_type
            }
        else:
            current_location = "בפנימייה"
        
        students_data.append({
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "class_name": class_name,
            "grade_level": student.grade_level,
            "current_location": current_location,
            "active_leave": active_leave_data,
            "risk_profile": risk_profile,
            # For privacy and performance, show only minimal metadata here.
            # Fetch full (encrypted) text via a separate endpoint with permissions.
            "recent_conversations": [
                {
                    "id": log.id,
                    "date": log.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "has_critical_alert": log.has_critical_alert,
                    "score": log.overall_score,
                } for log in logs
            ]
        })
            
    # Package the response
    return {
        "status": "success",
        "user_name": current_user.full_name,
        "classrooms_count": len(classrooms),
        "students": students_data,
        "pending_dorm_leaves": [
            {
                "leave_id": leave.id,
                "student_id": leave.student_id,
                "student_name": f"{leave.student.first_name} {leave.student.last_name}" if leave.student else "לא ידוע",
                "leave_type": leave.leave_type,
                "departure_date": leave.departure_date,
                "return_date": leave.return_date,
                "destination": leave.destination,
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

@router.get("/dashboard/student")
def get_student_dashboard(
    db: Session = Depends(database.get_db),
    current_user: models.Student = Depends(require_role(["student"]))
):
    """Fetches real staff members and exams for the student view."""
    # Fetch school's staff members for the contact dropdown
    staff = db.query(models.User).filter(models.User.organization_id == current_user.organization_id).all()
    
    # Fetch exams for student's courses
    exams = []
    if current_user.courses:
        course_ids = [c.id for c in current_user.courses]
        exams = db.query(models.Exam).filter(
            models.Exam.course_id.in_(course_ids),
            models.Exam.date_scheduled >= datetime.utcnow()
        ).all()
        
    return {
        "status": "success",
        "user_name": current_user.first_name,
        "student_id": current_user.id,
        "staff": [
            {"id": s.id, "name": s.full_name, "role": s.role} for s in staff
        ],
        "exams": [
            {
                "id": e.id,
                "subject": e.subject,
                "date": e.date_scheduled.strftime("%Y-%m-%d %H:%M")
            } for e in exams
        ]
    }
