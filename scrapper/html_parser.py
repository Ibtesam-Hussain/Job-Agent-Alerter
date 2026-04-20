"""
HTML parsing and formatting utilities for job scraping.
"""

from bs4 import BeautifulSoup


def format_html_with_bs(html_content: str) -> str:
    """Parse raw HTML and return a clean, indented text representation."""
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    lines = []

    def add_line(line: str, indent: int = 0):
        if line.strip():
            lines.append(" " * (indent * 2) + line.strip())

    def parse_element(element, depth: int = 0):
        if element.name is None:
            text = element.strip()
            if text:
                add_line(text, depth)
            return

        attrs = "".join([f" {k}=\"{v}\"" for k, v in element.attrs.items()])
        add_line(f"<{element.name}{attrs}>", depth)

        for child in element.children:
            parse_element(child, depth + 1)

        add_line(f"</{element.name}>", depth)

    parse_element(soup.body if soup.body else soup)
    return "\n".join(lines)


def parse_job_snippet(job_snippet):
    """Return a formatted version of a scraped job snippet."""
    html = job_snippet.get("html", "")
    source = job_snippet.get("source", "unknown")
    selector = job_snippet.get("selector", "unknown")

    formatted = format_html_with_bs(html)
    return f"=== {source} | {selector} ===\n{formatted}\n"