def discover_job_selectors(page, site_url):
    """Try common job listing selectors to find job containers"""
    common_selectors = [
        ".job-listing", ".jobs-list", ".job-item", ".career-item",
        ".position", ".opening", ".vacancy", ".job-card",
        "article.job", "div.job", ".job-posting",
        ".careers-listing", ".job-container", ".jobs-box",
        "tr.job", ".new-listing-container li",
        ".job-list-item", ".career-opportunity"
    ]

    for selector in common_selectors:
        try:
            elements = page.query_selector_all(selector)
            if len(elements) > 0 and len(elements) < 50:  # Reasonable number of jobs
                print(f"  ✓ Found {len(elements)} jobs with selector: {selector}")
                return selector, elements
        except:
            continue

    # Fallback: try to find any container with job-related text
    try:
        all_divs = page.query_selector_all("div, article, section")
        job_divs = []
        for div in all_divs[:20]:  # Check first 20 containers
            text = div.text_content().lower()
            if any(keyword in text for keyword in ["job", "position", "career", "hiring", "apply"]):
                job_divs.append(div)

        if job_divs:
            print(f"  ✓ Found {len(job_divs)} potential job containers via text analysis")
            return "text-discovered", job_divs
    except:
        pass

    return None, []