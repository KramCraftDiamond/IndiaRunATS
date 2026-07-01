"""Validate and split the manual company/title tier lookup."""

import argparse
import json
from pathlib import Path


ALLOWED_COMPANY_TIERS = {"PRODUCT", "CONSULTING", "UNKNOWN"}
ALLOWED_TITLE_TIERS = {"GOOD_FIT", "BAD_FIT", "NEUTRAL"}


def extract_universe(candidates_path):
    companies = set()
    titles = set()
    with Path(candidates_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            candidate = json.loads(line)
            for job in candidate.get("career_history") or []:
                company = job.get("company")
                title = job.get("title")
                if company:
                    companies.add(company)
                if title:
                    titles.add(title)
    return companies, titles


def validate_manual_tiers(candidates_path, manual_path):
    companies, titles = extract_universe(candidates_path)
    manual = json.loads(Path(manual_path).read_text(encoding="utf-8"))
    company_lookup = manual.get("companies") or {}
    title_lookup = manual.get("titles") or {}

    report = {
        "candidate_company_count": len(companies),
        "candidate_title_count": len(titles),
        "manual_company_count": len(company_lookup),
        "manual_title_count": len(title_lookup),
        "missing_companies": sorted(companies - set(company_lookup)),
        "extra_companies": sorted(set(company_lookup) - companies),
        "missing_titles": sorted(titles - set(title_lookup)),
        "extra_titles": sorted(set(title_lookup) - titles),
        "bad_company_tiers": {
            key: value
            for key, value in company_lookup.items()
            if value not in ALLOWED_COMPANY_TIERS
        },
        "bad_title_tiers": {
            key: value
            for key, value in title_lookup.items()
            if value not in ALLOWED_TITLE_TIERS
        },
    }
    is_valid = not any(
        report[key]
        for key in (
            "missing_companies",
            "extra_companies",
            "missing_titles",
            "extra_titles",
            "bad_company_tiers",
            "bad_title_tiers",
        )
    )
    return is_valid, report, company_lookup, title_lookup


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="data/raw/candidates.jsonl")
    parser.add_argument("--manual", default="data/raw/company_title_tiers.json")
    parser.add_argument("--founding-years", default="data/raw/company_founding_year.json")
    parser.add_argument("--output-dir", default="phase_a/output")
    args = parser.parse_args()

    is_valid, report, company_lookup, title_lookup = validate_manual_tiers(
        args.candidates, args.manual
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not is_valid:
        raise SystemExit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "company_tier_lookup.json").write_text(
        json.dumps(company_lookup, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "title_tier_lookup.json").write_text(
        json.dumps(title_lookup, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    founding_path = Path(args.founding_years)
    if founding_path.exists():
        founding_years = json.loads(founding_path.read_text(encoding="utf-8"))
        (output_dir / "company_founding_year_lookup.json").write_text(
            json.dumps(founding_years, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
