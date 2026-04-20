"""
Job data extraction utilities.
"""

from bs4 import BeautifulSoup


def extract_job_details(filtered_jobs: list) -> list:
    """Extract relevant job details from filtered job snippets."""
    extracted_jobs = []

    for job in filtered_jobs:
        html_content = job.get("html", "")
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract job title
        title = job.get("extracted_title", "")

        # Extract apply link
        apply_link = ""
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            link_text = link.get_text(strip=True).lower()
            if any(keyword in link_text for keyword in ["apply", "join", "submit", "application"]):
                apply_link = href
                break

        # If no specific apply link, take the first link
        if not apply_link:
            first_link = soup.find("a", href=True)
            if first_link:
                apply_link = first_link.get("href")

        # Normalize relative URLs
        if apply_link and not apply_link.startswith("http"):
            # We don't have the base URL here, so we'll leave it as-is
            pass

        # Extract source/company name
        source = job.get("source", "unknown")

        extracted_jobs.append({
            "title": title,
            "apply_link": apply_link,
            "source": source
        })

    return extracted_jobs