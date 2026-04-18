from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import database, models
from ..security.auth import require_role
from ..security.encryption import decrypt_text

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
