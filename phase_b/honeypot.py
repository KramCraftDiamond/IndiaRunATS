"""Honeypot detection for impossible or contradictory candidate profiles."""

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase_b.scoring.skill_score import has_assessment_mismatch


DEFAULT_REFERENCE_DATE = date(2026, 6, 24)
DEFAULT_FOUNDING_YEAR_LOOKUP = "phase_a/output/company_founding_year_lookup.json"
FOUNDING_YEAR_BUFFER_YEARS = 1
SEVERE_GAP_THRESHOLD_YEARS = 3


def evaluate_honeypot(candidate, founding_year_lookup=None, reference_date=DEFAULT_REFERENCE_DATE):
    founding_year_lookup = founding_year_lookup or {}
    checks = []

    founding_check = worked_before_company_founding(
        candidate,
        founding_year_lookup,
        buffer_years=FOUNDING_YEAR_BUFFER_YEARS,
    )
    if founding_check["applicable"]:
        checks.append(founding_check)

    checks.extend(
        [
            implausible_total_experience(candidate, reference_date=reference_date),
            expert_with_near_zero_skill_tenure(candidate),
            self_rating_assessment_contradiction(candidate),
            impossible_behavioral_combination(candidate),
        ]
    )

    active_checks = len(checks)
    flag_count = sum(1 for check in checks if check["flagged"])
    threshold = max(2, math.ceil(active_checks * 0.4))
    severe_violation_details = founding_check["details"].get("severe_violation")
    severe_violation = severe_violation_details is not None
    threshold_excluded = flag_count >= threshold

    return {
        "candidate_id": candidate.get("candidate_id"),
        "excluded": severe_violation or threshold_excluded,
        "exclusion_reason": _exclusion_reason(severe_violation, threshold_excluded),
        "severe_violation_details": severe_violation_details,
        "flag_count": flag_count,
        "active_check_count": active_checks,
        "exclusion_threshold": threshold,
        "checks": checks,
    }


def worked_before_company_founding(candidate, founding_year_lookup, buffer_years=1):
    flagged_jobs = []
    severe_violation = None
    checked_jobs = 0
    for job in candidate.get("career_history") or []:
        company = job.get("company")
        founding_year = founding_year_lookup.get(company)
        if not isinstance(founding_year, int):
            continue
        checked_jobs += 1
        start_date = _parse_date(job.get("start_date"))
        if start_date and start_date.year < founding_year - buffer_years:
            gap_years = founding_year - start_date.year
            # A 1-3 year gap is treated as founding-date ambiguity (incorporation
            # vs. public launch). A gap exceeding 3 years is the canonical honeypot
            # pattern described in submission_spec.md and is excluded outright.
            if gap_years > SEVERE_GAP_THRESHOLD_YEARS and severe_violation is None:
                severe_violation = {
                    "company": company,
                    "title": job.get("title"),
                    "start_date": job.get("start_date"),
                    "founding_year": founding_year,
                    "gap_years": gap_years,
                    "threshold_years": SEVERE_GAP_THRESHOLD_YEARS,
                }
            flagged_jobs.append(
                {
                    "company": company,
                    "title": job.get("title"),
                    "start_date": job.get("start_date"),
                    "founding_year": founding_year,
                    "buffer_years": buffer_years,
                    "gap_years": gap_years,
                }
            )

    return {
        "name": "worked_before_company_founding",
        "applicable": checked_jobs > 0,
        "flagged": bool(flagged_jobs),
        "details": {
            "checked_jobs": checked_jobs,
            "flagged_jobs": flagged_jobs,
            "severe_violation": severe_violation,
        },
    }


def implausible_total_experience(candidate, reference_date=DEFAULT_REFERENCE_DATE):
    profile = candidate.get("profile") or {}
    claimed_years = _to_float(profile.get("years_of_experience"), default=0.0)
    start_dates = [
        _parse_date(job.get("start_date"))
        for job in candidate.get("career_history") or []
        if job.get("start_date")
    ]
    start_dates = [item for item in start_dates if item is not None]
    if not start_dates:
        plausible_years = None
        flagged = False
    else:
        earliest_start = min(start_dates)
        plausible_years = max(0.0, (reference_date - earliest_start).days / 365.25)
        flagged = claimed_years > plausible_years + 1.0

    return {
        "name": "implausible_total_experience",
        "applicable": True,
        "flagged": flagged,
        "details": {
            "claimed_years_of_experience": claimed_years,
            "plausible_years_since_first_job": round(plausible_years, 3)
            if plausible_years is not None
            else None,
        },
    }


