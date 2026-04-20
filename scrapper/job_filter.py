"""
Job filtering utilities based on keywords and titles.
"""

import ast
import os
from bs4 import BeautifulSoup


def load_role_keywords(keyword_file=None):
    """Load broad job role keywords from the keyword definition file."""
    if keyword_file is None:
        keyword_file = os.path.join(os.path.dirname(__file__), "job-role-keywords.txt")

    if not os.path.exists(keyword_file):
        print(f"Keyword file not found: {keyword_file}")
        return []

    with open(keyword_file, "r", encoding="utf-8") as f:
        file_text = f.read()

    try:
        parsed = ast.parse(file_text, filename=keyword_file)
        for node in parsed.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "BROAD_KEYWORDS":
                        value = ast.literal_eval(node.value)
                        if isinstance(value, list):
                            return [str(v) for v in value if isinstance(v, str)]
                        return []
    except Exception:
        pass

    # Fallback: simple text parsing
    keywords = []
    for line in file_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" not in stripped:
            stripped = stripped.strip(',').strip('"').strip("'")
            if stripped:
                keywords.append(stripped)
    return [kw for kw in keywords if kw]


def extract_job_title_from_html(html_content: str) -> str:
    """Extract the most likely job title from raw HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Prefer heading tags
    for tag_name in ["h1", "h2", "h3", "strong", "b"]:
        tag = soup.find(tag_name)
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)

    # Look for common title classes or id patterns
    for selector in [".job-title", ".title", ".position", ".role", ".job-name"]:
        tag = soup.select_one(selector)
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)

    # Fallback to first meaningful text line
    text = soup.get_text(separator="\n").strip()
    for line in text.splitlines():
        candidate = line.strip()
        if len(candidate) > 3 and len(candidate) < 120:
            return candidate

    return ""


def title_matches_keywords(title: str, keywords: list) -> bool:
    """Check if the extracted title contains any broad role keyword."""
    title_lower = title.lower()
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            return True
    return False


def filter_snippets_by_title(job_snippets: list, keyword_file=None) -> list:
    """Keep only job snippets whose title matches broad role keywords."""
    keywords = load_role_keywords(keyword_file)
    filtered = []
    for snippet in job_snippets:
        title = extract_job_title_from_html(snippet.get("html", ""))
        if title and title_matches_keywords(title, keywords):
            snippet["extracted_title"] = title
            filtered.append(snippet)
    return filtered