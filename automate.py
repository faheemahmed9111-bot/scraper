import os
import sys
from urllib.parse import urlparse

from search import search_urls
from scraper import scrape_url
from db import (
    get_next_query, 
    update_query_status, 
    is_domain_scraped,
    add_to_scrape_cache,
    add_leads
)

def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain
    except:
        return ""

def main():
    print("---------------------------------------------")
    print("Starting automated lead extraction pipeline...")
    
    # Check if configured
    if not os.getenv("FIRECRAWL_API_KEY") or not os.getenv("SUPABASE_URL"):
        print("Missing API keys. Please check FIRECRAWL_API_KEY, SUPABASE_URL, and SUPABASE_KEY in environment variables.")
        sys.exit(1)

    # 1. Get next query from Supabase
    try:
        query_record = get_next_query()
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    if not query_record:
        print("No pending queries found. Exiting gracefully.")
        return

    query_id = query_record["id"]
    query_text = query_record["query"]
    print(f"[{query_id}] Found pending query: '{query_text}'")

    # 2. Update status to processing
    update_query_status(query_id, "processing")

    try:
        # 3. Use Firecrawl to search for up to 100 URLs
        print(f"Searching URLs via Firecrawl...")
        search_results = search_urls(query_text, limit=100)
        urls = [item.get("url") for item in search_results if isinstance(item, dict) and item.get("url")]
        print(f"Found {len(urls)} total URLs in search results.")

        if not urls:
            update_query_status(query_id, "completed")
            print("No URLs found for query. Marked as completed.")
            return

        # 4. Filter already scraped domains and deduplicate current list
        domains_to_scrape = {} # Map domain -> URL for deduplication
        for url in urls:
            domain = extract_domain(url)
            if not domain:
                continue
            
            if domain not in domains_to_scrape:
                if not is_domain_scraped(domain):
                    domains_to_scrape[domain] = url

        urls_to_scrape = list(domains_to_scrape.values())
        print(f"After filtering cached/duplicate domains, {len(urls_to_scrape)} URLs to scrape.")

        if not urls_to_scrape:
            update_query_status(query_id, "completed")
            print("All domains from search results have already been processed previously.")
            return

        # 5. Scrape URLs with Scrapling
        all_new_leads = []
        for index, url in enumerate(urls_to_scrape):
            domain = extract_domain(url)
            print(f"[{index + 1}/{len(urls_to_scrape)}] Scraping {url}...")
            
            try:
                # Add to cache BEFORE scraping. If scraper fails/crashes, we still don't want to retry breaking domain.
                add_to_scrape_cache(domain)
                
                result = scrape_url(url)
                
                if result and result.get("emails"):
                    for email_data in result["emails"]:
                        lead_record = {
                            "domain": result.get("domain", domain),
                            "website_name": result.get("website_name", ""),
                            "contact_name": result.get("contact_name", ""),
                            "niche": result.get("niche", ""),
                            "email": email_data.get("email", ""),
                            "source": email_data.get("source", ""),
                            "page_title": result.get("page_title", ""),
                            "page_url": result.get("page_url", url)
                        }
                        all_new_leads.append(lead_record)
                    print(f"  -> Found {len(result['emails'])} emails")
                else:
                    print(f"  -> No valid emails found")
                    
            except Exception as e:
                print(f"  -> Error executing scraper for {url}: {e}")

        # 6. Save new leads
        if all_new_leads:
            print(f"Saving {len(all_new_leads)} new leads to database...")
            add_leads(all_new_leads)
        else:
            print("No new leads found in this batch.")
        
        # 7. Mark as complete
        update_query_status(query_id, "completed")
        print(f"Finished processing query '{query_text}'.")

    except Exception as e:
        print(f"Fatal error processing query '{query_text}': {e}")
        update_query_status(query_id, "failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