def expert_with_near_zero_skill_tenure(candidate, near_zero_months=3):
    flagged_skills = []
    for skill in candidate.get("skills") or []:
        proficiency = str(skill.get("proficiency") or "").lower()
        duration_months = _to_int(skill.get("duration_months"), default=0)
        if proficiency == "expert" and duration_months <= near_zero_months:
            flagged_skills.append(
                {
                    "name": skill.get("name"),
                    "proficiency": skill.get("proficiency"),
                    "duration_months": duration_months,
                }
            )

    return {
        "name": "expert_with_near_zero_skill_tenure",
        "applicable": True,
        "flagged": bool(flagged_skills),
        "details": {
            "near_zero_months": near_zero_months,
            "flagged_skills": flagged_skills,
        },
    }


def self_rating_assessment_contradiction(candidate):
    assessments = (candidate.get("redrob_signals") or {}).get("skill_assessment_scores") or {}
    flagged_skills = []
    for skill in candidate.get("skills") or []:
        if has_assessment_mismatch(skill, assessments):
            flagged_skills.append(
                {
                    "name": skill.get("name"),
                    "proficiency": skill.get("proficiency"),
                    "assessment_score": assessments.get(skill.get("name")),
                }
            )

    return {
        "name": "self_rating_assessment_contradiction",
        "applicable": True,
        "flagged": bool(flagged_skills),
        "details": {
            "flagged_skills": flagged_skills,
        },
    }


def impossible_behavioral_combination(candidate):
    signals = candidate.get("redrob_signals") or {}
    offer_acceptance_rate = _to_float(signals.get("offer_acceptance_rate"), default=-1.0)
    interview_completion_rate = _to_float(
        signals.get("interview_completion_rate"),
        default=-1.0,
    )
    flagged = offer_acceptance_rate == 1.0 and interview_completion_rate == 0.0

    return {
        "name": "impossible_behavioral_combination",
        "applicable": True,
        "flagged": flagged,
        "details": {
            "offer_acceptance_rate": offer_acceptance_rate,
            "interview_completion_rate": interview_completion_rate,
        },
    }


def load_founding_year_lookup(path=DEFAULT_FOUNDING_YEAR_LOOKUP):
    lookup_path = Path(path)
    if not lookup_path.exists():
        return {}
    with lookup_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _exclusion_reason(severe_violation, threshold_excluded):
    if severe_violation:
        return "severe_founding_date_violation"
    if threshold_excluded:
        return "honeypot_threshold"
    return None


def scan_candidates(candidates_path, founding_year_lookup=None, sample_limit=5):
    founding_year_lookup = founding_year_lookup or {}
    total = 0
    excluded = 0
    severe_excluded = 0
    flag_histogram = {}
    excluded_samples = []
    with Path(candidates_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            result = evaluate_honeypot(candidate, founding_year_lookup)
            total += 1
            flag_histogram[str(result["flag_count"])] = flag_histogram.get(str(result["flag_count"]), 0) + 1
            if result["excluded"]:
                excluded += 1
                if result["exclusion_reason"] == "severe_founding_date_violation":
                    severe_excluded += 1
                if len(excluded_samples) < sample_limit:
                    profile = candidate.get("profile") or {}
                    excluded_samples.append(
                        {
                            "candidate_id": candidate.get("candidate_id"),
                            "name": profile.get("anonymized_name"),
                            "current_title": profile.get("current_title"),
                            "current_company": profile.get("current_company"),
                            "exclusion_reason": result["exclusion_reason"],
                            "severe_violation_details": result["severe_violation_details"],
                            "flag_count": result["flag_count"],
                            "flags": [
                                check["name"]
                                for check in result["checks"]
                                if check["flagged"]
                            ],
                        }
                    )
    return {
        "records_scanned": total,
        "excluded_count": excluded,
        "severe_founding_date_excluded_count": severe_excluded,
        "excluded_percent": (excluded / total * 100.0) if total else 0.0,
        "flag_count_histogram": flag_histogram,
        "excluded_samples": excluded_samples,
        "founding_year_lookup_entries": len(founding_year_lookup),
        "founding_year_buffer_years": FOUNDING_YEAR_BUFFER_YEARS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="data/raw/candidates.jsonl")
    parser.add_argument("--founding-year-lookup", default=DEFAULT_FOUNDING_YEAR_LOOKUP)
    parser.add_argument("--out", default="validation/results/honeypot_report.json")
    args = parser.parse_args()

    founding_lookup = load_founding_year_lookup(args.founding_year_lookup)
    report = scan_candidates(args.candidates, founding_lookup)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


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


if __name__ == "__main__":
    main()
