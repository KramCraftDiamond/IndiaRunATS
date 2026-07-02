"""Validate the official organizer submission CSV format."""

import argparse
import csv
import json
from pathlib import Path


REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
DEFAULT_SUBMISSION_PATH = "submission/official_submission.csv"


def validate_submission_format(path):
    csv_path = Path(path)
    errors = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if fieldnames != REQUIRED_HEADER:
        errors.append(
            {
                "check": "columns",
                "expected": REQUIRED_HEADER,
                "actual": fieldnames,
            }
        )

    if len(rows) != 100:
        errors.append({"check": "row_count", "expected": 100, "actual": len(rows)})

    candidate_ids = []
    ranked_rows = []
    seen_ranks = set()

    for index, row in enumerate(rows, start=1):
        candidate_id = row.get("candidate_id", "")
        candidate_ids.append(candidate_id)

        try:
            rank = int(row.get("rank", ""))
        except ValueError:
            rank = None
            errors.append({"check": "rank_integer", "row": index, "value": row.get("rank")})

        try:
            score = float(row.get("score", ""))
        except ValueError:
            score = None
            errors.append({"check": "score_float", "row": index, "value": row.get("score")})

        if not row.get("reasoning"):
            errors.append({"check": "reasoning_present", "row": index})

        if rank is not None:
            if rank < 1 or rank > 100:
                errors.append({"check": "rank_range", "row": index, "value": rank})
            if rank in seen_ranks:
                errors.append({"check": "duplicate_rank", "row": index, "value": rank})
            seen_ranks.add(rank)

        if rank is not None and score is not None:
            ranked_rows.append(
                {
                    "rank": rank,
                    "score": score,
                    "candidate_id": candidate_id,
                    "row": index,
                }
            )

    expected_ranks = set(range(1, 101))
    if seen_ranks != expected_ranks:
        errors.append(
            {
                "check": "rank_set",
                "expected": list(range(1, 101)),
                "actual": sorted(seen_ranks),
            }
        )

    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append({"check": "unique_candidate_id"})

    ranked_rows.sort(key=lambda item: item["rank"])
    for previous, current in zip(ranked_rows, ranked_rows[1:]):
        if current["score"] > previous["score"]:
            errors.append(
                {
                    "check": "non_increasing_scores",
                    "rank": current["rank"],
                    "previous_rank": previous["rank"],
                    "previous_score": previous["score"],
                    "score": current["score"],
                }
            )
            break

    for previous, current in zip(ranked_rows, ranked_rows[1:]):
        if current["score"] == previous["score"]:
            if current["candidate_id"] < previous["candidate_id"]:
                errors.append(
                    {
                        "check": "deterministic_tie_break",
                        "rank": current["rank"],
                        "previous_rank": previous["rank"],
                        "previous_candidate_id": previous["candidate_id"],
                        "candidate_id": current["candidate_id"],
                    }
                )
                break

    return {
        "path": str(csv_path),
        "valid": not errors,
        "row_count": len(rows),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?")
    parser.add_argument("--submission", default=None)
    args = parser.parse_args()

    submission_path = args.submission or args.path or DEFAULT_SUBMISSION_PATH
    result = validate_submission_format(submission_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
