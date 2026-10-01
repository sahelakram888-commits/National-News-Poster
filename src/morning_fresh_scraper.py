"""
National Reporter - Morning Fresh Scraper V4
- Deletes old cards, creates fresh morning news
- Sources: Munsif + Etemaad (priority) + India Today RSS + Indian Express RSS + NDTV RSS + The Hindu
- Translates English to Urdu & Roman Urdu
- Morning 6-11 AM covers ALL categories
"""
import re
import time
import logging
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8",
    "Referer": "https://www.google.com/"
}

POLITICS_KEYWORDS = ['bjp','congress','brs','trs','aimim','mim','assembly','election','minister','cm','chief minister','mla','mp','government','politics','revanth','ktr','kcr','owaisi','modi','rahul','telangana','mayor']

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_verified(title: str) -> bool:
    lower = title.lower()
    if len(title) < 15 or len(title) > 280:
        return False
    if any(x in lower for x in ['advertisement','subscribe','live tv','buy now','express premium']):
        return False
    return True

def fetch_page(url: str, timeout=10):
    try:
        # Use better headers V5 to avoid 403
        headers_v5 = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        }
        resp = requests.get(url, headers=headers_v5, timeout=timeout)
        resp.raise_for_status()
        # Handle encoding issues
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.warning(f"Failed {url}: {e}")
        return None

def fetch_rss(url: str, source_name: str, category: str = "india") -> List[Dict]:
    stories = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        # Parse XML
        root = ET.fromstring(resp.content)
        # RSS items
        for item in root.findall('.//item')[:10]:
            title_elem = item.find('title')
            if title_elem is not None and title_elem.text:
                title = clean_text(title_elem.text)
                if not is_verified(title):
                    continue
                is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS)
                cat = category
                if "hyderabad" in title.lower():
                    cat = "hyderabad"
                elif "telangana" in title.lower():
                    cat = "telangana"
                elif is_pol:
                    cat = "politics"
                stories.append({
                    "source": source_name,
                    "title": title,
                    "category": cat,
                    "is_politics": is_pol,
                    "verified": True,
                    "timestamp": datetime.now().isoformat(),
                    "is_urdu": False,
                    "needs_translation": True
                })
    except Exception as e:
        logger.warning(f"RSS failed {url}: {e}")
    return stories

def scrape_munsif_fresh() -> List[Dict]:
    stories = []
    # V5: Scrape category pages for truly fresh news, not just homepage
    urls = [
        ("https://munsifdaily.com/", "general"),
        ("https://munsifdaily.com/category/political-news/", "politics"),
        ("https://munsifdaily.com/category/hyderabad-news/", "hyderabad"),
        ("https://munsifdaily.com/category/telangana-news/", "telangana"),
    ]
    for url, cat in urls:
        soup = fetch_page(url, timeout=10)
        if soup:
            for el in soup.find_all(['h2','h3'], limit=15):
                title = clean_text(el.get_text())
                if not is_verified(title):
                    continue
                is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS) or cat=="politics"
                stories.append({
                    "source": "Munsif Daily",
                    "title": title,
                    "category": cat if cat!="general" else ("politics" if is_pol else "general"),
                    "is_politics": is_pol,
                    "verified": True,
                    "timestamp": datetime.now().isoformat(),
                    "is_urdu": any('\u0600' <= c <= '\u06FF' for c in title)
                })
        time.sleep(0.5)
    return stories

