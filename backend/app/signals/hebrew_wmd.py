import numpy as np
from gensim.models import KeyedVectors
from .clinical_lexicon import CLINICAL_WEIGHTS
from .signal_base import DistressSignal
from typing import List, Dict, Tuple

# Intensity mapping used across the engine
INTENSITY_TO_MULTIPLIER = {
    "whisper": 1.2,
    "normal": 1.0,
    "shout": 1.4,
}

# Minimal Hebrew stopword set for prototype
HE_STOPWORDS = {
    "של", "על", "אל", "אם", "עם", "אך", "גם", "לא", "אין", "כן",
    "אני", "אתה", "את", "הוא", "היא", "הם", "הן", "זה", "זו", "מה", "מי", "כמו", "מאוד"
}

# Approved clinical topics registry (prototype)
CLINICAL_TOPICS: List[Dict] = [
    {"id": "sadness", "weight": 0.6, "words": ["עצוב", "עצובה", "דכדוך", "עצבות", "בוכה", "לב שבור", "כואב לי", "מדוכא", "מדוכאת"]},
    {"id": "hopelessness", "weight": 0.9, "words": ["ייאוש", "אין תקווה", "חסר סיכוי", "חסרת סיכוי", "למה לנסות", "אבוד", "אבודה", "חסר תוחלת", "נגמר לי"]},
    {"id": "rumination", "weight": 0.7, "words": ["חושב שוב ושוב", "חוזר", "נתקע במחשבות", "טוחן", "לופ", "הראש לא מפסיק", "מחשבות טורדניות", "לא נרגע"]},
    {"id": "withdrawal", "weight": 0.6, "words": ["נסוג", "סגור", "סגורה", "מתרחק", "מתרחקת", "לבד", "לא רוצה לראות אף אחד", "התבודדות", "מנותק", "מנותקת"]},
    {"id": "guilt", "weight": 0.6, "words": ["אשם", "אשמה", "טעות שלי", "אשמתי", "בגללי", "יכולתי למנוע", "חרטה", "מכה על חטא"]},
    {"id": "fatigue", "weight": 0.5, "words": ["עייפות", "אין כוח", "מותש", "מותשת", "גמור", "גמורה", "שחוק", "שחוקה", "אין אנרגיה", "כבד לי"]},
    {"id": "self_harm_ideas", "weight": 0.95, "words": ["מוות", "לא לחיות", "להיעלם", "רוצה לגמור עם זה", "די", "סוף", "לחדול", "קץ"]},
    {"id": "anxiety_agitation", "weight": 0.7, "words": ["חרדה", "לחץ", "חוסר מנוחה", "דפיקות לב", "מחנק", "משתגע", "משתגעת", "מתוח", "מתוחה", "קצר בנשימה"]},
    {"id": "insomnia", "weight": 0.6, "words": ["נדודי שינה", "לא ישן", "לא ישנה", "לא הצלחתי לישון", "הפוך", "הפוכה", "ער כל הלילה", "מסתכל על התקרה"]},
]


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
        """Turn a full sentence into one average vector."""
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
        # Segment-aware path (preferred)
        segments = data.get("segments")
        if segments:
            return self._analyze_segments(segments)

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

    # Segment based custom topics scoring (clinical WMD idea)

    def _analyze_segments(self, segments: List[Dict]) -> Dict:
        """Score a list of segments, each with text and intensity, using topic matching.
        Returns the overall meaning score and a per segment breakdown.
        """
        # Fallback if no model: use keyword-based evaluation per segment
        if not self._model:
            return self._segments_keyword_fallback(segments)

        # Prepare topic vectors from the words that exist in the model
        topic_centroids = self._build_topic_centroids()
        if not topic_centroids:
            # If no centroids could be built, fallback to keyword
            return self._segments_keyword_fallback(segments)

        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        for idx, seg in enumerate(segments):
            seg_text = (seg.get("text") or "").strip()
            if not seg_text:
                continue

            tokens = self._tokenize(seg_text)
            tokens = [t for t in tokens if t not in HE_STOPWORDS and t in self._model]
            seg_len = max(1, len(seg_text))

            if not tokens:
                # No useful words found in the model
                base_score = 0.0
                method = "fallback_empty"
                base_distance = 1.0
                matched = []
            else:
                # Simple matching distance between sentence words and topic vectors
                base_distance, matched = self._greedy_assignment_distance(tokens, topic_centroids)
                # Turn distance into a score from 0 to 1
                base_score = 1.0 / (1.0 + base_distance)
                method = "cad_greedy"

            intensity = (seg.get("intensity") or "normal").lower()
            multiplier = INTENSITY_TO_MULTIPLIER.get(intensity, 1.0)
            weighted_score = min(base_score * multiplier, 1.0)

            segment_scores.append({
                "index": idx,
                "intensity": intensity,
                "multiplier": multiplier,
                "base_distance": round(base_distance, 3),
                "base": round(base_score, 3),
                "weighted": round(weighted_score, 3),
                "method": method,
                "matched": matched[:5]  # cap for brevity
            })

            total_len += seg_len
            weighted_sum += weighted_score * seg_len

        overall = round(weighted_sum / max(1, total_len), 2)

        return {
            "score": overall,
            "metadata": {
                "algorithm": "custom_wmd_cad",
                "is_vector_based": True,
                "segment_scores": segment_scores
            }
        }

    def _segments_keyword_fallback(self, segments: List[Dict]) -> Dict:
        """Keyword only per segment evaluation if vectors are unavailable."""
        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        # Build a simple keyword weight list from topics and the existing lexicon
        kw_weights = dict(CLINICAL_WEIGHTS)
        for topic in CLINICAL_TOPICS:
            w = topic.get("weight", 0.5)
            for word in topic.get("words", []):
                kw_weights[word] = max(kw_weights.get(word, 0.0), float(w))

        for idx, seg in enumerate(segments):
            seg_text = (seg.get("text") or "").strip()
            if not seg_text:
                continue
            tokens = self._tokenize(seg_text)
            seg_len = max(1, len(seg_text))
            matched_weights = [kw_weights[t] for t in tokens if t in kw_weights]
            base = max(matched_weights) if matched_weights else 0.0

            intensity = (seg.get("intensity") or "normal").lower()
            multiplier = INTENSITY_TO_MULTIPLIER.get(intensity, 1.0)
            weighted = min(base * multiplier, 1.0)

            segment_scores.append({
                "index": idx,
                "intensity": intensity,
                "multiplier": multiplier,
                "base": round(base, 3),
                "weighted": round(weighted, 3),
                "method": "keyword_fallback"
            })

            total_len += seg_len
            weighted_sum += weighted * seg_len

        overall = round(weighted_sum / max(1, total_len), 2)
        return {
            "score": overall,
            "metadata": {
                "algorithm": "keyword_fallback_segments",
                "is_vector_based": False,
                "segment_scores": segment_scores,
                "reason": "semantic_model_not_loaded_or_no_centroids"
            }
        }

    # ------------------------ Helpers ------------------------ #

    def _tokenize(self, text: str) -> List[str]:
        # Split by spaces and remove common punctuation
        for ch in [",", ".", "!", "?", ":", ";", "(", ")", "[", "]", "\n"]:
            text = text.replace(ch, " ")
        tokens = text.split()
        return [t.strip() for t in tokens if t.strip()]

    def _build_topic_centroids(self) -> Dict[str, Tuple[List[str], np.ndarray, float]]:
        """Build topic vectors from known words in the model.
        Returns a map: topic_id -> (words_in_vocab, centroid_vector, topic_weight).
        """
        centroids = {}
        for topic in CLINICAL_TOPICS:
            words = [w for w in topic.get("words", []) if w in self._model]
            if not words:
                continue
            vecs = [self._model[w] for w in words]
            centroid = np.mean(vecs, axis=0)
            centroids[topic["id"]] = (words, centroid, float(topic.get("weight", 0.5)))
        return centroids

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _greedy_assignment_distance(self, tokens: List[str], centroids: Dict[str, Tuple[List[str], np.ndarray, float]]):
        """Simple one to one matching cost between word vectors and topic vectors.
        Returns the average distance and a small list of matches for display.
        """
        # Load token vectors once
        token_vecs = {t: self._model[t] for t in tokens}
        topics_left = set(centroids.keys())
        pairs = []  # for metadata

        # Check if the sentence has negation words
        has_negation = any(t in {"לא", "אין", "בלי"} for t in tokens)

        # For each word pick the closest topic. Then match the best pairs first.
        candidates = []
        for t in tokens:
            best_topic = None
            best_cost = 1.0
            for tid, (_, cvec, sev) in centroids.items():
                sim = self._cosine(token_vecs[t], cvec)
                # Base distance
                cost = 1.0 - sim
                # Lower the cost a bit for more severe topics so they count more
                cost *= (1.0 - 0.5 * sev)
                # If negation words exist, push the cost up slightly
                if has_negation:
                    cost += 0.05
                if cost < best_cost:
                    best_cost = cost
                    best_topic = tid
            candidates.append((t, best_topic, best_cost))

        # Sort by lowest cost first
        candidates.sort(key=lambda x: x[2])
        total_cost = 0.0
        matched = 0
        for t, tid, cost in candidates:
            if tid is None:
                continue
            if tid not in topics_left:
                continue
            topics_left.remove(tid)
            total_cost += max(0.0, min(2.0, cost))
            matched += 1
            pairs.append({"token": t, "topic": tid, "cost": round(float(cost), 3)})

        if matched == 0:
            return 1.0, []
        return total_cost / matched, pairs

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
