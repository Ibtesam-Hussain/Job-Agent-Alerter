"""
Job data extraction utilities.
"""

from bs4 import BeautifulSoup


def extract_snippet_from_html(html_content: str) -> str:
    """Extract snippet from job card HTML (Step 1 - Primary)."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Priority-based element selection
    for selector in ["p", "span", "div"]:
        elements = soup.select(selector)
        for el in elements:
            text = el.get_text(strip=True)
            # Take first meaningful text (50-250 chars)
            if text and 20 <= len(text) <= 500:
                return clean_snippet(text[:250])
    
    return ""


def clean_snippet(text: str) -> str:
    """Clean snippet: remove extra whitespace and newlines."""
    if not text:
        return ""
    # Replace multiple whitespace/newlines with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_snippet_from_detail_page(page, apply_link: str, base_url: str = "") -> str:
    """Extract snippet from job detail page (Step 2 - Fallback)."""
    try:
        # Handle relative URLs
        full_url = apply_link
        if not apply_link.startswith("http"):
            if base_url:
                from urllib.parse import urljoin
                full_url = urljoin(base_url, apply_link)
        
        if full_url.startswith("http"):
            page.goto(full_url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            # Try to get content from common job description areas
            for selector in [".job-description", ".description", "#job-description", "main", "article"]:
                try:
                    content = page.locator(selector).inner_text()
                    if content and len(content) > 50:
                        return clean_snippet(content[:250])
                except:
                    continue
            
            # Fallback to body text
            content = page.inner_text("body")
            if content:
                return clean_snippet(content[:250])
    except Exception as e:
        print(f"      Could not extract from detail page: {e}")
    
    return ""


def extract_job_details(filtered_jobs: list, page=None, base_url: str = "") -> list:
    """
    Extract relevant job details from filtered job snippets.
    
    Args:
        filtered_jobs: List of job dictionaries with HTML content
        page: Playwright page object (optional, for detail page extraction)
        base_url: Base URL for handling relative links
    
    Returns:
        List of job dictionaries with title, apply_link, source, snippet
    """
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

        # Extract source/company name
        source = job.get("source", "unknown")

        # Extract snippet (Step 1 - Primary: from job card HTML)
        snippet = extract_snippet_from_html(html_content)
        
        # Step 2 - Fallback: Visit detail page if snippet is empty
        if not snippet and page and apply_link:
            snippet = extract_snippet_from_detail_page(page, apply_link, base_url)

        extracted_jobs.append({
            "title": title,
            "apply_link": apply_link,
            "source": source,
            "snippet": snippet
        })

    return extracted_jobs