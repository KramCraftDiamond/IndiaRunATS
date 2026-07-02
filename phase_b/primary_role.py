"""Verbatim primary role extraction for output display."""


def extract_primary_role(candidate):
    """Return the candidate's most recent career_history title verbatim."""
    career_history = candidate.get("career_history") or []
    selected = None
    for job in career_history:
        if job.get("is_current") is True:
            selected = job
            break
    if selected is None and career_history:
        selected = max(career_history, key=lambda job: job.get("start_date") or "")

    if selected:
        return {
            "primary_role": selected.get("title") or "",
            "source": "career_history",
            "company": selected.get("company") or "",
            "start_date": selected.get("start_date"),
            "is_current": selected.get("is_current"),
        }

    profile = candidate.get("profile") or {}
    return {
        "primary_role": profile.get("current_title") or "",
        "source": "profile.current_title",
        "company": profile.get("current_company") or "",
        "start_date": None,
        "is_current": None,
    }
