"""Career relevance scoring for the Senior AI Engineer JD."""

import json
from pathlib import Path

from phase_b.scoring.tenure_pattern import score_tenure_pattern


COMPANY_TIER_SCORES = {
    "PRODUCT": 1.0,
    "CONSULTING": 0.25,
    "UNKNOWN": 0.55,
}

TITLE_TIER_SCORES = {
    "GOOD_FIT": 1.0,
    "NEUTRAL": 0.55,
    "BAD_FIT": 0.05,
}


def load_lookup(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_career(candidate, company_tiers, title_tiers):
    career_history = candidate.get("career_history") or []
    profile = candidate.get("profile") or {}
    years_of_experience = _to_float(profile.get("years_of_experience"), default=0.0)

    current_job = _current_or_most_recent_job(career_history)
    current_company = current_job.get("company") or profile.get("current_company") or ""
    current_title = current_job.get("title") or profile.get("current_title") or ""

    title_scores = []
    company_scores = []
    relevant_role_months = 0
    product_company_months = 0
    consulting_only_months = 0
    role_trace = []

    for job in career_history:
        company = job.get("company") or ""
        title = job.get("title") or ""
        duration_months = _to_int(job.get("duration_months"), default=0)
        company_tier = company_tiers.get(company, "UNKNOWN")
        title_tier = title_tiers.get(title, "NEUTRAL")
        title_score = TITLE_TIER_SCORES.get(title_tier, TITLE_TIER_SCORES["NEUTRAL"])
        company_score = COMPANY_TIER_SCORES.get(company_tier, COMPANY_TIER_SCORES["UNKNOWN"])

        title_scores.append(title_score)
        company_scores.append(company_score)
        if title_tier == "GOOD_FIT":
            relevant_role_months += duration_months
        if company_tier == "PRODUCT":
            product_company_months += duration_months
        elif company_tier == "CONSULTING":
            consulting_only_months += duration_months

        role_trace.append(
            {
                "company": company,
                "company_tier": company_tier,
                "title": title,
                "title_tier": title_tier,
                "duration_months": duration_months,
            }
        )

    current_title_tier = title_tiers.get(current_title, "NEUTRAL")
    current_company_tier = company_tiers.get(current_company, "UNKNOWN")
    current_title_score = TITLE_TIER_SCORES.get(
        current_title_tier, TITLE_TIER_SCORES["NEUTRAL"]
    )
    current_company_score = COMPANY_TIER_SCORES.get(
        current_company_tier, COMPANY_TIER_SCORES["UNKNOWN"]
    )

    historical_title_score = _average(title_scores, default=TITLE_TIER_SCORES["NEUTRAL"])
    historical_company_score = _average(
        company_scores, default=COMPANY_TIER_SCORES["UNKNOWN"]
    )
    experience_score = _experience_fit_score(years_of_experience)
    relevant_months_score = min(1.0, relevant_role_months / 48.0)

    base_score = (
        0.30 * current_title_score
        + 0.20 * historical_title_score
        + 0.20 * current_company_score
        + 0.10 * historical_company_score
        + 0.10 * experience_score
        + 0.10 * relevant_months_score
    )

    tenure = score_tenure_pattern(career_history)
    score = _clamp(base_score + tenure["score_adjustment"], 0.0, 1.0)

    return {
        "career_score": round(score, 6),
        "career_base_score": round(base_score, 6),
        "current_title": current_title,
        "current_title_tier": current_title_tier,
        "current_company": current_company,
        "current_company_tier": current_company_tier,
        "years_of_experience": years_of_experience,
        "experience_score": round(experience_score, 6),
        "relevant_role_months": relevant_role_months,
        "product_company_months": product_company_months,
        "consulting_company_months": consulting_only_months,
        "tenure_pattern": tenure,
        "role_trace": role_trace,
    }


def _current_or_most_recent_job(career_history):
    for job in career_history:
        if job.get("is_current") is True:
            return job
    if not career_history:
        return {}
    return max(career_history, key=lambda job: job.get("start_date") or "")


def _experience_fit_score(years):
    if 5.0 <= years <= 9.0:
        return 1.0
    if 3.0 <= years < 5.0:
        return 0.65 + ((years - 3.0) / 2.0) * 0.25
    if 9.0 < years <= 12.0:
        return 0.85
    if 12.0 < years <= 16.0:
        return 0.65
    return 0.35


def _average(values, default=0.0):
    return sum(values) / len(values) if values else default


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))
