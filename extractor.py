"""
Email Extraction Engine — comprehensive email extraction from HTML/text content.
"""

import re
import json
from urllib.parse import urlparse

from config import (
    FILTERED_EMAIL_PREFIXES,
    FILTERED_EMAIL_DOMAINS,
    FALSE_POSITIVE_TLDS,
    FILTERED_EXACT_EMAILS,
)


# ─── Core Email Regex ───────────────────────────────────────────────────────────
# Matches standard email formats: user@domain.tld
# Handles: dots, hyphens, underscores, plus signs in local part
# Requires 2+ char TLD to reduce false positives
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Mailto link pattern
MAILTO_PATTERN = re.compile(
    r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    re.IGNORECASE
)

# JSON-LD email pattern
JSONLD_PATTERN = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE
)

# Obfuscated email patterns (common tricks)
# e.g., "user [at] domain [dot] com" or "user(at)domain(dot)com"
OBFUSCATED_AT = re.compile(
    r'([a-zA-Z0-9._%+\-]+)\s*[\[\(]\s*at\s*[\]\)]\s*([a-zA-Z0-9.\-]+)\s*[\[\(]\s*dot\s*[\]\)]\s*([a-zA-Z]{2,})',
    re.IGNORECASE
)

# HTML entity encoded emails: &#64; = @, &#46; = .
HTML_ENTITY_AT = re.compile(r'&#0*64;|&#x0*40;', re.IGNORECASE)
HTML_ENTITY_DOT = re.compile(r'&#0*46;|&#x0*2[eE];', re.IGNORECASE)


def _clean_email(email: str) -> str:
    """Clean and normalize an email address."""
    email = email.strip().lower()
    # Remove trailing punctuation that got captured
    email = email.rstrip(".,;:!?)")
    # Remove leading punctuation
    email = email.lstrip("(<")
    return email


def _is_valid_email(email: str) -> bool:
    """Validate an email is real and not a false positive."""
    if not email or len(email) < 5:
        return False

    parts = email.split("@")
    if len(parts) != 2:
        return False

    local, domain = parts
    if not local or not domain:
        return False

    # Check TLD isn't a file extension
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    if tld.lower() in FALSE_POSITIVE_TLDS:
        return False

    # Check against exact matches
    if email in FILTERED_EXACT_EMAILS:
        return False

    # Check against filtered prefixes
    for prefix in FILTERED_EMAIL_PREFIXES:
        if email.startswith(prefix):
            return False

    # Check against filtered domains
    domain_lower = domain.lower()
    for filtered_domain in FILTERED_EMAIL_DOMAINS:
        if domain_lower == filtered_domain:
            return False

    # Must have at least one dot in domain
    if "." not in domain:
        return False

    # Local part sanity check
    if len(local) > 64 or len(domain) > 253:
        return False

    # No consecutive dots
    if ".." in local or ".." in domain:
        return False

    return True


def extract_emails_from_text(text: str) -> set[str]:
    """Extract emails from plain text using regex."""
    if not text:
        return set()

    emails = set()
    for match in EMAIL_PATTERN.findall(text):
        cleaned = _clean_email(match)
        if _is_valid_email(cleaned):
            emails.add(cleaned)
    return emails


def extract_emails_from_mailto(html: str) -> set[str]:
    """Extract emails from mailto: links in HTML."""
    if not html:
        return set()

    emails = set()
    for match in MAILTO_PATTERN.findall(html):
        cleaned = _clean_email(match)
        if _is_valid_email(cleaned):
            emails.add(cleaned)
    return emails


def extract_emails_from_jsonld(html: str) -> set[str]:
    """Extract emails from JSON-LD structured data."""
    if not html:
        return set()

    emails = set()
    for script_match in JSONLD_PATTERN.findall(html):
        try:
            data = json.loads(script_match)
            _extract_emails_from_dict(data, emails)
        except (json.JSONDecodeError, TypeError):
            continue
    return emails


def _extract_emails_from_dict(data, emails: set):
    """Recursively extract emails from a dict/list structure (JSON-LD)."""
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in ("email", "contactpoint", "contactemail", "author"):
                if isinstance(value, str) and "@" in value:
                    cleaned = _clean_email(value.replace("mailto:", ""))
                    if _is_valid_email(cleaned):
                        emails.add(cleaned)
                elif isinstance(value, dict):
                    _extract_emails_from_dict(value, emails)
                elif isinstance(value, list):
                    for item in value:
                        _extract_emails_from_dict(item, emails)
            else:
                _extract_emails_from_dict(value, emails)
    elif isinstance(data, list):
        for item in data:
            _extract_emails_from_dict(item, emails)


def extract_obfuscated_emails(text: str) -> set[str]:
    """Extract obfuscated emails like 'user [at] domain [dot] com'."""
    if not text:
        return set()

    emails = set()
    for match in OBFUSCATED_AT.findall(text):
        email = f"{match[0]}@{match[1]}.{match[2]}"
        cleaned = _clean_email(email)
        if _is_valid_email(cleaned):
            emails.add(cleaned)
    return emails


def extract_html_entity_emails(html: str) -> set[str]:
    """Extract emails that use HTML entities for @ and . symbols."""
    if not html:
        return set()

    # Replace HTML entities with actual characters
    decoded = HTML_ENTITY_AT.sub("@", html)
    decoded = HTML_ENTITY_DOT.sub(".", decoded)

    # Now run standard extraction on decoded text
    return extract_emails_from_text(decoded)


def extract_all_emails(html: str, text: str = "") -> dict[str, set[str]]:
    """
    Run all extraction methods and return emails categorized by source.
    
    Args:
        html: Raw HTML content of the page
        text: Plain text content (optional, extracted from HTML if not provided)
    
    Returns:
        Dict mapping source names to sets of emails found
    """
    results = {}

    # 1. Mailto links (highest confidence)
    mailto_emails = extract_emails_from_mailto(html)
    if mailto_emails:
        results["mailto"] = mailto_emails

    # 2. JSON-LD structured data (high confidence)
    jsonld_emails = extract_emails_from_jsonld(html)
    if jsonld_emails:
        results["structured_data"] = jsonld_emails

    # 3. Visible page text
    text_emails = extract_emails_from_text(text or html)
    if text_emails:
        results["page_text"] = text_emails

    # 4. Raw HTML (catches emails in attributes, comments, etc.)
    html_emails = extract_emails_from_text(html)
    if html_emails:
        results["html_source"] = html_emails

    # 5. Obfuscated emails
    obfuscated = extract_obfuscated_emails(text or html)
    if obfuscated:
        results["obfuscated"] = obfuscated

    # 6. HTML entity encoded emails
    entity_emails = extract_html_entity_emails(html)
    if entity_emails:
        results["html_entities"] = entity_emails

    return results


def merge_emails(email_sources: dict[str, set[str]]) -> list[dict]:
    """
    Merge emails from all sources, deduplicate, and track the best source.
    
    Returns:
        List of dicts with 'email' and 'source' keys
    """
    # Priority order (first seen source wins)
    source_priority = [
        "mailto", "structured_data", "page_text",
        "html_source", "obfuscated", "html_entities"
    ]

    seen = {}
    for source in source_priority:
        for email in email_sources.get(source, set()):
            if email not in seen:
                seen[email] = source

    return [{"email": email, "source": source} for email, source in seen.items()]
