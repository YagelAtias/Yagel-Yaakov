import os
import re
import numpy as np
from pathlib import Path
from gensim.models import KeyedVectors
from .clinical_lexicon import CLINICAL_WEIGHTS
from .signal_base import DistressSignal
from typing import List, Dict, Tuple

# Mapping voice labels to numeric multipliers.
# I use this to amplify the distress score if the student is shouting or whispering.
INTENSITY_TO_MULTIPLIER = {
    "whisper": 1.2,
    "normal": 1.0,
    "shout": 1.4,
}

# Minimum cosine similarity threshold.
# I lowered this slightly to 0.40 because we now have neutral topics to filter out noise.
SIM_MIN = 0.40

# Standard Hebrew stopwords list
HE_STOPWORDS = {
    "של", "על", "אל", "אם", "עם", "אך", "גם", "לא", "אין", "כן",
    "אני", "אתה", "את", "הוא", "היא", "הם", "הן", "זה", "זו", "מה", "מי", "כמו", "מאוד",
    "היה", "היתה", "היו", "יהיה"
}

# --- 1. Clinical (Distress) Topics ---
# These are the target clusters we want to detect.
CLINICAL_TOPICS: List[Dict] = [
    {"id": "sadness", "weight": 0.6, "words": ["עצוב", "עצובה", "דכדוך", "עצבות", "בוכה", "לב שבור", "כואב לי", "מדוכא", "מדוכאת"]},
    {"id": "hopelessness", "weight": 0.9, "words": ["ייאוש", "אין תקווה", "חסר סיכוי", "חסרת סיכוי", "למה לנסות", "אבוד", "אבודה", "חסר תוחלת", "נגמר לי"]},
    {"id": "rumination", "weight": 0.7, "words": ["חושב שוב ושוב", "חוזר", "נתקע במחשבות", "טוחן", "לופ", "הראש לא מפסיק", "מחשבות טורדניות", "לא נרגע"]},
    {"id": "withdrawal", "weight": 0.6, "words": ["נסוג", "סגור", "סגורה", "מתרחק", "מתרחקת", "לבד", "לא רוצה לראות אף אחד", "התבודדות", "מנותק", "מנותקת"]},
    {"id": "guilt", "weight": 0.6, "words": ["אשם", "אשמה", "טעות שלי", "אשמתי", "בגללי", "יכולתי למנוע", "חרטה", "מכה על חטא"]},
    {"id": "fatigue", "weight": 0.5, "words": ["עייף", "עייפה", "עייפות", "אין כוח", "מותש", "מותשת", "גמור", "גמורה", "שחוק", "שחוקה", "אין אנרגיה", "כבד לי"]},
    {"id": "self_harm_ideas", "weight": 0.95, "words": [
        "מוות", "למות", "לא לחיות", "להיעלם", "קץ",
        "להתאבד", "התאבדות", "אתאבד", "להרוג את עצמי",
        "רוצה לגמור עם זה", "לחדול"
    ]},
    {"id": "anxiety_agitation", "weight": 0.7, "words": ["חרדה", "לחץ", "חוסר מנוחה", "דפיקות לב", "מחנק", "משתגע", "משתגעת", "מתוח", "מתוחה", "קצר בנשימה"]},
    {"id": "insomnia", "weight": 0.6, "words": ["נדודי שינה", "לא ישן", "לא ישנה", "לא הצלחתי לישון", "הפוך", "הפוכה", "ער כל הלילה", "מסתכל על התקרה", "לישון", "שינה"]},
]

