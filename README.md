Making an agentic ai system that will tell me about jobs from n number of company's career pages. So, i dont miss the oppurtunity at the right time :)

## Scraping Pipeline Completed

The following steps have been implemented:

1. Web Scraping - Playwright-based automated browser scraping with URL reachability checks and selector detection
2. HTML Parsing - BeautifulSoup processing to clean and format HTML content
3. Job Filtering - Keyword-based filtering using job-role-keywords.txt to identify relevant positions
4. Details Extraction - Extraction of job title, apply link, and source information
5. Database Deduplication - SQLite-based storage with automatic duplicate job detection and filtering
6. Output Formatting - JSON output of extracted job details
7. Configuration Management - Support for default and user-defined job sites
8. Modular Architecture - Clean separation into 7 focused modules with main.py as single entry point

## Database Integration Added

SQLite database integration with deduplication functionality:

- Database file: `memory/jobs.db`
- Table schema: jobs (id, title, apply_link UNIQUE, source, status, created_at)
- Functions: init_db(), is_job_exists(), insert_job(), filter_new_jobs()
- Pipeline integration: Only new jobs proceed to output, duplicates are filtered out
- Although, all the scrapped + filtered job (via generic keywords) will remain stored in db
- Just for LLM, only new jobs will go to it which will be cost effective for us.
- Automatic insertion of new jobs with status tracking

Usage: python main.py [--save-json OUTPUT_FILE]

## LLM Integration Added

OpenRouter API integration for intelligent job filtering:

- Decision Engine: `agent/decision_engine.py` - Uses gpt-oss-120b:free model
- LLM Filtering: Scores jobs 0-10 based on user preferences
- Rate Limit Handling: Automatic fallback to pass-through mode when rate limited
- User Preferences: Stored in `memory/user_preferences.db` table (user_preferences)
- Preferences include: roles, tech, keywords, exclude, experience_level
- Functions: get_preferences_from_db(), filter_jobs_with_llm()

## Database Architecture Refactored

Clean separation with two tables in `memory/jobs.db`:

### scraped_jobs table
- Stores ALL scraped jobs for deduplication
- Schema: id, title, apply_link UNIQUE, snippet, source, status, created_at
- Functions: insert_scraped_jobs(), get_new_jobs()

### selected_jobs table
- Stores ONLY LLM-selected relevant jobs (final output)
- Schema: id, title, apply_link UNIQUE, snippet, score, reason, alerted, created_at
- Functions: insert_selected_jobs(), get_selected_jobs(), mark_alerted()

Pipeline: scraped_jobs → get_new_jobs() → LLM → selected_jobs

## Agent Orchestration

Main agent loop in `agent/agent_loop.py`:

- 5-stage pipeline: SCRAPING → FILTERING → EXTRACTING → SAVING → LLM
- Preferences loaded from user_preferences.db automatically
- Rate limit protection: skips DB save when LLM unavailable
- Snippet preservation: snippets carried through from scraped to selected jobs
- Run modes: python agent/agent_loop.py (single) or python main.py --agent --loop

