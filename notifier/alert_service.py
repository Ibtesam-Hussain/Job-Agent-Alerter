"""
Alert service for WhatsApp notifications based on selected job alerts.
"""

import sqlite3
from notifier.whatsapp_sender import send_whatsapp_message


def get_unalerted_jobs(conn):
    """
    Fetch selected jobs that have not been alerted yet.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, apply_link, snippet, score, reason FROM selected_jobs WHERE alerted = 0"
    )
    rows = cursor.fetchall()

    jobs = []
    for row in rows:
        jobs.append({
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "apply_link": row[2],
            "snippet": row[3],
            "score": row[4],
            "reason": row[5]
        })
    return jobs


def format_job_message(job):
    """
    Format a selected job into a WhatsApp-friendly alert message.
    """
    return (
        "🚀 New Job Alert\n\n"
        f"Role: {job.get('title', 'Unknown')}\n"
        f"Match Score: {job.get('score', 0)}/10\n\n"
        "Reason:\n"
        f"{job.get('reason', 'No reason provided')}\n\n"
        "Apply:\n"
        f"{job.get('link', 'No link provided')}\n\n"
        "Your JobAgent"
    )


def mark_job_alerted(conn, job_id):
    """
    Mark a selected job as alerted in the database.
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE selected_jobs SET alerted = 1 WHERE id = ?",
        (job_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


def send_job_alerts(conn):
    """
    Send WhatsApp alerts for unalerted jobs.
    """
    jobs = get_unalerted_jobs(conn)
    if not jobs:
        print("[ALERT] No new alerts to send.")
        return {
            "total": 0,
            "success": 0,
            "failed": 0
        }

    print(f"[ALERT] Sending alerts for {len(jobs)} job(s)...")
    success_count = 0
    failure_count = 0

    for job in jobs:
        message = format_job_message(job)
        print(f"[ALERT] Sending job id={job['id']} title={job['title']}")
        if send_whatsapp_message(message):
            if mark_job_alerted(conn, job['id']):
                success_count += 1
            else:
                print(f"[ALERT] Could not mark job id={job['id']} as alerted.")
                failure_count += 1
        else:
            print(f"[ALERT] Failed to send job id={job['id']}.")
            failure_count += 1

    print(f"[ALERT] Completed. Total={len(jobs)}, Success={success_count}, Failed={failure_count}")
    return {
        "total": len(jobs),
        "success": success_count,
        "failed": failure_count
    }
