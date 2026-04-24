#!/usr/bin/env python3
"""
Main entry point for the Job Agent Alerter application.

This is just a CLI entry point that delegates to agent_loop.py.
All scraping, filtering, and processing logic is in the agent module.
"""

import argparse
import sys
import os

# Add project directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapper'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'memory'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from memory.job_database import init_db
from agent.agent_loop import run_agent, start_agent


# Default user preferences for LLM filtering
DEFAULT_PREFERENCES = {
    "roles": ["backend", "ai", "machine learning", "data science"],
    "tech": ["python", "django", "fastapi", "flask"],
    "exclude": ["frontend", "wordpress", "php"]
}


def main():
    """Main entry point - delegates to agent_loop.py"""
    parser = argparse.ArgumentParser(description="Job Agent Alerter - Scrape and filter job openings")
    parser.add_argument("--agent", action="store_true", help="Run in agent mode (uses LLM filtering)")
    parser.add_argument("--loop", action="store_true", help="Run agent in continuous loop")
    parser.add_argument("--interval", type=int, default=86400, help="Agent loop interval in seconds (default: 86400 = 24 hours)")
    args = parser.parse_args()

    # Initialize database
    db_path = os.path.join(os.path.dirname(__file__), 'memory', 'jobs.db')
    conn = init_db(db_path)

    try:
        if args.agent or args.loop:
            # Agent mode: Use LLM-based filtering
            print("\n=== Running in AGENT MODE ===")
            print("Using LLM decision engine for job filtering\n")
            
            if args.loop:
                # Continuous loop mode
                start_agent(conn, interval=args.interval, preferences=DEFAULT_PREFERENCES)
            else:
                # Single agent cycle
                results = run_agent(conn, preferences=DEFAULT_PREFERENCES)
                print(f"\nAgent cycle complete. Found {len(results)} relevant jobs.")
        else:
            # Standalone mode: Use agent_loop without LLM (basic scraping)
            print("\n=== Running in STANDALONE MODE ===")
            print("Basic scraping pipeline (no LLM filtering)\n")
            
            # Use agent_loop but with no preferences (skip LLM)
            results = run_agent(conn, preferences=None)
            print(f"\nStandalone cycle complete. Found {len(results)} new jobs.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
