"""
Scrapling Scraper Module — fetches pages and extracts emails + metadata.
"""

import re
from urllib.parse import urlparse, urljoin

from scrapling.fetchers import Fetcher

from extractor import extract_all_emails, merge_emails
from config import CONTACT_PAGE_PATHS


# ─── Metadata Extraction Helpers ────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extract root domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove port
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain
    except Exception:
        return ""


def _extract_site_name(page, url: str, title: str = "") -> str:
    """Extract website/brand name from page metadata."""
    try:
        # Try og:site_name
        og_site = page.css('meta[property="og:site_name"]')
        if og_site:
            content = og_site[0].attrib.get("content", "")
            if content:
                return content.strip()

        # Try application-name
        app_name = page.css('meta[name="application-name"]')
        if app_name:
            content = app_name[0].attrib.get("content", "")
            if content:
                return content.strip()

        # Use title (first part before separator)
        page_title = title
        if not page_title:
            title_el = page.css("title")
            if title_el:
                page_title = title_el[0].text or ""

        if page_title:
            # Split on common separators and take the last/first meaningful part
            for sep in [" | ", " - ", " — ", " · ", " :: ", " » "]:
                if sep in page_title:
                    parts = page_title.split(sep)
                    # Usually site name is the last part
                    return parts[-1].strip()
            return page_title.strip()

        # Fallback to domain
        return _extract_domain(url)
    except Exception:
        return _extract_domain(url)


def _extract_contact_name(page) -> str:
    """Try to extract a person's name from structured data or meta tags."""
    try:
        # Check JSON-LD for author/person
        scripts = page.css('script[type="application/ld+json"]')
        for script in scripts:
            text = script.text or ""
            if '"name"' in text and ('"Person"' in text or '"author"' in text.lower()):
                import json
                try:
                    data = json.loads(text)
                    name = _find_person_name(data)
                    if name:
                        return name
                except (json.JSONDecodeError, TypeError):
                    pass

        # Check meta author
        author = page.css('meta[name="author"]')
        if author:
            content = author[0].attrib.get("content", "")
            if content and len(content) < 60:
                return content.strip()

        return ""
    except Exception:
        return ""


