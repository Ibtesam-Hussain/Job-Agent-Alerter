"""
Configuration management for the job scraper.
Handles loading user-defined sites and other configuration.
"""

import json
import os


def load_user_sites():
    """Load user-defined sites from config file"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_sites.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user sites: {e}")
            return []
    return []