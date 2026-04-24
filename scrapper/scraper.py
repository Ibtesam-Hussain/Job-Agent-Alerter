"""
Core web scraping functionality using Playwright.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from playwright.sync_api import sync_playwright
from sites_configs import DEFAULT_SITES
from config_manager import load_user_sites
from utils.test_url_reachability import test_url_reachability
from utils.discover_job_selectors import discover_job_selectors


def scrape_site(page, site):
    """Scrape job listings from a single site."""
    print(f"Scraping {site['name']}...")

    # First test if URL is reachable
    if not test_url_reachability(site["url"]):
        print(f"xxxxx URL not reachable: {site['url']}")
        return []

    try:
        # Add user agent to avoid bot detection
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

        print(f"  Navigating to: {site['url']}")
        response = page.goto(site["url"], timeout=60000, wait_until="domcontentloaded")

        if response.status >= 400:
            print(f"xxxx HTTP Error: {response.status} - {response.status_text}")
            return []

        print(f"  ✓ Page loaded successfully (status: {response.status})")

        # Wait for network to be idle and some extra time
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(3000)

        # Try known selector first, then auto-discover
        elements = []
        selector_used = ""

        if "job_selector" in site and site["job_selector"]:
            # Known site with hardcoded selector
            try:
                elements = page.query_selector_all(site["job_selector"])
                selector_used = site["job_selector"]
                print(f"  ✓ Using known selector: {selector_used} ({len(elements)} elements)")
            except Exception as e:
                print(f"xxxx Known selector failed: {e}")
                elements = []

        if not elements:
            # Auto-discover selectors for unknown sites
            print(f"  Auto-discovering selectors for {site['name']}...")
            selector_used, elements = discover_job_selectors(page, site["url"])

        if not elements:
            print(f"xxxx No job elements found on {site['name']}")
            print(f"  Page URL: {site['url']}")
            print(f"  Page content length: {len(page.content())}")

            # Debug: show some page content
            body_text = page.locator("body").text_content()[:500]
            print(f"  Page body preview: {body_text}...")
            return []

        jobs = []
        for idx, el in enumerate(elements, start=1):
            try:
                html_snippet = el.inner_html()
                jobs.append({
                    "source": site["name"],
                    "selector": selector_used or site.get("job_selector", "unknown"),
                    "html": html_snippet,
                })
                print(f"  ✓ Captured HTML for element #{idx}")
            except Exception as e:
                print(f"xxxx Error extracting HTML for element #{idx}: {e}")
                continue

        print(f"  ✓ Collected {len(jobs)} HTML snippets from {site['name']}")
        return jobs

    except Exception as e:
        print(f"xxxx Error scraping {site['name']}: {e}")
        print(f"  Error type: {type(e).__name__}")
        return []


def run_scraper(return_page=False):
    """
    Run the complete scraping process across all configured sites.
    
    Args:
        return_page: If True, returns (jobs, page, browser, playwright) tuple for further processing
                   If False, returns just jobs and auto-closes browser
    
    Returns:
        If return_page=False: List of job dictionaries
        If return_page=True: Tuple of (jobs, page, browser, playwright)
    """
    # Combine default sites with user-added sites
    user_sites = load_user_sites()
    all_sites = DEFAULT_SITES + user_sites

    all_jobs = []

    if return_page:
        # Don't use context manager - keep browser alive for detail page extraction
        p = sync_playwright().start()
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        page = browser.new_page()

        for site in all_sites:
            try:
                jobs = scrape_site(page, site)
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error with {site['name']}: {e}")

        return all_jobs, page, browser, p
    else:
        with sync_playwright() as p:
            # Launch browser with more permissive settings
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            page = browser.new_page()

            for site in all_sites:
                try:
                    jobs = scrape_site(page, site)
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"Error with {site['name']}: {e}")

            browser.close()

        return all_jobs
    

if __name__ == "__main__":
    print("Starting scraper...")
    jobs = run_scraper()
    print(f"Scraping complete. Total jobs collected: {len(jobs)}")
    