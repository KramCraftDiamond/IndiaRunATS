import tempfile
import unittest
from datetime import date
from pathlib import Path

from phase_b.rank import rank_candidates, write_portal_csv
from phase_b.scoring.behavioral_modifier import compute_behavioral_modifier


class Phase25RankTest(unittest.TestCase):
    def test_behavioral_modifier_is_multiplicative_and_traceable(self):
        result = compute_behavioral_modifier(
            {
                "recruiter_response_rate": 0.8,
                "notice_period_days": 20,
                "last_active_date": "2026-06-20",
                "github_activity_score": 80,
                "verified_email": True,
                "verified_phone": True,
                "linkedin_connected": True,
            },
            reference_date=date(2026, 6, 24),
        )

        self.assertGreater(result["behavioral_modifier"], 1.0)
        self.assertEqual(result["notice_period_days"], 20)
        self.assertEqual(result["days_since_active"], 4)

    def test_rank_candidates_sorts_by_score_then_candidate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidates = tmp_path / "candidates.jsonl"
            company_lookup = tmp_path / "companies.json"
            title_lookup = tmp_path / "titles.json"
            out = tmp_path / "ranked.csv"

            candidates.write_text(
                "\n".join(
                    [
                        _candidate_json("CAND_0000002", "Senior AI Engineer", "ProductCo"),
                        _candidate_json("CAND_0000001", "Accountant", "ConsultingCo"),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            company_lookup.write_text(
                '{"ProductCo": "PRODUCT", "ConsultingCo": "CONSULTING"}',
                encoding="utf-8",
            )
            title_lookup.write_text(
                '{"Senior AI Engineer": "GOOD_FIT", "Accountant": "BAD_FIT"}',
                encoding="utf-8",
            )

            result = rank_candidates(candidates, company_lookup, title_lookup)
            ranked = result["ranked"]
            write_portal_csv(ranked, out, limit=2)

            self.assertEqual(ranked[0]["candidate_id"], "CAND_0000002")
            self.assertEqual(ranked[0]["rank"], 1)
            self.assertTrue(out.exists())
            header = out.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(
                header,
                "candidate_id,rank,score,reasoning",
            )


def _candidate_json(candidate_id, title, company):
    return (
        "{"
        f'"candidate_id": "{candidate_id}",'
        '"profile": {'
        '"anonymized_name": "Test Candidate",'
        f'"current_title": "{title}",'
        f'"current_company": "{company}",'
        '"years_of_experience": 7.0,'
        '"location": "Pune, Maharashtra",'
        '"country": "India"'
        "},"
        '"career_history": ['
        "{"
        f'"company": "{company}",'
        f'"title": "{title}",'
        '"start_date": "2021-01-01",'
        '"end_date": null,'
        '"duration_months": 60,'
        '"is_current": true'
        "}"
        "],"
        '"education": [{"institution": "College", "degree": "B.E.", "tier": "tier_1"}],'
        '"skills": ['
        '{"name": "Python", "proficiency": "advanced", "endorsements": 10, "duration_months": 48},'
        '{"name": "Embeddings", "proficiency": "advanced", "endorsements": 10, "duration_months": 24},'
        '{"name": "Vector Search", "proficiency": "advanced", "endorsements": 10, "duration_months": 24}'
        "],"
        '"redrob_signals": {'
        '"skill_assessment_scores": {"Python": 80, "Embeddings": 80, "Vector Search": 80},'
        '"willing_to_relocate": false,'
        '"recruiter_response_rate": 0.8,'
        '"notice_period_days": 30,'
        '"last_active_date": "2026-06-20",'
        '"github_activity_score": 80,'
        '"verified_email": true,'
        '"verified_phone": true,'
        '"linkedin_connected": true'
        "}"
        "}"
    )


if __name__ == "__main__":
    unittest.main()
