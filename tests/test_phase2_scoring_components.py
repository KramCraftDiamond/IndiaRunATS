import unittest

from phase_b.primary_role import extract_primary_role
from phase_b.scoring.career_score import score_career
from phase_b.scoring.edu_location_score import score_edu_location
from phase_b.scoring.skill_score import has_assessment_mismatch, score_skills


class Phase2ScoringComponentsTest(unittest.TestCase):
    def test_career_score_uses_lookup_tiers_and_tenure_pattern(self):
        candidate = {
            "profile": {"years_of_experience": 7.0},
            "career_history": [
                {
                    "company": "ProductCo",
                    "title": "Senior AI Engineer",
                    "start_date": "2023-01-01",
                    "duration_months": 24,
                    "is_current": True,
                },
                {
                    "company": "ProductCo",
                    "title": "Software Engineer",
                    "start_date": "2020-01-01",
                    "duration_months": 36,
                    "is_current": False,
                },
            ],
        }

        result = score_career(
            candidate,
            company_tiers={"ProductCo": "PRODUCT"},
            title_tiers={"Senior AI Engineer": "GOOD_FIT", "Software Engineer": "NEUTRAL"},
        )

        self.assertGreater(result["career_score"], 0.7)
        self.assertEqual(result["current_title_tier"], "GOOD_FIT")
        self.assertEqual(result["current_company_tier"], "PRODUCT")
        self.assertIn("tenure_pattern", result)

    def test_skill_mismatch_flag_reuses_assessment_score(self):
        self.assertTrue(
            has_assessment_mismatch(
                {"name": "Python", "proficiency": "expert"},
                {"Python": 30.0},
            )
        )
        self.assertFalse(
            has_assessment_mismatch(
                {"name": "Python", "proficiency": "intermediate"},
                {"Python": 30.0},
            )
        )

    def test_skill_score_rewards_retrieval_ranking_stack(self):
        candidate = {
            "skills": [
                {
                    "name": "Python",
                    "proficiency": "advanced",
                    "endorsements": 20,
                    "duration_months": 60,
                },
                {
                    "name": "Embeddings",
                    "proficiency": "advanced",
                    "endorsements": 12,
                    "duration_months": 24,
                },
                {
                    "name": "Vector Search",
                    "proficiency": "advanced",
                    "endorsements": 12,
                    "duration_months": 24,
                },
                {
                    "name": "Learning to Rank",
                    "proficiency": "intermediate",
                    "endorsements": 10,
                    "duration_months": 18,
                },
            ],
            "redrob_signals": {
                "skill_assessment_scores": {
                    "Python": 80,
                    "Embeddings": 76,
                    "Vector Search": 74,
                    "Learning to Rank": 70,
                }
            },
        }

        result = score_skills(candidate)

        self.assertGreater(result["skill_score"], 0.5)
        self.assertEqual(result["skill_assessment_count"], 4)
        self.assertEqual(result["assessment_mismatch_skills"], [])

    def test_edu_location_scores_preferred_city_and_best_education_tier(self):
        candidate = {
            "profile": {"location": "Pune, Maharashtra", "country": "India"},
            "education": [
                {"institution": "College A", "degree": "B.E.", "tier": "tier_3"},
                {"institution": "College B", "degree": "M.Tech", "tier": "tier_1"},
            ],
            "redrob_signals": {"willing_to_relocate": False},
        }

        result = score_edu_location(candidate)

        self.assertEqual(result["education_score"], 1.0)
        self.assertEqual(result["location_score"], 1.0)
        self.assertEqual(result["edu_location_score"], 1.0)

    def test_primary_role_extracts_current_career_history_title_verbatim(self):
        candidate = {
            "profile": {"current_title": "Profile Title"},
            "career_history": [
                {
                    "company": "CurrentCo",
                    "title": "Senior ML Engineer \u2014 Search & Ranking",
                    "start_date": "2024-01-01",
                    "is_current": True,
                }
            ],
        }

        result = extract_primary_role(candidate)

        self.assertEqual(result["primary_role"], "Senior ML Engineer \u2014 Search & Ranking")
        self.assertEqual(result["source"], "career_history")


if __name__ == "__main__":
    unittest.main()
