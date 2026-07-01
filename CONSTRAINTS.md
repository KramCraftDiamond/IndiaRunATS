# Hard constraints â€” never violate these even if it seems convenient

- rank.py runs CPU-only, no network access, must finish in under 5 minutes
  on the full ~100k-row dataset. This is the ONLY timed/judged entrypoint.
- rank.py NEVER calls an LLM or any network API. It only reads frozen JSON
  lookup files from phase_a/output/.
- Phase A (LLM company/title classification) runs once, ahead of time,
  outside the timed window. Once frozen, phase_a/output/*.json is never
  regenerated for the final submission without an explicit instruction
  from me to redo it.
- Tenure pattern logic (short-stint penalty under 12 months, seniority
  progression bonus) exists in exactly ONE place:
  phase_b/scoring/tenure_pattern.py. Never reimplement or duplicate this
  logic in any other file.
- The behavioral modifier (recruiter response rate, notice period, last
  login, GitHub activity, verified contact) is MULTIPLICATIVE on top of
  base relevance score â€” never added into the weighted sum. Implement as
  its own function producing its own named column.
- Base relevance = weighted sum of career (0.5) + skill (0.3) +
  edu/location (0.2). These weights are provisional until
  validation/ablation_test.py has actually run and produced overlap
  numbers â€” do not treat them as final without that evidence existing
  in validation/results/.
- UNKNOWN is a valid, neutrally-scored category for company/title tier â€”
  never an error, crash, or forced guess.
- Honeypot exclusion requires >=2 of 5 independent flags. No single flag
  excludes a candidate on its own. Reuse the skill mismatch check from
  skill_score.py inside honeypot.py â€” do not reimplement it.
- The Primary role field in the output CSV is the candidate's verbatim
  most-recent job title as it appears in the data â€” it does NOT go through
  the title-tier classifier. It's a display field, not a scoring input.
- Every score component must be traceable: if asked "why did this
  candidate get this score," the answer must come from a real field in
  the data, never an invented or templated explanation.
- Before touching any file outside the current phase's stated scope, stop
  and ask me first.

# Revisions after Phase 0 data recon

- The candidate dataset is data/raw/candidates.jsonl (JSONL, NOT CSV).
  100,000 records. Job history is nested under career_history[] per
  candidate. Every script that reads candidate data must parse JSONL
  with nested career_history, never assume a flat CSV.
- The universe of unique companies (63) and unique job titles (48) is
  small enough that company/title tier classification is being done
  MANUALLY by the team, not by an LLM. There is no classify_llm.py in
  this build. Do not propose adding one.
- Company founding year does NOT exist anywhere in the dataset schema
  or records. Honeypot check #1 ("worked at a company before it was
  founded") can only run if a manual founding-year lookup is supplied
  by me for the 63 companies. Until that file exists, honeypot.py must
  implement only 4 checks (not 5) and the >=2 threshold stays the same
  ratio relative to however many checks are actually active. Never
  invent, estimate, or hallucinate a founding year for any company.
  If I have not provided data/raw/company_founding_year.json by the
  time you build honeypot.py, build the 4-check version and say so
  explicitly - do not silently drop the requirement without flagging it
  to me in your response.
- I am hand-writing two files myself, not generating them:
  data/raw/company_title_tiers.json (manual classification of all 63
  companies as PRODUCT/CONSULTING/UNKNOWN and all 48 titles as
  GOOD_FIT/BAD_FIT/NEUTRAL relative to the JD) and, optionally,
  data/raw/company_founding_year.json. When these are present, treat
  them as the FROZEN ground truth - read them, never regenerate or
  "improve" them.
- When Phase 4 builds the founding-year honeypot check, use a buffer:
  flag only if a job starts more than 1 year before the company's
  founding year. Do not flag exact-year or 1-year discrepancies because
  candidate histories have exact dates while the lookup stores only
  founding years, and some early-stage company dates are ambiguous.