# --- 2. Neutral (Control) Topics ---
# I added these to solve the "False Positive" issue.
# If a student talks about "tests" or "sleeping" in a normal context, the model should match these topics
# instead of defaulting to "Anxiety" or "Insomnia".
NEUTRAL_TOPICS: List[Dict] = [
    {"id": "school_academic", "weight": 0.0, "words": ["מבחן", "שיעורי בית", "ללמוד", "כיתה", "מורה", "ציון", "מתמטיקה", "היסטוריה", "ספרות", "ביולוגיה", "מחברת", "ספר", "שאלה", "תשובה"]},
    {"id": "daily_routine", "weight": 0.0, "words": ["אוכל", "לישון", "חברים", "משחק", "הפסקה", "בוקר", "ערב", "טלפון", "מקלחת", "בגד", "אוטובוס", "הולך", "חוזר", "שינה"]},
    {"id": "positive_mood", "weight": 0.0, "words": ["שמח", "כיף", "מצחיק", "נהנה", "טוב", "סבבה", "אחלה", "רגוע", "אוהב", "מעולה", "מצויין"]}
]

# Human-friendly Hebrew labels for UI display
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
    "school_academic": "לימודים",
    "daily_routine": "שגרה",
    "positive_mood": "חיובי"
}

# --- Anchors & Constants ---
# I use these anchor sets to perform safety checks and context window analysis.
INSOMNIA_ANCHORS = {"לישון", "שינה", "ישנתי", "נדודי", "לילה"}
# I included base forms here to ensure we catch self-harm even if normalization fails.
SELF_HARM_ANCHORS = {"מוות", "למות", "להיעלם", "קץ", "להתאבד", "התאבדות", "אתאבד", "להרוג", "להרוג את עצמי", "לא לחיות", "התאבד"}
SELF_HARM_IGNORE = {"די", "סוף"} # Context dependent ignore list
ANXIETY_ANCHORS = {"חרדה", "לחץ", "לחוצה", "לחוץ", "בלחץ", "מתוח"}
HOPELESSNESS_ANCHORS = {"ייאוש", "מיואש", "מיואשת", "אבוד", "אבודה"}
# Words to ignore during the semantic match (too generic)
NEUTRAL_IGNORE = {"מחר", "היום", "מחרתיים", "יש", "אלך", "אילך", "אעלה", "אבוא"}

# Words implying negation or difficulty. I use these for the 'window logic' to detect context.
DISTRESS_CONTEXT_WORDS = {'לא', 'אין', 'בלי', 'קשה', 'איני', 'בלתי', 'נורא', 'סיוט', 'רע', 'אפס', 'נמאס', 'כוח'}

def _normalize_token(tok: str) -> str:
    """
    Light Hebrew normalization logic.
    I added a specific 'Protection' layer here because standard normalization was stripping
    critical prefixes (like the 'M' in 'M-yoash'), causing missed detections.
    """
    if not tok:
        return tok

    # Protection List: These words must remain untouched to preserve their semantic meaning.
    PROTECTED_WORDS = {
        "מיואש", "מיואשת",
        "מדוכא", "מדוכאת",
        "מתוח", "מתוחה",
        "משוגע", "משוגעת",
        "מוות", "מת", "מתה",
        "מסכן", "מסכנה",
        "מפחד", "מפחדת",
        "לבד",
        "לישון", "שינה", "ישן", "נרדם", # Protected for Insomnia detection
        "להתאבד", "התאבדות", "אתאבד", # Critical for safety override
        "לחיות", "חיים" # Added to prevent stripping 'L' from Lichyot
    }

    if tok in PROTECTED_WORDS:
        return tok

    # Strip common prefixes (single letters) only if the word is long enough
    if len(tok) > 3 and tok[0] in {"ב", "כ", "ל", "ה", "ו", "מ", "ש"}:
        tok = tok[1:]

    # Map common end forms to base forms for better vector matching
    repl = {
        "ישנה": "שינה",
        "ישנתי": "ישנתי",
        "לחוצה": "לחוץ",
        "מיואשת": "מיואש",
        "מדוכאת": "מדוכא",
        "בדידות": "לבד",
        "טובה": "טוב"
    }
    tok = repl.get(tok, tok)
    return tok


