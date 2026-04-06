"""
Configuration module — loads environment variables and default settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Firecrawl
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# Defaults
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 100  # Streamlit UI max input limit

# Contact page paths to auto-discover when no emails found on main page
CONTACT_PAGE_PATHS = [
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/get-in-touch",
    "/reach-us",
    "/support",
]

# Emails to filter out (system / no-reply / placeholder)
FILTERED_EMAIL_PREFIXES = [
    "noreply@",
    "no-reply@",
    "no_reply@",
    "donotreply@",
    "do-not-reply@",
    "mailer-daemon@",
    "postmaster@",
    "hostmaster@",
    "webmaster@",
    "abuse@",
    "root@",
    "admin@",
    "info@",
]

FILTERED_EMAIL_DOMAINS = [
    "example.com",
    "example.org",
    "test.com",
    "domain.com",
    "email.com",
    "yourwebsite.com",
    "yourdomain.com",
    "company.com",
    "sentry.io",
    "wixpress.com",
]

# Exact emails to filter out (placeholders)
FILTERED_EXACT_EMAILS = [
    "example@gmail.com",
    "email@example.com",
    "yourname@email.com",
    "john@doe.com",
    "name@domain.com",
]

# False positive file extensions that look like TLDs
FALSE_POSITIVE_TLDS = [
    "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico",
    "css", "js", "map", "woff", "woff2", "ttf", "eot",
]
