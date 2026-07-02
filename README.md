# India Runs ATS

Hackathon submission repo for Redrob AI's India Runs Track 1: Intelligent Candidate Ranking.

The file to upload to the portal is `submission/official_submission.csv`. `submission/top_100.csv` has been removed - it was an earlier internal-review format and is not a valid submission.

## Objective

Rank the top 100 candidates for Redrob's Senior AI Engineer, Founding Team role. The JD targets a hands-on production ML/AI engineer with retrieval, ranking, embeddings, evaluation, and product-shipping experience.

## Data

- Full candidate data: `data/raw/candidates.jsonl`
- Format: JSONL, 100,000 records
- Job history shape: nested `career_history[]`
- Phase 0 notes: `data/data_dictionary.md`

`data/raw/` is gitignored because it contains the large dataset and original challenge bundle. The frozen lookup artifacts used by the timed ranker are committed under `phase_a/output/`.

## Phase A

Company and title tiering is manual because Phase 0 found a small universe: 63 unique career-history companies and 48 unique career-history titles. Manual classification is stronger than an LLM pass here because every company/title can be reviewed directly.

Frozen ranker inputs:

- `phase_a/output/company_tier_lookup.json`
- `phase_a/output/title_tier_lookup.json`
- `phase_a/output/company_founding_year_lookup.json`

Founding-year caveat: Phase 4's founding-year honeypot check uses a buffer and flags only when a candidate job starts more than 1 year before the company's founding year. Krutrim, Sarvam AI, and Glance are treated cautiously because incorporation, launch, product, and public-announcement dates can differ.

## Known Limitations

- Founding-year coverage is 43/63 companies. The remaining 20 have no founding-year entry and are treated as "check not applicable" for that candidate, never as a trigger: Accenture, Acme Corp, Aganitha, Dunder Mifflin, Genpact AI, Globex Inc, HCL, Hooli, Initech, Locobuzz, Mad Street Den, Mphasis, Niramai, Pied Piper, Rephrase.ai, Saarthi.ai, Stark Industries, Vedantu, Verloop.io, Wayne Enterprises.
- Krutrim, Sarvam AI, and Glance have inherent founding-date ambiguity because incorporation, public launch, product launch, and announcement dates can differ; this is why the founding-year honeypot check uses a 1-year buffer rather than an exact-year cutoff.
- The 60-day notice-period threshold was chosen over alternatives because `validation/results/threshold_results.json` showed top-100 overlap dropping to 85.0% at 45 days, while 75 days held at 100% overlap; 60 days is closest to typical Indian notice-period norms within the range that does not destabilize the ranking.

Honeypot near-miss audit: `validation/honeypot_near_miss_audit.py` checks whether single-flag near-misses or literal suspicious expert-skill profiles reach the top ranks. The latest run found 4 candidates with `honeypot_flag_count == 1` in the top 100, 1 in the top 10, 0 full-pool candidates with 8+ expert skills at near-zero duration, and 0 such profiles in the top 100.

## Scoring

The timed entrypoint is:

```bash
python phase_b/rank.py
```

It reads only local JSON/JSONL files, runs CPU-only, and makes no network calls.

Base relevance:

```text
0.5 * career_score + 0.3 * skill_score + 0.2 * edu_location_score
```

The behavioral modifier is multiplicative:

```text
final_score = (base_relevance * behavioral_modifier)/1.30
```
Score is normalized to a 0-1 range by dividing by the behavioral modifier's defined maximum (1.30).

Honeypot exclusion runs before final ranking. A candidate is excluded only when at least two independent flags trigger.

## Validation Results

Full ranking run:

```text
records_scanned: 100000
records_ranked_after_honeypot: 99989
honeypot_excluded: 16
elapsed_seconds: 29.333
```

Phase 3 ablation top-100 overlap vs baseline:

```text
baseline_50_30_20: 100.0%
skill_heavy_40_40_20: 96.0%
career_heavy_60_25_15: 97.0%
edu_loc_heavier_45_30_25: 97.0%
```

Threshold sensitivity top-100 overlap vs baseline:

```text
short_stint_minus_25pct_9mo: 98.0%
short_stint_baseline_12mo: 100.0%
short_stint_plus_25pct_15mo: 98.0%
notice_minus_25pct_45d: 85.0%
notice_baseline_60d: 100.0%
notice_plus_25pct_75d: 100.0%
```

Phase 5.4 reproducibility:

```text
official_submission.csv byte-identical: True
PASS: True
```

## Outputs

Portal-ready output matching the official validator:

- `submission/official_submission.csv`
- Columns: `candidate_id`, `rank`, `score`, `reasoning`

Reproducibility log:

- `submission/repro_check_log.txt`

## Checks

Run all unit tests:

```bash
python -m unittest discover -s tests
```

Validate the official submission CSV with the local validator:

```bash
python phase_b/validate_format.py submission/official_submission.csv
```

Validate the portal CSV with the official helper:

```bash
python data/raw/validate_submission.py submission/official_submission.csv
```

## Sandbox

Open `notebooks/sandbox_demo.ipynb` in Google Colab and run all cells. The notebook clones this public repo, loads only `data/sample/sample_candidates.json`, converts at most 100 sample candidates into a temporary JSONL file, reuses `phase_b.rank.rank_candidates`, and writes `/content/sandbox_official_submission.csv` with the official `candidate_id,rank,score,reasoning` schema. It does not embed, fetch, or require the full private `data/raw/candidates.jsonl` dataset.

After saving the notebook to your own Google Drive or Colab account, use Colab's sharing controls to create a public or organizer-accessible link. Add that URL manually to `submission_metadata.yaml` under `sandbox_link`; the repo intentionally leaves that field as `TODO_HUMAN` until publication.
