from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

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

    # Relationships
    organization = relationship("Organization", back_populates="users")
    classrooms = relationship("Classroom", back_populates="teacher")

class Student(Base):
    """Represents a student being monitored by the DistressEngine."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    grade_level = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="students")
    classroom = relationship("Classroom", back_populates="students")
    distress_logs = relationship("DistressLog", back_populates="student")
    grades = relationship("Grade", back_populates="student")
    dorm_leaves = relationship("DormLeave", back_populates="student")

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

class DistressLog(Base):
    """Highly confidential analysis output. Text is ENCRYPTED."""
    __tablename__ = "distress_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # AES-256-GCM Encrypted Base64 string. NEVER PLAIN TEXT!
    encrypted_raw_text = Column(String, nullable=True) 
    
    overall_score = Column(Float, nullable=False)
    has_critical_alert = Column(Boolean, default=False)
    
    # Store the sub-scores (semantic, typing, audio) as JSON
    signals_metadata = Column(JSON, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="distress_logs")

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
    """Tracks boarding school (Ulpana/Yeshiva) weekend leave and dorm status."""
    __tablename__ = "dorm_leaves"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # e.g., "Home - Jerusalem", "Staying for Shabbat"
    destination = Column(String, nullable=False) 
    
    departure_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=False)
    
    # Needs counselor/teacher approval
    is_approved = Column(Boolean, default=False) 
    
    # Relationships
    student = relationship("Student", back_populates="dorm_leaves")
