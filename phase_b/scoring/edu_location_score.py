"""Education and location scoring for the Redrob Senior AI Engineer JD."""


EDUCATION_TIER_SCORES = {
    "tier_1": 1.0,
    "tier_2": 0.75,
    "tier_3": 0.45,
    "tier_4": 0.25,
    "unknown": 0.50,
}

PREFERRED_CITY_KEYWORDS = {
    "pune",
    "noida",
}

WELCOME_CITY_KEYWORDS = {
    "hyderabad",
    "mumbai",
    "delhi",
    "ncr",
    "bangalore",
    "bengaluru",
}


def score_edu_location(candidate):
    profile = candidate.get("profile") or {}
    education = candidate.get("education") or []
    signals = candidate.get("redrob_signals") or {}

    education_score, education_trace = _score_education(education)
    location_score, location_trace = _score_location(profile, signals)

    score = 0.45 * education_score + 0.55 * location_score

    return {
        "edu_location_score": round(score, 6),
        "education_score": round(education_score, 6),
        "location_score": round(location_score, 6),
        "education_trace": education_trace,
        "location_trace": location_trace,
    }


def _score_education(education):
    if not education:
        return EDUCATION_TIER_SCORES["unknown"], []

    trace = []
    scores = []
    for item in education:
        tier = item.get("tier") or "unknown"
        score = EDUCATION_TIER_SCORES.get(tier, EDUCATION_TIER_SCORES["unknown"])
        scores.append(score)
        trace.append(
            {
                "institution": item.get("institution"),
                "degree": item.get("degree"),
                "field_of_study": item.get("field_of_study"),
                "tier": tier,
                "score": score,
            }
        )
    return max(scores), trace


def _score_location(profile, signals):
    location = profile.get("location") or ""
    country = profile.get("country") or ""
    willing_to_relocate = bool(signals.get("willing_to_relocate"))
    norm_location = location.lower()
    norm_country = country.lower()

    if any(city in norm_location for city in PREFERRED_CITY_KEYWORDS):
        score = 1.0
        reason = "preferred_office_city"
    elif any(city in norm_location for city in WELCOME_CITY_KEYWORDS):
        score = 0.85
        reason = "welcome_india_city"
    elif norm_country == "india" and willing_to_relocate:
        score = 0.75
        reason = "india_relocation_ready"
    elif norm_country == "india":
        score = 0.60
        reason = "india_other_city"
    elif willing_to_relocate:
        score = 0.45
        reason = "outside_india_relocation_ready"
    else:
        score = 0.30
        reason = "outside_india_no_relocation_signal"

    return score, {
        "location": location,
        "country": country,
        "willing_to_relocate": willing_to_relocate,
        "reason": reason,
    }
