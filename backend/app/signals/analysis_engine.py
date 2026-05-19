from fastapi import APIRouter, File, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from app.schemas import DistressAnalysisRequest
from app.signals.text_entropy import EntropySignal
from app.signals.hebrew_wmd import HebrewWMDSignal
from app.signals.audio_processing import AudioProcessor
from app.signals.typing_latency import TypingLatencySignal

# Database imports
from app.db import database, models
from app.security.encryption import encrypt_text
from app.services.push_service import PushNotificationService

router = APIRouter()

@router.post("/analyze_audio")
async def analyze_audio(
    file: UploadFile = File(...), 
    student_id: int = Form(1),
    db: Session = Depends(database.get_db)
):
    audio_bytes = await file.read()
    processor = AudioProcessor()
    audio_result = processor.process_audio(audio_bytes)
    
    if audio_result.get("status") == "error":
        return audio_result
        
    segments = audio_result.get("segments", [])
    
    # Automatically analyze the resulting segments with the distress engine
    request = DistressAnalysisRequest(segments=segments, student_id=student_id)
    analysis_result = await analyze_all_signals(request, db=db)
    
    # Merge the transcription info into the response
    analysis_result["transcription_segments"] = segments
    return analysis_result


@router.post("/analyze_all")
async def analyze_all_signals(
    request: DistressAnalysisRequest,
    db: Session = Depends(database.get_db)
):
    # Initialize signal processing engines
    entropy_engine = EntropySignal()
    wmd_engine = HebrewWMDSignal()
    latency_engine = TypingLatencySignal()

    req = request.model_dump()

    segments = req.get("segments") or []

    # Prepare inputs: Entropy needs full context, while WMD needs granular segments
    if segments:
        # Join segments for global entropy assessment
        full_text = " ".join([s.get("text", "") for s in segments if s.get("text")])
        # Pass structured segments for per-segment semantic scoring
        semantic_input = {
            "segments": segments,
            "latencies": req.get("latencies") or []
        }
        entropy_input = {"text": full_text}
    else:
        # Fallback for raw text input (legacy support)
        # The WMD engine handles internal sentence splitting
        semantic_input = {
            "text": req.get("text", ""),
            "avg_decibels": req.get("avg_decibels", 0.0),
            "latencies": req.get("latencies") or []
        }
        entropy_input = {"text": req.get("text", "")}

    # Execute analysis
    entropy_res = entropy_engine.analyze(entropy_input)
    wmd_res = wmd_engine.analyze(semantic_input)
    
    latency_input = {"latencies": req.get("latencies") or []}
    latency_res = latency_engine.analyze(latency_input)

    # Calculate acoustic intensity distribution (if segments exist)
    acoustic_signal = None
    if segments:
        total = len([s for s in segments if s.get("text")]) or 1
        counts = {"whisper": 0, "normal": 0, "shout": 0}
        for s in segments:
            label = (s.get("intensity") or "normal").lower()
            if label in counts:
                counts[label] += 1
        distribution = {k: round(v / total, 2) for k, v in counts.items()}
        # Score reflects the ratio of abnormal intensity (whisper/shout)
        non_normal = (counts["whisper"] + counts["shout"]) / total
        acoustic_signal = {
            "score": round(non_normal, 2),
            "metadata": {
                "distribution": distribution,
                "mapping": {"whisper": 1.2, "normal": 1.0, "shout": 1.4}
            }
        }

    # Signal Fusion: Adjust weights if typing latency data is valid
    latency_score = latency_res.get("score", 0.0)
    if latency_score > 0:
        fused = 0.5 * (wmd_res.get("score", 0.0)) + 0.3 * (entropy_res.get("score", 0.0)) + 0.2 * latency_score
    else:
        fused = 0.6 * (wmd_res.get("score", 0.0)) + 0.4 * (entropy_res.get("score", 0.0))
        
    overall_score = min(fused, 1.0)

    # SAFETY OVERRIDE
    # Check for critical markers (e.g., self-harm indications) from the semantic engine.
    # Policy: Prefer false positives to ensure immediate safety.
    try:
        has_critical = bool(wmd_res.get("metadata", {}).get("has_critical_alert"))
    except Exception:
        has_critical = False

    if has_critical:
        # Immediate escalation to high distress (0.95) upon critical detection,
        # overriding any conflicting low signals from other engines.
        overall_score = max(overall_score, 0.95)

    overall_score = round(overall_score, 2)

    signals = {
        "entropy": entropy_res,
        "semantic_wmd": wmd_res
    }
    
    if latency_res.get("score", 0.0) > 0 or latency_res.get("metadata", {}).get("skip_reason") is None:
         signals["typing_latency"] = latency_res
         
    if acoustic_signal is not None:
        signals["acoustic"] = acoustic_signal

    # PHASE 2: DATABASE PERSISTENCE & ENCRYPTION
    # 1. Ensure a dummy student exists for UI backward compatibility
    student = db.query(models.Student).filter(models.Student.id == request.student_id).first()
    if not student:
        dummy_org = db.query(models.Organization).first()
        if not dummy_org:
            dummy_org = models.Organization(name="Demo School")
            db.add(dummy_org)
            db.commit()
            db.refresh(dummy_org)
            
        student = models.Student(
            id=request.student_id,
            first_name="Anonymous", 
            last_name="Student", 
            organization_id=dummy_org.id
        )
        db.add(student)
        db.commit()

    # 2. Extract raw text for encryption
    if segments:
        formatted_text_parts = []
        for seg in segments:
            for w in seg.get("words", []):
                word = w.get("word", "")
                intensity = w.get("intensity", "normal")
                if intensity == "shout":
                    formatted_text_parts.append(f"**{word}**")
                elif intensity == "whisper":
                    formatted_text_parts.append(f"*{word}*")
                else:
                    formatted_text_parts.append(word)
        raw_text = " ".join(formatted_text_parts)
    else:
        raw_text = req.get("text", "")
    
    # 3. MILITARY-GRADE ENCRYPTION: Encrypt the text before it touches the hard drive
    encrypted_text = encrypt_text(raw_text)
    
    # 4. Save the secured log to the database
    new_log = models.DistressLog(
        student_id=request.student_id,
        encrypted_raw_text=encrypted_text,
        overall_score=overall_score,
        has_critical_alert=has_critical,
        signals_metadata=signals
    )
    db.add(new_log)
    db.commit()

    # 5. PUSH NOTIFICATIONS: Alert staff if distress is high
    if has_critical or overall_score >= 0.8:
        student_name = f"{student.first_name} {student.last_name}"
        alert_reason = "התראת מצוקה קריטית" if has_critical else "ציון מצוקה גבוה זוהה"
        PushNotificationService.send_to_staff_for_student(
            student_id=request.student_id,
            title=f"🚨 התראת DistressEngine: {student_name}",
            body=f"{alert_reason}. המערכת זיהתה רמת מצוקה של {int(overall_score * 10)}/10. אנא בדוק את יומן השיחות באופן מיידי.",
            db_session=db
        )

    return {
        "status": "success",
        "overall_distress_score": overall_score,
        "signals": signals
    }