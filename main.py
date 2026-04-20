#!/usr/bin/env python3
"""
Main entry point for the Job Agent Alerter application.
"""

import json
import argparse
import sys
import os

# Add scrapper directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapper'))

from scrapper.scraper import run_scraper
from scrapper.html_parser import parse_job_snippet
from scrapper.job_filter import filter_snippets_by_title
from scrapper.job_extractor import extract_job_details
from scrapper.file_utils import save_job_snippets


def main():
    """Main entry point for the scraper application."""
    parser = argparse.ArgumentParser(description="Job Agent Alerter - Scrape and filter job openings")
    parser.add_argument("--save-json", help="Save scraped job snippets to this JSON file")
    args = parser.parse_args()

    jobs = run_scraper()
    print(f"\n{'='*60}")
    print(f"Total HTML snippets found: {len(jobs)}")
    print(f"{'='*60}\n")

    print("\n=== All formatted job snippets ===")
    for idx, job in enumerate(jobs, 1):
        print(f"\n--- Job snippet #{idx} ---")
        print(parse_job_snippet(job))

    filtered_jobs = filter_snippets_by_title(jobs)
    print("\n=== Filtered job snippets ===")
    if not filtered_jobs:
        print("No matching job titles found based on job-role-keywords.txt")
    else:
        for idx, job in enumerate(filtered_jobs, 1):
            title = job.get("extracted_title", "(no title extracted)")
            print(f"\n--- Filtered job #{idx}: {title} ---")
            print(parse_job_snippet(job))

    # Extract and output job details in JSON format
    if filtered_jobs:
        job_details = extract_job_details(filtered_jobs)
        print("\n=== Extracted Job Details (JSON) ===")
        print(json.dumps(job_details, indent=2, ensure_ascii=False))

    if args.save_json:
        save_job_snippets(jobs, args.save_json)
        print(f"Saved {len(jobs)} snippets to {args.save_json}")


if __name__ == "__main__":
    main()
