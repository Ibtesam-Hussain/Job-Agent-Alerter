"""
Agent orchestration layer - the brain of the job monitoring system.
Coordinates scraping, database, and LLM decision engine.
"""

import sys
import os
import time
import json

# Add project directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapper'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent'))

from scraper import run_scraper
from job_filter import filter_snippets_by_title
from job_extractor import extract_job_details
from memory.job_database import (
    init_db,
    insert_scraped_jobs,
    get_new_jobs,
    insert_selected_jobs,
    get_scraped_jobs_count,
    get_selected_jobs_count
)
from memory.user_pref_database import (
    get_connection as get_user_pref_connection,
    init_user_pref_db,
    get_preferences_with_default
)
from decision_engine import filter_jobs_with_llm, get_preferences_from_db


def run_agent(conn, preferences=None):
    """
    Main agent function that orchestrates the job monitoring pipeline.
    
    Args:
        conn: SQLite database connection
        preferences: Optional user preferences for LLM filtering
    
    Returns:
        List of relevant jobs found (score >= 7)
    """
    print("\n" + "=" * 60)
    print("Starting Agent Cycle")
    print("=" * 60)
    
    # Stage 1: Scraping (keep page open for detail page extraction)
    print("\n[1/5] SCRAPING: Fetching jobs from configured sites...")
    jobs, page, browser, playwright = run_scraper(return_page=True)
    print(f"      Total HTML snippets found: {len(jobs)}")
    
    if not jobs:
        print("No jobs found during scraping.")
        browser.close()
        playwright.stop()
        return []
    
    # Stage 2: Keyword Filtering
    print("\n[2/5] FILTERING: Applying keyword filters...")
    filtered_jobs = filter_snippets_by_title(jobs)
    print(f"      Jobs after keyword filter: {len(filtered_jobs)}")
    
    if not filtered_jobs:
        print("No jobs matched the keyword filter.")
        return []
    
    # Stage 3: Extract Details (with page for detail page fallback)
    print("\n[3/5] EXTRACTING: Extracting job details...")
    job_details = extract_job_details(filtered_jobs, page=page, base_url="")
    print(f"      Job details extracted: {len(job_details)}")

    # Close browser and stop playwright properly
    browser.close()
    playwright.stop()
    
    # Stage 4: Insert ALL scraped jobs into scraped_jobs table
    print("\n[4/5] SAVING: Inserting all scraped jobs into database...")
    insert_scraped_jobs(conn, job_details)
    
    # Get new jobs (not already in selected_jobs) for LLM processing
    new_jobs = get_new_jobs(conn)
    print(f"      New jobs for LLM: {len(new_jobs)}")
    
    if not new_jobs:
        print("\nNo new jobs found. All scraped jobs already processed.")
        return []
    
    # Stage 5: LLM Decision Engine (only if preferences provided)
    if preferences:
        print("\n[5/5] LLM PROCESSING: Analyzing jobs with AI...")
        relevant_jobs = filter_jobs_with_llm(new_jobs, preferences)
        print(f"      Relevant jobs (score >= 7): {len(relevant_jobs)}")
        
        if not relevant_jobs:
            print("No jobs matched user preferences.")
            return []
        
        # Check if rate-limited (don't save to DB on rate limit)
        is_rate_limited = any('Rate limited' in job.get('reason', '') for job in relevant_jobs)
        if is_rate_limited:
            print("[LLM] Rate limited - skipping DB save, only showing in console")
            # Still return jobs for console display but don't save to DB
            return relevant_jobs
        
        # Preserve snippet from original new_jobs
        for job in relevant_jobs:
            link = job.get('apply_link', job.get('link', ''))
            for original_job in new_jobs:
                if original_job.get('apply_link') == link or original_job.get('link') == link:
                    job['snippet'] = original_job.get('snippet', '')
                    break
        
        # Insert selected jobs into selected_jobs table
        insert_selected_jobs(conn, relevant_jobs)
    else:
        # No preferences - use all new jobs (standalone mode)
        print("\n[5/5] STANDALONE MODE: No LLM filtering, using all new jobs...")
        relevant_jobs = new_jobs
        print(f"      New jobs to process: {len(relevant_jobs)}")
        
        # Insert as selected jobs (with default score)
        for job in relevant_jobs:
            job['score'] = 10
            job['reason'] = 'Manual (no LLM filtering)'
        insert_selected_jobs(conn, relevant_jobs)
    
    # Print alert messages for new relevant jobs
    print("\n" + "=" * 60)
    print("NEW JOB ALERTS")
    print("=" * 60)
    for job in relevant_jobs:
        print(f"\n>>> NEW JOB: {job.get('title', 'Unknown')}")
        print(f"    Link: {job.get('link', job.get('apply_link', 'N/A'))}")
        if preferences and 'score' in job:
            print(f"    Score: {job.get('score', 'N/A')}/10")
            print(f"    Reason: {job.get('reason', 'No reason provided')}")
        else:
            print(f"    Source: {job.get('source', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Agent Cycle Complete")
    print("=" * 60)
    
    return relevant_jobs


def start_agent(conn, interval=86400, preferences=None):
    """
    Start the agent in a continuous loop.
    
    Args:
        conn: SQLite database connection
        interval: Sleep interval in seconds (default 24 hours = 86400)
        preferences: Optional user preferences for LLM filtering
    
    Note:
        - Press Ctrl+C to stop the agent
        - Each cycle runs the full pipeline: scrape -> filter -> dedupe -> LLM -> save
    """
    print("\n" + "=" * 60)
    print("JOB AGENT STARTED")
    print("=" * 60)
    print(f"Running interval: {interval} seconds ({interval // 3600} hours)")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n\n>>> CYCLE #{cycle_count} <<<")
            
            try:
                run_agent(conn, preferences)
            except Exception as e:
                print(f"Error in agent cycle: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\nSleeping for {interval} seconds...")
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user.")
        print(f"Total cycles completed: {cycle_count}")


# Default user preferences (loaded from DB, with fallback)
def get_default_preferences():
    """Get preferences from database or return defaults."""
    try:
        pref_conn = get_user_pref_connection()
        init_user_pref_db(pref_conn)
        prefs = get_preferences_with_default(pref_conn)
        pref_conn.close()
        print(f"[PREFERENCES] Loaded from DB: roles={prefs.get('roles', [])[:2]}...")
        return prefs
    except Exception as e:
        print(f"[PREFERENCES] Using hardcoded defaults: {e}")
        return {
            "roles": ["qa", "automation", "test"],
            "tech": ["selenium", "python", "api"],
            "exclude": ["manual", "non-technical"]
        }


# Example usage
if __name__ == "__main__":
    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'memory', 'jobs.db')
    conn = init_db(db_path)
    
    # Load preferences from DB
    prefs = get_default_preferences()
    
    try:
        # Run single agent cycle
        print("Running single agent cycle (for testing)...")
        results = run_agent(conn, prefs)
        # print(f"\nFinal results: {len(results)} relevant jobs")
        
    finally:
        conn.close()
    
    # To run continuous loop:
    # start_agent(conn, interval=86400, preferences=get_default_preferences())