"""Deterministic, fact-grounded reasoning for top-ranked candidates."""


def generate_reasoning(row):
    """Generate 2 sentence reasoning from scored row facts only."""
    skills = _compact_unique(
        (row.get("matched_core_skills") or []) + (row.get("matched_vector_infra_skills") or [])
    )
    skill_text = ", ".join(skills[:3]) if skills else "the scored skill profile"
    response_pct = row.get("recruiter_response_rate", 0.0) * 100.0
    notice_days = row.get("notice_period_days")
    days_since_active = row.get("days_since_active")
    short_stints = row.get("short_stint_count")
    progression_steps = row.get("progression_steps")

    first = (
        f"{row.get('resume_name')} is {_article(row.get('primary_role'))} "
        f"{row.get('primary_role')} with "
        f"{row.get('years_of_experience'):.1f} years of experience, currently at "
        f"{row.get('current_company')} ({row.get('current_company_tier')}) and scored "
        f"{row.get('career_score'):.3f} career / {row.get('skill_score'):.3f} skill "
        f"on the production AI-ranking profile."
    )
    second = (
        f"Relevant evidence includes {skill_text}, {progression_steps} seniority "
        f"progression step(s), {short_stints} short stint(s), a {notice_days}-day "
        f"notice period, {response_pct:.0f}% recruiter response rate, and "
        f"{_activity_phrase(days_since_active)}."
    )
    if row.get("assessment_mismatch_count", 0):
        second += f" Assessment mismatch flags remain visible: {row['assessment_mismatch_count']}."
    return f"{first} {second}"


def _activity_phrase(days_since_active):
    if days_since_active is None:
        return "no usable last-active date"
    if days_since_active == 0:
        return "activity today"
    return f"last activity {days_since_active} day(s) ago"


def _compact_unique(values):
    seen = set()
    result = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _article(value):
    text = str(value or "").strip().lower()
    if text[:1] in {"a", "e", "i", "o", "u"}:
        return "an"
    return "a"
