from fastapi import APIRouter
from app.schemas import DistressAnalysisRequest
from app.signals.text_entropy import EntropySignal
from app.signals.hebrew_wmd import HebrewWMDSignal

router = APIRouter()

@router.post("/analyze_all")
async def analyze_all_signals(request: DistressAnalysisRequest):
    # Set up the analysis parts
    entropy_engine = EntropySignal()
    wmd_engine = HebrewWMDSignal()

    req = request.model_dump()

    segments = req.get("segments") or []

    # Build one big text for entropy and set up input for the meaning check
    if segments:
        # Concatenate segments for entropy calculation
        full_text = " ".join([s.get("text", "") for s in segments if s.get("text")])
        # Send the segments to the meaning check so it can score each one
        semantic_input = {
            "segments": segments,
            "latencies": req.get("latencies") or []
        }
        entropy_input = {"text": full_text}
    else:
        # Single text path (works with older requests)
        semantic_input = {
            "text": req.get("text", ""),
            "avg_decibels": req.get("avg_decibels", 0.0),
            "latencies": req.get("latencies") or []
        }
        entropy_input = {"text": req.get("text", "")}

    # Run the checks
    entropy_res = entropy_engine.analyze(entropy_input)
    wmd_res = wmd_engine.analyze(semantic_input)

    # Summarize how many segments are whisper, normal, or shout
    acoustic_signal = None
    if segments:
        total = len([s for s in segments if s.get("text")]) or 1
        counts = {"whisper": 0, "normal": 0, "shout": 0}
        for s in segments:
            label = (s.get("intensity") or "normal").lower()
            if label in counts:
                counts[label] += 1
        distribution = {k: round(v / total, 2) for k, v in counts.items()}
        # Display score: share of segments that are not normal
        non_normal = (counts["whisper"] + counts["shout"]) / total
        acoustic_signal = {
            "score": round(non_normal, 2),
            "metadata": {
                "distribution": distribution,
                "mapping": {"whisper": 1.2, "normal": 1.0, "shout": 1.4}
            }
        }

    # Combine the meaning and repetition scores and cap at 1.0
    fused = 0.6 * (wmd_res.get("score", 0.0)) + 0.4 * (entropy_res.get("score", 0.0))
    overall_score = min(fused, 1.0)

    # Critical override: if any segment has a critical alert (e.g., self-harm),
    # raise the overall score so the main gauge signals urgency during demo.
    try:
        has_critical = bool(wmd_res.get("metadata", {}).get("has_critical_alert"))
    except Exception:
        has_critical = False
    if has_critical:
        # Strong override for the prototype demo; adjust to 0.9 if you prefer softer.
        overall_score = max(overall_score, 0.95)
    overall_score = round(overall_score, 2)

    signals = {
        "entropy": entropy_res,
        "semantic_wmd": wmd_res
    }
    if acoustic_signal is not None:
        signals["acoustic"] = acoustic_signal

    return {
        "status": "success",
        "overall_distress_score": overall_score,
        "signals": signals
    }