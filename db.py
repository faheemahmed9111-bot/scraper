import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

def get_supabase_client():
    if not supabase:
        raise ValueError("Supabase credentials not found in environment variables. Set SUPABASE_URL and SUPABASE_KEY.")
    return supabase

def get_next_query():
    """Get the next pending query from the database."""
    client = get_supabase_client()
    response = client.table("queries").select("*").eq("status", "pending").order("created_at").limit(1).execute()
    if response.data:
        return response.data[0]
    return None

def update_query_status(query_id: int, status: str):
    """Update the status of a query."""
    client = get_supabase_client()
    client.table("queries").update({"status": status}).eq("id", query_id).execute()

def is_domain_scraped(domain: str) -> bool:
    """Check if a domain has already been scraped/checked."""
    client = get_supabase_client()
    response = client.table("scrape_cache").select("domain").eq("domain", domain).execute()
    return len(response.data) > 0

def add_to_scrape_cache(domain: str):
    """Add a domain to the scrape cache to prevent future re-scraping."""
    client = get_supabase_client()
    try:
        client.table("scrape_cache").insert({"domain": domain}).execute()
    except Exception as e:
        # Ignore unique constraint violations (already exists)
        if "duplicate key value violates unique constraint" not in str(e).lower():
            pass

def add_leads(leads_data: list[dict]):
    """Insert multiple leads into the database."""
    if not leads_data:
        return
    client = get_supabase_client()
    try:
        client.table("leads").insert(leads_data).execute()
    except Exception as e:
        print(f"Error adding leads to database: {e}")