def scrape_etemaad_fresh() -> List[Dict]:
    stories = []
    urls = [
        ("https://www.en.etemaaddaily.com/", "general"),
        ("https://www.en.etemaaddaily.com/world/national", "india"),
        ("https://www.en.etemaaddaily.com/world/hyderabad", "hyderabad"),
        ("https://www.en.etemaaddaily.com/world/telangana", "telangana"),
    ]
    for url, cat in urls:
        soup = fetch_page(url, timeout=10)
        if soup:
            for sel in ['h4','h3','h2']:
                for el in soup.find_all(sel, limit=15):
                    title = clean_text(el.get_text())
                    if not is_verified(title):
                        continue
                    is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS) or "election" in title.lower() or "minister" in title.lower() or "cm" in title.lower() or "mla" in title.lower()
                    stories.append({
                        "source": "Etemaad Daily",
                        "title": title,
                        "category": cat if cat!="general" else ("politics" if is_pol else "general"),
                        "is_politics": is_pol,
                        "verified": True,
                        "timestamp": datetime.now().isoformat(),
                        "is_urdu": any('\u0600' <= c <= '\u06FF' for c in title)
                    })
                if len([s for s in stories if s['category']==cat]) >= 5:
                    break
        time.sleep(0.5)
    return stories[:20]

def scrape_india_today_fresh() -> List[Dict]:
    stories = []
    # Try homepage
    soup = fetch_page("https://www.indiatoday.in/", timeout=8)
    if soup:
        for el in soup.find_all(['h2','a'], limit=30):
            title = clean_text(el.get_text())
            if len(title) < 20 or len(title) > 200:
                continue
            if not is_verified(title):
                continue
            is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS)
            cat = "india"
            if "hyderabad" in title.lower():
                cat = "hyderabad"
            elif "telangana" in title.lower():
                cat = "telangana"
            elif is_pol:
                cat = "politics"
            elif "world" in title.lower():
                cat = "world"
            stories.append({
                "source": "India Today",
                "title": title,
                "category": cat,
                "is_politics": is_pol,
                "verified": True,
                "timestamp": datetime.now().isoformat(),
                "is_urdu": False,
                "needs_translation": True
            })
    
    # RSS fallback
    if len(stories) < 5:
        rss_urls = [
            ("https://www.indiatoday.in/rss/1206578", "india"),
            ("https://www.indiatoday.in/rss/1206584", "india"),
            ("https://www.indiatoday.in/rss/1206628", "politics"),
        ]
        for rss_url, cat in rss_urls:
            rss_stories = fetch_rss(rss_url, "India Today", cat)
            stories.extend(rss_stories)
            time.sleep(0.3)
    
    return stories[:15]

def scrape_indian_express_fresh() -> List[Dict]:
    stories = []
    # Try RSS first (more reliable than HTML which blocks)
    rss_urls = [
        ("https://indianexpress.com/feed/", "india"),
        ("https://indianexpress.com/section/india/feed/", "india"),
        ("https://indianexpress.com/section/cities/feed/", "hyderabad"),
        ("https://indianexpress.com/section/political-pulse/feed/", "politics"),
    ]
    for rss_url, cat in rss_urls:
        rss_stories = fetch_rss(rss_url, "Indian Express", cat)
        stories.extend(rss_stories)
        time.sleep(0.3)
    
    # Try homepage if RSS fails
    if len(stories) < 5:
        soup = fetch_page("https://indianexpress.com/latest-news/", timeout=8)
        if soup:
            for el in soup.find_all(['h2','h3'], limit=20):
                title = clean_text(el.get_text())
                if len(title) < 20 or len(title) > 200:
                    continue
                if not is_verified(title):
                    continue
                is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS)
                stories.append({
                    "source": "Indian Express",
                    "title": title,
                    "category": "politics" if is_pol else "india",
                    "is_politics": is_pol,
                    "verified": True,
                    "timestamp": datetime.now().isoformat(),
                    "is_urdu": False,
                    "needs_translation": True
                })
    
    return stories[:15]

def scrape_ndtv_fresh() -> List[Dict]:
    stories = []
    rss_urls = [
        ("https://feeds.feedburner.com/ndtvnews-india-news", "india"),
        ("https://feeds.feedburner.com/ndtvnews-top-stories", "india"),
        ("https://feeds.feedburner.com/ndtvnews-cities", "hyderabad"),
    ]
    for rss_url, cat in rss_urls:
        rss_stories = fetch_rss(rss_url, "NDTV", cat)
        stories.extend(rss_stories)
        time.sleep(0.3)
    return stories[:10]

