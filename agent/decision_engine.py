"""
Decision engine using OpenAI API to filter relevant jobs based on user preferences.

Note:
- Preferred source for preferences is `config/user_preferences.json`.
- DB-based preference loading is deprecated and retained only for legacy compatibility.
"""

import json
import os
import sys
import warnings
from dotenv import load_dotenv
from openai import OpenAI

# Add memory directory to path for user preferences DB
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory'))
from user_pref_database import (
    get_connection as get_user_pref_connection,
    init_user_pref_db,
    get_preferences_with_default
)

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()


# Default user preferences (can be overridden)
DEFAULT_PREFERENCES = {
    "roles": ["backend", "ai", "machine learning"],
    "tech": ["python", "django"],
    "exclude": ["frontend", "wordpress"]
}


def get_preferences_from_db():
    """
    DEPRECATED: load preferences from SQLite.

    Prefer loading preferences from `config/user_preferences.json` and passing
    them into `filter_jobs_with_llm(..., preferences=...)`.

    Get user preferences from the database.
    Falls back to DEFAULT_PREFERENCES if DB is empty or unavailable.
    
    Returns:
        dict: User preferences
    """
    warnings.warn(
        "get_preferences_from_db() is deprecated. Use JSON config preferences instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        conn = get_user_pref_connection()
        init_user_pref_db(conn)
        prefs = get_preferences_with_default(conn)
        conn.close()
        return prefs
    except Exception as e:
        print(f"Warning: Could not load preferences from DB: {e}")
        return DEFAULT_PREFERENCES.copy()


def filter_jobs_with_llm(jobs, preferences=None):
    """
    Filter relevant jobs using OpenAI LLM based on user preferences.
    
    Args:
        jobs: List of job dictionaries with title, apply_link, source
        preferences: Dict with roles, tech, exclude keys (optional).
                     Preferred source is config/user_preferences.json.
                     If None, loads from user_preferences.db (deprecated fallback).
    
    Returns:
        List of filtered jobs with score >= 7
    """
    if not jobs:
        return []
    
    # If no preferences provided, load from database
    if preferences is None:
        preferences = get_preferences_from_db()
        print(f"[LLM] Using preferences from DB: {preferences.get('roles', [])[:3]}...")
    
    # Initialize OpenAI client with OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    
    # Build the prompt
    prompt = build_filter_prompt(jobs, preferences)
    
    try:
        # Calling OpenRouter API with gpt-oss-120b model
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a job matching assistant that filters job listings based on user preferences. Return ONLY valid JSON array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=4000,
            extra_body={"reasoning": {"enabled": True}}
        )
        
        # Extract response content
        content = response.choices[0].message.content
        
        # Parse JSON safely
        filtered_jobs = parse_llm_response(content)
        
        # Filter by minimum score
        return [job for job in filtered_jobs if job.get("score", 0) >= 7]
    
    except Exception as e:
        error_msg = str(e)
        if "429" or "503" in error_msg or "rate-limited" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"[LLM] Rate limit exceeded - Free model is temporarily unavailable.")
            print(f"[LLM] Please wait a moment or add your own API key to OpenRouter.")
            print(f"[LLM] Falling back to pass-through (all jobs accepted)")
            # Return all jobs without filtering when rate limited
            for job in jobs:
                job['score'] = 'Cannot score - rate limited'
                job['reason'] = 'Rate limited - auto-accepted'
            return jobs
        else:
            print(f"[LLM] Error calling OpenRouter API: {e}")
            return []


def build_filter_prompt(jobs, preferences):
    """Build the prompt for the LLM with jobs and preferences."""
    roles = preferences.get("roles", [])
    tech = preferences.get("tech", [])
    exclude = preferences.get("exclude", [])
    
    prompt = f"""You are a job matching assistant. Filter jobs based on user preferences.

User Preferences:
- Roles interested in: {', '.join(roles)}
- Tech stack preferred: {', '.join(tech)}
- Exclude these: {', '.join(exclude)}

Jobs to evaluate:
{json.dumps(jobs, indent=2)}

Instructions:
1. Evaluate each job against the user preferences
2. Consider job title, description, and source
3. Score each job from 0-10 based on relevance
4. Provide a brief reason for the score

Return ONLY a JSON array with this exact structure (no other text):
[
  {{
    "title": "job title",
    "link": "apply_link",
    "score": 8,
    "reason": "short explanation"
  }}
]

Only include jobs with score >= 7. Return empty array if no relevant jobs."""
    
    return prompt


def parse_llm_response(content):
    """Safely parse the LLM JSON response."""
    if not content:
        return []
    
    try:
        # Try to find JSON array in the response
        content = content.strip()
        
        # Handle cases where LLM might wrap JSON in markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        return json.loads(content)
    
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}")
        print(f"Response content: {content[:500]}...")
        return []


# Example usage
if __name__ == "__main__":
    # Test loading preferences from database
    print("Testing decision engine with database preferences...")
    
    # Load preferences from DB (or use defaults)
    prefs = get_preferences_from_db()
    print(f"Loaded preferences: {prefs}")
    
    # Sample jobs for testing
    sample_jobs = [
        {
            "title": "Senior Python Backend Developer",
            "apply_link": "https://example.com/job1",
            "source": "Company A",
            "snippet": "We are looking for a Python developer with Django experience..."
        },
        {
            "title": "Frontend React Developer",
            "apply_link": "https://example.com/job2",
            "source": "Company B",
            "snippet": "React developer needed for frontend work..."
        },
        {
            "title": "AI/ML Engineer",
            "apply_link": "https://example.com/job3",
            "source": "Company C",
            "snippet": "Machine learning engineer with Python skills..."
        }
    ]
    
    # Note: Requires OPENROUTER_API_KEY environment variable
    # filtered = filter_jobs_with_llm(sample_jobs, prefs)
    # print(json.dumps(filtered, indent=2))
    
    print("Decision engine module loaded.")
    print("To use: set OPENROUTER_API_KEY env var and call filter_jobs_with_llm(jobs)")
    print("Preferences will be loaded from user_preferences.db automatically.")