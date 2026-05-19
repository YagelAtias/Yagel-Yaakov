"""add attendance tables

Revision ID: 20260519_01
Revises: 
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260519_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # attendance_sessions
    op.create_table(
        'attendance_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id', ondelete=None), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete=None), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_attendance_sessions_course_id', 'attendance_sessions', ['course_id'])
    op.create_index('ix_attendance_sessions_date', 'attendance_sessions', ['date'])

    # attendance_records
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('attendance_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete=None), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='present'),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('marked_by', sa.Integer(), sa.ForeignKey('users.id', ondelete=None), nullable=True),
        sa.Column('marked_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_attendance_records_session_id', 'attendance_records', ['session_id'])
    op.create_index('ix_attendance_records_student_id', 'attendance_records', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_attendance_records_student_id', table_name='attendance_records')
    op.drop_index('ix_attendance_records_session_id', table_name='attendance_records')
    op.drop_table('attendance_records')
    op.drop_index('ix_attendance_sessions_date', table_name='attendance_sessions')
    op.drop_index('ix_attendance_sessions_course_id', table_name='attendance_sessions')
    op.drop_table('attendance_sessions')
