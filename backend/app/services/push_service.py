import logging
from typing import Dict, Any

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("push_service")
logger.setLevel(logging.INFO)

# These should be set in your environment variables or a .env file later
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SYSTEM_EMAIL = os.getenv("SMTP_EMAIL", "your-system-email@gmail.com")
SYSTEM_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

class PushNotificationService:
    @staticmethod
    def send_to_user(user_id: int, title: str, body: str, db_session, data: Dict[str, Any] = None):
        """
        Sends an email notification to a specific user using smtplib.
        """
        from app.db import models
        user = db_session.query(models.User).filter(models.User.id == user_id).first()
        
        if not user or not user.email:
            logger.warning(f"Could not send email to User {user_id}: No email found.")
            return False
            
        logger.info(f"📧 Sending EMAIL to {user.email}: [{title}]")
        
        # In a real presentation, if the credentials aren't set, we just log it and return.
        if SYSTEM_EMAIL == "your-system-email@gmail.com":
            logger.info(f"Mock Email Body: {body}")
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = f"DistressEngine System <{SYSTEM_EMAIL}>"
            msg['To'] = user.email
            msg['Subject'] = title

            # Create a simple, clean HTML email template
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">{title}</h2>
                <p style="font-size: 16px; color: #333; line-height: 1.5;">{body}</p>
                <br>
                <p style="font-size: 12px; color: #7f8c8d; text-align: center;">הודעה זו נשלחה אוטומטית ממערכת DistressEngine.<br>נא לא להשיב למייל זה.</p>
            </div>
            """
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SYSTEM_EMAIL, SYSTEM_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_to_role_in_org(organization_id: int, role: str, title: str, body: str, db_session):
        """
        Sends a push notification to all users with a specific role in an organization.
        """
        from app.db import models
        users = db_session.query(models.User).filter(
            models.User.organization_id == organization_id,
            models.User.role == role
        ).all()
        
        for user in users:
            PushNotificationService.send_to_user(user.id, title, body, db_session)
            
    @staticmethod
    def send_to_staff_for_student(student_id: int, title: str, body: str, db_session):
        """
        Sends a push notification to the homeroom teacher and counselors responsible for the student.
        """
        from app.db import models
        student = db_session.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            return
            
        # Send to homeroom teacher
        if student.classroom and student.classroom.teacher_id:
            PushNotificationService.send_to_user(student.classroom.teacher_id, title, body, db_session)
            
        # Send to all counselors in the school
        PushNotificationService.send_to_role_in_org(student.organization_id, "counselor", title, body, db_session)

    @staticmethod
    def send_to_staff_with_permission(organization_id: int, permission: str, title: str, body: str, db_session):
        """
        Sends a push notification to all users in the organization who have a specific permission.
        (e.g., 'can_manage_leaves')
        """
        from app.db import models
        import json
        users = db_session.query(models.User).filter(
            models.User.organization_id == organization_id
        ).all()
        
        for user in users:
            try:
                # permissions is JSON. Load it if string, otherwise it's a list.
                perms = user.permissions
                if isinstance(perms, str):
                    perms = json.loads(perms)
                if permission in perms:
                    PushNotificationService.send_to_user(user.id, title, body, db_session)
            except Exception:
                pass
