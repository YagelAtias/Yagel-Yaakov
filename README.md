# Yagel-Yaakov: Holistic Education Management & Multi-Signal Distress Analysis

## Overview
The Yagel-Yaakov Platform is a dual-purpose institutional system designed for boarding school environments (Yeshivot and Ulpanot). It bridges the gap between traditional pedagogical management and innovative emotional safety by fusing academic performance data with a sophisticated multi-signal distress analysis engine.

## 1. Holistic Student Management
The platform provides a 360-degree view of the student by integrating management modules with emotional tracking:
* **Pedagogical Tracking:** Centralized management of grades, attendance, and academic trends to identify declines that may correlate with emotional distress.
* **Institutional Logistics:** Specialized modules for boarding school life, including room assignments and weekend leave request management.
* **Teacher Dashboards:** Targeted alerts for educational staff to provide personalized assistance before a clinical crisis occurs.

## 2. Multi-Signal Distress Analysis Engine
The system analyzes four distinct signals to generate a weighted distress score:
* **Semantic Geometry (WMD):** Uses vector similarity to measure the mathematical distance between dialogue and clinical definitions of distress.
* **Cognitive Entropy:** Analyzes text patterns (using algorithms like Lempel-Ziv) to identify rumination, repetitive thoughts, or chaotic emotional states.
* **Acoustic Intensity & Transcription:** * **Intensity:** Real-time decibel analysis identifies vocal context such as shouting (agitation) or whispering (fear/secrecy).
    * **Transcription:** Microphone listeners transcribe spoken dialogue into text, serving as an additional signal for semantic and entropy processing.
* **Typing Latency:** Analyzes the time delays and hesitation between keystrokes to identify emotional friction or cognitive instability during self-reporting.

## 3. Security & Privacy Infrastructure
To protect sensitive student data, the system implements a robust security layer designed to ensure absolute privacy:
* **Stateless Processing:** The analysis engine operates in a mode where sensitive text is processed in volatile memory and immediately discarded.
* **Privacy-First Architecture:** Ensuring that personal indicators are handled with high-level encryption standards, prioritizing student confidentiality and data integrity.

## Project Roadmap
* **Phase 1: Multi-Signal Prototype (Jan 27):** Implementation of WMD, Entropy, Decibel multipliers, and Frontend Typing Latency.
* **Phase 2: Security & Infrastructure (Feb 20):** Development of the secure data handling layer and volatile RAM management.
* **Phase 3: Institutional Management (March-April):** Database integration for pedagogical tracking and boarding school logistics.
* **Phase 4: Full Integration (May):** Connecting passive analysis results to the final Teacher Dashboard and weekend leave modules.

## Setup
1. **Frontend:** Navigate to `/frontend`, run `npm install`, followed by `npm run dev`.
2. **Backend:** Navigate to `/backend`, install requirements from `requirements.txt`, and run the FastAPI server.
3. **Models:** A pre-trained Hebrew Word2Vec model must be placed in `backend/app/models/he_model_small.bin` (not included in repository due to size).