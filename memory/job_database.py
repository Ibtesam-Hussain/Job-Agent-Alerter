"""
Database operations for job scraping pipeline with clean architecture.
Uses separate tables for scraped jobs and LLM-selected jobs.
"""

import sqlite3
import os
from datetime import datetime


def _table_has_column(conn, table: str, column: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def init_db(db_path="jobs.db"):
    """
    Initialize the database and create both tables if they don't exist.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table 1: scraped_jobs - stores ALL scraped jobs (for deduplication)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            apply_link TEXT UNIQUE,
            snippet TEXT,
            source TEXT NOT NULL,
            status TEXT DEFAULT 'seen',
            llm_processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 2: selected_jobs - stores ONLY LLM-selected relevant jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selected_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            apply_link TEXT UNIQUE,
            snippet TEXT,
            score INTEGER,
            reason TEXT,
            alerted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Migrate older DBs that predate llm_processed tracking
    if not _table_has_column(conn, "scraped_jobs", "llm_processed"):
        cursor.execute("ALTER TABLE scraped_jobs ADD COLUMN llm_processed INTEGER DEFAULT 0")
        conn.commit()

    # Backfill: anything already selected should not be re-sent to the LLM
    cursor.execute('''
        UPDATE scraped_jobs
        SET llm_processed = 1
        WHERE apply_link IN (SELECT apply_link FROM selected_jobs)
    ''')
    conn.commit()

    return conn


def insert_scraped_jobs(conn, jobs):
    """
    Insert ALL jobs into scraped_jobs table.
    Uses INSERT OR IGNORE to avoid overwriting existing rows.
    
    Args:
        conn: Database connection
        jobs: List of job dictionaries with keys: title, apply_link, snippet, source
        
    Returns:
        int: Number of jobs actually inserted
    """
    cursor = conn.cursor()
    inserted_count = 0
    
    for job in jobs:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO scraped_jobs (title, apply_link, snippet, source, status, llm_processed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job.get('title', ''),
                job.get('apply_link', job.get('link', '')),
                job.get('snippet', ''),
                job.get('source', ''),
                job.get('status', 'seen'),
                int(job.get('llm_processed', 0) or 0),
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
        except sqlite3.Error as e:
            print(f"Error inserting scraped job: {e}")
    
    conn.commit()
    print(f"[DB] Scraped jobs inserted: {inserted_count}/{len(jobs)}")
    return inserted_count


def get_new_jobs(conn):
    """
    Get jobs from scraped_jobs that have not been processed by the LLM yet.
    This prevents rejected/non-selected scraped jobs from being re-sent every cycle.
    Includes snippet from scraped_jobs.
    
    Args:
        conn: Database connection
        
    Returns:
        list: List of job dictionaries that haven't been selected yet
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.title, s.apply_link, s.snippet, s.source, s.created_at
        FROM scraped_jobs s
        WHERE (s.llm_processed IS NULL OR s.llm_processed = 0)
          AND s.apply_link IS NOT NULL
          AND TRIM(s.apply_link) != ''
        ORDER BY s.created_at DESC
    ''')
    
    rows = cursor.fetchall()
    jobs = []
    for row in rows:
        jobs.append({
            'id': row[0],
            'title': row[1],
            'apply_link': row[2],
            'snippet': row[3],  # Include snippet from scraped_jobs
            'source': row[4],
            'created_at': row[5]
        })
    
    print(f"[DB] New jobs for LLM: {len(jobs)}")
    return jobs


def mark_scraped_jobs_llm_processed(conn, jobs):
    """
    Mark scraped_jobs rows as processed by the LLM for the given job dicts.
    Uses apply_link as the key.
    """
    cursor = conn.cursor()
    links = []
    for job in jobs or []:
        link = job.get("apply_link") or job.get("link") or ""
        link = (link or "").strip()
        if link:
            links.append(link)

    if not links:
        return 0

    placeholders = ",".join(["?"] * len(links))
    cursor.execute(
        f'''
        UPDATE scraped_jobs
        SET llm_processed = 1
        WHERE apply_link IN ({placeholders})
        ''',
        links,
    )
    conn.commit()
    return cursor.rowcount


def insert_selected_jobs(conn, jobs):
    """
    Insert LLM-selected jobs into selected_jobs table.
    Uses INSERT OR IGNORE to avoid duplicates.
    
    Args:
        conn: Database connection
        jobs: List of job dictionaries with keys: title, apply_link, snippet, score, reason
        
    Returns:
        int: Number of jobs actually inserted
    """
    cursor = conn.cursor()
    inserted_count = 0
    
    for job in jobs:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO selected_jobs (title, apply_link, snippet, score, reason, alerted)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job.get('title', ''),
                job.get('apply_link', job.get('link', '')),
                job.get('snippet', ''),
                job.get('score', 0),
                job.get('reason', ''),
                job.get('alerted', 0)
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
        except sqlite3.Error as e:
            print(f"Error inserting selected job: {e}")
    
    conn.commit()
    print(f"[DB] Selected jobs inserted: {inserted_count}/{len(jobs)}")
    return inserted_count


def get_selected_jobs(conn, alerted=None):
    """
    Get all selected jobs from the database.
    
    Args:
        conn: Database connection
        alerted: Optional filter - True for alerted, False for not alerted, None for all
        
    Returns:
        list: List of selected job dictionaries
    """
    cursor = conn.cursor()
    
    if alerted is None:
        cursor.execute("SELECT * FROM selected_jobs ORDER BY created_at DESC")
    elif alerted:
        cursor.execute("SELECT * FROM selected_jobs WHERE alerted = 1 ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM selected_jobs WHERE alerted = 0 ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    jobs = []
    for row in rows:
        jobs.append({
            'id': row[0],
            'title': row[1],
            'apply_link': row[2],
            'snippet': row[3],
            'score': row[4],
            'reason': row[5],
            'alerted': row[6],
            'created_at': row[7]
        })
    
    return jobs


def mark_alerted(conn, job_id):
    """
    Mark a selected job as alerted.
    
    Args:
        conn: Database connection
        job_id: ID of the job to mark
        
    Returns:
        bool: True if updated, False otherwise
    """
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE selected_jobs SET alerted = 1 WHERE id = ?", (job_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error marking job as alerted: {e}")
        return False


def get_scraped_jobs_count(conn):
    """Get total number of scraped jobs in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scraped_jobs")
    return cursor.fetchone()[0]


def get_selected_jobs_count(conn):
    """Get total number of selected jobs in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM selected_jobs")
    return cursor.fetchone()[0]


def get_all_scraped_jobs(conn):
    """Get all scraped jobs from the database (for debugging/testing)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_jobs ORDER BY created_at DESC")
    return cursor.fetchall()


# Legacy functions for backward compatibility
def is_job_exists(conn, link):
    """Check if a job with the given link already exists in scraped_jobs."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM scraped_jobs WHERE apply_link = ?", (link,))
    return cursor.fetchone() is not None


def insert_job(conn, job):
    """Insert a job into scraped_jobs (legacy compatibility)."""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO scraped_jobs (title, apply_link, source, snippet, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            job.get('title', ''),
            job.get('apply_link', ''),
            job.get('source', ''),
            job.get('snippet', ''),
            job.get('status', 'seen')
        ))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error inserting job: {e}")
        return False


def filter_new_jobs(conn, jobs):
    """Filter out jobs that already exist in scraped_jobs (legacy compatibility)."""
    new_jobs = []
    for job in jobs:
        if not is_job_exists(conn, job.get('apply_link', '')):
            new_jobs.append(job)
    return new_jobs


def get_all_jobs(conn):
    """Get all jobs from the database (for debugging/testing)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_jobs ORDER BY created_at DESC")
    return cursor.fetchall()


def get_job_count(conn):
    """Get total number of scraped jobs (legacy compatibility)."""
    return get_scraped_jobs_count(conn)