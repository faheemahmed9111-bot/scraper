"""
Export Module — handles CSV and JSON export of lead data.
"""

import csv
import json
import io
from typing import Optional

import pandas as pd


CSV_COLUMNS = [
    "domain",
    "website_name",
    "contact_name",
    "niche",
    "email",
    "email_source",
    "page_title",
    "page_url",
]


def results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    """
    Convert raw scraping results to a flat DataFrame.
    Each email gets its own row.
    
    Args:
        results: List of scraper result dicts (one per URL)
    
    Returns:
        pandas DataFrame with one row per email found
    """
    rows = []
    for result in results:
        if result.get("emails"):
            for email_info in result["emails"]:
                rows.append({
                    "domain": result.get("domain", ""),
                    "website_name": result.get("website_name", ""),
                    "contact_name": result.get("contact_name", ""),
                    "niche": result.get("niche", ""),
                    "email": email_info.get("email", ""),
                    "email_source": email_info.get("source", ""),
                    "page_title": result.get("page_title", ""),
                    "page_url": result.get("page_url", ""),
                })
        else:
            # Include URLs where no email was found
            rows.append({
                "domain": result.get("domain", ""),
                "website_name": result.get("website_name", ""),
                "contact_name": result.get("contact_name", ""),
                "niche": result.get("niche", ""),
                "email": "",
                "email_source": "",
                "page_title": result.get("page_title", ""),
                "page_url": result.get("page_url", ""),
            })

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    return df


def export_csv(results: list[dict], filepath: str) -> str:
    """Export results to CSV file."""
    df = results_to_dataframe(results)
    df.to_csv(filepath, index=False, encoding="utf-8")
    return filepath


def export_csv_string(results: list[dict]) -> str:
    """Export results to CSV string (for Streamlit download)."""
    df = results_to_dataframe(results)
    return df.to_csv(index=False, encoding="utf-8")


def export_json(results: list[dict], filepath: Optional[str] = None) -> str:
    """Export results to JSON."""
    df = results_to_dataframe(results)
    json_str = df.to_json(orient="records", indent=2)
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
    return json_str
