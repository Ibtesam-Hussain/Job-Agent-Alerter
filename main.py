#!/usr/bin/env python3
"""
Official entry point for Job Agent Alerter.
Orchestrates the complete scraping -> LLM -> alert pipeline.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "scrapper"))
sys.path.insert(0, str(BASE_DIR / "memory"))
sys.path.insert(0, str(BASE_DIR / "agent"))
sys.path.insert(0, str(BASE_DIR / "notifier"))

from scrapper.scraper import run_scraper
from scrapper.job_filter import filter_snippets_by_title
from scrapper.job_extractor import extract_job_details
from memory.job_database import (
    get_new_jobs,
    get_scraped_jobs_count,
    get_selected_jobs_count,
    init_db,
    insert_scraped_jobs,
    mark_scraped_jobs_llm_processed,
)
from agent.agent_loop import persist_selected_jobs, run_agent_decision, send_job_alerts
from utils.logger import get_logger
from utils.preferences_loader import load_preferences


def run_pipeline(conn, preferences: dict) -> dict:
    """
    Execute one full pipeline cycle.
    """
    logger = get_logger()
    summary = {
        "scraped_html_count": 0,
        "filtered_count": 0,
        "extracted_count": 0,
        "new_jobs_count": 0,
        "selected_count": 0,
        "alert_summary": {"total": 0, "success": 0, "failed": 0},
    }

    page = None
    browser = None
    playwright = None

    try:
        jobs, page, browser, playwright = run_scraper(return_page=True)
        summary["scraped_html_count"] = len(jobs)
        logger.info("[SCRAPER] Found %s HTML snippets", len(jobs))

        if not jobs:
            return summary

        filtered_jobs = filter_snippets_by_title(jobs)
        summary["filtered_count"] = len(filtered_jobs)
        logger.info("[FILTER] %s jobs after keyword filtering", len(filtered_jobs))
        if not filtered_jobs:
            return summary

        job_details = extract_job_details(filtered_jobs, page=page, base_url="")
        summary["extracted_count"] = len(job_details)
        logger.info("[EXTRACT] Extracted details for %s jobs", len(job_details))
        if not job_details:
            return summary

    finally:
        if browser is not None:
            browser.close()
        if playwright is not None:
            playwright.stop()

    inserted_scraped = insert_scraped_jobs(conn, job_details)
    logger.info("[DB] Inserted %s new job(s) into scraped_jobs", inserted_scraped)

    new_jobs = get_new_jobs(conn)
    summary["new_jobs_count"] = len(new_jobs)
    logger.info("[DB] %s unseen/new jobs ready for LLM", len(new_jobs))
    if not new_jobs:
        return summary

    selected_jobs = run_agent_decision(new_jobs, preferences)
    summary["selected_count"] = len(selected_jobs)
    logger.info("[LLM] Selected %s job(s)", len(selected_jobs))

    mark_scraped_jobs_llm_processed(conn, new_jobs)

    if selected_jobs:
        inserted_selected = persist_selected_jobs(conn, selected_jobs)
        logger.info("[DB] Inserted %s selected job(s) into selected_jobs", inserted_selected)

    alert_summary = send_job_alerts(conn)
    summary["alert_summary"] = alert_summary
    logger.info(
        "[ALERT] Completed - total=%s success=%s failed=%s",
        alert_summary["total"],
        alert_summary["success"],
        alert_summary["failed"],
    )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Agent Alerter production entrypoint")
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Legacy flag retained for backward compatibility (main.py always runs agent pipeline).",
    )
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=86400,
        help="Loop interval in seconds (default: 86400 / 24h)",
    )
    args = parser.parse_args()

    load_dotenv()
    logger = get_logger()
    logger.info("Job Agent starting from main entrypoint")

    try:
        preferences = load_preferences()
        logger.info("[PREFERENCES] Loaded preferences for user '%s'", preferences.get("user_name", "User"))
    except Exception as exc:
        logger.error("[ERROR] Failed to load preferences: %s", exc)
        raise

    db_path = BASE_DIR / "memory" / "jobs.db"
    conn = init_db(str(db_path))

    try:
        if args.loop:
            cycle = 0
            while True:
                cycle += 1
                logger.info("----- Agent cycle %s started -----", cycle)
                summary = run_pipeline(conn, preferences)
                logger.info(
                    "Cycle %s summary: scraped=%s filtered=%s extracted=%s new=%s selected=%s alerts(sent=%s,failed=%s)",
                    cycle,
                    summary["scraped_html_count"],
                    summary["filtered_count"],
                    summary["extracted_count"],
                    summary["new_jobs_count"],
                    summary["selected_count"],
                    summary["alert_summary"]["success"],
                    summary["alert_summary"]["failed"],
                )
                logger.info(
                    "[DB] Totals: scraped_jobs=%s selected_jobs=%s",
                    get_scraped_jobs_count(conn),
                    get_selected_jobs_count(conn),
                )
                logger.info("Sleeping for %s seconds", args.interval)
                time.sleep(args.interval)
        else:
            summary = run_pipeline(conn, preferences)
            logger.info(
                "Run summary: scraped=%s filtered=%s extracted=%s new=%s selected=%s alerts(sent=%s,failed=%s)",
                summary["scraped_html_count"],
                summary["filtered_count"],
                summary["extracted_count"],
                summary["new_jobs_count"],
                summary["selected_count"],
                summary["alert_summary"]["success"],
                summary["alert_summary"]["failed"],
            )
            logger.info(
                "[DB] Totals: scraped_jobs=%s selected_jobs=%s",
                get_scraped_jobs_count(conn),
                get_selected_jobs_count(conn),
            )

    except KeyboardInterrupt:
        logger.info("Agent stopped by user.")
    except Exception as exc:
        logger.exception("[ERROR] Pipeline execution failed: %s", exc)
        raise
    finally:
        conn.close()
        logger.info("Database connection closed. Exiting cleanly.")


if __name__ == "__main__":
    main()
