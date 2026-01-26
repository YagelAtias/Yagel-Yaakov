import os
import numpy as np
from pathlib import Path
from gensim.models import KeyedVectors
from .clinical_lexicon import CLINICAL_WEIGHTS
from .signal_base import DistressSignal
from typing import List, Dict, Tuple

# How we map the voice label to a numeric multiplier
INTENSITY_TO_MULTIPLIER = {
    "whisper": 1.2,
    "normal": 1.0,
    "shout": 1.4,
}

# Minimum cosine similarity for a token→topic to be considered a valid match
# Raised to avoid false positives on neutral academic text
SIM_MIN = 0.50

# Small Hebrew stopword list (good enough for the demo)
HE_STOPWORDS = {
    "של", "על", "אל", "אם", "עם", "אך", "גם", "לא", "אין", "כן",
    "אני", "אתה", "את", "הוא", "היא", "הם", "הן", "זה", "זו", "מה", "מי", "כמו", "מאוד"
}

# Clinical topics we look for (prototype list)
CLINICAL_TOPICS: List[Dict] = [
    {"id": "sadness", "weight": 0.6, "words": ["עצוב", "עצובה", "דכדוך", "עצבות", "בוכה", "לב שבור", "כואב לי", "מדוכא", "מדוכאת"]},
    {"id": "hopelessness", "weight": 0.9, "words": ["ייאוש", "אין תקווה", "חסר סיכוי", "חסרת סיכוי", "למה לנסות", "אבוד", "אבודה", "חסר תוחלת", "נגמר לי"]},
    {"id": "rumination", "weight": 0.7, "words": ["חושב שוב ושוב", "חוזר", "נתקע במחשבות", "טוחן", "לופ", "הראש לא מפסיק", "מחשבות טורדניות", "לא נרגע"]},
    {"id": "withdrawal", "weight": 0.6, "words": ["נסוג", "סגור", "סגורה", "מתרחק", "מתרחקת", "לבד", "לא רוצה לראות אף אחד", "התבודדות", "מנותק", "מנותקת"]},
    {"id": "guilt", "weight": 0.6, "words": ["אשם", "אשמה", "טעות שלי", "אשמתי", "בגללי", "יכולתי למנוע", "חרטה", "מכה על חטא"]},
    {"id": "fatigue", "weight": 0.5, "words": ["עייפות", "אין כוח", "מותש", "מותשת", "גמור", "גמורה", "שחוק", "שחוקה", "אין אנרגיה", "כבד לי"]},
    {"id": "self_harm_ideas", "weight": 0.95, "words": [
        "מוות", "למות", "לא לחיות", "להיעלם", "קץ",
        "להתאבד", "התאבדות", "אתאבד", "להרוג את עצמי",
        "רוצה לגמור עם זה", "לחדול"
    ]},
    {"id": "anxiety_agitation", "weight": 0.7, "words": ["חרדה", "לחץ", "חוסר מנוחה", "דפיקות לב", "מחנק", "משתגע", "משתגעת", "מתוח", "מתוחה", "קצר בנשימה"]},
    {"id": "insomnia", "weight": 0.6, "words": ["נדודי שינה", "לא ישן", "לא ישנה", "לא הצלחתי לישון", "הפוך", "הפוכה", "ער כל הלילה", "מסתכל על התקרה"]},
]

# Human-friendly Hebrew labels for topic ids (for UI display)
TOPIC_LABELS: Dict[str, str] = {
    "sadness": "עצבות",
    "hopelessness": "ייאוש",
    "rumination": "רומינציה",
    "withdrawal": "הסתגרות",
    "guilt": "אשמה",
    "fatigue": "עייפות",
    "self_harm_ideas": "מחשבות על פגיעה עצמית",
    "anxiety_agitation": "חרדה/אי שקט",
    "insomnia": "קשיי שינה",
}

