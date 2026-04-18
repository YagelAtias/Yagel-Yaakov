import numpy as np
from .signal_base import DistressSignal

class TypingLatencySignal(DistressSignal):
    def analyze(self, data: dict) -> dict:
        """
        Analyzes the millisecond delays between keystrokes to detect emotional friction.
        High variance and frequent long pauses indicate hesitation, cognitive load, or distress.
        """
        latencies = data.get("latencies", [])
        
        # We need a minimum number of keystrokes to establish a baseline typing speed
        if not latencies or len(latencies) < 10:
            return {"score": 0.0, "metadata": {"skip_reason": "not_enough_keystrokes"}}
            
        arr = np.array(latencies)
        
        # Filter out abnormally long pauses (e.g., someone walking away from the keyboard for 5 minutes)
        # We cap legitimate "hesitation" at 10,000 ms (10 seconds)
        arr = arr[arr < 10000]
        
        if len(arr) < 10:
            return {"score": 0.0, "metadata": {"skip_reason": "filtered_too_few_keystrokes"}}
        
        avg_delay = np.mean(arr)
        variance = np.std(arr)
        
        # A "hesitation pause" is defined as any delay longer than 1500ms
        long_pauses = np.sum(arr > 1500)
        pause_ratio = long_pauses / len(arr)
        
        # --- Scoring Logic ---
        # 1. Delay Score: 200ms is fast/normal, 800ms+ is sluggish/depressed
        delay_score = min(max((avg_delay - 200) / 600, 0.0), 1.0)
        
        # 2. Variance Score: 100ms is a steady rhythm, 500ms+ is erratic/anxious
        variance_score = min(max((variance - 100) / 400, 0.0), 1.0)
        
        # 3. Pause Score: 0% is fluent, 10%+ is highly hesitant/frozen
        pause_score = min(pause_ratio / 0.10, 1.0)
        
        # We weight hesitation pauses the heaviest, as freezing is a strong clinical indicator
        final_score = (0.2 * delay_score) + (0.3 * variance_score) + (0.5 * pause_score)
        
        return {
            "score": round(float(final_score), 2),
            "metadata": {
                "algorithm": "latency_hesitation_analyzer",
                "avg_delay_ms": round(float(avg_delay), 2),
                "variance": round(float(variance), 2),
                "long_pauses_count": int(long_pauses),
                "pause_ratio": round(float(pause_ratio), 3)
            }
        }
