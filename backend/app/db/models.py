from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# Junction table for Student <-> Course relationship
student_courses = Table(
    "student_courses",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True)
)

class Organization(Base):
    """Represents a specific School, Yeshiva, or Ulpana."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    students = relationship("Student", back_populates="organization")
    classrooms = relationship("Classroom", back_populates="organization")

class User(Base):
    """Represents Staff (Teachers, Counselors, Principals)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="teacher") # 'counselor', 'teacher', 'admin'
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    # Key Management: The Organization's DEK wrapped by this User's KEK (derived from password)
    encrypted_dek = Column(String, nullable=True) 

    # Privileges: Granular access control array (e.g. ["can_manage_leaves", "can_view_grades"])
    permissions = Column(JSON, default=list)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    classrooms = relationship("Classroom", back_populates="teacher")
    courses = relationship("Course", back_populates="teacher")
    authored_logs = relationship("DistressLog", back_populates="author")

class Student(Base):
    """Represents a student being monitored by the DistressEngine."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    
    # Student login credentials (Optional until they register on the app)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    
    grade_level = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="students")
    classroom = relationship("Classroom", back_populates="students")
    courses = relationship("Course", secondary=student_courses, back_populates="students")
    distress_logs = relationship("DistressLog", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    dorm_leaves = relationship("DormLeave", back_populates="student")
    bagrut_records = relationship("BagrutStatus", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")

class Classroom(Base):
    """Links Teachers to Students to restrict who can see whose data."""
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., "Kitah Aleph 1"
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    teacher_id = Column(Integer, ForeignKey("users.id")) # Homeroom teacher

    # Relationships
    organization = relationship("Organization", back_populates="classrooms")
    teacher = relationship("User", back_populates="classrooms")
    students = relationship("Student", back_populates="classroom")
    schedule_slots = relationship("ScheduleSlot", back_populates="classroom")

class Course(Base):
    """Subject classes taught by Subject Teachers."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) # e.g., "Math 4 Units - Group B"
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    teacher_id = Column(Integer, ForeignKey("users.id")) # Subject teacher

    # Relationships
    teacher = relationship("User", back_populates="courses")
    students = relationship("Student", secondary=student_courses, back_populates="courses")
    exams = relationship("Exam", back_populates="course")
    attendance_sessions = relationship("AttendanceSession", back_populates="course")

class DistressLog(Base):
    """Highly confidential analysis output. Text is ENCRYPTED."""
    __tablename__ = "distress_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Teacher who held the conversation
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # AES-256-GCM Encrypted Base64 string. NEVER PLAIN TEXT!
    encrypted_raw_text = Column(String, nullable=True) 
    
    overall_score = Column(Float, nullable=False)
    has_critical_alert = Column(Boolean, default=False)
    
    # Store the sub-scores (semantic, typing, audio) as JSON
    signals_metadata = Column(JSON, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="distress_logs")
    author = relationship("User", back_populates="authored_logs")

class Grade(Base):
    """Tracks academic performance over time for distress correlation."""
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String, nullable=False)
    score = Column(Float, nullable=False) # 0-100 scale
    date_recorded = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="grades")

class DormLeave(Base):
    """Tracks boarding school (Ulpana/Yeshiva) dorm status and leave requests."""
    __tablename__ = "dorm_leaves"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # e.g., "mid_week", "shabbat_stay", "shabbat_home", "temporary"
    leave_type = Column(String, nullable=False)
    
    # e.g., "Doctor appointment in Jerusalem", "Sister's wedding"
    reason = Column(String, nullable=True)
    destination = Column(String, nullable=False) 
    
    departure_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=False)
    
    # Needs counselor/teacher/madrich approval
    is_approved = Column(Boolean, default=False) 
    
    # e.g., "pending", "approved", "active_leave", "returned", "late"
    status = Column(String, default="pending")
    
    # When the student actually checks back in with the guard/madrich
    actual_return_time = Column(DateTime, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="dorm_leaves")

class BagrutStatus(Base):
    """Tracks Israeli Matriculation (Bagrut) progress."""
    __tablename__ = "bagrut_status"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String, nullable=False) # e.g., "Math", "English", "Tanakh"
    units = Column(Integer, nullable=False)  # e.g., 3, 4, or 5 yechidot
    final_score = Column(Float, nullable=True) # None if exam not taken yet
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    student = relationship("Student", back_populates="bagrut_records")

class Exam(Base):
    """Allows teachers to schedule upcoming exams for their course."""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    subject = Column(String, nullable=False)
    date_scheduled = Column(DateTime, nullable=False)
    description = Column(String, nullable=True)
    
    # Relationships
    course = relationship("Course", back_populates="exams")

class ScheduleSlot(Base):
    """Weekly class schedule for a classroom."""
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 1 = Sunday, 2 = Monday, etc.
    period = Column(Integer, nullable=False)       # 1st period, 2nd period, etc.
    subject = Column(String, nullable=False)
    teacher_name = Column(String, nullable=True)   # The specific teacher for this period
    
    # Relationships
    classroom = relationship("Classroom", back_populates="schedule_slots")


# --- Attendance (pedagogical) ---
class AttendanceSession(Base):
    """A single attendance session for a course on a given date/period."""
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    period = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    """Per-student mark inside an attendance session."""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    # present | late | excused | unexcused
    status = Column(String, nullable=False, default="present")
    note = Column(String, nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    marked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student", back_populates="attendance_records")
