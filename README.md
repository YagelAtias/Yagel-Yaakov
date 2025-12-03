# Yagel-Yaakov: Personalized Education & Distress Detection Platform

[Work in Progress]

Yagel-Yaakov is a planned system for educational institutions (specifically boarding schools) to monitor and improve student well-being through multi-signal analysis. The goal is to identify early signs of psychological distress using text, audio, and context analysis while maintaining strict data privacy protocols.

## Project Roadmap

### Phase 1: Infrastructure (Current Focus)
- [x] Set up Python Backend (FastAPI) environment
- [x] Set up React Frontend (Vite) environment
- [x] Configure Git & Version Control
- [ ] Connect Frontend to Backend (Basic "Hello World")

### Phase 2: Distress Analysis Engine
- [ ] Geometric Semantics: Implement Word Mover's Distance (WMD) for semantic similarity
- [ ] Compression Analysis: Implement Lempel-Ziv / Entropy algorithms for identifying repetitive patterns
- [ ] Audio Analysis: Implement basic decibel/pitch detection using Librosa

### Phase 3: Security & Data Privacy
Since the system handles sensitive personal and academic data, security is a core priority.
- [ ] Design PII (Personal Identifiable Information) encryption strategy
- [ ] Implement secure authentication for staff vs. students
- [ ] Set up secure database schema

### Phase 4: Interface & Integration
- [ ] Build Teacher Dashboard (React)
- [ ] Visualize distress levels over time
- [ ] Graph-based student placement recommendations

---
Student: Yagel Atias | Advisor: Dr. Shira Zucker