def _find_person_name(data) -> str:
    """Recursively find a person's name in JSON-LD data."""
    if isinstance(data, dict):
        dtype = data.get("@type", "")
        if dtype == "Person" and "name" in data:
            return data["name"]
        if "author" in data:
            author = data["author"]
            if isinstance(author, dict) and "name" in author:
                return author["name"]
            elif isinstance(author, str):
                return author
        for value in data.values():
            result = _find_person_name(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_person_name(item)
            if result:
                return result
    return ""


def _extract_niche(page, description: str = "") -> str:
    """Infer site niche/category from metadata."""
    try:
        # Check og:type
        og_type = page.css('meta[property="og:type"]')
        if og_type:
            content = og_type[0].attrib.get("content", "")
            if content and content != "website":
                return content.strip()

        # Check category meta
        category = page.css('meta[name="category"]')
        if category:
            content = category[0].attrib.get("content", "")
            if content:
                return content.strip()

        # Check keywords
        keywords = page.css('meta[name="keywords"]')
        if keywords:
            content = keywords[0].attrib.get("content", "")
            if content:
                # Return first 2-3 keywords as the niche
                kw_list = [k.strip() for k in content.split(",") if k.strip()]
                return ", ".join(kw_list[:3])

        # Use description snippet
        desc = description
        if not desc:
            meta_desc = page.css('meta[name="description"]')
            if meta_desc:
                desc = meta_desc[0].attrib.get("content", "")
        if desc and len(desc) > 10:
            # Return first sentence or up to 80 chars
            first_sentence = desc.split(".")[0]
            return first_sentence[:80].strip()

        return ""
    except Exception:
        return ""


# ─── Main Scraping Function ─────────────────────────────────────────────────────

def scrape_url(url: str, title: str = "", description: str = "") -> dict:
    """
    Scrape a single URL for emails and metadata.
    
    Args:
        url: The URL to scrape
        title: Pre-fetched title from search results (optional)
        description: Pre-fetched description from search results (optional)
    
    Returns:
        Dict with domain, website_name, contact_name, niche, emails list, page_title, page_url
    """
    domain = _extract_domain(url)
    result = {
        "domain": domain,
        "website_name": "",
        "contact_name": "",
        "niche": "",
        "emails": [],
        "page_title": title,
        "page_url": url,
        "status": "success",
        "error": "",
    }

    try:
        # Fetch page with Scrapling Fetcher
        page = Fetcher.get(url, stealthy_headers=True, timeout=15)

        if page is None:
            result["status"] = "failed"
            result["error"] = "No response from server"
            return result

        # Get raw HTML and text
        html = str(page.body) if page.body else ""
        text = page.get_all_text() if hasattr(page, "get_all_text") else ""

        # Extract metadata
        result["website_name"] = _extract_site_name(page, url, title)
        result["contact_name"] = _extract_contact_name(page)
        result["niche"] = _extract_niche(page, description)
        if not result["page_title"]:
            title_el = page.css("title")
            if title_el:
                result["page_title"] = (title_el[0].text or "").strip()

        # Extract emails from main page
        email_sources = extract_all_emails(html, text)
        all_emails = merge_emails(email_sources)

        # If no emails found, try contact pages
        if not all_emails:
            all_emails = _try_contact_pages(url, domain, page)

        result["emails"] = all_emails

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _try_contact_pages(base_url: str, domain: str, page) -> list[dict]:
    """Try scraping internal pages to find emails, prioritizing contact/about pages."""
    parsed_base = urlparse(base_url)
    base = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    # Pre-seed with common paths just in case they aren't linked
    paths_to_check = set(CONTACT_PAGE_PATHS)
    
    # Extract internal links from the main page that might be contact pages
    if page:
        try:
            # Only look for these relevant keywords in paths
            keywords = ["contact", "about", "support", "help", "reach", "team"]
            for link in page.css("a"):
                href = link.attrib.get("href", "")
                if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    continue
                
                # Make URL absolute
                full_url = urljoin(base, href)
                parsed_link = urlparse(full_url)
                
                # Check if it's internal
                if parsed_link.netloc == parsed_base.netloc or not parsed_link.netloc:
                    path = getattr(parsed_link, "path", "")
                    if path and hasattr(path, "lower"):
                        path_str = path.lower()
                        # ONLY add the link if it matches our relevancy keywords
                        if any(kw in path_str for kw in keywords):
                            paths_to_check.add(path_str)
        except Exception as e:
            print(f"DEBUG: Error extracting links: {e}")

    # Remove the exact base path if it's in there (we already checked the homepage)
    current_path = parsed_base.path.lower() or "/"
    if current_path in paths_to_check:
        paths_to_check.remove(current_path)

    # Score paths: lower score = checked first
    def score_path(p):
        p_lower = str(p).lower()
        if any(kw in p_lower for kw in ["contact", "reach"]): return 0
        if any(kw in p_lower for kw in ["about", "team"]): return 1
        if any(kw in p_lower for kw in ["support", "help"]): return 2
        # Check standard inner pages before deep generic links
        if len(p_lower) < 20: return 3
        return 4

    # Sort and take top 7 links to check (to avoid crawling the whole site and wasting time/memory)
    sorted_paths = sorted(list(paths_to_check), key=score_path)[:7]

    for path in sorted_paths:
        contact_url = urljoin(base, path)
        try:
            contact_page = Fetcher.get(contact_url, stealthy_headers=True, timeout=10)
            if contact_page is None:
                continue

            html = str(contact_page.body) if contact_page.body else ""
            text = contact_page.get_all_text() if hasattr(contact_page, "get_all_text") else ""

            email_sources = extract_all_emails(html, text)
            emails = merge_emails(email_sources)
            if emails:
                # Tag the source as internal page
                for e in emails:
                    e["source"] = f"internal_page ({path})"
                return emails
        except Exception:
            continue

    return []