# Topic-specific helpers
# Anchors help nudge clear sleep complaints toward insomnia (and away from self-harm)
INSOMNIA_ANCHORS = {"לישון", "שינה", "ישנתי", "נדודי", "לילה"}
SELF_HARM_ANCHORS = {"מוות", "למות", "להיעלם", "קץ", "להתאבד", "התאבדות", "אתאבד", "להרוג", "להרוג את עצמי", "לא לחיות"}
# Generic tokens to ignore when building the self-harm centroid (too broad on their own)
SELF_HARM_IGNORE = {"די", "סוף"}
ANXIETY_ANCHORS = {"חרדה", "לחץ", "לחוצה", "לחוץ", "בלחץ", "מתוח"}
HOPELESSNESS_ANCHORS = {"ייאוש", "מיואש", "מיואשת", "אבוד", "אבודה"}
RUMINATION_ANCHORS = {"שוב", "שוב ושוב", "חוזר", "חוזרת", "חוזרים", "לופ", "טוחן", "טוחנת"}
GUILT_ANCHORS = {"אשמה", "אשם", "אשמתי"}

# Words we want to ignore completely for matching (neutral school/scheduling terms)
NEUTRAL_IGNORE = {
    "מבחן", "בחינה", "בגרות",
    "ספריה", "ספרייה",
    "ללמוד", "לימוד", "לומד", "לומדת",
    "מחר", "היום", "מחרתיים",
    "יש",
    "אלך", "אילך", "אעלה", "אבוא"
}

def _normalize_token(tok: str) -> str:
    """Light Hebrew normalization: strip common one-letter prefixes and normalize forms.
    This is intentionally simple for the prototype.
    """
    if not tok:
        return tok
    # Strip common prefixes (single letters)
    # e.g., 'בלחץ' -> 'לחץ', 'והרגשתי' -> 'הרגשתי'
    if len(tok) > 1 and tok[0] in {"ב", "כ", "ל", "ה", "ו", "מ", "ש"}:
        tok = tok[1:]
    # Common end forms to base forms (very light touch)
    repl = {
        "ישנה": "שינה",
        "ישנתי": "ישנתי",
        "לחוצה": "לחוץ",
        "מיואשת": "מיואש",
    }
    tok = repl.get(tok, tok)
    return tok


