import zlib


def calculate_ratio(text):
    if not text: return 0
    encoded = text.encode("utf-8")
    compressed = zlib.compress(encoded)
    ratio = len(encoded) / len(compressed)
    return round(ratio, 2)


print("Calibration Test:")
normal_sentences = [
    "היום הלכתי לבית הספר והיה שיעור מעניין במתמטיקה",
    "אני הולך לישון עכשיו נדבר מחר בבוקר",
    "מה המצב אחי הכל טוב?",
    "התוצאה במשחק אתמול הייתה מפתיעה מאוד"
]

rumination_sentences = [
    "למה זה קורה לי למה זה קורה לי למה זה קורה לי",
    "אני כישלון אני כישלון אני כישלון אני כישלון",
    "לא מצליח להירדם לא מצליח להירדם לא מצליח להירדם",
    "שונא את עצמי שונא את עצמי שונא את עצמי"
]

normal_scores = []
rumination_scores = []

print("--- Normal Sentences ---")
for s in normal_sentences:
    r = calculate_ratio(s)
    normal_scores.append(r)  # Store the score
    print(f"Ratio: {r} | Text: {s}")

print("\n--- Rumination Sentences ---")
for s in rumination_sentences:
    r = calculate_ratio(s)
    rumination_scores.append(r)  # Store the score
    print(f"Ratio: {r} | Text: {s}")

avg_normal = sum(normal_scores) / len(normal_scores)
avg_rumination = sum(rumination_scores) / len(rumination_scores)

threshold = (avg_normal + avg_rumination) / 2

print("\n" + "="*30)
print(f"Avg Normal:     {avg_normal:.2f}")
print(f"Avg Rumination: {avg_rumination:.2f}")
print("-" * 30)
print(f"RECOMMENDED THRESHOLD: {threshold:.2f}")
print("="*30)