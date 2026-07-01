# Phase 0 Data Dictionary

Generated on 2026-06-24 from the downloaded Redrob India Runs challenge bundle.

## File layout

The downloaded bundle has been rearranged as follows:

| Path | Purpose | Notes |
| --- | --- | --- |
| `data/raw/candidates.jsonl` | Full candidate dataset | 100,000 JSONL records, 487,259,903 bytes. This is the exact candidate file for Phase 0. No CSV was provided. |
| `data/raw/candidate_schema.json` | Official JSON schema | Used as the primary structure reference. |
| `data/raw/job_description.docx` | Official role JD | Senior AI Engineer, Founding Team. |
| `data/raw/redrob_signals_doc.docx` | Official Redrob signal documentation | Describes platform engagement signals. |
| `data/raw/submission_spec.docx` | Official submission/evaluation notes | Mentions honeypots and output expectations. |
| `data/raw/README.docx` | Official bundle README | Challenge-provided documentation. |
| `data/raw/sample_submission.csv` | Official sample submission | Kept with raw challenge materials for provenance. |
| `data/raw/submission_metadata_template.yaml` | Official metadata template | Kept with raw challenge materials. |
| `data/raw/validate_submission.py` | Official validation helper | Kept with raw challenge materials. |
| `data/sample/sample_candidates.json` | Provided small candidate sample | Small enough for fast local iteration. |

`data/raw/` is gitignored because it contains the full dataset and original challenge materials.

## Dataset shape

- Candidate file: `data/raw/candidates.jsonl`
- Format: newline-delimited JSON, one candidate object per line
- Records scanned: 100,000
- Parse errors: 0
- Top-level keys: `candidate_id`, `profile`, `career_history`, `education`, `skills`, `certifications`, `languages`, `redrob_signals`

## Top-level fields

| Field | JSON type | Missing % | Null % | Notes |
| --- | --- | ---: | ---: | --- |
| `candidate_id` | string | 0.0000 | 0.0000 | Format `CAND_XXXXXXX`. |
| `profile` | object | 0.0000 | 0.0000 | Candidate identity, location, current role, current company, experience. |
| `career_history` | array | 0.0000 | 0.0000 | Nested job history. 1-9 jobs per candidate. |
| `education` | array | 0.0000 | 0.0000 | 1-2 education records per candidate. |
| `skills` | array | 0.0000 | 0.0000 | 5+ skill records per candidate. |
| `certifications` | array | 0.0000 | 0.0000 | Empty for most candidates. |
| `languages` | array | 0.0000 | 0.0000 | Always 2 records in this dataset. |
| `redrob_signals` | object | 0.0000 | 0.0000 | Platform behavioral and assessment signals. |

## Profile fields

All scanned profile fields are present and non-null in 100,000 of 100,000 records.

| Field | JSON type | Missing % | Null % | Example |
| --- | --- | ---: | ---: | --- |
| `profile.anonymized_name` | string | 0.0000 | 0.0000 | `Ira Vora` |
| `profile.headline` | string | 0.0000 | 0.0000 | `Backend Engineer | SQL, Spark, Cloud` |
| `profile.summary` | string | 0.0000 | 0.0000 | Multi-sentence resume summary. |
| `profile.location` | string | 0.0000 | 0.0000 | `Toronto` |
| `profile.country` | string | 0.0000 | 0.0000 | `Canada` |
| `profile.years_of_experience` | number | 0.0000 | 0.0000 | `6.9` |
| `profile.current_title` | string | 0.0000 | 0.0000 | `Backend Engineer` |
| `profile.current_company` | string | 0.0000 | 0.0000 | `Mindtree` |
| `profile.current_company_size` | string | 0.0000 | 0.0000 | `10001+` |
| `profile.current_industry` | string | 0.0000 | 0.0000 | `IT Services` |

## Career history

`career_history` is nested, not flat. Each candidate has an array of job records.

Career history length distribution:

| Jobs per candidate | Candidate count |
| ---: | ---: |
| 1 | 18,508 |
| 2 | 24,186 |
| 3 | 22,126 |
| 4 | 17,131 |
| 5 | 11,469 |
| 6 | 5,196 |
| 7 | 1,218 |
| 8 | 152 |
| 9 | 14 |

Total job records scanned: 300,171.

