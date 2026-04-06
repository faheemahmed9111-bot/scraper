-- Run this in your Supabase SQL Editor to instantly set up your tables

-- 1. Queries Table
CREATE TABLE queries (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Scrape Cache Table (Deduplication)
CREATE TABLE scrape_cache (
    id SERIAL PRIMARY KEY,
    domain TEXT UNIQUE NOT NULL, -- UNIQUE ensures we can't insert the same domain twice
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Leads Table
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    domain TEXT NOT NULL,
    website_name TEXT,
    contact_name TEXT,
    niche TEXT,
    email TEXT,
    source TEXT,
    page_title TEXT,
    page_url TEXT,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
