"""
File I/O utilities for the job scraper.
"""

import json


def save_job_snippets(jobs, output_path):
    """Save auto_scrapper output to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)