| Field | JSON type | Missing count | Null count | Notes |
| --- | --- | ---: | ---: | --- |
| `career_history[].company` | string | 0 | 0 | Company name for each job. |
| `career_history[].title` | string | 0 | 0 | Verbatim job title for each job. |
| `career_history[].start_date` | string date | 0 | 0 | ISO date string. |
| `career_history[].end_date` | string date or null | 0 | 100,000 | Null for current jobs. |
| `career_history[].duration_months` | integer | 0 | 0 | Stated job duration. |
| `career_history[].is_current` | boolean | 0 | 0 | Marks current role. |
| `career_history[].industry` | string | 0 | 0 | Employer industry. |
| `career_history[].company_size` | string | 0 | 0 | Employer size bucket. |
| `career_history[].description` | string | 0 | 0 | Role description and achievements. |

## Education

`education` is nested. Each candidate has 1 or 2 education records.

Education length distribution:

| Education records per candidate | Candidate count |
| ---: | ---: |
| 1 | 60,222 |
| 2 | 39,778 |

Total education records scanned: 139,778.

| Field | JSON type | Missing count | Null count | Notes |
| --- | --- | ---: | ---: | --- |
| `education[].institution` | string | 0 | 0 | Institution name. |
| `education[].degree` | string | 0 | 0 | Degree name. |
| `education[].field_of_study` | string | 0 | 0 | Major/field. |
| `education[].start_year` | integer | 0 | 0 | Start year. |
| `education[].end_year` | integer | 0 | 0 | End year. |
| `education[].grade` | string | 0 | 0 | GPA/percentage/class text. |
| `education[].tier` | string | 0 | 0 | `tier_1`, `tier_2`, `tier_3`, `tier_4`. |

Education tier counts across education records:

| Tier | Count |
| --- | ---: |
| `tier_1` | 6,852 |
| `tier_2` | 27,821 |
| `tier_3` | 53,220 |
| `tier_4` | 51,885 |

## Skills

`skills` is nested. Each skill has a self-declared proficiency, endorsement count, and duration.

Total skill records scanned: 960,302.

| Field | JSON type | Missing count | Null count | Notes |
| --- | --- | ---: | ---: | --- |
| `skills[].name` | string | 0 | 0 | Skill name. |
| `skills[].proficiency` | string enum | 0 | 0 | `beginner`, `intermediate`, `advanced`, `expert`. |
| `skills[].endorsements` | integer | 0 | 0 | Skill-specific endorsement count. |
| `skills[].duration_months` | integer | 0 | 0 | Claimed months using the skill. |

Unique skill names: 133.

## Redrob signals

All listed Redrob signal fields are present and non-null in 100,000 of 100,000 records unless noted below.

| Field | JSON type | Missing % | Null % | Notes |
| --- | --- | ---: | ---: | --- |
| `redrob_signals.profile_completeness_score` | number | 0.0000 | 0.0000 | 0-100. |
| `redrob_signals.signup_date` | string date | 0.0000 | 0.0000 | ISO date string. |
| `redrob_signals.last_active_date` | string date | 0.0000 | 0.0000 | This is the available "last login"/activity proxy. |
| `redrob_signals.open_to_work_flag` | boolean | 0.0000 | 0.0000 | Open to work flag. |
| `redrob_signals.profile_views_received_30d` | integer | 0.0000 | 0.0000 | Last 30 days. |
| `redrob_signals.applications_submitted_30d` | integer | 0.0000 | 0.0000 | Last 30 days. |
| `redrob_signals.recruiter_response_rate` | number | 0.0000 | 0.0000 | 0-1. Nonzero for all candidates. |
| `redrob_signals.avg_response_time_hours` | number | 0.0000 | 0.0000 | Average response time. |
| `redrob_signals.skill_assessment_scores` | object | 0.0000 | 0.0000 | Dict of skill name to Redrob assessment score. Empty for 75,756 candidates. |
| `redrob_signals.connection_count` | integer | 0.0000 | 0.0000 | Platform connections. |
| `redrob_signals.endorsements_received` | integer | 0.0000 | 0.0000 | Profile-level endorsement count. |
| `redrob_signals.notice_period_days` | integer | 0.0000 | 0.0000 | 0-180. |
| `redrob_signals.expected_salary_range_inr_lpa.min` | number | 0.0000 | 0.0000 | Min expected LPA. |
| `redrob_signals.expected_salary_range_inr_lpa.max` | number | 0.0000 | 0.0000 | Max expected LPA. |
| `redrob_signals.preferred_work_mode` | string enum | 0.0000 | 0.0000 | `remote`, `hybrid`, `onsite`, `flexible`. |
| `redrob_signals.willing_to_relocate` | boolean | 0.0000 | 0.0000 | Relocation flag. |
| `redrob_signals.github_activity_score` | number | 0.0000 | 0.0000 | 0-100, or -1 if no GitHub linked. -1 for 64,637 candidates. |
| `redrob_signals.search_appearance_30d` | integer | 0.0000 | 0.0000 | Last 30 days. |
| `redrob_signals.saved_by_recruiters_30d` | integer | 0.0000 | 0.0000 | Last 30 days. |
| `redrob_signals.interview_completion_rate` | number | 0.0000 | 0.0000 | 0-1 rate, not raw interview count/history. |
| `redrob_signals.offer_acceptance_rate` | number | 0.0000 | 0.0000 | 0-1, or -1 if no offer history. -1 for 59,554 candidates. |
| `redrob_signals.verified_email` | boolean | 0.0000 | 0.0000 | Contact verification signal. |
| `redrob_signals.verified_phone` | boolean | 0.0000 | 0.0000 | Contact verification signal. |
| `redrob_signals.linkedin_connected` | boolean | 0.0000 | 0.0000 | Connected account signal. |

