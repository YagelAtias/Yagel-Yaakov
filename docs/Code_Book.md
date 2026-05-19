# Yagel-Yaakov Code Book

Welcome to the Yagel-Yaakov project. This guide explains how the system is built, the architecture, and what each part of the code does.

## Architecture Overview
The platform has two main sides:
1. **The Volatile Engine:** Takes in sensitive data (transcripts, audio, typing latency). It runs models in RAM, generates a distress score, and discards raw sensitive data.
2. **The Institutional Database:** Built with SQLAlchemy for school management (student records, logins, grades, weekend leave requests). Encrypted transcripts are stored here safely.

## Backend (FastAPI)
The backend is written in Python using FastAPI. The main entry point is `backend/main.py`.

### The Signals (`app/signals/`)
* **`analysis_engine.py`:** The conductor. Combines text, audio data, and typing data into one final distress score. Handles the encryption pipeline.
* **`hebrew_wmd.py`:** The Semantic Engine using Word2Vec.
* **`text_entropy.py`:** The Rumination Engine using zlib compression analysis.
* **`audio_processing.py`:** Uses `faster-whisper` and `librosa` to transcribe audio from volatile `.webm` files and detect word-level decibel intensity (shout/whisper).
* **`typing_latency.py`:** Analyzes keystroke timing.

### The Database (`app/db/`)
* **`models.py`:** Contains SQLAlchemy schemas: `Organization`, `User` (Staff), `Student`, `Classroom`, `DistressLog`, `DormLeave`, `Exam`, etc.

### Security & Services (`app/security/` & `app/services/`)
* **`encryption.py`:** AES-256-GCM encryption.
* **`auth.py`:** Handles JWT logins and role/permission gatekeeping.
* **`push_service.py`:** A scalable notification engine that uses `smtplib` to send real-time email alerts to staff for critical distress scores and dorm leave updates.

### API Endpoints (`app/api/`)
* **`dashboard.py`:** The "Mega-Endpoint". Packages a teacher's roster, pending leaves, upcoming exams, student location tracking, and critical distress alerts into one fast JSON response.
* **`leaves.py`:** Handles DormLeave submissions, approvals, and "returned to dorms" status updates, while triggering push notifications.
* **`logs.py`, `classrooms.py`, `management.py`:** Standard CRUD and gatekeeper endpoints.

## Frontend (React + Vite)
The frontend is built with React and heavily utilizes state-driven architecture without complex routing (conditional rendering based on role).
* **`TeacherDashboard.jsx`:** A robust staff view with expandable student cards, active leave tracking ("בפנימייה" vs "לא נמצא"), live audio recording, and rendering of formatted distress logs (red for shouting).
* **`StudentDashboard.jsx`:** The student interface featuring daily schedules, exams, a leave request form, and a microphone integration for sending voice messages directly to staff.
* **`api.js`:** Handles `secureFetch` with JWT injection and `FormData` parsing for audio files.
