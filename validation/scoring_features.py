"""Shared Phase 3 feature generation for validation scripts."""

import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from phase_b.scoring.behavioral_modifier import compute_behavioral_modifier
from phase_b.scoring.career_score import score_career
from phase_b.scoring.edu_location_score import score_edu_location
from phase_b.scoring.skill_score import score_skills
from phase_b.scoring.tenure_pattern import score_tenure_pattern


BASELINE_WEIGHTS = {
    "career": 0.50,
    "skill": 0.30,
    "edu_location": 0.20,
}


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_candidates(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def build_scoring_features(
    candidates_path="data/raw/candidates.jsonl",
    company_lookup_path="phase_a/output/company_tier_lookup.json",
    title_lookup_path="phase_a/output/title_tier_lookup.json",
):
    company_tiers = load_json(company_lookup_path)
    title_tiers = load_json(title_lookup_path)
    features = []

    for candidate in iter_candidates(candidates_path):
        career = score_career(candidate, company_tiers, title_tiers)
        skills = score_skills(candidate)
        edu_location = score_edu_location(candidate)
        behavior = compute_behavioral_modifier(candidate.get("redrob_signals") or {})

        features.append(
            {
                "candidate_id": candidate.get("candidate_id") or "",
                "career_score": career["career_score"],
                "career_base_score": career["career_base_score"],
                "skill_score": skills["skill_score"],
                "edu_location_score": edu_location["edu_location_score"],
                "behavioral_modifier": behavior["behavioral_modifier"],
                "notice_factor": behavior["notice_factor"],
                "notice_period_days": behavior["notice_period_days"],
                "career_history": candidate.get("career_history") or [],
                "tenure_score_adjustment": career["tenure_pattern"]["score_adjustment"],
            }
        )

    return features


def score_with_weights(feature, weights):
    base_relevance = (
        weights["career"] * feature["career_score"]
        + weights["skill"] * feature["skill_score"]
        + weights["edu_location"] * feature["edu_location_score"]
    )
    return base_relevance * feature["behavioral_modifier"]


def top_ids(scored_rows, limit=100):
    ranked = sorted(scored_rows, key=lambda item: (-item["score"], item["candidate_id"]))
    return [item["candidate_id"] for item in ranked[:limit]]


def overlap_percent(candidate_ids, baseline_ids):
    return len(set(candidate_ids) & set(baseline_ids)) / len(baseline_ids) * 100.0


def career_score_with_short_stint_threshold(feature, threshold_months):
    tenure = score_tenure_pattern(
        feature["career_history"],
        short_stint_threshold_months=threshold_months,
    )
    score = feature["career_base_score"] + tenure["score_adjustment"]
    return max(0.0, min(1.0, score))


def behavioral_modifier_with_notice_threshold(feature, notice_threshold_days):
    base_modifier = feature["behavioral_modifier"]
    base_notice_factor = feature["notice_factor"] or 1.0
    replacement_notice_factor = notice_factor_for_threshold(
        feature["notice_period_days"],
        notice_threshold_days,
    )
    modifier = base_modifier / base_notice_factor * replacement_notice_factor
    return max(0.50, min(1.30, modifier))


def notice_factor_for_threshold(notice_days, notice_threshold_days):
    quick_threshold = max(1, notice_threshold_days / 2.0)
    slow_threshold = notice_threshold_days * 1.5
    high_threshold = notice_threshold_days * 2.0
    if notice_days <= quick_threshold:
        return 1.12
    if notice_days <= notice_threshold_days:
        return 1.0
    if notice_days <= slow_threshold:
        return 0.90
    if notice_days <= high_threshold:
        return 0.78
    return 0.65
