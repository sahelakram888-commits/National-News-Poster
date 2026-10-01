"""
National Reporter - Morning Fresh Scraper V5 - FRESH NEWS FIX
- Fixes: Only old cards not new fresh news publishing
- Scrapes category pages for politics, hyderabad, telangana to get truly fresh
- Better headers to avoid 403 for India Today
- NDTV + Munsif + Etemaad priority
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

HEADERS_V5 = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}

POLITICS_KEYWORDS = ['bjp','congress','brs','trs','aimim','mim','assembly','election','minister','cm','chief minister','mla','mp','government','politics','revanth','ktr','kcr','owaisi','modi','rahul','telangana','mayor','high court','supreme court','eci','harish rao','kcr','ktr','revanth','congress','bjp','trs','aimim','election','mla','mp','cm','pm','minister','governor','mayor','reservation','cbi','ed','assets','hostel clash','cctv','parth pawar','land deal','terrorism','israel','envoy']

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
    if any(x in lower for x in ['advertisement','subscribe','live tv','buy now','express premium','newsletter','privacy policy']):
        return False
    return True

def fetch_page(url: str, timeout=10):
    try:
        resp = requests.get(url, headers=HEADERS_V5, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')
    except Exception as e:
        logger.warning(f"Failed {url}: {e}")
        return None

def fetch_rss(url: str, source_name: str, category: str = "india") -> List[Dict]:
    stories = []
    try:
        resp = requests.get(url, headers=HEADERS_V5, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item')[:15]:
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
                elif "world" in title.lower():
                    cat = "world"
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

def scrape_munsif_fresh_v5() -> List[Dict]:
    stories = []
    # Scrape homepage + category pages for fresh
    urls = [
        ("https://munsifdaily.com/", "general"),
        ("https://munsifdaily.com/category/political-news/", "politics"),
        ("https://munsifdaily.com/category/hyderabad-news/", "hyderabad"),
        ("https://munsifdaily.com/category/telangana-news/", "telangana"),
        ("https://munsifdaily.com/category/india-news/", "india"),
    ]
    for url, cat in urls:
        soup = fetch_page(url, timeout=8)
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

def scrape_etemaad_fresh_v5() -> List[Dict]:
    stories = []
    urls = [
        ("https://www.en.etemaaddaily.com/", "general"),
        ("https://www.en.etemaaddaily.com/world/national", "india"),
        ("https://www.en.etemaaddaily.com/world/hyderabad", "hyderabad"),
        ("https://www.en.etemaaddaily.com/world/telangana", "telangana"),
    ]
    for url, cat in urls:
        soup = fetch_page(url, timeout=8)
        if soup:
            for sel in ['h4','h3','h2']:
                for el in soup.find_all(sel, limit=15):
                    title = clean_text(el.get_text())
                    if not is_verified(title):
                        continue
                    is_pol = any(k in title.lower() for k in POLITICS_KEYWORDS) or "election" in title.lower() or "minister" in title.lower()
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

def scrape_ndtv_fresh_v5() -> List[Dict]:
    stories = []
    rss_urls = [
        ("https://feeds.feedburner.com/ndtvnews-top-stories", "india"),
        ("https://feeds.feedburner.com/ndtvnews-india-news", "india"),
        ("https://feeds.feedburner.com/ndtvnews-cities", "hyderabad"),
    ]
    for rss_url, cat in rss_urls:
        rss_stories = fetch_rss(rss_url, "NDTV", cat)
        stories.extend(rss_stories)
        time.sleep(0.3)
    return stories[:15]

def scrape_india_today_fallback() -> List[Dict]:
    # India Today blocked 403, use alternative scraping via Bing or just skip and use NDTV
    # Try with different UA
    stories = []
    try:
        # Try India Today via textise or alternative
        soup = fetch_page("https://www.indiatoday.in/india", timeout=8)
        if soup:
            for el in soup.find_all(['h2','a'], limit=20):
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
    except:
        pass
    return stories[:10]

def aggregate_fresh_morning_v5() -> Dict:
    logger.info("=== FRESH MORNING NEWS V5 - CATEGORY PAGES FOR FRESH ===")
    logger.info("Sources: Munsif (homepage+politics+hyd+telangana+india) + Etemaad (national+hyd+telangana) + NDTV + India Today fallback")
    
    all_stories = []
    
    logger.info("Scraping Munsif Daily V5 (category pages)...")
    munsif = scrape_munsif_fresh_v5()
    logger.info(f"Munsif V5: {len(munsif)}")
    all_stories.extend(munsif)
    
    logger.info("Scraping Etemaad Daily V5 (category pages)...")
    etemaad = scrape_etemaad_fresh_v5()
    logger.info(f"Etemaad V5: {len(etemaad)}")
    all_stories.extend(etemaad)
    
    logger.info("Scraping NDTV V5 (fresh)...")
    ndtv = scrape_ndtv_fresh_v5()
    logger.info(f"NDTV V5: {len(ndtv)}")
    all_stories.extend(ndtv)
    
    logger.info("Scraping India Today fallback...")
    india_today = scrape_india_today_fallback()
    logger.info(f"India Today fallback: {len(india_today)}")
    all_stories.extend(india_today)
    
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
    is_morning = True
    
    categorized = {
        "politics": [s for s in unique if s.get('is_politics') or s['category']=='politics'][:20],
        "hyderabad": [s for s in unique if s['category']=='hyderabad'][:15],
        "telangana": [s for s in unique if s['category']=='telangana'][:15],
        "india": [s for s in unique if s['category']=='india'][:15],
        "world": [s for s in unique if s['category']=='world'][:10],
        "all": unique[:40],
    }
    
    # Morning: ensure ALL categories covered, politics first
    morning_titles = []
    # Politics first - 5 titles
    for s in categorized.get("politics", [])[:5]:
        if s['title'] not in morning_titles:
            morning_titles.append(s['title'])
    # Hyderabad 3
    for s in categorized.get("hyderabad", [])[:3]:
        if s['title'] not in morning_titles:
            morning_titles.append(s['title'])
    # Telangana 3
    for s in categorized.get("telangana", [])[:3]:
        if s['title'] not in morning_titles:
            morning_titles.append(s['title'])
    # India 3
    for s in categorized.get("india", [])[:3]:
        if s['title'] not in morning_titles:
            morning_titles.append(s['title'])
    # World 2
    for s in categorized.get("world", [])[:2]:
        if s['title'] not in morning_titles:
            morning_titles.append(s['title'])
    
    # Fill remaining with unique
    for s in unique:
        if s['title'] not in morning_titles and len(morning_titles) < 25:
            morning_titles.append(s['title'])
    
    raw_titles = morning_titles[:25]
    
    logger.info(f"Aggregated V5 {len(unique)} fresh | Politics: {len(categorized['politics'])} | Hyd: {len(categorized['hyderabad'])} | Telangana: {len(categorized['telangana'])} | India: {len(categorized['india'])} | World: {len(categorized['world'])}")
    logger.info(f"Sources V5: Munsif {len(munsif)}, Etemaad {len(etemaad)}, NDTV {len(ndtv)}, IndiaToday {len(india_today)}")
    
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
            "ndtv": len(ndtv)
        }
    }

def aggregate_fresh_morning():
    return aggregate_fresh_morning_v5()

if __name__ == "__main__":
    data = aggregate_fresh_morning_v5()
    print(f"\nTotal: {data['total_count']}")
    for cat in ["politics","hyderabad","telangana","india","world"]:
        stories = data['categorized'].get(cat, [])
        if stories:
            print(f"\n--- {cat.upper()} ({len(stories)}) ---")
            for s in stories[:5]:
                print(f" [{s['source']}] {s['title'][:80]}")
