from importlib.metadata import metadata

import numpy as np
from .clinical_lexicon import CLINICAL_WEIGHTS
from .signal_base import DistressSignal


class HebrewWMDSignal(DistressSignal):
    def analyze(self, data: dict) -> dict:
        """
        Calculates semantic distress and applies intensity multipliers.
        """
        text = data.get("text", "")
        decibels = data.get("avg_decibels", 0.0)

        # Split text into words.
        words = text.split()
        if not words:
            return {"score": 0.0, "metadata": {"reason": "no_text"}}

        # Check how many words from the text are in our clinical dictionary
        score_sum = 0
        matches = 0
        for word in words:
            if word in CLINICAL_WEIGHTS:
                score_sum += CLINICAL_WEIGHTS[word]
                matches += 1

        # Calculate base semantic score
        base_score = min(score_sum / max(len(words), 1), 1.0)

        # We treat decibels as a clinical 'booster' for the distress score
        multiplier = 1.0
        intensity_label = "Normal"

        if decibels > 75:
            multiplier = 1.4  # Boost for shouting
            intensity_label = "Shouting"
        elif 0 < decibels < 40:
            multiplier = 1.2  # Boost for whispering
            intensity_label = "Whispering"

        # Calculate final weighted score
        final_score = round(min(base_score * multiplier, 1.0), 2)

        return {
            "score": final_score,
            "metadata": {
                "algorithm": "relaxed_hebrew_wmd",
                "base_semantic_score": round(base_score, 2),
                "intensity_multiplier": multiplier,
                "intensity_zone": intensity_label,
                "clinical_matches": matches
            }
        }
