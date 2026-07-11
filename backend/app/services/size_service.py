from typing import Optional

SIZE_CHARTS = {
    "h&m": {
        "XS": (76, 80,  60, 64,  84, 88),
        "S":  (81, 85,  65, 69,  89, 93),
        "M":  (86, 91,  70, 75,  94, 99),
        "L":  (92, 97,  76, 81, 100,105),
        "XL": (98,103,  82, 87, 106,111),
        "XXL":(104,110, 88, 94, 112,118),
    },
    "zara": {
        "XS": (78, 82,  62, 66,  86, 90),
        "S":  (83, 87,  67, 71,  91, 95),
        "M":  (88, 92,  72, 76,  96,100),
        "L":  (93, 97,  77, 81, 101,105),
        "XL": (98,103,  82, 87, 106,111),
    },
    "myntra": {
        "XS": (74, 78,  58, 62,  82, 86),
        "S":  (79, 83,  63, 67,  87, 91),
        "M":  (84, 88,  68, 72,  92, 96),
        "L":  (89, 93,  73, 77,  97,101),
        "XL": (94, 99,  78, 83, 102,107),
        "XXL":(100,106, 84, 90, 108,114),
        "3XL":(107,114, 91, 98, 115,122),
    },
    "generic": {
        "XS": (76, 80,  60, 64,  84, 88),
        "S":  (81, 86,  65, 70,  89, 94),
        "M":  (87, 92,  71, 76,  95,100),
        "L":  (93, 98,  77, 82, 101,106),
        "XL": (99,104,  83, 88, 107,112),
        "XXL":(105,112, 89, 96, 113,120),
    }
}

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "3XL"]

def _score_size(chest, waist, hip, chest_min, chest_max, waist_min, waist_max, hip_min, hip_max):
    def dim_score(val, lo, hi, weight=1.0):
        if lo <= val <= hi:
            mid = (lo + hi) / 2
            spread = (hi - lo) / 2
            return weight * (1.0 - abs(val - mid) / spread * 0.2)
        else:
            dist = min(abs(val - lo), abs(val - hi))
            penalty = dist / ((hi - lo) + 1e-6)
            return weight * max(0.0, 1.0 - penalty)

    score = (
        dim_score(chest, chest_min, chest_max, weight=1.0) +
        dim_score(waist, waist_min, waist_max, weight=0.8) +
        dim_score(hip,   hip_min,   hip_max,   weight=1.2)
    ) / 3.0
    return round(score, 4)

def _bmi_note(height_cm, weight_kg):
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5: return "lean build"
    if bmi < 25:   return "average build"
    if bmi < 30:   return "fuller build"
    return "plus build"

def _build_fit_notes(chest, waist, hip, dims, build, category):
    if not dims or len(dims) < 6:
        return f"{build.capitalize()} — standard fit expected."
    chest_min, chest_max, waist_min, waist_max, hip_min, hip_max = dims
    notes = []
    if hip > hip_max:
        notes.append("hip measurement is on the fuller side — consider sizing up")
    elif hip < hip_min:
        notes.append("hip measurement is slimmer — recommended size will have extra room")
    if chest > chest_max:
        notes.append("chest runs slightly large for this size")
    if category.lower() in ("kurta", "kurti", "dress", "gown"):
        notes.append("for ethnic wear, we recommend going one size up for ease of movement")
    if not notes:
        notes.append("measurements fall well within the size range — confident fit")
    return f"{build.capitalize()} — " + "; ".join(notes) + "."

def recommend_size(height_cm, weight_kg, chest_cm, waist_cm, hip_cm, brand="generic", category="top"):
    import math
    brand = brand.lower()
    chart = SIZE_CHARTS.get(brand, SIZE_CHARTS["generic"])
    scores = {}
    for size_label, dims in chart.items():
        scores[size_label] = _score_size(chest_cm, waist_cm, hip_cm, *dims)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_size, best_score = ranked[0]

    # Confidence = how decisively the best size beats the others
    # (softmax over size scores — a probability, not a raw fit score).
    exps = {s: math.exp(v * 8.0) for s, v in scores.items()}
    total = sum(exps.values())
    confidence_pct = round(exps[best_size] / total * 100, 1)

    alt_size = ranked[1][0] if len(ranked) > 1 else None
    build = _bmi_note(height_cm, weight_kg)
    fit_notes = _build_fit_notes(chest_cm, waist_cm, hip_cm, chart.get(best_size, ()), build, category)
    # Return risk reflects absolute fit quality (does ANY size fit well?)
    return_risk = "LOW" if best_score >= 0.75 else "MEDIUM" if best_score >= 0.55 else "HIGH"
    return {
        "recommended_size": best_size,
        "confidence_pct":   confidence_pct,
        "fit_notes":        fit_notes,
        "size_chart_used":  brand,
        "alternate_size":   alt_size,
        "return_risk":      return_risk,
    }
