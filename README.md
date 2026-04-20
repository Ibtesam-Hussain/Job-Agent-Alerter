Making an agentic ai system that will tell me about jobs from n number of company's career pages. So, i dont miss the oppurtunity at the right time :)

## Scraping Pipeline Completed

The following steps have been implemented:

1. Web Scraping - Playwright-based automated browser scraping with URL reachability checks and selector detection
2. HTML Parsing - BeautifulSoup processing to clean and format HTML content
3. Job Filtering - Keyword-based filtering using job-role-keywords.txt to identify relevant positions
4. Details Extraction - Extraction of job title, apply link, and source information
5. Output Formatting - JSON output of extracted job details
6. Configuration Management - Support for default and user-defined job sites
7. Modular Architecture - Clean separation into 7 focused modules with main.py as single entry point

Usage: python main.py [--save-json OUTPUT_FILE]