"""
Lead Scraper — Streamlit UI
A premium web app for scraping emails from URLs found via Firecrawl search.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime

from config import FIRECRAWL_API_KEY, DEFAULT_SEARCH_LIMIT, MAX_SEARCH_LIMIT
from search import search_urls
from scraper import scrape_url
from export import results_to_dataframe, export_csv_string, export_json


# ─── Page Config ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LeadScraper — Email Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Custom CSS ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Import Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide default Streamlit elements ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: visible !important; background: transparent !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.15);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e7ff !important;
    }

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown label {
        color: #a5b4fc !important;
    }

    /* ── Hero Header ── */
    .hero-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(99, 102, 241, 0.25);
        box-shadow: 0 8px 32px rgba(67, 56, 202, 0.15);
    }

    .hero-header h1 {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #c7d2fe 0%, #a5b4fc 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.03em;
    }

    .hero-header p {
        color: #a5b4fc;
        font-size: 0.95rem;
        margin: 0;
        font-weight: 400;
    }

    /* ── Stats Cards ── */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-card {
        background: linear-gradient(145deg, #1e1b4b, #1a1a2e);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.15);
    }

    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #818cf8;
        line-height: 1.2;
    }

    .stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6366f1;
        font-weight: 600;
        margin-top: 0.3rem;
    }

    /* ── URL Cards ── */
    .url-card {
        background: linear-gradient(145deg, rgba(30, 27, 75, 0.6), rgba(26, 26, 46, 0.8));
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 1rem 1.4rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s;
    }

    .url-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }

    .url-card .url-title {
        font-weight: 600;
        color: #c7d2fe;
        font-size: 0.95rem;
        margin-bottom: 0.2rem;
    }

    .url-card .url-link {
        font-size: 0.8rem;
        color: #6366f1;
        word-break: break-all;
    }

    .url-card .url-desc {
        font-size: 0.82rem;
        color: #a5b4fc;
        margin-top: 0.3rem;
        line-height: 1.4;
    }

    /* ── Status Badge ── */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-success {
        background: rgba(52, 211, 153, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    .badge-warning {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }

    .badge-error {
        background: rgba(248, 113, 113, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }

    /* ── Email Result Row ── */
    .email-row {
        background: rgba(30, 27, 75, 0.4);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .email-address {
        font-weight: 600;
        color: #34d399;
        font-size: 0.95rem;
        font-family: 'JetBrains Mono', monospace;
    }

    .email-domain {
        color: #6366f1;
        font-size: 0.82rem;
    }

    .email-source-tag {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
    }

    /* ── Dork Guide ── */
    .dork-guide {
        background: linear-gradient(145deg, rgba(30, 27, 75, 0.5), rgba(26, 26, 46, 0.6));
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }

    .dork-guide code {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.82rem;
    }

    /* ── Section Header ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.5rem 0 1rem 0;
    }

    .section-header h3 {
        color: #c7d2fe;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 0;
    }

    .section-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.3), transparent);
    }

    /* ── Button styling ── */
    .stButton > button {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #34d399 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(52, 211, 153, 0.25) !important;
    }

    /* ── Dataframe styling ── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Input styling ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(30, 27, 75, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.25) !important;
        border-radius: 10px !important;
        color: #e0e7ff !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }

    /* ── Spinner styling ── */
    .stSpinner > div {
        border-top-color: #6366f1 !important;
    }

    /* ── Progress bar ── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4338ca, #6366f1, #818cf8) !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ──────────────────────────────────────────────────────────

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "scrape_results" not in st.session_state:
    st.session_state.scrape_results = []
if "search_done" not in st.session_state:
    st.session_state.search_done = False
if "scrape_done" not in st.session_state:
    st.session_state.scrape_done = False
if "api_key" not in st.session_state:
    st.session_state.api_key = FIRECRAWL_API_KEY


# ─── Sidebar ──────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_key_input = st.text_input(
        "Firecrawl API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your API key from firecrawl.dev",
        placeholder="fc-...",
    )
    st.session_state.api_key = api_key_input

    st.markdown("---")

    st.markdown("## 🎯 Search Query Operators")
    st.markdown("""
