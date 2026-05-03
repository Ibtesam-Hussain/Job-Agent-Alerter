"""
Reusable business logic for LLM decisioning + alert dispatch.
No direct process entrypoint is defined in this module.
"""

from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "memory"))
sys.path.insert(0, str(BASE_DIR / "notifier"))

from agent.decision_engine import filter_jobs_with_llm
from memory.job_database import insert_selected_jobs
from notifier.alert_service import send_job_alerts as notifier_send_job_alerts
from utils.logger import get_logger


def _build_llm_preferences(preferences: dict) -> dict:
    """
    Normalize JSON preferences to decision_engine expected format.
    """
    target_roles = preferences.get("target_roles") or preferences.get("roles") or []
    skills = preferences.get("skills") or preferences.get("tech") or []
    exclude = preferences.get("exclude") or []
    return {
        "roles": target_roles,
        "tech": skills,
        "exclude": exclude,
    }


def _apply_min_match_score(jobs: list, min_score: int) -> list:
    selected = []
    for job in jobs:
        score = job.get("score", 0)
        if isinstance(score, (int, float)) and score >= min_score:
            selected.append(job)
    return selected


def run_agent_decision(new_jobs: list, preferences: dict) -> list:
    """
    Run LLM decisioning over unseen jobs.

    Args:
        new_jobs: Jobs that have not yet reached selected_jobs table.
        preferences: JSON-based preferences loaded from config.

    Returns:
        LLM selected jobs with snippet/apply_link normalized.
    """
    logger = get_logger()
    if not new_jobs:
        return []

    llm_preferences = _build_llm_preferences(preferences)
    min_score = int(preferences.get("min_match_score", 7))
    llm_jobs = filter_jobs_with_llm(new_jobs, llm_preferences)
    logger.info("[LLM] Decision engine returned %s candidate jobs", len(llm_jobs))

    selected_jobs = _apply_min_match_score(llm_jobs, min_score)

    # Preserve snippet + apply_link from original job payload.
    lookup = {job.get("apply_link", ""): job for job in new_jobs if job.get("apply_link")}
    for job in selected_jobs:
        link = job.get("apply_link") or job.get("link", "")
        if "apply_link" not in job:
            job["apply_link"] = link
        original = lookup.get(link)
        if original:
            job["snippet"] = original.get("snippet", "")
            job["source"] = original.get("source", "")

    logger.info("[LLM] Selected %s job(s) with min score %s", len(selected_jobs), min_score)
    return selected_jobs


def persist_selected_jobs(conn, jobs: list) -> int:
    """
    Persist LLM-selected jobs to selected_jobs table.
    Skips DB writes when decisions are rate-limit fallback results.
    """
    logger = get_logger()
    if not jobs:
        return 0

    is_rate_limited = any("Rate limited" in str(job.get("reason", "")) for job in jobs)
    if is_rate_limited:
        logger.error("[ERROR] LLM rate limited, skipping selected_jobs write for this cycle")
        return 0

    inserted_count = insert_selected_jobs(conn, jobs)
    return inserted_count


def send_job_alerts(conn) -> dict:
    """
    Send WhatsApp alerts for unalerted jobs and return summary.
    """
    logger = get_logger()
    logger.info("[ALERT] Triggering WhatsApp delivery for unalerted jobs")
    result = notifier_send_job_alerts(conn)
    logger.info(
        "[ALERT] Delivery result total=%s success=%s failed=%s",
        result["total"],
        result["success"],
        result["failed"],
    )
    return result