import numpy as np
from gensim.models import KeyedVectors
from .clinical_lexicon import CLINICAL_WEIGHTS
from .signal_base import DistressSignal


class HebrewWMDSignal(DistressSignal):
    _model = None  # Class level variable to store the model once

    def __init__(self):
        # Only load the model if it hasn't been loaded yet
        if HebrewWMDSignal._model is None:
            print("Loading Hebrew Semantic Brain... Please wait.")
            try:
                # Load the model
                HebrewWMDSignal._model = KeyedVectors.load_word2vec_format(
                    'app/models/he_model_small.bin', binary=True
                )
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Warning: Model not found. Falling back to keyword mode. {e}")

        self._model = HebrewWMDSignal._model

    def get_sentence_vector(self, text):
        """Turns a whole sentence into one 'Average Vector'."""
        if not self._model:
            return None

        words = text.split()
        # Extract vectors for words that exist in the model's vocabulary
        vectors = [self._model[w] for w in words if w in self._model]

        if not vectors:
            return np.zeros(self._model.vector_size)

        # Mathematical mean of all word vectors in the sentence
        return np.mean(vectors, axis=0)

    def analyze(self, data: dict) -> dict:
        text = data.get("text", "")
        decibels = data.get("avg_decibels", 0.0)

        # 1. Fallback Logic: If no model, use basic keyword matching
        if not self._model:
            return self._keyword_fallback(text, decibels)

        # 2. Geometric Semantic Calculation
        student_vec = self.get_sentence_vector(text)
        # Create a 'Master Distress Vector' by averaging lexicon keywords
        clinical_vec = self.get_sentence_vector(" ".join(CLINICAL_WEIGHTS.keys()))

        # 3. Cosine Similarity (The 'Distance' between student and distress)
        # Calculate the dot product divided by the product of the magnitudes
        norm_product = np.linalg.norm(student_vec) * np.linalg.norm(clinical_vec)

        if norm_product == 0:
            base_score = 0.0
        else:
            similarity = np.dot(student_vec, clinical_vec) / norm_product
            base_score = float(np.nan_to_num(similarity))

        # 4. Apply Acoustic multipliers
        multiplier = 1.0
        intensity_label = "Normal"

        if decibels > 75:
            multiplier = 1.4
            intensity_label = "Shouting"
        elif 0 < decibels < 40:
            multiplier = 1.2
            intensity_label = "Whispering"

        final_score = round(min(base_score * multiplier, 1.0), 2)

        return {
            "score": final_score,
            "metadata": {
                "algorithm": "semantic_vector_similarity",
                "intensity_zone": intensity_label,
                "is_vector_based": True,
                "base_score": round(base_score, 2)
            }
        }

    def _keyword_fallback(self, text: str, decibels: float) -> dict:
        """
        A safety net that uses direct keyword matching if the
        semantic model is unavailable.
        """
        words = text.split()
        # Find the maximum weight of any clinical word found in the text
        matched_weights = [CLINICAL_WEIGHTS[w] for w in words if w in CLINICAL_WEIGHTS]

        # If no keywords found, base score is 0
        base_score = max(matched_weights) if matched_weights else 0.0

        # Apply Acoustic multipliers (same logic as geometric mode)
        multiplier = 1.0
        intensity_label = "Normal"
        if decibels > 75:
            multiplier = 1.4
            intensity_label = "Shouting"
        elif 0 < decibels < 40:
            multiplier = 1.2
            intensity_label = "Whispering"

        final_score = round(min(base_score * multiplier, 1.0), 2)

        return {
            "score": final_score,
            "metadata": {
                "algorithm": "keyword_fallback",
                "intensity_zone": intensity_label,
                "is_vector_based": False,
                "reason": "semantic_model_not_loaded"
            }
        }
