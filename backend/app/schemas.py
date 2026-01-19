from pydantic import BaseModel
from typing import List, Optional

class DistressAnalysisRequest(BaseModel):
    text: str
    latencies: Optional[List[int]] = []
    avg_decibels: Optional[float] = 0.0