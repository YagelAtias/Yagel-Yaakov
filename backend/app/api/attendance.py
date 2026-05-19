from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import database, models
from ..security.auth import require_permission
from ..schemas_attendance import (
    AttendanceSessionCreate,
    AttendanceBulkMark,
    AttendanceSessionOut,
    AttendanceRecordOut,
)


router = APIRouter()


@router.post("/sessions", response_model=AttendanceSessionOut)
def create_attendance_session(
    body: AttendanceSessionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("can_take_attendance")),
):
    # Verify course belongs to the same org and (if teacher) to the current teacher
    course = db.query(models.Course).filter(models.Course.id == body.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if getattr(current_user, "role", None) == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to create session for this course")

    session = models.AttendanceSession(
        course_id=body.course_id,
        date=body.date,
        period=body.period,
        created_by=current_user.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return AttendanceSessionOut(
        id=session.id,
        course_id=session.course_id,
        date=session.date,
        period=session.period,
        records=[],
    )


@router.post("/sessions/{session_id}/records", response_model=AttendanceSessionOut)
def bulk_mark_records(
    session_id: int,
    body: AttendanceBulkMark,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("can_take_attendance")),
):
    session = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Permission check: teachers may only update their own course sessions
    if getattr(current_user, "role", None) == "teacher":
        course = db.query(models.Course).filter(models.Course.id == session.course_id).first()
        if not course or course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to mark this session")

    # Build a map of course students to validate marks
    course_students: List[models.Student] = (
        db.query(models.Student)
        .join(models.student_courses, models.student_courses.c.student_id == models.Student.id)
        .filter(models.student_courses.c.course_id == session.course_id)
        .all()
    )
    allowed_ids = {s.id for s in course_students}

    # Upsert-style: if a record for (session, student) exists, update it; otherwise, insert
    existing = (
        db.query(models.AttendanceRecord)
        .filter(models.AttendanceRecord.session_id == session.id)
        .all()
    )
    by_student = {r.student_id: r for r in existing}

    for rec in body.records:
        if rec.student_id not in allowed_ids:
            continue  # silently skip students not in this course
        row = by_student.get(rec.student_id)
        if row:
            row.status = rec.status
            row.note = rec.note
            row.marked_by = current_user.id
            row.marked_at = datetime.utcnow()
        else:
            row = models.AttendanceRecord(
                session_id=session.id,
                student_id=rec.student_id,
                status=rec.status,
                note=rec.note,
                marked_by=current_user.id,
                marked_at=datetime.utcnow(),
            )
            db.add(row)
            by_student[rec.student_id] = row

    db.commit()

    out_records = [
        AttendanceRecordOut(
            student_id=r.student_id, status=r.status, note=r.note, marked_at=r.marked_at
        )
        for r in by_student.values()
    ]

    return AttendanceSessionOut(
        id=session.id,
        course_id=session.course_id,
        date=session.date,
        period=session.period,
        records=sorted(out_records, key=lambda x: x.student_id),
    )


@router.get("/courses/{course_id}/today", response_model=List[AttendanceSessionOut])
def get_today_sessions(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("can_take_attendance")),
):
    # Permission: teachers can only read their own courses
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if getattr(current_user, "role", None) == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to read this course")

    # Today range in UTC (00:00 .. 23:59:59). Adjust later if you store local tz.
    now = datetime.utcnow()
    start = datetime(year=now.year, month=now.month, day=now.day)
    end = start + timedelta(days=1)

    sessions = (
        db.query(models.AttendanceSession)
        .filter(
            models.AttendanceSession.course_id == course_id,
            models.AttendanceSession.date >= start,
            models.AttendanceSession.date < end,
        )
        .all()
    )

    # Prefetch records per session
    result: List[AttendanceSessionOut] = []
    for s in sessions:
        recs = (
            db.query(models.AttendanceRecord)
            .filter(models.AttendanceRecord.session_id == s.id)
            .all()
        )
        result.append(
            AttendanceSessionOut(
                id=s.id,
                course_id=s.course_id,
                date=s.date,
                period=s.period,
                records=[
                    AttendanceRecordOut(
                        student_id=r.student_id,
                        status=r.status,
                        note=r.note,
                        marked_at=r.marked_at,
                    )
                    for r in recs
                ],
            )
        )

    return result
