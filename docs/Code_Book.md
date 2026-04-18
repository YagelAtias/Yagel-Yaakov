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

## Frontend (React + Vite)
The frontend is built with React and Vite. It lives in the `frontend/` folder.
Currently, it serves as an analysis lab where you can test the engine. 

* **`App.jsx`:** The main screen where you can toggle between simple text input or segmented transcript input.
* **`SegmentedEditor.jsx`:** Allows you to break down a conversation sentence by sentence and assign a volume level (whisper, normal, shout) to see how the engine reacts.
* **`AcousticControl.jsx`:** A slider to simulate the overall decibel level of a conversation.
* **`AnalysisResult.jsx`:** Displays the final score and a beautiful breakdown of exactly why the engine gave that score.

*This code book will be updated as we build out the database and the teacher dashboards!*
