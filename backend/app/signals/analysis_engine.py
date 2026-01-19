from fastapi import APIRouter
from app.schemas import DistressAnalysisRequest
from app.signals.text_entropy import EntropySignal
from app.signals.hebrew_wmd import HebrewWMDSignal

router = APIRouter()

@router.post("/analyze_all")
async def analyze_all_signals(request: DistressAnalysisRequest):
    # Initialize both specialized engines
    entropy_engine = EntropySignal()
    wmd_engine = HebrewWMDSignal()

    data = request.model_dump()

    # Run analyses
    entropy_res = entropy_engine.analyze(data)
    wmd_res = wmd_engine.analyze(data)

    # We take the maximum of the two as the immediate indicator
    overall_score = max(entropy_res["score"], wmd_res["score"])

    return {
        "status": "success",
        "overall_distress_score": overall_score,
        "signals": {
            "entropy": entropy_res,
            "semantic_wmd": wmd_res
        }
    }