"""Single source of truth for tenure pattern scoring."""


def score_tenure_pattern(career_history, short_stint_threshold_months=12):
    """Score short stints and title progression from a candidate's job history.

    The returned adjustment is additive and intentionally small; career_score.py
    can combine it with company/title relevance without reimplementing tenure
    logic. Jobs are sorted by start_date ascending because the dataset stores
    current roles first.
    """
    jobs = list(career_history or [])
    ordered_jobs = sorted(
        enumerate(jobs),
        key=lambda item: ((item[1].get("start_date") or ""), item[0]),
    )

    seniority_keywords = {
        "intern": 0,
        "trainee": 0,
        "junior": 1,
        "associate": 1,
        "engineer": 2,
        "developer": 2,
        "analyst": 2,
        "scientist": 2,
        "specialist": 2,
        "senior": 3,
        "sr.": 3,
        "lead": 4,
        "manager": 4,
        "principal": 5,
        "staff": 5,
        "director": 5,
        "head": 5,
        "vp": 5,
        "chief": 5,
        "cto": 5,
    }

    seniority_sequence = []
    role_trace = []
    short_stint_roles = []

    for _, job in ordered_jobs:
        title = str(job.get("title") or "")
        title_lower = title.lower()
        seniority = 2
        for keyword, rank in seniority_keywords.items():
            if keyword in title_lower:
                seniority = max(seniority, rank)

        duration_months = job.get("duration_months")
        try:
            duration_months = int(duration_months)
        except (TypeError, ValueError):
            duration_months = None

        seniority_sequence.append(seniority)
        role_trace.append(
            {
                "company": job.get("company"),
                "title": title,
                "start_date": job.get("start_date"),
                "duration_months": duration_months,
                "seniority_rank": seniority,
            }
        )
        if duration_months is not None and duration_months < short_stint_threshold_months:
            short_stint_roles.append(
                {
                    "company": job.get("company"),
                    "title": title,
                    "duration_months": duration_months,
                }
            )

    progression_steps = 0
    regression_steps = 0
    flat_steps = 0
    for previous, current in zip(seniority_sequence, seniority_sequence[1:]):
        if current > previous:
            progression_steps += 1
        elif current < previous:
            regression_steps += 1
        else:
            flat_steps += 1

    short_stint_count = len(short_stint_roles)
    short_stint_penalty = min(0.35, 0.07 * short_stint_count)
    progression_bonus = min(0.20, 0.05 * progression_steps)
    score_adjustment = max(-0.35, min(0.20, progression_bonus - short_stint_penalty))

    return {
        "job_count": len(jobs),
        "short_stint_threshold_months": short_stint_threshold_months,
        "short_stint_count": short_stint_count,
        "short_stint_roles": short_stint_roles,
        "short_stint_penalty": round(short_stint_penalty, 4),
        "progression_steps": progression_steps,
        "regression_steps": regression_steps,
        "flat_steps": flat_steps,
        "progression_bonus": round(progression_bonus, 4),
        "score_adjustment": round(score_adjustment, 4),
        "seniority_sequence": seniority_sequence,
        "role_trace": role_trace,
    }
