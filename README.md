# Yagel-Yaakov: Holistic Education Management System

## Overview
The Yagel-Yaakov Platform is a dual-purpose institutional system designed for boarding school environments (Yeshivot and Ulpanot). It bridges the gap between traditional pedagogical management and innovative emotional safety by fusing academic performance data with a sophisticated multi-signal distress analysis engine.

## Core Features
### 1. Holistic Student Management
* **Teacher & Student Dashboards:** A robust React-based UI providing tailored views for staff and students.
* **Institutional Logistics (Dorm Leaves):** Comprehensive management of weekend leaves and temporary exits. Staff can track active leaves, approve requests, and monitor student locations (e.g., "בפנימייה" vs "לא נמצא").
* **Pedagogical Tracking:** Centralized management of schedules and exams.

### 2. Multi-Signal Distress Analysis Engine
The system analyzes multiple distinct signals to generate a weighted distress score:
* **Semantic Geometry (WMD):** Uses vector similarity to measure the mathematical distance between dialogue and clinical definitions of distress.
* **Cognitive Entropy:** Analyzes text patterns to identify rumination, repetitive thoughts, or chaotic emotional states.
* **Acoustic Intensity & Transcription:** Uses `faster-whisper` for word-level transcription and real-time decibel analysis to detect shouting or whispering. The UI automatically formats shouting in **bold/red** and whispering in *italic/light*.
* **Typing Latency:** Analyzes the time delays and hesitation between keystrokes to identify emotional friction.

### 3. Security, Privacy & Push Notifications
* **Data-at-Rest Encryption:** Military-grade AES-256-GCM encryption pipeline. Raw text is never stored in plaintext.
* **Granular RBAC:** Role-Based and Permission-Based Access Control ensures only authorized staff can view specific distress logs or manage leaves.
* **Push Notification Service:** Automated email alerts (`smtplib`) triggered for critical distress scores (>0.8) and dorm leave requests/returns, ensuring staff are instantly aware of emergencies even when logged off.

## Setup
1. **Frontend:** Navigate to `/frontend`, run `npm install`, followed by `npm run dev`.
2. **Backend:** Navigate to `/backend`, install requirements from `requirements.txt`.
3. **Environment Variables:** Create a `.env` in the `backend` folder with `SMTP_EMAIL` and `SMTP_PASSWORD` for email push notifications.
4. **Run Server:** Start the FastAPI server using `uvicorn main:app --reload` or `python main.py`.
5. **Models:** A pre-trained Hebrew Word2Vec model must be placed in `backend/app/models/he_model_small.bin` (not included in repository due to size). Whisper model downloads automatically.