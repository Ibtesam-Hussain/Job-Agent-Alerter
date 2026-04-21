"""
Database operations for scrapped jobs deduplication and storage.
"""

import sqlite3
import os
from datetime import datetime


def init_db(db_path="scrapped_jobs.db"):
    """Initialize the database and create jobs table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            apply_link TEXT UNIQUE,
            source TEXT NOT NULL,
            status TEXT DEFAULT 'seen',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    return conn


def is_job_exists(conn, link):
    """Check if a job with the given link already exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE apply_link = ?", (link,))
    return cursor.fetchone() is not None


def insert_job(conn, job):
    """Insert a job into the database if it doesn't already exist."""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO jobs (title, apply_link, source, status)
            VALUES (?, ?, ?, ?)
        ''', (job['title'], job['apply_link'], job['source'], 'seen'))

        conn.commit()
        return cursor.rowcount > 0  # Returns True if inserted, False if ignored
    except sqlite3.Error as e:
        print(f"Error inserting job: {e}")
        return False


def filter_new_jobs(conn, jobs):
    """Filter out jobs that already exist in the database."""
    new_jobs = []
    for job in jobs:
        if not is_job_exists(conn, job.get('apply_link', '')):
            new_jobs.append(job)
    return new_jobs


def get_all_jobs(conn):
    """Get all jobs from the database (for debugging/testing)."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    return cursor.fetchall()


def get_job_count(conn):
    """Get total number of jobs in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    return cursor.fetchone()[0]