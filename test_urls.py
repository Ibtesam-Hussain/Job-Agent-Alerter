#!/usr/bin/env python3
"""
General & Simple test script to check if job site URLs are reachable
"""

import requests

TEST_URLS = [
    "https://weworkremotely.com/remote-jobs",
    "https://remoteok.com/remote-dev-jobs",
    "https://weworkremotely.com",  # base URL
    "https://remoteok.com"         # base URL
]

def test_urls():
    print("Testing URL reachability...\n")

    for url in TEST_URLS:
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            status = "REACHABLE" if response.status_code < 400 else f"❌ HTTP {response.status_code}"
            print(f"{status}: {url}")
        except requests.exceptions.RequestException as e:
            print(f"ERROR: {url} - {str(e)}")

if __name__ == "__main__":
    test_urls()