def aggregate_fresh_morning() -> Dict:
    logger.info("=== FRESH MORNING NEWS - ALL CATEGORIES ===")
    logger.info("Sources: Munsif + Etemaad + India Today + Indian Express + NDTV")
    
    all_stories = []
    
    logger.info("Scraping Munsif Daily (priority)...")
    munsif = scrape_munsif_fresh()
    logger.info(f"Munsif: {len(munsif)}")
    all_stories.extend(munsif)
    
    logger.info("Scraping Etemaad Daily (priority)...")
    etemaad = scrape_etemaad_fresh()
    logger.info(f"Etemaad: {len(etemaad)}")
    all_stories.extend(etemaad)
    
    logger.info("Scraping India Today (fresh morning)...")
    india_today = scrape_india_today_fresh()
    logger.info(f"India Today: {len(india_today)}")
    all_stories.extend(india_today)
    
    logger.info("Scraping Indian Express (fresh)...")
    express = scrape_indian_express_fresh()
    logger.info(f"Indian Express: {len(express)}")
    all_stories.extend(express)
    
    logger.info("Scraping NDTV (fresh backup)...")
    ndtv = scrape_ndtv_fresh()
    logger.info(f"NDTV: {len(ndtv)}")
    all_stories.extend(ndtv)
    
    # Deduplicate
    seen = set()
    unique = []
    for s in all_stories:
        key = s['title'].lower().strip()
        if key not in seen and len(key) > 10:
            seen.add(key)
            unique.append(s)
    
    # Categorize
    hour = datetime.now().hour
    is_morning = True  # Always morning mode for full coverage per user request
    
    categorized = {
        "politics": [s for s in unique if s.get('is_politics')][:15],
        "hyderabad": [s for s in unique if s['category']=='hyderabad'][:10],
        "telangana": [s for s in unique if s['category']=='telangana'][:10],
        "india": [s for s in unique if s['category']=='india'][:10],
        "world": [s for s in unique if s['category']=='world'][:8],
        "all": unique[:30],
    }
    
    # Morning: ensure ALL categories covered nicely
    morning_titles = []
    for cat in ["politics", "hyderabad", "telangana", "india", "world"]:
        for s in categorized.get(cat, [])[:3]:
            if s['title'] not in morning_titles:
                morning_titles.append(s['title'])
    
    # Fill remaining
    for s in unique:
        if s['title'] not in morning_titles and len(morning_titles) < 20:
            morning_titles.append(s['title'])
    
    raw_titles = morning_titles[:20]
    
    logger.info(f"Aggregated {len(unique)} fresh | Politics: {len(categorized['politics'])} | Hyd: {len(categorized['hyderabad'])} | Telangana: {len(categorized['telangana'])} | India: {len(categorized['india'])} | World: {len(categorized['world'])}")
    logger.info(f"Sources: Munsif {len(munsif)}, Etemaad {len(etemaad)}, IndiaToday {len(india_today)}, Express {len(express)}, NDTV {len(ndtv)}")
    
    return {
        "fetched_at": datetime.now().isoformat(),
        "total_count": len(unique),
        "politics_count": len(categorized['politics']),
        "is_morning": is_morning,
        "hour": hour,
        "categorized": categorized,
        "raw_titles": raw_titles,
        "all_stories": unique,
        "sources_used": {
            "munsif": len(munsif),
            "etemaad": len(etemaad),
            "india_today": len(india_today),
            "indian_express": len(express),
            "ndtv": len(ndtv)
        }
    }

if __name__ == "__main__":
    data = aggregate_fresh_morning()
    print(f"\nTotal: {data['total_count']}")
    for cat in ["politics","hyderabad","telangana","india","world"]:
        stories = data['categorized'].get(cat, [])
        if stories:
            print(f"\n--- {cat.upper()} ({len(stories)}) ---")
            for s in stories[:3]:
                print(f" [{s['source']}] {s['title'][:80]}")
