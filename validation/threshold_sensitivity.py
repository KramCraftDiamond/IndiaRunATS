"""Phase 3 threshold sensitivity for tenure and notice-period thresholds."""

import json
import sys
import time
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.scoring_features import (
    BASELINE_WEIGHTS,
    behavioral_modifier_with_notice_threshold,
    build_scoring_features,
    career_score_with_short_stint_threshold,
    overlap_percent,
    score_with_weights,
    top_ids,
)


SHORT_STINT_THRESHOLDS_MONTHS = {
    "short_stint_minus_25pct_9mo": 9,
    "short_stint_baseline_12mo": 12,
    "short_stint_plus_25pct_15mo": 15,
}

NOTICE_THRESHOLDS_DAYS = {
    "notice_minus_25pct_45d": 45,
    "notice_baseline_60d": 60,
    "notice_plus_25pct_75d": 75,
}


def run_threshold_sensitivity():
    started = time.perf_counter()
    features = build_scoring_features()
    baseline_rows = [
        {"candidate_id": feature["candidate_id"], "score": score_with_weights(feature, BASELINE_WEIGHTS)}
        for feature in features
    ]
    baseline_top100 = top_ids(baseline_rows)

    results = {
        "records_scored": len(features),
        "baseline_weights": BASELINE_WEIGHTS,
        "top_n": 100,
        "elapsed_seconds": None,
        "short_stint_threshold_months": {},
        "notice_period_threshold_days": {},
    }

    for name, threshold in SHORT_STINT_THRESHOLDS_MONTHS.items():
        rows = []
        for feature in features:
            career_score = career_score_with_short_stint_threshold(feature, threshold)
            base_relevance = (
                BASELINE_WEIGHTS["career"] * career_score
                + BASELINE_WEIGHTS["skill"] * feature["skill_score"]
                + BASELINE_WEIGHTS["edu_location"] * feature["edu_location_score"]
            )
            rows.append(
                {
                    "candidate_id": feature["candidate_id"],
                    "score": base_relevance * feature["behavioral_modifier"],
                }
            )
        ids = top_ids(rows)
        results["short_stint_threshold_months"][name] = {
            "threshold_months": threshold,
            "top_100_overlap_count_vs_baseline": len(set(ids) & set(baseline_top100)),
            "top_100_overlap_percent_vs_baseline": overlap_percent(ids, baseline_top100),
            "top_100_candidate_ids": ids,
        }

    for name, threshold in NOTICE_THRESHOLDS_DAYS.items():
        rows = []
        for feature in features:
            modifier = behavioral_modifier_with_notice_threshold(feature, threshold)
            base_relevance = (
                BASELINE_WEIGHTS["career"] * feature["career_score"]
                + BASELINE_WEIGHTS["skill"] * feature["skill_score"]
                + BASELINE_WEIGHTS["edu_location"] * feature["edu_location_score"]
            )
            rows.append(
                {
                    "candidate_id": feature["candidate_id"],
                    "score": base_relevance * modifier,
                }
            )
        ids = top_ids(rows)
        results["notice_period_threshold_days"][name] = {
            "threshold_days": threshold,
            "top_100_overlap_count_vs_baseline": len(set(ids) & set(baseline_top100)),
            "top_100_overlap_percent_vs_baseline": overlap_percent(ids, baseline_top100),
            "top_100_candidate_ids": ids,
        }

    results["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return results


def main():
    results = run_threshold_sensitivity()
    output = Path("validation/results/threshold_results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
