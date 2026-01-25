from pydantic import BaseModel
from typing import List, Optional, Literal

class Segment(BaseModel):
    text: str
    intensity: Literal["whisper", "normal", "shout"]


class DistressAnalysisRequest(BaseModel):
    # Allow either plain text, segments, or both (for backward compatibility)
    text: Optional[str] = ""
    segments: Optional[List[Segment]] = None
    latencies: Optional[List[int]] = []
    avg_decibels: Optional[float] = 0.0