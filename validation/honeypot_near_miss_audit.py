"""Audit honeypot near-misses in the final ranked output."""

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase_b.honeypot import expert_with_near_zero_skill_tenure
from phase_b.rank import (
    DEFAULT_CANDIDATES_PATH,
    DEFAULT_COMPANY_LOOKUP_PATH,
    DEFAULT_FOUNDING_YEAR_LOOKUP_PATH,
    DEFAULT_TITLE_LOOKUP_PATH,
    rank_candidates,
)


def build_report(
    candidates_path=DEFAULT_CANDIDATES_PATH,
    company_lookup_path=DEFAULT_COMPANY_LOOKUP_PATH,
    title_lookup_path=DEFAULT_TITLE_LOOKUP_PATH,
    founding_year_lookup_path=DEFAULT_FOUNDING_YEAR_LOOKUP_PATH,
):
    ranking = rank_candidates(
        candidates_path,
        company_lookup_path,
        title_lookup_path,
        founding_year_lookup_path,
    )
    ranked = ranking["ranked"]
    top_100 = ranked[:100]
    top_10 = ranked[:10]
    top_100_by_id = {item["candidate_id"]: item for item in top_100}

    suspicious_count = 0
    suspicious_in_top_100 = []

    for candidate in _iter_candidates(candidates_path):
        suspicious = _suspicious_expert_profile(candidate)
        if not suspicious["matches"]:
            continue

        suspicious_count += 1
        candidate_id = candidate.get("candidate_id") or ""
        ranked_item = top_100_by_id.get(candidate_id)
        if ranked_item:
            suspicious_in_top_100.append(
                {
                    "candidate_id": candidate_id,
                    "rank": ranked_item["rank"],
                    "expert_near_zero_skill_count": suspicious["skill_count"],
                    "skills": suspicious["skills"],
                }
            )

    return {
        "flag_count_1_in_top_100": sum(
            1 for item in top_100 if item.get("honeypot_flag_count") == 1
        ),
        "flag_count_1_in_top_10": sum(
            1 for item in top_10 if item.get("honeypot_flag_count") == 1
        ),
        "suspicious_expert_profile_count_full_pool": suspicious_count,
        "suspicious_expert_profiles_in_top_100": suspicious_in_top_100,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--company-lookup", default=DEFAULT_COMPANY_LOOKUP_PATH)
    parser.add_argument("--title-lookup", default=DEFAULT_TITLE_LOOKUP_PATH)
    parser.add_argument("--founding-year-lookup", default=DEFAULT_FOUNDING_YEAR_LOOKUP_PATH)
    parser.add_argument("--out", default="validation/results/honeypot_near_miss_audit.json")
    args = parser.parse_args()

    report = build_report(
        candidates_path=args.candidates,
        company_lookup_path=args.company_lookup,
        title_lookup_path=args.title_lookup,
        founding_year_lookup_path=args.founding_year_lookup,
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Honeypot near-miss audit: "
        f"flag_count_1_in_top_100={report['flag_count_1_in_top_100']}, "
        f"flag_count_1_in_top_10={report['flag_count_1_in_top_10']}, "
        "suspicious_expert_profile_count_full_pool="
        f"{report['suspicious_expert_profile_count_full_pool']}, "
        "suspicious_expert_profiles_in_top_100="
        f"{len(report['suspicious_expert_profiles_in_top_100'])}"
    )


def _suspicious_expert_profile(candidate):
    check = expert_with_near_zero_skill_tenure(candidate)
    flagged_skills = check["details"]["flagged_skills"]
    return {
        "matches": len(flagged_skills) >= 8,
        "skill_count": len(flagged_skills),
        "skills": flagged_skills,
    }


def _iter_candidates(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


if __name__ == "__main__":
    main()
