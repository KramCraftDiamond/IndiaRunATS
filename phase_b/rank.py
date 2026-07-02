"""Timed CPU-only ranking entrypoint."""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase_b.primary_role import extract_primary_role
from phase_b.honeypot import evaluate_honeypot, load_founding_year_lookup
from phase_b.scoring.behavioral_modifier import compute_behavioral_modifier
from phase_b.scoring.career_score import score_career
from phase_b.scoring.edu_location_score import score_edu_location
from phase_b.scoring.skill_score import score_skills


DEFAULT_CANDIDATES_PATH = "data/raw/candidates.jsonl"
DEFAULT_COMPANY_LOOKUP_PATH = "phase_a/output/company_tier_lookup.json"
DEFAULT_TITLE_LOOKUP_PATH = "phase_a/output/title_tier_lookup.json"
DEFAULT_FOUNDING_YEAR_LOOKUP_PATH = "phase_a/output/company_founding_year_lookup.json"


def rank_candidates(
    candidates_path,
    company_lookup_path,
    title_lookup_path,
    founding_year_lookup_path=DEFAULT_FOUNDING_YEAR_LOOKUP_PATH,
):
    company_tiers = _load_json(company_lookup_path)
    title_tiers = _load_json(title_lookup_path)
    founding_years = load_founding_year_lookup(founding_year_lookup_path)
    ranked = []
    scanned_count = 0
    excluded_count = 0

    for candidate in _iter_candidates(candidates_path):
        scanned_count += 1
        honeypot = evaluate_honeypot(candidate, founding_years)
        if honeypot["excluded"]:
            excluded_count += 1
            continue

        career = score_career(candidate, company_tiers, title_tiers)
        skills = score_skills(candidate)
        edu_location = score_edu_location(candidate)
        behavior = compute_behavioral_modifier(candidate.get("redrob_signals") or {})
        primary_role = extract_primary_role(candidate)

        # Provisional 0.5/0.3/0.2 weights until Phase 3 ablation results exist.
        base_relevance = (
            0.5 * career["career_score"]
            + 0.3 * skills["skill_score"]
            + 0.2 * edu_location["edu_location_score"]
        )
        final_score = (base_relevance * behavior["behavioral_modifier"])/1.30

        profile = candidate.get("profile") or {}
        ranked.append(
            {
                "candidate_id": candidate.get("candidate_id") or "",
                "resume_name": profile.get("anonymized_name") or "",
                "primary_role": primary_role["primary_role"],
                "candidate_score": round(final_score, 8),
                "base_relevance": round(base_relevance, 8),
                "career_score": career["career_score"],
                "skill_score": skills["skill_score"],
                "edu_location_score": edu_location["edu_location_score"],
                "behavioral_modifier": behavior["behavioral_modifier"],
                "current_company": career["current_company"],
                "current_company_tier": career["current_company_tier"],
                "current_title_tier": career["current_title_tier"],
                "years_of_experience": career["years_of_experience"],
                "notice_period_days": behavior["notice_period_days"],
                "recruiter_response_rate": behavior["recruiter_response_rate"],
                "days_since_active": behavior["days_since_active"],
                "short_stint_count": career["tenure_pattern"]["short_stint_count"],
                "progression_steps": career["tenure_pattern"]["progression_steps"],
                "matched_core_skills": [
                    skill["name"] for skill in skills["matched_core_skills"][:5]
                ],
                "matched_vector_infra_skills": [
                    skill["name"] for skill in skills["matched_vector_infra_skills"][:5]
                ],
                "assessment_mismatch_count": len(skills["assessment_mismatch_skills"]),
                "honeypot_flag_count": honeypot["flag_count"],
            }
        )

    ranked.sort(key=lambda item: (-item["candidate_score"], item["candidate_id"]))
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank
    return {
        "ranked": ranked,
        "scanned_count": scanned_count,
        "excluded_count": excluded_count,
        "founding_year_lookup_entries": len(founding_years),
    }


def write_portal_csv(ranked, output_path, limit=100):
    from phase_b.reasoning_gen import generate_reasoning

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["candidate_id", "rank", "score", "reasoning"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in ranked[:limit]:
            writer.writerow(
                {
                    "candidate_id": item["candidate_id"],
                    "rank": item["rank"],
                    "score": f"{item['candidate_score']:.8f}",
                    "reasoning": generate_reasoning(item),
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--company-lookup", default=DEFAULT_COMPANY_LOOKUP_PATH)
    parser.add_argument("--title-lookup", default=DEFAULT_TITLE_LOOKUP_PATH)
    parser.add_argument("--founding-year-lookup", default=DEFAULT_FOUNDING_YEAR_LOOKUP_PATH)
    parser.add_argument("--out", default="submission/official_submission.csv")
    parser.add_argument("--top-n", type=int, default=100)
    parser.add_argument("--no-output", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    result = rank_candidates(
        args.candidates,
        args.company_lookup,
        args.title_lookup,
        args.founding_year_lookup,
    )
    ranked = result["ranked"]
    elapsed = time.perf_counter() - started

    if args.out and not args.no_output:
        write_portal_csv(ranked, args.out, args.top_n)

    print(
        json.dumps(
            {
                "records_scanned": result["scanned_count"],
                "records_ranked_after_honeypot": len(ranked),
                "honeypot_excluded": result["excluded_count"],
                "founding_year_lookup_entries": result["founding_year_lookup_entries"],
                "top_score": ranked[0]["candidate_score"] if ranked else None,
                "elapsed_seconds": round(elapsed, 3),
            },
            indent=2,
        )
    )


def _iter_candidates(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    main()
