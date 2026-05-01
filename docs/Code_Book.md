# Yagel-Yaakov Code Book

Welcome to the Yagel-Yaakov project. This guide explains how the system is built, the architecture, and what each part of the code does.

## Architecture Overview
The platform has two main sides:
1. **The Volatile Engine:** This takes in sensitive data like student transcripts, audio, and typing latency. It runs the data through analysis models in the server's RAM (memory), generates a distress score, and then throws away the raw sensitive data so nothing is left behind on the server.
2. **The Institutional Database (SQLAlchemy):** This is for the standard school management stuff like student records, teacher logins, grades, and weekend leave requests. If we ever save a transcript for an authorized teacher to read later, it is encrypted before it hits the database so the server hard drive only has unreadable text.

## Backend (FastAPI)
The backend is written in Python using FastAPI. The main entry point is `backend/main.py`.

### The Signals
Inside `backend/app/signals/` you will find the engines that actually do the thinking.

* **`analysis_engine.py`:** This is the conductor. It takes the text, audio data, and typing data, passes them to the individual signal engines, and combines their results into one final distress score (from 0 to 1). If the semantic engine finds something extremely critical like self harm, this engine will force the final score very high to make sure the staff is alerted.
* **`hebrew_wmd.py`:** The Semantic Engine. It uses a Word2Vec model to understand the meaning of the Hebrew words. It measures the "distance" between the student's sentences and specific clinical topics like sadness or anxiety. Closer distance means higher distress. It also has safety nets built in to catch critical phrases.
* **`text_entropy.py`:** The Rumination Engine. It takes the text and compresses it using an algorithm called zlib. If a student is repeating themselves a lot, the text compresses really well. High compression means high repetition, which we flag as "rumination" or obsessive thoughts.
* **`clinical_lexicon.py`:** A small helper file that holds base weights for specific distress words.

### The Database (`app/db/`)
* **`database.py`:** Handles the connection to the SQLite database (which we use for prototyping). It creates the `engine` and the `SessionLocal` factory.
* **`models.py`:** Contains the SQLAlchemy schemas. 
    * `Organization` (School/Yeshiva)
    * `User` (Staff member with roles and passwords)
    * `Student` 
    * `Classroom` (Links specific teachers to specific students)
    * `DistressLog` (Stores the analysis results and the *encrypted* raw text).

### Security & Encryption (`app/security/`)
* **`encryption.py`:** A strict, military-grade `AES-256-GCM` encryption pipeline. Before any transcript is saved to the database, it passes through here. It uses a secret Master Key to scramble the text.
* **`auth.py`:** Handles everything related to logging in. It uses `bcrypt` to hash passwords and `PyJWT` to create secure JSON Web Tokens. It also contains the `require_role` gatekeeper to block unauthorized staff.

### API Endpoints (`app/api/`)
* **`auth.py`:** Contains `/login` and `/register`. Handles unified logins for both Teachers and Students using JWT tokens.
* **`logs.py`:** The Gatekeeper Endpoint (`/students/{student_id}/logs`). Decrypts raw transcripts in RAM if a teacher is authorized.
* **`classrooms.py`:** Endpoints for creating classrooms, registering students, and scheduling upcoming exams.
* **`management.py`:** Handles school operations: submitting grades, Bagrut (matriculation) tracking, and managing Dorm Leave requests (including temporary exits and Shabbat stays).
* **`dashboard.py`:** The "Mega-Endpoint". Designed specifically for mobile app performance. It packages a teacher's entire day (roster, pending leaves, upcoming exams, and critical distress alerts) into one lightning-fast JSON response to save battery and network bandwidth.

## Frontend (React + Vite)
The frontend is built with React and Vite. It lives in the `frontend/` folder.
Currently, it serves as an analysis lab where you can test the engine. 

* **`App.jsx`:** The main screen where you can toggle between simple text input or segmented transcript input.
* **`SegmentedEditor.jsx`:** Allows you to break down a conversation sentence by sentence and assign a volume level (whisper, normal, shout) to see how the engine reacts.
* **`AcousticControl.jsx`:** A slider to simulate the overall decibel level of a conversation.
* **`AnalysisResult.jsx`:** Displays the final score and a beautiful breakdown of exactly why the engine gave that score.
* **`AudioRecorder.jsx`:** Captures raw, unfiltered audio from the user's microphone for Whisper transcription.
