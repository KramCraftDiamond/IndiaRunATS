import unittest
from datetime import date

from phase_b.honeypot import (
    evaluate_honeypot,
    expert_with_near_zero_skill_tenure,
    impossible_behavioral_combination,
    implausible_total_experience,
    self_rating_assessment_contradiction,
    worked_before_company_founding,
)


class HoneypotTest(unittest.TestCase):
    def test_founding_year_check_uses_more_than_one_year_buffer(self):
        candidate = {
            "career_history": [
                {"company": "NewCo", "title": "Engineer", "start_date": "2020-01-01"},
                {"company": "NewCo", "title": "Engineer", "start_date": "2021-01-01"},
            ]
        }

        result = worked_before_company_founding(candidate, {"NewCo": 2022})

        self.assertTrue(result["applicable"])
        self.assertTrue(result["flagged"])
        self.assertEqual(len(result["details"]["flagged_jobs"]), 1)
        self.assertEqual(result["details"]["flagged_jobs"][0]["start_date"], "2020-01-01")

    def test_missing_founding_year_is_not_applicable(self):
        result = worked_before_company_founding(
            {"career_history": [{"company": "UnknownCo", "start_date": "1990-01-01"}]},
            {},
        )

        self.assertFalse(result["applicable"])
        self.assertFalse(result["flagged"])

    def test_implausible_experience_flags_claim_before_first_job(self):
        result = implausible_total_experience(
            {
                "profile": {"years_of_experience": 10},
                "career_history": [{"start_date": "2023-01-01"}],
            },
            reference_date=date(2026, 6, 24),
        )

        self.assertTrue(result["flagged"])

    def test_expert_near_zero_skill_tenure_flags(self):
        result = expert_with_near_zero_skill_tenure(
            {"skills": [{"name": "Python", "proficiency": "expert", "duration_months": 0}]}
        )

        self.assertTrue(result["flagged"])

    def test_assessment_contradiction_reuses_skill_mismatch_logic(self):
        result = self_rating_assessment_contradiction(
            {
                "skills": [{"name": "Python", "proficiency": "expert", "duration_months": 24}],
                "redrob_signals": {"skill_assessment_scores": {"Python": 20}},
            }
        )

        self.assertTrue(result["flagged"])

    def test_impossible_behavioral_combination_flags(self):
        result = impossible_behavioral_combination(
            {
                "redrob_signals": {
                    "offer_acceptance_rate": 1.0,
                    "interview_completion_rate": 0.0,
                }
            }
        )

        self.assertTrue(result["flagged"])

    def test_single_flag_does_not_exclude_candidate(self):
        result = evaluate_honeypot(
            {
                "candidate_id": "CAND_0000001",
                "profile": {"years_of_experience": 5},
                "career_history": [{"company": "NewCo", "start_date": "2020-01-01"}],
                "skills": [],
                "redrob_signals": {
                    "skill_assessment_scores": {},
                    "offer_acceptance_rate": 0.5,
                    "interview_completion_rate": 0.5,
                },
            },
            founding_year_lookup={"NewCo": 2022},
        )

        self.assertEqual(result["flag_count"], 1)
        self.assertFalse(result["excluded"])
        self.assertEqual(result["exclusion_threshold"], 2)
        self.assertIsNone(result["exclusion_reason"])

    def test_one_year_founding_gap_is_not_excluded_by_itself(self):
        result = evaluate_honeypot(
            {
                "candidate_id": "CAND_0000002",
                "profile": {
                    "years_of_experience": 4.0,
                    "current_title": "AI Engineer",
                    "current_company": "NewCo",
                },
                "career_history": [
                    {
                        "company": "NewCo",
                        "title": "AI Engineer",
                        "start_date": "2021-01-01",
                        "end_date": None,
                        "duration_months": 24,
                        "is_current": True,
                    }
                ],
                "skills": [],
                "redrob_signals": {
                    "skill_assessment_scores": {},
                    "offer_acceptance_rate": 0.5,
                    "interview_completion_rate": 0.5,
                },
            },
            founding_year_lookup={"NewCo": 2022},
        )

        self.assertEqual(result["flag_count"], 0)
        self.assertFalse(result["excluded"])
        self.assertIsNone(result["exclusion_reason"])
        self.assertIsNone(result["severe_violation_details"])

    def test_five_year_founding_gap_is_standalone_exclusion(self):
        result = evaluate_honeypot(
            {
                "candidate_id": "CAND_0000003",
                "profile": {
                    "years_of_experience": 7.0,
                    "current_title": "AI Engineer",
                    "current_company": "Sarvam AI",
                },
                "career_history": [
                    {
                        "company": "Sarvam AI",
                        "title": "AI Engineer",
                        "start_date": "2018-09-22",
                        "end_date": None,
                        "duration_months": 60,
                        "is_current": True,
                    }
                ],
                "skills": [],
                "redrob_signals": {
                    "skill_assessment_scores": {},
                    "offer_acceptance_rate": 0.5,
                    "interview_completion_rate": 0.5,
                },
            },
            founding_year_lookup={"Sarvam AI": 2023},
        )

        self.assertEqual(result["flag_count"], 1)
        self.assertTrue(result["excluded"])
        self.assertEqual(result["exclusion_reason"], "severe_founding_date_violation")
        self.assertEqual(result["severe_violation_details"]["company"], "Sarvam AI")
        self.assertEqual(result["severe_violation_details"]["gap_years"], 5)


if __name__ == "__main__":
    unittest.main()
