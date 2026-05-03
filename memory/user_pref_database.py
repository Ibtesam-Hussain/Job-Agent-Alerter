"""
DEPRECATED: User preferences database module.

This module is retained for legacy compatibility only.
Active preference source is `config/user_preferences.json`.
"""

import sqlite3
import json
import os


# Default preferences (used when DB is empty)
DEFAULT_PREFERENCES = {
    "roles": ["qa", "automation", "test", "developer"],
    "tech": ["selenium", "python", "api", "playwright"],
    "keywords": ["qa", "automation", "testing", "engineer"],
    "exclude": ["manual", "non-technical", "intern"],
    "experience_level": ["junior", "mid", "senior"]
}


def get_connection(db_path=None):
    """
    Connect to user_preferences.db database.
    
    Args:
        db_path: Optional custom path for the database file.
                 Defaults to memory/user_preferences.db
        
    Returns:
        sqlite3.Connection: Database connection
    """
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), 'user_preferences.db')
    
    conn = sqlite3.connect(db_path)
    return conn


def init_user_pref_db(conn):
    """
    Create user_preferences table if it doesn't exist.
    
    Args:
        conn: Database connection
        
    Returns:
        bool: True if successful
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roles TEXT,
            tech TEXT,
            keywords TEXT,
            exclude TEXT,
            experience_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return True


def save_user_preferences(conn, prefs: dict):
    """
    Save user preferences into the database.
    Converts list fields to JSON strings for storage.
    
    Args:
        conn: Database connection
        prefs: Dictionary with keys: roles, tech, keywords, exclude, experience_level
        
    Returns:
        int: Number of rows inserted
    """
    cursor = conn.cursor()
    
    # Convert lists to JSON strings
    roles_json = json.dumps(prefs.get('roles', []))
    tech_json = json.dumps(prefs.get('tech', []))
    keywords_json = json.dumps(prefs.get('keywords', []))
    exclude_json = json.dumps(prefs.get('exclude', []))
    experience_json = json.dumps(prefs.get('experience_level', []))
    
    cursor.execute('''
        INSERT INTO user_preferences (roles, tech, keywords, exclude, experience_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        roles_json,
        tech_json,
        keywords_json,
        exclude_json,
        experience_json
    ))
    
    conn.commit()
    return cursor.rowcount


def get_latest_preferences(conn):
    """
    Fetch the most recent user preferences from the database.
    Converts JSON strings back to Python lists.
    
    Args:
        conn: Database connection
        
    Returns:
        dict: Preferences dictionary, or None if no preferences exist
    """
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT roles, tech, keywords, exclude, experience_level
        FROM user_preferences
        ORDER BY id DESC
        LIMIT 1
    ''')
    
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    # Convert JSON strings back to Python lists
    return {
        "roles": json.loads(row[0]) if row[0] else [],
        "tech": json.loads(row[1]) if row[1] else [],
        "keywords": json.loads(row[2]) if row[2] else [],
        "exclude": json.loads(row[3]) if row[3] else [],
        "experience_level": json.loads(row[4]) if row[4] else []
    }


def get_preferences_with_default(conn):
    """
    Get preferences, falling back to defaults if DB is empty.
    
    Args:
        conn: Database connection
        
    Returns:
        dict: User preferences or defaults
    """
    prefs = get_latest_preferences(conn)
    return prefs if prefs else DEFAULT_PREFERENCES.copy()


def update_preferences(conn, prefs: dict):
    """
    Replace existing preferences by inserting new ones.
    The latest row always takes priority (ORDER BY id DESC).
    
    Args:
        conn: Database connection
        prefs: Dictionary with preference fields
        
    Returns:
        int: Number of rows inserted
    """
    return save_user_preferences(conn, prefs)


def delete_all_preferences(conn):
    """
    Delete all preferences from the database.
    Use with caution!
    
    Args:
        conn: Database connection
        
    Returns:
        int: Number of rows deleted
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_preferences")
    conn.commit()
    return cursor.rowcount


def get_preferences_count(conn):
    """
    Get total number of preference records.
    
    Args:
        conn: Database connection
        
    Returns:
        int: Number of preference records
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_preferences")
    return cursor.fetchone()[0]


# Example usage
if __name__ == "__main__":
    # Test the module
    print("Testing user_pref_database module...")
    
    # Get connection
    conn = get_connection()
    
    # Initialize DB
    init_user_pref_db(conn)
    print("✓ Database initialized")
    
    # Save sample preferences
    sample_prefs = {
        "roles": ["qa", "automation engineer", "test engineer"],
        "tech": ["selenium", "python", "playwright", "api testing"],
        "keywords": ["qa", "automation", "testing"],
        "exclude": ["manual", "non-technical", "intern"],
        "experience_level": ["mid", "senior"]
    }
    
    save_user_preferences(conn, sample_prefs)
    print("✓ Preferences saved")
    
    # Retrieve preferences
    retrieved = get_latest_preferences(conn)
    print(f"✓ Retrieved preferences: {retrieved}")
    
    # Get with default fallback
    prefs_with_default = get_preferences_with_default(conn)
    print(f"✓ Preferences with default: {prefs_with_default}")
    
    # Close connection
    conn.close()
    
    print("\nAll tests passed!")