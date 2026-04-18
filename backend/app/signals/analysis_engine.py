from fastapi import APIRouter, File, UploadFile
from app.schemas import DistressAnalysisRequest
from app.signals.text_entropy import EntropySignal
from app.signals.hebrew_wmd import HebrewWMDSignal
from app.signals.audio_processing import AudioProcessor
from app.signals.typing_latency import TypingLatencySignal

router = APIRouter()

@router.post("/analyze_audio")
async def analyze_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    processor = AudioProcessor()
    audio_result = processor.process_audio(audio_bytes)
    
    if audio_result.get("status") == "error":
        return audio_result
        
    segments = audio_result.get("segments", [])
    
    # Automatically analyze the resulting segments with the distress engine
    request = DistressAnalysisRequest(segments=segments)
    analysis_result = await analyze_all_signals(request)
    
    # Merge the transcription info into the response
    analysis_result["transcription_segments"] = segments
    return analysis_result


@router.post("/analyze_all")
async def analyze_all_signals(request: DistressAnalysisRequest):
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

    # --- SAFETY OVERRIDE ---
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

    return {
        "status": "success",
        "overall_distress_score": overall_score,
        "signals": signals
    }