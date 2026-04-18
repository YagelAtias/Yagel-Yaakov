import zlib
from fastapi import APIRouter, HTTPException
from .signal_base import DistressSignal

router = APIRouter()

# CONFIGURATION CONSTANTS
MIN_TEXT_LENGTH = 30  # Text shorter than this is unreliable for compression
MAX_SEVERITY_RATIO = 3.0  # The ratio that equals "100% score" (1.0)
RUMINATION_THRESHOLD = 1.5  # The ratio where the text is officially flagged as "is_repetitive"


class EntropySignal(DistressSignal):
    def analyze(self, data: dict) -> dict:
        """
        Analyzes text entropy using the zlib compression ratio.
        High ratio = Repetitive/Obsessive text (Rumination).
        Low ratio = Chaotic text.
        """
        text = data.get("text", "")

        # Input test.
        if not text or not isinstance(text, str):
            return {"score": 0.0, "metadata": {"error": "Invalid Input"}}

        if len(text) < MIN_TEXT_LENGTH:
            return {"score": 0.0, "metadata": {"skip_reason": "text_too_short"}}

        # Type conversion to bytes and compression using Deflate algorithm (LZ77 and Huffman Coding)
        encoded_data = text.encode("utf-8")
        compressed_data = zlib.compress(encoded_data)

        original_len = len(encoded_data)
        compressed_len = len(compressed_data)

        # Prevent division by zero
        if compressed_len == 0:
            return {"score": 0.0,
                    "metadata": {}}

        # The larger this ratio is -> The lower the entropy -> Higher "Obsession" level.
        compression_ratio = original_len / compressed_len

        # Calculate score (capped at 1.0)
        normalized_score = min(compression_ratio / MAX_SEVERITY_RATIO, 1.0)

        return {
            "score": round(normalized_score, 2),
            "metadata": {
                "algorithm": "zlib_entropy",
                "compression_ratio": round(compression_ratio, 2),
                "original_length": original_len,
                "is_repetitive": compression_ratio > RUMINATION_THRESHOLD
            }
        }
