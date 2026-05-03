"""
JSON preference loader and validator.
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_PREFERENCES = {
    "user_name": "User",
    "target_roles": [],
    "skills": [],
    "work_mode": ["remote"],
    "locations": ["Remote"],
    "experience_level": "entry-mid",
    "min_match_score": 7,
}

REQUIRED_KEYS = ("user_name", "target_roles", "skills", "experience_level")
OPTIONAL_DEFAULTS = {
    "work_mode": DEFAULT_PREFERENCES["work_mode"],
    "locations": DEFAULT_PREFERENCES["locations"],
    "min_match_score": DEFAULT_PREFERENCES["min_match_score"],
}


def validate_preferences(data: dict) -> bool:
    """
    Validate user preferences schema.
    Raises:
        ValueError: when the payload is invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Preferences must be a JSON object.")

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(f"Missing required preference keys: {', '.join(missing)}")

    if not isinstance(data["user_name"], str) or not data["user_name"].strip():
        raise ValueError("'user_name' must be a non-empty string.")

    if not isinstance(data["target_roles"], list) or not all(isinstance(v, str) for v in data["target_roles"]):
        raise ValueError("'target_roles' must be a list of strings.")

    if not isinstance(data["skills"], list) or not all(isinstance(v, str) for v in data["skills"]):
        raise ValueError("'skills' must be a list of strings.")

    if not isinstance(data["experience_level"], str) or not data["experience_level"].strip():
        raise ValueError("'experience_level' must be a non-empty string.")

    if "work_mode" in data and (
        not isinstance(data["work_mode"], list) or not all(isinstance(v, str) for v in data["work_mode"])
    ):
        raise ValueError("'work_mode' must be a list of strings.")

    if "locations" in data and (
        not isinstance(data["locations"], list) or not all(isinstance(v, str) for v in data["locations"])
    ):
        raise ValueError("'locations' must be a list of strings.")

    if "min_match_score" in data:
        score = data["min_match_score"]
        if not isinstance(score, int) or score < 0 or score > 10:
            raise ValueError("'min_match_score' must be an integer between 0 and 10.")

    return True


def load_preferences() -> dict:
    """
    Load preferences from config/user_preferences.json with defaults for optional fields.
    """
    project_root = Path(__file__).resolve().parents[1]
    pref_path = project_root / "config" / "user_preferences.json"

    if not pref_path.exists():
        raise FileNotFoundError(
            f"Preferences file not found at '{pref_path}'. "
            "Create config/user_preferences.json before running the agent."
        )

    try:
        with pref_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in preferences file '{pref_path}': {exc}") from exc

    validate_preferences(raw_data)

    normalized = dict(raw_data)
    for key, default_value in OPTIONAL_DEFAULTS.items():
        if key not in normalized:
            normalized[key] = list(default_value) if isinstance(default_value, list) else default_value

    return normalized
