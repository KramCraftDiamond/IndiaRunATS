import csv
import tempfile
import unittest
from pathlib import Path

from phase_b.validate_format import REQUIRED_HEADER, validate_submission_format


class FormatValidatorTest(unittest.TestCase):
    def test_validates_expected_official_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official_submission.csv"
            _write_rows(path)

            result = validate_submission_format(path)

            self.assertTrue(result["valid"])
            self.assertEqual(result["row_count"], 100)

    def test_rejects_duplicate_candidate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official_submission.csv"
            _write_rows(
                path,
                candidate_id_for_rank=lambda rank: (
                    "CAND_0000001" if rank <= 2 else f"CAND_{rank:07d}"
                ),
            )

            result = validate_submission_format(path)

            self.assertFalse(result["valid"])
            self.assertIn("unique_candidate_id", _error_checks(result))

    def test_rejects_candidate_id_tie_break_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official_submission.csv"
            _write_rows(
                path,
                candidate_id_for_rank=lambda rank: (
                    "CAND_0000002"
                    if rank == 1
                    else "CAND_0000001"
                    if rank == 2
                    else f"CAND_{rank:07d}"
                ),
                score_for_rank=lambda rank: "0.99000000" if rank <= 2 else f"{1.0 - rank / 1000:.8f}",
            )

            result = validate_submission_format(path)

            self.assertFalse(result["valid"])
            self.assertIn("deterministic_tie_break", _error_checks(result))


def _write_rows(path, candidate_id_for_rank=None, score_for_rank=None):
    candidate_id_for_rank = candidate_id_for_rank or (lambda rank: f"CAND_{rank:07d}")
    score_for_rank = score_for_rank or (lambda rank: f"{1.0 - rank / 1000:.8f}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_HEADER)
        writer.writeheader()
        for rank in range(1, 101):
            writer.writerow(
                {
                    "candidate_id": candidate_id_for_rank(rank),
                    "rank": rank,
                    "score": score_for_rank(rank),
                    "reasoning": "Uses only concrete row facts.",
                }
            )


def _error_checks(result):
    return {error["check"] for error in result["errors"]}


if __name__ == "__main__":
    unittest.main()
