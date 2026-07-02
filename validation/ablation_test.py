"""Phase 3 ablation validation for score weight configurations."""

import json
import sys
import time
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validation.scoring_features import build_scoring_features, overlap_percent, score_with_weights, top_ids


WEIGHT_CONFIGS = {
    "baseline_50_30_20": {"career": 0.50, "skill": 0.30, "edu_location": 0.20},
    "skill_heavy_40_40_20": {"career": 0.40, "skill": 0.40, "edu_location": 0.20},
    "career_heavy_60_25_15": {"career": 0.60, "skill": 0.25, "edu_location": 0.15},
    "edu_loc_heavier_45_30_25": {"career": 0.45, "skill": 0.30, "edu_location": 0.25},
}


def run_ablation():
    started = time.perf_counter()
    features = build_scoring_features()

    top100_by_config = {}
    for name, weights in WEIGHT_CONFIGS.items():
        scored_rows = [
            {
                "candidate_id": feature["candidate_id"],
                "score": score_with_weights(feature, weights),
            }
            for feature in features
        ]
        top100_by_config[name] = top_ids(scored_rows)

    baseline = top100_by_config["baseline_50_30_20"]
    results = {
        "records_scored": len(features),
        "baseline_config": "baseline_50_30_20",
        "top_n": 100,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "configs": {},
    }
    for name, weights in WEIGHT_CONFIGS.items():
        ids = top100_by_config[name]
        results["configs"][name] = {
            "weights": weights,
            "top_100_overlap_count_vs_baseline": len(set(ids) & set(baseline)),
            "top_100_overlap_percent_vs_baseline": overlap_percent(ids, baseline),
            "top_100_candidate_ids": ids,
        }
    return results


def main():
    results = run_ablation()
    output = Path("validation/results/ablation_results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