Skill assessment score object length distribution:

| Assessment skills per candidate | Candidate count |
| ---: | ---: |
| 0 | 75,756 |
| 1 | 17,215 |
| 2 | 4,057 |
| 3 | 1,741 |
| 4 | 812 |
| 5 | 419 |

## Required Phase 0 signal presence

| Requested signal | Present? | Field(s) | Shape |
| --- | --- | --- | --- |
| Job history | Yes | `career_history[]` | Nested array of job objects. |
| Skill self-rating | Yes | `skills[].proficiency` | String enum per skill. |
| Redrob skill assessment score | Yes | `redrob_signals.skill_assessment_scores` | Dict of skill name to numeric 0-100 score; may be empty. |
| Endorsement count | Yes | `skills[].endorsements`, `redrob_signals.endorsements_received` | Integer per skill and integer profile-level total. |
| Education tier | Yes | `education[].tier` | String enum per education record. |
| Location | Yes | `profile.location`, `profile.country` | String city/region and country. |
| Recruiter response rate | Yes | `redrob_signals.recruiter_response_rate` | Numeric 0-1. |
| Notice period | Yes | `redrob_signals.notice_period_days` | Integer days. |
| Last login/activity | Yes | `redrob_signals.last_active_date` | ISO date string. |
| GitHub activity | Yes | `redrob_signals.github_activity_score` | Numeric 0-100, with -1 sentinel for no GitHub linked. |
| Verified contact | Yes | `redrob_signals.verified_email`, `redrob_signals.verified_phone`, `redrob_signals.linkedin_connected` | Booleans. |
| Offer-acceptance history | Partial | `redrob_signals.offer_acceptance_rate` | Rate only; no raw offer count/history. -1 means no offer history. |
| Interview-completion history | Partial | `redrob_signals.interview_completion_rate` | Rate only; no raw interview count/history. |
| Company founding year | No | Not present in `candidate_schema.json` or any scanned candidate key | `submission_spec.docx` mentions this as a honeypot example, but the dataset does not expose a founding-year field. |

## Unique counts

| Entity | Count | Basis |
| --- | ---: | --- |
| Companies | 63 | Unique names across `profile.current_company` and `career_history[].company`. |
| Current companies | 63 | Unique names in `profile.current_company`. |
| Job titles | 48 | Unique titles across `profile.current_title` and `career_history[].title`. |
| Current job titles | 47 | Unique names in `profile.current_title`. |
| Skill names | 133 | Unique names in `skills[].name`. |
| Assessed skill names | 56 | Unique keys in `redrob_signals.skill_assessment_scores`. |
| Locations | 28 | Unique `profile.location`. |
| Countries | 8 | Unique `profile.country`. |

## Country distribution

| Country | Candidate count |
| --- | ---: |
| India | 75,113 |
| USA | 9,978 |
| Australia | 2,579 |
| Canada | 2,506 |
| UK | 2,472 |
| Germany | 2,469 |
| Singapore | 2,453 |
| UAE | 2,430 |

## Notes for later phases

- Phase A unique extraction should read from `data/raw/candidates.jsonl`, not a CSV.
- `Primary role` for the final output should come verbatim from `profile.current_title` or the `career_history[]` item where `is_current == true`; these matched the inspected record structure.
- Company founding year is absent from the candidate records and schema. Phase 4 honeypot design will need an explicit decision before implementing that check.
- `offer_acceptance_rate` and `github_activity_score` use `-1` as a sentinel value, not null.
- `skill_assessment_scores` is present for every candidate but is empty for most candidates.