<div class="dork-guide">
<p style="font-size: 0.85rem; color: #a5b4fc; margin-bottom: 0.5rem;">Use Google-style dork operators:</p>
<p><code>site:</code> — limit to a domain</p>
<p><code>inurl:</code> — URL must contain term</p>
<p><code>intitle:</code> — title must contain term</p>
<p><code>filetype:</code> — filter by file type</p>
<p><code>-site:</code> — exclude a domain</p>
<p><code>"exact phrase"</code> — exact match</p>
</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("## 💡 Example Queries")
    st.code('web design agency "contact us"', language=None)
    st.code('site:shopify.com store contact email', language=None)
    st.code('"@gmail.com" freelance developer portfolio', language=None)
    st.code('inurl:contact local bakery', language=None)


# ─── Hero Header ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <h1>🔍 LeadScraper</h1>
    <p>Find contact emails from any niche using smart search queries. Powered by Firecrawl + Scrapling.</p>
</div>
""", unsafe_allow_html=True)


# ─── Search Section ──────────────────────────────────────────────────────────────

col_query, col_limit = st.columns([4, 1])

with col_query:
    query = st.text_input(
        "🔎 Search Query",
        placeholder='e.g. web design agency "contact us" email',
        help="Enter your search query. Supports dork operators like site:, inurl:, intitle:",
        label_visibility="collapsed",
    )

with col_limit:
    limit = st.number_input(
        "Results",
        min_value=1,
        max_value=MAX_SEARCH_LIMIT,
        value=DEFAULT_SEARCH_LIMIT,
        step=1,
        help=f"Number of URLs to search (max {MAX_SEARCH_LIMIT})",
    )


# ─── Action Button ─────────────────────────────────────────────────────────────

# Single button to trigger the entire pipeline
col_btn1, col_btn2, col_spacer = st.columns([1, 1, 3])
with col_btn1:
    search_and_extract_clicked = st.button("🚀 Search & Extract Leads", use_container_width=True)


# ─── Full Pipeline Execution ──────────────────────────────────────────────────

if search_and_extract_clicked:
    if not st.session_state.api_key:
        st.error("⚠️ Please enter your Firecrawl API Key in the sidebar.")
    elif not query.strip():
        st.warning("Please enter a search query.")
    else:
        # Reset state
        st.session_state.search_done = False
        st.session_state.scrape_done = False
        st.session_state.search_results = []
        st.session_state.scrape_results = []

        # 1. Search Phase
        st.markdown("""
        <div class="section-header">
            <h3>🌐 Finding target URLs...</h3>
            <div class="section-line"></div>
        </div>
        """, unsafe_allow_html=True)
        
        search_status = st.empty()
        with search_status.container():
            with st.spinner("Searching for URLs via Firecrawl..."):
                try:
                    results = search_urls(
                        query=query.strip(),
                        limit=int(limit),
                        api_key=st.session_state.api_key,
                    )
                    st.session_state.search_results = results
                    st.session_state.search_done = True
                except Exception as e:
                    st.error(f"❌ Search failed: {str(e)}")
                    st.stop()
        
        if not st.session_state.search_results:
            search_status.warning("No URLs found for your query. Try different search terms.")
            st.stop()
            
        search_status.success(f"✅ Found {len(st.session_state.search_results)} URLs to scrape!")

        # 2. Extract Phase
        urls = st.session_state.search_results
        total = len(urls)

        st.markdown("""
        <div class="section-header">
            <h3>📧 Extracting Emails & Metadata...</h3>
            <div class="section-line"></div>
        </div>
        """, unsafe_allow_html=True)

        progress_bar = st.progress(0, text="Starting email extraction...")
        scrape_status_container = st.empty()

        all_results = []

        for i, url_data in enumerate(urls):
            url = url_data.get("url", "")
            title = url_data.get("title", "")
            description = url_data.get("description", "")

            progress = (i + 1) / total
            progress_bar.progress(progress, text=f"Scraping ({i+1}/{total}): {url[:60]}...")

            try:
                result = scrape_url(url, title=title, description=description)
                all_results.append(result)

                email_count = len(result.get("emails", []))
                if email_count > 0:
                    scrape_status_container.success(f"✅ Found {email_count} email(s) on {result['domain']}")
                else:
                    scrape_status_container.info(f"🔍 No emails found on {result['domain']}")
            except Exception as e:
                all_results.append({
                    "domain": url_data.get("url", ""),
                    "website_name": "",
                    "contact_name": "",
                    "niche": "",
                    "emails": [],
                    "page_title": title,
                    "page_url": url,
                    "status": "error",
                    "error": str(e),
                })
                scrape_status_container.error(f"❌ Error scraping {url[:50]}: {str(e)}")

        progress_bar.progress(1.0, text="✅ Extraction complete!")
        st.session_state.scrape_results = all_results
        st.session_state.scrape_done = True
        st.rerun()


# ─── Display Scrape Results ──────────────────────────────────────────────────────

if st.session_state.scrape_done and st.session_state.scrape_results:
    results = st.session_state.scrape_results

    # Calculate stats
    total_urls = len(results)
    total_emails = sum(len(r.get("emails", [])) for r in results)
    urls_with_emails = sum(1 for r in results if r.get("emails"))
    success_rate = (urls_with_emails / total_urls * 100) if total_urls > 0 else 0

    # Stats Grid
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_urls}</div>
            <div class="stat-label">URLs Scraped</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_emails}</div>
            <div class="stat-label">Emails Found</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{urls_with_emails}</div>
            <div class="stat-label">Sites with Email</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{success_rate:.0f}%</div>
            <div class="stat-label">Hit Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Results Table
    st.markdown("""
    <div class="section-header">
        <h3>📋 Results</h3>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    df = results_to_dataframe(results)

    if not df.empty:
        # Only show rows with emails by default, with toggle
        show_all = st.toggle("Show URLs without emails", value=False)
        if not show_all:
            df_display = df[df["email"] != ""].reset_index(drop=True)
        else:
            df_display = df

        if not df_display.empty:
            st.dataframe(
                df_display,
                use_container_width=True,
                height=400,
                column_config={
                    "domain": st.column_config.TextColumn("Domain", width="medium"),
                    "website_name": st.column_config.TextColumn("Website", width="medium"),
                    "contact_name": st.column_config.TextColumn("Contact Name", width="medium"),
                    "niche": st.column_config.TextColumn("Niche", width="medium"),
                    "email": st.column_config.TextColumn("Email", width="medium"),
                    "email_source": st.column_config.TextColumn("Source", width="small"),
                    "page_title": st.column_config.TextColumn("Page Title", width="medium"),
                    "page_url": st.column_config.LinkColumn("URL", width="medium"),
                },
            )
        else:
            st.info("No emails were found in any of the scraped URLs.")

        # ── Export Section ──
        st.markdown("""
        <div class="section-header">
            <h3>📥 Export Results</h3>
            <div class="section-line"></div>
        </div>
        """, unsafe_allow_html=True)

        col_csv, col_json, _ = st.columns([1, 1, 3])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        with col_csv:
            csv_data = export_csv_string(results)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"leads_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_json:
            json_data = export_json(results)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"leads_{timestamp}.json",
                mime="application/json",
                use_container_width=True,
            )

        # ── Per-URL Detail Expander ──
        st.markdown("""
        <div class="section-header">
            <h3>🔎 Detailed Results</h3>
            <div class="section-line"></div>
        </div>
        """, unsafe_allow_html=True)

        for result in results:
            email_count = len(result.get("emails", []))
            domain = result.get("domain", "unknown")

            if email_count > 0:
                icon = "✅"
                badge = f'<span class="badge badge-success">{email_count} emails</span>'
            else:
                icon = "⚪"
                badge = '<span class="badge badge-warning">no emails</span>'

            with st.expander(f"{icon} {domain} — {result.get('website_name', '')}", expanded=False):
                col_info, col_emails = st.columns([1, 1])

                with col_info:
                    st.markdown("**🌐 URL:**")
                    st.code(result.get("page_url", ""), language=None)
                    st.markdown(f"**📛 Website:** {result.get('website_name', 'N/A')}")
                    st.markdown(f"**👤 Contact:** {result.get('contact_name', 'N/A') or 'N/A'}")
                    st.markdown(f"**🏷️ Niche:** {result.get('niche', 'N/A') or 'N/A'}")

                    if result.get("error"):
                        st.error(f"Error: {result['error']}")

                with col_emails:
                    if email_count > 0:
                        st.markdown("**📧 Emails found:**")
                        for email_info in result["emails"]:
                            st.markdown(f"""
                            <div class="email-row">
                                <span class="email-address">{email_info['email']}</span>
                                <span class="email-source-tag">{email_info['source']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No contact emails found on this page.")
    else:
        st.info("No data to display.")