class HebrewWMDSignal(DistressSignal):
    _model = None
    _model_path: str | None = None

    def __init__(self):
        # Load the Word2Vec model only once to save resources
        if HebrewWMDSignal._model is None:
            print("Loading Hebrew semantic model... please wait.")
            env_path = os.environ.get("HE_MODEL_PATH")
            try:
                project_root = Path(__file__).resolve().parents[3]
            except Exception:
                project_root = Path.cwd()

            model_folders = []
            model_files = []
            if env_path:
                p_env = Path(env_path)
                p_env = p_env if p_env.is_absolute() else (project_root / p_env)
                if p_env.is_dir():
                    model_folders.append(p_env)
                else:
                    model_files.append(p_env)

            models_dir = project_root / "models"
            model_folders.append(models_dir)
            backend_models_dir = project_root / "backend" / "app" / "models"
            wiki_dir = backend_models_dir / "wiki-w2v"
            twitter_dir = backend_models_dir / "twitter-w2v"
            if wiki_dir.exists(): model_folders.append(wiki_dir)
            if twitter_dir.exists(): model_folders.append(twitter_dir)
            model_files.append(models_dir / "he_model_small.txt")

            model_loaded = False
            for d in model_folders:
                try:
                    model = self._try_load_from_np_txt(d)
                    if model is None: continue
                    HebrewWMDSignal._model = model
                    try: HebrewWMDSignal._model.fill_norms(force=True)
                    except: pass
                    print(f"Semantic model loaded from: {d}")
                    HebrewWMDSignal._model_path = str(d)
                    model_loaded = True
                    break
                except Exception: continue

            if not model_loaded:
                for p in model_files:
                    try:
                        if not p.exists(): continue
                        model = self._try_load_any(str(p))
                        if model is None: continue
                        HebrewWMDSignal._model = model
                        try: HebrewWMDSignal._model.fill_norms(force=True)
                        except: pass
                        print(f"Semantic model loaded from: {p}")
                        HebrewWMDSignal._model_path = str(p)
                        model_loaded = True
                        break
                    except Exception: continue

            if not model_loaded:
                print("Warning: Model not loaded. Using keyword fallback.")
                HebrewWMDSignal._model_path = None

        self._model = HebrewWMDSignal._model

    def _try_load_any(self, path: str):
        p = Path(path)
        if not p.exists(): return None
        if p.suffix.lower() == ".txt":
            return KeyedVectors.load_word2vec_format(str(p), binary=False)
        return None

    def _try_load_from_np_txt(self, directory: Path):
        word_candidates = [
            directory / "words_list.txt", directory / "words_list",
            directory / "words.txt", directory / "words_list.npy", directory / "words.npy"
        ]
        vec_candidates = [
            directory / "words_vectors.npy", directory / "words_vectors", directory / "vectors.npy"
        ]
        words, vecs = None, None
        for wp in word_candidates:
            if not wp.exists(): continue
            try:
                if wp.suffix == ".npy" or "npy" in wp.name:
                    arr = np.load(str(wp), allow_pickle=True)
                    words = [w if isinstance(w, str) else str(w) for w in arr.tolist()]
                else:
                    with open(wp, "r", encoding="utf-8") as f:
                        words = [line.strip() for line in f if line.strip()]
                break
            except: continue
        for vp in vec_candidates:
            if not vp.exists(): continue
            try:
                vecs = np.load(str(vp))
                break
            except: continue

        if words is None or vecs is None: return None
        if len(words) != vecs.shape[0]: return None
        kv = KeyedVectors(vector_size=vecs.shape[1])
        kv.add_vectors(words, vecs)
        return kv

    def get_sentence_vector(self, text):
        if not self._model: return None
        words = text.split()
        vectors = []
        for w in words:
            try: vectors.append(self._model[w])
            except: continue
        if not vectors: return np.zeros(self._model.vector_size)
        return np.mean(vectors, axis=0)

    def analyze(self, data: dict) -> dict:
        segments = data.get("segments")
        if segments:
            return self._analyze_segments(segments)

        text = data.get("text", "")
        decibels = data.get("avg_decibels", 0.0)

        if decibels > 75:
            intensity = "shout"
        elif 0 < decibels < 40:
            intensity = "whisper"
        else:
            intensity = "normal"

        raw_sentences = re.split(r'[.?!:\n]+', text)
        generated_segments = [
            {"text": s.strip(), "intensity": intensity}
            for s in raw_sentences
            if s.strip()
        ]

        if not generated_segments:
            generated_segments = [{"text": text, "intensity": intensity}]

        if not self._model:
            return self._segments_keyword_fallback(generated_segments)

        return self._analyze_segments(generated_segments)

    def _analyze_segments(self, segments: List[Dict]) -> Dict:
        if not self._model:
            return self._segments_keyword_fallback(segments)

        topic_docs = self._build_topic_documents()

        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        clinical_map = {t["id"]: t["weight"] for t in CLINICAL_TOPICS}
        neutral_ids = {t["id"] for t in NEUTRAL_TOPICS}

        for idx, seg in enumerate(segments):
            seg_text = (seg.get("text") or "").strip()
            if not seg_text: continue

            tokens_raw = self._tokenize(seg_text)
            has_neg = any(t in {"לא", "אין", "בלי"} for t in tokens_raw)

            tokens = [t for t in tokens_raw if t not in HE_STOPWORDS]
            norm_tokens = [_normalize_token(t) for t in tokens]
            norm_tokens = [t for t in norm_tokens if t not in NEUTRAL_IGNORE]
            seg_len = max(1, len(seg_text))

            method = "relaxed_wmd"
            matched = []
            base_score = 0.0

            if not tokens:
                method = "empty"
            else:
                dist, best_topic, pairs = self._calculate_relaxed_wmd(norm_tokens, topic_docs, has_neg)

                # --- KEYWORD RESCUE (NEW) ---
                # If vectors failed (OOV) or gave a 0 score, check strictly against keywords.
                if best_topic is None or (dist == 1.0 and not pairs):
                    for t in norm_tokens:
                        found_rescue = False
                        for topic in CLINICAL_TOPICS:
                            if t in topic["words"]:
                                best_topic = topic["id"]
                                base_score = float(topic["weight"]) # Use defined weight
                                method = "keyword_rescue"
                                matched = [{"token": t, "matched_to": t, "topic": best_topic, "cost": 0.0}]
                                found_rescue = True
                                break
                        if found_rescue: break

                # --- CONTEXT CHECKER HELPER ---
                def _check_negation_window(target_roots):
                    """Checks if any target root is preceded by distress/negation within 3 words."""
                    # Check whole sentence tokens, not just matches, to be safe
                    is_target_word = any(t in target_roots for t in norm_tokens)
                    if not is_target_word: return False

                    for i, t in enumerate(tokens_raw):
                        norm_t = _normalize_token(t)
                        if norm_t in target_roots:
                            start_window = max(0, i - 3)
                            window = tokens_raw[start_window:i]
                            if any(_normalize_token(w) in DISTRESS_CONTEXT_WORDS for w in window):
                                return True
                    return False

                # --- 1. OVERRIDE: SELF HARM / LIFE NEGATION ---
                life_roots = {'לחיות', 'חיים'}
                is_negated_life = _check_negation_window(life_roots)
                has_selfharm_keyword = any(t in SELF_HARM_ANCHORS for t in norm_tokens)

                if has_selfharm_keyword or is_negated_life:
                    best_topic = "self_harm_ideas"
                    base_score = 0.95
                    method = "critical_override"
                    trigger_word = next((t for t in norm_tokens if t in life_roots or t in SELF_HARM_ANCHORS), "סכנה")
                    matched = [{"token": trigger_word, "matched_to": "סכנת חיים", "topic": "self_harm_ideas", "cost": 0.0}]

                # --- 2. OVERRIDE: INSOMNIA LOGIC ---
                elif best_topic != "self_harm_ideas":
                    sleep_roots = {'לישון', 'ישן', 'שינה', 'נרדם'}
                    is_distressed_sleep = _check_negation_window(sleep_roots)

                    if is_distressed_sleep:
                        is_vector_distress = best_topic not in neutral_ids and best_topic != "insomnia" and best_topic is not None
                        if is_vector_distress:
                            base_score = max(base_score, 0.85)
                            matched_token = next((t for t in norm_tokens if t in sleep_roots), "שינה")
                            pairs.insert(0, {"token": matched_token, "matched_to": "נדודי שינה", "topic": "insomnia", "cost": 0.0})
                            matched = pairs
                            method = "hybrid_distress"
                        else:
                            best_topic = "insomnia"
                            base_score = 0.85
                            method = "explicit_symptom"
                            if not matched:
                                matched = [{"token": "שינה", "topic": "insomnia", "cost": 0.1}]

                    elif best_topic == "insomnia":
                        best_topic = "daily_routine"
                        base_score = 0.0
                        method = "neutral_forced_sleep"
                        matched = []

                    elif best_topic == "positive_mood":
                        positive_roots = {'טוב', 'שמח', 'כיף', 'נהנה', 'רגוע', 'מעולה', 'סבבה', 'אחלה'}
                        is_negated_positive = _check_negation_window(positive_roots)
                        if is_negated_positive:
                            best_topic = "sadness"
                            sim = max(0.0, 1.0 - dist)
                            base_score = float(sim)
                            method = "negated_positive_flip"

                # --- 3. FINAL NEUTRAL FILTER ---
                if best_topic in neutral_ids and method in ["relaxed_wmd", "keyword_rescue"]:
                    base_score = 0.0
                    method = "neutral_match"
                    matched = []
                elif method == "relaxed_wmd":
                    # Only recalculate base_score if it wasn't already set by a Rescue or Override
                    if base_score == 0.0:
                        sim = max(0.0, 1.0 - dist)
                        base_score = float(sim)
                    matched = pairs
                    if has_neg and base_score > 0.2:
                        base_score *= 0.5

            critical_alert = (best_topic == "self_harm_ideas")

            intensity = (seg.get("intensity") or "normal").lower()
            multiplier = INTENSITY_TO_MULTIPLIER.get(intensity, 1.0)
            intensity_he = {"whisper": "לחישה", "normal": "דיבור רגיל", "shout": "צעקה"}.get(intensity, "רגיל")

            weighted_score = min(base_score * multiplier, 1.0)
            snippet = seg_text if len(seg_text) <= 40 else (seg_text[:40] + "…")

            segment_scores.append({
                "index": idx,
                "intensity": intensity,
                "intensity_he": intensity_he,
                "multiplier": multiplier,
                "base": round(float(base_score), 3),
                "weighted": round(float(weighted_score), 3),
                "method": method,
                "matched": matched[:5],
                "snippet": snippet,
                "critical_alert": critical_alert
            })

            total_len += seg_len
            weighted_sum += weighted_score * seg_len

        overall = round(float(weighted_sum / max(1, total_len)), 2)
        has_critical = any(s.get("critical_alert") for s in segment_scores)
        critical_count = sum(1 for s in segment_scores if s.get("critical_alert"))

        return {
            "score": overall,
            "metadata": {
                "algorithm": "relaxed_wmd_contrastive",
                "segment_scores": segment_scores,
                "topic_weights": clinical_map,
                "topic_labels": TOPIC_LABELS,
                "has_critical_alert": has_critical,
                "critical_segments_count": critical_count
            }
        }

    def _calculate_relaxed_wmd(self, tokens: List[str], topic_docs: Dict[str, List[np.ndarray]], has_negation: bool):
        # ... (Same as before) ...
        student_vecs = []
        student_words = []
        for t in tokens:
            try:
                v = self._model[t]
                v = v / np.linalg.norm(v)
                student_vecs.append(v)
                student_words.append(t)
            except: continue

        if not student_vecs:
            return 1.0, None, []

        topic_scores = []
        for topic_id, topic_vectors in topic_docs.items():
            if not topic_vectors: continue

            topic_matrix = np.array(topic_vectors)
            norms = np.linalg.norm(topic_matrix, axis=1, keepdims=True)
            topic_matrix = topic_matrix / norms

            total_dist = 0.0
            for sv in student_vecs:
                sims = np.dot(topic_matrix, sv)
                best_sim = np.max(sims)
                dist = 1.0 - best_sim
                total_dist += dist

            avg_wmd = total_dist / len(student_vecs)
            topic_scores.append((topic_id, avg_wmd))

        topic_scores.sort(key=lambda x: x[1])
        best_topic_id, best_dist = topic_scores[0]

        final_pairs = []
        topics_to_check = [best_topic_id]
        if len(topic_scores) > 1:
            runner_up_id, runner_up_dist = topic_scores[1]
            if runner_up_dist < 0.65:
                topics_to_check.append(runner_up_id)

        all_topics = CLINICAL_TOPICS + NEUTRAL_TOPICS

        for t_id in topics_to_check:
            target_vecs = np.array(topic_docs[t_id])
            target_norms = np.linalg.norm(target_vecs, axis=1, keepdims=True)
            target_vecs = target_vecs / target_norms

            target_words = []
            topic_def = next((t for t in all_topics if t["id"] == t_id), None)
            if topic_def:
                for item in topic_def.get("words", []):
                    for tok in self._tokenize(str(item)):
                        tok = _normalize_token(tok)
                        if tok not in HE_STOPWORDS:
                            try:
                                _ = self._model[tok]
                                target_words.append(tok)
                            except: pass

            for i, sv in enumerate(student_vecs):
                sims = np.dot(target_vecs, sv)
                best_idx = np.argmax(sims)
                cost = 1.0 - sims[best_idx]

                if cost < 0.6:
                    matched_word = target_words[best_idx] if best_idx < len(target_words) else "?"
                    final_pairs.append({
                        "token": student_words[i],
                        "matched_to": matched_word,
                        "topic": t_id,
                        "cost": round(float(cost), 3)
                    })

        return float(best_dist), best_topic_id, final_pairs

    def _build_topic_documents(self) -> Dict[str, List[np.ndarray]]:
        # ... (Same as before) ...
        topic_docs = {}
        all_topics = CLINICAL_TOPICS + NEUTRAL_TOPICS

        for topic in all_topics:
            raw_items = topic.get("words", [])
            valid_vectors = []
            if self._model is None: break

            for item in raw_items:
                for tok in self._tokenize(str(item)):
                    tok = _normalize_token(tok)
                    if tok in HE_STOPWORDS: continue
                    if topic.get("id") == "self_harm_ideas" and tok in SELF_HARM_IGNORE:
                        continue
                    try:
                        vec = self._model[tok]
                        valid_vectors.append(vec)
                    except: continue

            if valid_vectors:
                topic_docs[topic["id"]] = valid_vectors
        return topic_docs

    def _tokenize(self, text: str) -> List[str]:
        for ch in [",", ".", "!", "?", ":", ";", "(", ")", "[", "]", "\n", "-", '"']:
            text = text.replace(ch, " ")
        return [t.strip() for t in text.split() if t.strip()]

    def _segments_keyword_fallback(self, segments: List[Dict]) -> Dict:
        # ... (Same as before) ...
        segment_scores = []
        total_len = 0
        weighted_sum = 0.0

        kw_weights = dict(CLINICAL_WEIGHTS)
        for topic in CLINICAL_TOPICS:
            w = topic.get("weight", 0.5)
            for word in topic.get("words", []):
                kw_weights[word] = max(kw_weights.get(word, 0.0), float(w))

        for idx, seg in enumerate(segments):
            seg_text = (seg.get("text") or "").strip()
            if not seg_text: continue
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
                "base": round(float(base), 3),
                "weighted": round(float(weighted), 3),
                "method": "keyword_fallback"
            })
            total_len += seg_len
            weighted_sum += weighted * seg_len

        return {
            "score": round(float(weighted_sum / max(1, total_len)), 2),
            "metadata": {
                "algorithm": "keyword_fallback",
                "segment_scores": segment_scores,
                "topic_weights": {t["id"]: t["weight"] for t in CLINICAL_TOPICS},
                "topic_labels": TOPIC_LABELS,
            }
        }