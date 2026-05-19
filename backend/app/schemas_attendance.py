from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


AttendanceStatus = Literal["present", "late", "excused", "unexcused"]


class AttendanceSessionCreate(BaseModel):
    course_id: int
    date: datetime
    period: int


class AttendanceRecordInput(BaseModel):
    student_id: int
    status: AttendanceStatus
    note: Optional[str] = None


class AttendanceBulkMark(BaseModel):
    records: List[AttendanceRecordInput]


class AttendanceRecordOut(BaseModel):
    student_id: int
    status: AttendanceStatus
    note: Optional[str] = None
    marked_at: datetime

    class Config:
        orm_mode = True


class AttendanceSessionOut(BaseModel):
    id: int
    course_id: int
    date: datetime
    period: int
    records: List[AttendanceRecordOut] = []

    class Config:
        orm_mode = True
