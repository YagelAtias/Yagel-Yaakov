from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import database, models
from ..security.auth import require_role
from ..security.encryption import decrypt_text
from ..signals.global_risk import GlobalRiskEngine

router = APIRouter()

@router.get("/students/{student_id}/logs")
def get_student_logs(
    student_id: int, 
    db: Session = Depends(database.get_db),
    # THE GATEKEEPER: Only counselors and admins can access this endpoint
    current_user: models.User = Depends(require_role(["counselor", "admin"]))
):
    """
    Retrieves and decrypts distress logs for a specific student.
    The raw text is decrypted in RAM and sent securely over the network.
    """
    # 1. Check if the student belongs to the teacher's organization
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student or student.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Student not found in your organization.")

    # 2. Fetch the encrypted logs from the database
    logs = db.query(models.DistressLog).filter(models.DistressLog.student_id == student_id).order_by(models.DistressLog.timestamp.desc()).all()
    
    # 3. Decrypt the text in RAM
    decrypted_logs = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "timestamp": log.timestamp,
            "overall_score": log.overall_score,
            "has_critical_alert": log.has_critical_alert,
            "signals": log.signals_metadata,
            # Use the AES-256 Master Key to decrypt the ciphertext
            "decrypted_text": decrypt_text(log.encrypted_raw_text) if log.encrypted_raw_text else ""
        }
        decrypted_logs.append(log_dict)
        
        
    return {"status": "success", "student_name": f"{student.first_name} {student.last_name}", "logs": decrypted_logs}

@router.get("/students/{student_id}/risk_profile")
def get_student_risk_profile(
    student_id: int,
    db: Session = Depends(database.get_db),
    # Teachers can view the math/risk score, even though they can't read the encrypted transcripts
    current_user: models.User = Depends(require_role(["teacher", "counselor", "admin"]))
):
    """
    Returns the fused Global Risk Score (Median Distress + Grade Trends).
    Applies strict Classroom-level verification for standard Teachers.
    """
    # 1. Organization Firewall
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student or student.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Student not found in your organization.")
        
    # 2. Classroom-level Authorization (If role == teacher)
    if current_user.role == "teacher":
        classroom = db.query(models.Classroom).filter(
            models.Classroom.id == student.classroom_id,
            models.Classroom.teacher_id == current_user.id
        ).first()
        if not classroom:
            raise HTTPException(status_code=403, detail="You are not authorized to view this student's risk profile.")

    # 3. Calculate and return the Global Risk Score
    risk_engine = GlobalRiskEngine(db)
    risk_profile = risk_engine.calculate_student_risk(student_id)
    
    return {
        "status": "success",
        "student_name": f"{student.first_name} {student.last_name}",
        "risk_profile": risk_profile
    }