class HebrewWMDSignal(DistressSignal):
    _model = None  # Class level variable to store the model once
    _model_path: str | None = None

    def __init__(self):
        # Load the model once (first use)
        if HebrewWMDSignal._model is None:
            print("Loading Hebrew semantic model... please wait.")
            # We look in a few simple places. HE_MODEL_PATH can be a folder or a file.
            env_path = os.environ.get("HE_MODEL_PATH")
            try:
                project_root = Path(__file__).resolve().parents[3]
            except Exception:
                project_root = Path.cwd()

            model_folders = []  # folders that may contain words_list + words_vectors
            model_files = []    # explicit Word2Vec text files (.txt)
            if env_path:
                p_env = Path(env_path)
                p_env = p_env if p_env.is_absolute() else (project_root / p_env)
                if p_env.is_dir():
                    model_folders.append(p_env)
                else:
                    model_files.append(p_env)

            models_dir = project_root / "models"
            model_folders.append(models_dir)

            # Also look under backend/app/models for standard folders from the repo
            backend_models_dir = project_root / "backend" / "app" / "models"
            wiki_dir = backend_models_dir / "wiki-w2v"
            twitter_dir = backend_models_dir / "twitter-w2v"
            # Prefer Wiki over Twitter; skip POS variant by default
            if wiki_dir.exists():
                model_folders.append(wiki_dir)
            if twitter_dir.exists():
                model_folders.append(twitter_dir)
            # Common filenames inside models dir (Word2Vec text)
            model_files.append(models_dir / "he_model_small.txt")

            model_loaded = False
            last_error = None
            # Try a folder with words_list + words_vectors first
            for d in model_folders:
                try:
                    model = self._try_load_from_np_txt(d)
                    if model is None:
                        continue
                    HebrewWMDSignal._model = model
                    try:
                        HebrewWMDSignal._model.fill_norms(force=True)
                    except Exception:
                        pass
                    print(f"Semantic model loaded from: {d}")
                    HebrewWMDSignal._model_path = str(d)
                    model_loaded = True
                    break
                except Exception as e:
                    last_error = e
                    continue

            # Then try explicit files (.txt)
            for p in ([] if model_loaded else model_files):
                try:
                    if not p.exists():
                        continue
                    model = self._try_load_any(str(p))
                    if model is None:
                        continue
                    HebrewWMDSignal._model = model
                    try:
                        HebrewWMDSignal._model.fill_norms(force=True)
                    except Exception:
                        pass
                    print(f"Semantic model loaded from: {p}")
                    HebrewWMDSignal._model_path = str(p)
                    model_loaded = True
                    break
                except Exception as e:
                    last_error = e
                    continue

            if not model_loaded:
                msg = "Model not loaded. Using keyword fallback."
                if last_error:
                    msg += f" Last error: {last_error}"
                print(f"Warning: {msg}")
                HebrewWMDSignal._model_path = None

        self._model = HebrewWMDSignal._model

    def _try_load_any(self, path: str):
        """Load vectors from a Word2Vec text file (.txt). Returns KeyedVectors or None."""
        p = Path(path)
        if not p.exists():
            return None
        suf = p.suffix.lower()
        if suf == ".txt":
            return KeyedVectors.load_word2vec_format(str(p), binary=False)
        # Unknown extension
        return None

    def _try_load_from_np_txt(self, directory: Path):
        """Build vectors from a folder that contains a words list and a vectors matrix.
        Supports common names from the Bar‑Ilan repo:
        - words list:  words_list.txt | words_list | words.txt | words_list.npy
        - vectors:     words_vectors.npy | words_vectors | vectors.npy
        Returns KeyedVectors or None.
        """
        # Resolve candidate files for words
        word_candidates = [
            directory / "words_list.txt",
            directory / "words_list",
            directory / "words.txt",
            directory / "words_list.npy",
            directory / "words.npy",
        ]
        vec_candidates = [
            directory / "words_vectors.npy",
            directory / "words_vectors",
            directory / "vectors.npy",
        ]

        words = None
        vecs = None

        # Find a words file we can read
        for wp in word_candidates:
            if not wp.exists():
                continue
            if wp.suffix.lower() == ".npy" or wp.name.endswith("words_list"):  # allow npy or extensionless numpy
                try:
                    arr = np.load(str(wp), allow_pickle=True)
                    # Ensure python strings
                    words = [w if isinstance(w, str) else str(w) for w in arr.tolist()]
                    break
                except Exception:
                    continue
            else:
                try:
                    with open(wp, "r", encoding="utf-8") as f:
                        words = [line.strip() for line in f if line.strip()]
                    break
                except Exception:
                    continue

        # Find a vectors file we can read
        for vp in vec_candidates:
            if not vp.exists():
                continue
            try:
                vecs = np.load(str(vp))
                break
            except Exception:
                continue

        if words is None or vecs is None:
            return None
        if len(words) != vecs.shape[0]:
            raise ValueError(
                f"words_list and words_vectors size mismatch: {len(words)} vs {vecs.shape[0]}"
            )

        kv = KeyedVectors(vector_size=vecs.shape[1])
        kv.add_vectors(words, vecs)
        return kv

    def get_sentence_vector(self, text):
        """Turn a sentence into one average vector (ignores tokens we can't vectorize)."""
        if not self._model:
            return None

        words = text.split()
        # Extract vectors for tokens; for fastText, OOV tokens are supported via subword vectors
        vectors = []
        for w in words:
            try:
                vectors.append(self._model[w])
            except Exception:
                continue

        if not vectors:
            return np.zeros(self._model.vector_size)

        # Mathematical mean of all word vectors in the sentence
        return np.mean(vectors, axis=0)

    def analyze(self, data: dict) -> dict:
        # If we get segments (preferred path)
        segments = data.get("segments")
        if segments:
            return self._analyze_segments(segments)

        # Text-only path: analyse as a single segment with intensity derived from decibels
        text = data.get("text", "")
        decibels = data.get("avg_decibels", 0.0)

        # Map decibels to an intensity label (whisper/normal/shout)
        if decibels > 75:
            intensity = "shout"
        elif 0 < float(decibels) < 40:
            intensity = "whisper"
        else:
            intensity = "normal"

        pseudo_segments = [{"text": text, "intensity": intensity}]

        # If no model, delegate to keyword fallback (segment-aware)
        if not self._model:
            return self._segments_keyword_fallback(pseudo_segments)

        # Use the same segment-aware logic to keep behavior consistent
        return self._analyze_segments(pseudo_segments)

    # Segment based custom topics scoring (clinical WMD idea)

    def _analyze_segments(self, segments: List[Dict]) -> Dict:
        """Score each segment (text + intensity) and return overall meaning plus per‑segment details."""
        # No model? Use keyword fallback per segment
        if not self._model:
            return self._segments_keyword_fallback(segments)

        # Build topic vectors (centroids) from words we can vectorize
        topic_centroids = self._build_topic_centroids()
        if not topic_centroids:
            # If none could be built, fall back and explain
            print("Warning: No topic centroids could be built from the model vocabulary. Falling back to keyword mode.")
            return self._segments_keyword_fallback(segments)

        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        for idx, seg in enumerate(segments):
            seg_text = (seg.get("text") or "").strip()
            if not seg_text:
                continue

            tokens_raw = self._tokenize(seg_text)
            has_neg = any(t in {"לא", "אין", "בלי"} for t in tokens_raw)
            # Keep non-stopword tokens; we will skip tokens without vectors later
            tokens = [t for t in tokens_raw if t not in HE_STOPWORDS]
            # Normalized tokens (for anchors & matching robustness)
            norm_tokens = [_normalize_token(t) for t in tokens]
            # Remove neutral/school words after normalization
            norm_tokens = [t for t in norm_tokens if t not in NEUTRAL_IGNORE]
            seg_len = max(1, len(seg_text))

            if not tokens:
                # No useful words found in the model
                base_score = 0.0
                method = "fallback_empty"
                base_distance = 1.0
                matched = []
            else:
                # Match sentence words to topics and compute an average distance
                base_distance, matched = self._greedy_assignment_distance(norm_tokens, topic_centroids, has_neg)
                # Turn distance into a score from 0 to 1
                base_score = 1.0 / (1.0 + base_distance)
                method = "cad_greedy"

            # Neutral dampening: if no distress anchors and match is weak, cap score
            has_any_anchor = (
                any(t in INSOMNIA_ANCHORS for t in norm_tokens) or
                any(t in SELF_HARM_ANCHORS for t in norm_tokens) or
                any(t in ANXIETY_ANCHORS for t in norm_tokens) or
                any(t in HOPELESSNESS_ANCHORS for t in norm_tokens)
            )
            # If explicit self-harm language is present, ensure a very high score
            has_selfharm_anchor = any(t in SELF_HARM_ANCHORS for t in norm_tokens)
            if has_selfharm_anchor:
                base_score = max(base_score, 0.95)
            if not has_any_anchor:
                # If weak match and no anchors, cap aggressively
                if base_distance > 0.55:
                    base_score = min(base_score, 0.2)
                # If almost no tokens matched, push even lower
                matched_cnt = len(matched)
                total_cnt = max(1, len(norm_tokens))
                matched_ratio = matched_cnt / total_cnt
                if matched_cnt <= 1 or matched_ratio < 0.3:
                    base_score = min(base_score, 0.15)
                # If segment is neutral and weak, clear topic matches to avoid misleading labels
                if base_score <= 0.2:
                    matched = []
                    method = "neutral"

            intensity = (seg.get("intensity") or "normal").lower()
            multiplier = INTENSITY_TO_MULTIPLIER.get(intensity, 1.0)
            intensity_he = {"whisper": "לחישה", "normal": "דיבור רגיל", "shout": "צעקה"}.get(intensity, "רגיל")
            weighted_score = min(base_score * multiplier, 1.0)
            # Short snippet for UI (first 40 chars)
            snippet = seg_text if len(seg_text) <= 40 else (seg_text[:40] + "…")

            # Critical alert: force visible self-harm label at top of matches if anchor found
            critical_alert = False
            if has_selfharm_anchor:
                critical_alert = True
                # Prefer showing the first anchor token that appeared
                anchor_tok = next((t for t in norm_tokens if t in SELF_HARM_ANCHORS), "התאבדות")
                # Ensure self_harm_ideas appears first in matched list
                forced = {"token": anchor_tok, "topic": "self_harm_ideas", "cost": 0.0}
                # Remove any existing self_harm_ideas entries to avoid duplicates
                others = [m for m in matched if (m.get("topic") or m.get("concept_id")) != "self_harm_ideas"]
                # Put self-harm first, but keep other topics so additional distress is visible
                matched = [forced] + others

            segment_scores.append({
                "index": idx,
                "intensity": intensity,
                "intensity_he": intensity_he,
                "multiplier": multiplier,
                "base_distance": round(base_distance, 3),
                "base": round(base_score, 3),
                "weighted": round(weighted_score, 3),
                "method": method,
                "matched": matched[:5],  # cap for brevity
                "snippet": snippet,
                "critical_alert": critical_alert
            })

            total_len += seg_len
            weighted_sum += weighted_score * seg_len

        overall = round(weighted_sum / max(1, total_len), 2)

        # Bubble up a global critical alert if any segment has it
        has_critical = any(s.get("critical_alert") for s in segment_scores)
        critical_count = sum(1 for s in segment_scores if s.get("critical_alert"))
        return {
            "score": overall,
            "metadata": {
                "algorithm": "custom_wmd_cad",
                "is_vector_based": True,
                "segment_scores": segment_scores,
                "topic_weights": {t["id"]: float(t.get("weight", 0.5)) for t in CLINICAL_TOPICS},
                "topic_labels": TOPIC_LABELS,
                "model_loaded": bool(self._model is not None),
                "model_path": HebrewWMDSignal._model_path,
                "has_critical_alert": has_critical,
                "critical_segments_count": critical_count
            }
        }

    def _segments_keyword_fallback(self, segments: List[Dict]) -> Dict:
        """Keyword‑only scoring per segment when vectors are unavailable."""
        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        # Merge topic words and the built‑in clinical lexicon into one weight map
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
                "topic_weights": {t["id"]: float(t.get("weight", 0.5)) for t in CLINICAL_TOPICS},
                "reason": "semantic_model_not_loaded_or_no_centroids",
                "topic_labels": TOPIC_LABELS,
                "model_loaded": bool(self._model is not None),
                "model_path": HebrewWMDSignal._model_path
            }
        }

    # ------------------------ Helpers ------------------------ #

    def _tokenize(self, text: str) -> List[str]:
        # Basic tokenizer: remove punctuation and split on spaces
        for ch in [",", ".", "!", "?", ":", ";", "(", ")", "[", "]", "\n"]:
            text = text.replace(ch, " ")
        tokens = text.split()
        return [t.strip() for t in tokens if t.strip()]

    def _build_topic_centroids(self) -> Dict[str, Tuple[List[str], np.ndarray, float]]:
        """Create a centroid (average vector) for each topic from tokens we can vectorize.
        Returns: { topic_id: (used_tokens, centroid_vector, topic_weight) }.
        """
        centroids = {}
        missing_topics = []
        for topic in CLINICAL_TOPICS:
            raw_items = topic.get("words", [])
            used_tokens: List[str] = []
            if self._model is None:
                break
            # Split phrases to tokens and keep the ones we can vectorize
            for item in raw_items:
                # Reuse our tokenizer to strip punctuation and split Hebrew phrases safely
                for tok in self._tokenize(str(item)):
                    tok = _normalize_token(tok)
                    # Skip generic stopwords inside topic centroids to reduce noise (e.g., 'לא')
                    if tok in HE_STOPWORDS:
                        continue
                    # Filter overly-generic tokens from self-harm centroid
                    if topic.get("id") == "self_harm_ideas" and tok in SELF_HARM_IGNORE:
                        continue
                    try:
                        # Try getting a vector (fastText supports OOV via subwords)
                        _ = self._model[tok]
                        used_tokens.append(tok)
                    except Exception:
                        continue

            if not used_tokens:
                missing_topics.append(topic.get("id"))
                continue

            vecs = []
            for tok in used_tokens:
                try:
                    vecs.append(self._model[tok])
                except Exception:
                    continue
            centroid = np.mean(vecs, axis=0)
            centroids[topic["id"]] = (used_tokens, centroid, float(topic.get("weight", 0.5)))
        if not centroids:
            print(f"Info: No topic words found in model vocab. Missing topics: {missing_topics}")
        return centroids

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _greedy_assignment_distance(self, tokens: List[str], centroids: Dict[str, Tuple[List[str], np.ndarray, float]], has_negation: bool):
        """Greedy one‑to‑one matching between token vectors and topic centroids.
        Returns (avg_distance, list_of_matches_for_display)."""
        # Load token vectors once
        token_vecs = {}
        for t in tokens:
            try:
                token_vecs[t] = self._model[t]
            except Exception:
                continue
        topics_left = set(centroids.keys())
        pairs = []  # for metadata

        # Soft rules using anchors: if insomnia anchors present and self-harm not present,
        # nudge costs to favor insomnia a bit and penalize self-harm slightly.
        has_insomnia_anchor = any(t in INSOMNIA_ANCHORS for t in tokens)
        has_selfharm_anchor = any(t in SELF_HARM_ANCHORS for t in tokens)
        has_anxiety_anchor = any(t in ANXIETY_ANCHORS for t in tokens)
        has_hopeless_anchor = any(t in HOPELESSNESS_ANCHORS for t in tokens)
        has_guilt_anchor = any(t in GUILT_ANCHORS for t in tokens)
        has_rumination_anchor = any(t in RUMINATION_ANCHORS for t in tokens)
        has_any_distress_anchor = (
            has_insomnia_anchor or has_selfharm_anchor or has_anxiety_anchor or has_hopeless_anchor or has_rumination_anchor
        )

        # For each token pick the closest topic, then match best pairs first
        candidates = []
        for t in token_vecs.keys():
            best_topic = None
            best_cost = 1.0
            best_sim = -1.0
            for tid, (_, cvec, sev) in centroids.items():
                sim = self._cosine(token_vecs[t], cvec)
                # Base distance
                cost = 1.0 - sim
                # Lower the cost slightly for more severe topics so they count more (milder than before)
                cost *= (1.0 - 0.25 * sev)
                # If negation words exist, push the cost up slightly
                if has_negation:
                    cost += 0.05
                # Anchor-based tweak (only small nudges):
                if has_insomnia_anchor and not has_selfharm_anchor:
                    if tid == "self_harm_ideas":
                        cost += 0.20
                    elif tid == "insomnia":
                        cost -= 0.10
                # Avoid accidental rumination when there are no rumination anchors
                if not has_rumination_anchor and tid == "rumination":
                    cost += 0.15
                # Extra safety: avoid accidental insomnia tagging when there are no insomnia anchors
                if not has_insomnia_anchor and tid == "insomnia":
                    cost += 0.15
                # Extra safety: when self-harm anchors exist but no guilt anchors, avoid guilt matches
                if has_selfharm_anchor and not has_guilt_anchor and tid == "guilt":
                    cost += 0.25
                # Strongly prefer self-harm topic when encountering self-harm anchors
                if t in SELF_HARM_ANCHORS and tid == "self_harm_ideas":
                    cost -= 0.20
                if cost < best_cost:
                    best_cost = cost
                    best_topic = tid
                if sim > best_sim:
                    best_sim = sim
            # Only accept a match if similarity clears the minimum threshold
            if best_topic is not None and best_sim >= SIM_MIN:
                # Topic-specific stricter threshold for rumination to reduce false positives
                if best_topic == "rumination" and best_sim < 0.60:
                    pass  # skip weak rumination matches
                else:
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
