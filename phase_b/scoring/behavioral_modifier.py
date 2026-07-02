"""Multiplicative behavioral modifier for candidate availability signals."""

from datetime import date, datetime


DEFAULT_REFERENCE_DATE = date(2026, 6, 24)


def compute_behavioral_modifier(redrob_signals, reference_date=DEFAULT_REFERENCE_DATE):
    signals = redrob_signals or {}

    response_rate = _clamp(_to_float(signals.get("recruiter_response_rate"), 0.0), 0.0, 1.0)
    notice_days = max(0, _to_int(signals.get("notice_period_days"), 180))
    last_active_date = _parse_date(signals.get("last_active_date"))
    github_activity = _to_float(signals.get("github_activity_score"), -1.0)
    verified_email = bool(signals.get("verified_email"))
    verified_phone = bool(signals.get("verified_phone"))
    linkedin_connected = bool(signals.get("linkedin_connected"))

    response_factor = 0.85 + 0.35 * response_rate
    notice_factor = _notice_factor(notice_days)
    activity_factor, days_since_active = _activity_factor(last_active_date, reference_date)
    github_factor = _github_factor(github_activity)
    verified_factor = 1.0
    if verified_email:
        verified_factor += 0.035
    if verified_phone:
        verified_factor += 0.035
    if linkedin_connected:
        verified_factor += 0.03

    modifier = response_factor * notice_factor * activity_factor * github_factor * verified_factor
    modifier = _clamp(modifier, 0.50, 1.30)

    return {
        "behavioral_modifier": round(modifier, 6),
        "response_factor": round(response_factor, 6),
        "notice_factor": round(notice_factor, 6),
        "activity_factor": round(activity_factor, 6),
        "github_factor": round(github_factor, 6),
        "verified_factor": round(verified_factor, 6),
        "recruiter_response_rate": response_rate,
        "notice_period_days": notice_days,
        "last_active_date": signals.get("last_active_date"),
        "days_since_active": days_since_active,
        "github_activity_score": github_activity,
        "verified_email": verified_email,
        "verified_phone": verified_phone,
        "linkedin_connected": linkedin_connected,
    }


def _notice_factor(notice_days):
    if notice_days <= 30:
        return 1.12
    if notice_days <= 60:
        return 1.0
    if notice_days <= 90:
        return 0.90
    if notice_days <= 120:
        return 0.78
    return 0.65


def _activity_factor(last_active_date, reference_date):
    if last_active_date is None:
        return 0.70, None
    days_since_active = (reference_date - last_active_date).days
    if days_since_active < 0:
        days_since_active = 0
    if days_since_active <= 14:
        return 1.12, days_since_active
    if days_since_active <= 45:
        return 1.02, days_since_active
    if days_since_active <= 90:
        return 0.90, days_since_active
    if days_since_active <= 180:
        return 0.75, days_since_active
    return 0.60, days_since_active


def _github_factor(github_activity):
    if github_activity < 0:
        return 0.96
    if github_activity >= 75:
        return 1.10
    if github_activity >= 40:
        return 1.05
    if github_activity > 0:
        return 1.0
    return 0.98


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


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
