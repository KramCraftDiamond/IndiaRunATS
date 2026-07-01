import unittest

from phase_b.scoring.tenure_pattern import score_tenure_pattern


class TenurePatternTest(unittest.TestCase):
    def test_job_hopper_gets_short_stint_penalty(self):
        result = score_tenure_pattern(
            [
                {
                    "company": "Gamma",
                    "title": "Software Engineer",
                    "start_date": "2023-01-01",
                    "duration_months": 8,
                },
                {
                    "company": "Beta",
                    "title": "Software Engineer",
                    "start_date": "2022-01-01",
                    "duration_months": 10,
                },
                {
                    "company": "Alpha",
                    "title": "Software Engineer",
                    "start_date": "2021-01-01",
                    "duration_months": 9,
                },
            ]
        )

        self.assertEqual(result["short_stint_count"], 3)
        self.assertEqual(result["progression_steps"], 0)
        self.assertGreater(result["short_stint_penalty"], 0)
        self.assertLess(result["score_adjustment"], 0)

    def test_steady_progression_gets_progression_bonus(self):
        result = score_tenure_pattern(
            [
                {
                    "company": "CurrentCo",
                    "title": "Lead AI Engineer",
                    "start_date": "2023-01-01",
                    "duration_months": 24,
                },
                {
                    "company": "MiddleCo",
                    "title": "Senior Software Engineer",
                    "start_date": "2020-01-01",
                    "duration_months": 36,
                },
                {
                    "company": "EarlyCo",
                    "title": "Software Engineer",
                    "start_date": "2017-01-01",
                    "duration_months": 36,
                },
            ]
        )

        self.assertEqual(result["seniority_sequence"], [2, 3, 4])
        self.assertEqual(result["short_stint_count"], 0)
        self.assertEqual(result["progression_steps"], 2)
        self.assertGreater(result["progression_bonus"], 0)
        self.assertGreater(result["score_adjustment"], 0)

    def test_single_job_is_neutral_without_short_stint(self):
        result = score_tenure_pattern(
            [
                {
                    "company": "OnlyCo",
                    "title": "Machine Learning Engineer",
                    "start_date": "2022-01-01",
                    "duration_months": 30,
                }
            ]
        )

        self.assertEqual(result["job_count"], 1)
        self.assertEqual(result["short_stint_count"], 0)
        self.assertEqual(result["progression_steps"], 0)
        self.assertEqual(result["progression_bonus"], 0)
        self.assertEqual(result["short_stint_penalty"], 0)
        self.assertEqual(result["score_adjustment"], 0)


if __name__ == "__main__":
    unittest.main()
