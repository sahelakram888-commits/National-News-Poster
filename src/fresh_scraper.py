"""
National Reporter - Fresh Scraper V3 - Morning News Coverage
- Munsif & Etemaad priority, fallback to India Today & Indian Express
- Translates English to Urdu & Roman Urdu
- Morning 6-11 AM covers ALL categories nicely
"""
import re
import time
import logging
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8"
}

POLITICS_KEYWORDS = [
    'bjp', 'congress', 'brs', 'trs', 'aimim', 'mim', 'assembly', 'election', 'minister', 
    'cm', 'chief minister', 'mla', 'mp', 'government', 'politics', 'political', 'revanth', 
    'ktr', 'kcr', 'owaisi', 'modi', 'rahul', 'telangana', 'mayor', 'corporation', 'council',
    'parliament', 'lok sabha', 'rajya sabha', 'vidhan', 'election commission', 'campaign'
]

FAKE_INDICATORS = ['shocking', 'you won\'t believe', 'viral', 'rumor', 'unconfirmed', 'hoax', 'clickbait']

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_verified(title: str) -> bool:
    lower = title.lower()
    if any(ind in lower for ind in FAKE_INDICATORS):
        return False
    if len(title) < 15 or len(title) > 280:
        return False
    if title.count('!') > 1 or title.count('?') > 1:
        return False
    return True

def fetch_page(url: str, timeout=8):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')
    except Exception as e:
        logger.warning(f"Failed {url}: {e}")
        return None

# --- MUNSIF ---
def scrape_munsif() -> List[Dict]:
    stories = []
    urls = [
        "https://munsifdaily.com/",
        "https://munsifdaily.com/category/hyderabad/",
        "https://munsifdaily.com/category/telangana/",
        "https://munsifdaily.com/category/national/",
        "https://munsifdaily.com/category/politics/"
    ]
    for url in urls:
        soup = fetch_page(url, timeout=8)
        if not soup:
            continue
        for el in soup.find_all(['h2','h3'], limit=15):
            title = clean_text(el.get_text())
            if not is_verified(title):
                continue
            cat = "politics" if any(k in title.lower() for k in POLITICS_KEYWORDS) else "general"
            if "hyderabad" in url:
                cat = "hyderabad"
            elif "telangana" in url:
                cat = "telangana"
            stories.append({
                "source": "Munsif Daily",
                "title": title,
                "category": cat,
                "is_politics": cat=="politics" or any(k in title.lower() for k in POLITICS_KEYWORDS),
                "verified": True,
                "timestamp": datetime.now().isoformat(),
                "is_urdu": any('\u0600' <= c <= '\u06FF' for c in title)
            })
        time.sleep(0.2)
    return stories

# --- ETEMAAD ---
def scrape_etemaad() -> List[Dict]:
    stories = []
    urls = [
        "https://www.en.etemaaddaily.com/",
        "https://www.en.etemaaddaily.com/world/hyderabad",
        "https://www.en.etemaaddaily.com/world/telangana",
        "https://www.en.etemaaddaily.com/world/national",
    ]
    for url in urls:
        soup = fetch_page(url, timeout=8)
        if not soup:
            continue
        for selector in ['h4','h3','h2']:
            for el in soup.find_all(selector, limit=15):
                title = clean_text(el.get_text())
                if not is_verified(title):
                    continue
                cat = "politics" if any(k in title.lower() for k in POLITICS_KEYWORDS) else "general"
                if "hyderabad" in url:
                    cat = "hyderabad"
                elif "telangana" in url:
                    cat = "telangana"
                stories.append({
                    "source": "Etemaad Daily",
                    "title": title,
                    "category": cat,
                    "is_politics": cat=="politics" or any(k in title.lower() for k in POLITICS_KEYWORDS),
                    "verified": True,
                    "timestamp": datetime.now().isoformat(),
                    "is_urdu": any('\u0600' <= c <= '\u06FF' for c in title)
                })
            if stories:
                break
        time.sleep(0.2)
    return stories[:15]

# --- INDIA TODAY (FRESH MORNING NEWS) ---
def scrape_india_today() -> List[Dict]:
    stories = []
    urls = [
        "https://www.indiatoday.in/india",
        "https://www.indiatoday.in/cities/hyderabad",
        "https://www.indiatoday.in/cities",
        "https://www.indiatoday.in/politics",
        "https://www.indiatoday.in/world"
    ]
    for url in urls:
        soup = fetch_page(url, timeout=8)
        if not soup:
            continue
        # India Today uses h2 with story titles
        for el in soup.find_all(['h2','a'], limit=20):
            title = clean_text(el.get_text())
            if len(title) < 20 or len(title) > 200:
                continue
            if not is_verified(title):
                continue
            # Filter out non-news
            if any(x in title.lower() for x in ['advertisement', 'subscribe', 'live tv', 'magazine']):
                continue
            cat = "india"
            if "hyderabad" in url or "hyderabad" in title.lower():
                cat = "hyderabad"
            elif "politics" in url or any(k in title.lower() for k in POLITICS_KEYWORDS):
                cat = "politics"
            elif "world" in url:
                cat = "world"
            elif "telangana" in title.lower():
                cat = "telangana"
            
            stories.append({
                "source": "India Today",
                "title": title,
                "category": cat,
                "is_politics": cat=="politics" or any(k in title.lower() for k in POLITICS_KEYWORDS),
                "verified": True,
                "timestamp": datetime.now().isoformat(),
                "is_urdu": False,
                "needs_translation": True
            })
        time.sleep(0.2)
        if len(stories) >= 15:
            break
    return stories[:15]

# --- INDIAN EXPRESS (FRESH) ---
def scrape_indian_express() -> List[Dict]:
    stories = []
    urls = [
        "https://indianexpress.com/section/india/",
        "https://indianexpress.com/section/cities/hyderabad/",
        "https://indianexpress.com/section/political-pulse/",
        "https://indianexpress.com/section/cities/",
        "https://indianexpress.com/section/world/"
    ]
    for url in urls:
        soup = fetch_page(url, timeout=8)
        if not soup:
            continue
        for el in soup.find_all(['h2','h3','a'], limit=25):
            title = clean_text(el.get_text())
            if len(title) < 20 or len(title) > 200:
                continue
            if not is_verified(title):
                continue
            if any(x in title.lower() for x in ['express premium', 'advertisement', 'buy now', 'subscribe']):
                continue
            cat = "india"
            if "hyderabad" in url or "hyderabad" in title.lower():
                cat = "hyderabad"
            elif "political" in url or any(k in title.lower() for k in POLITICS_KEYWORDS):
                cat = "politics"
            elif "world" in url:
                cat = "world"
            elif "telangana" in title.lower():
                cat = "telangana"
            
            stories.append({
                "source": "Indian Express",
                "title": title,
                "category": cat,
                "is_politics": cat=="politics" or any(k in title.lower() for k in POLITICS_KEYWORDS),
                "verified": True,
                "timestamp": datetime.now().isoformat(),
                "is_urdu": False,
                "needs_translation": True
            })
        time.sleep(0.2)
        if len(stories) >= 15:
            break
    return stories[:15]

def aggregate_fresh_news() -> Dict:
    logger.info("Starting FRESH news aggregation - Morning coverage ALL categories")
    logger.info("Sources: Munsif (priority) + Etemaad (priority) + India Today + Indian Express (fresh fallback)")
    
    all_stories = []
    
    # Priority 1: Munsif & Etemaad
    logger.info("Scraping Munsif Daily...")
    munsif = scrape_munsif()
    logger.info(f"Munsif: {len(munsif)} stories")
    all_stories.extend(munsif)
    
    logger.info("Scraping Etemaad Daily...")
    etemaad = scrape_etemaad()
    logger.info(f"Etemaad: {len(etemaad)} stories")
    all_stories.extend(etemaad)
    
    # Fallback fresh: India Today & Indian Express for morning news
    # If Munsif+Etemaad < 10 stories, fetch fresh from India Today & Express
    if len(all_stories) < 10:
        logger.info(f"Only {len(all_stories)} from Munsif+Etemaad, fetching fresh from India Today & Indian Express for morning coverage")
    
    logger.info("Scraping India Today (fresh morning)...")
    india_today = scrape_india_today()
    logger.info(f"India Today: {len(india_today)} stories")
    all_stories.extend(india_today)
    
    logger.info("Scraping Indian Express (fresh)...")
    express = scrape_indian_express()
    logger.info(f"Indian Express: {len(express)} stories")
    all_stories.extend(express)
    
    # Deduplicate
    seen = set()
    unique = []
    for s in all_stories:
        key = s['title'].lower().strip()
        if key not in seen and len(key) > 10:
            seen.add(key)
            unique.append(s)
    
    # Sort: politics first, then fresh
    unique.sort(key=lambda x: (not x.get('is_politics', False), x['title']))
    
    hour = datetime.now().hour
    is_morning = hour in [6,7,8,9,10,11] or True  # For now, always morning mode for coverage
    
    categorized = {
        "politics": [s for s in unique if s.get('is_politics')][:15],
        "hyderabad": [s for s in unique if s['category']=='hyderabad'][:10],
        "telangana": [s for s in unique if s['category']=='telangana'][:10],
        "india": [s for s in unique if s['category']=='india'][:10],
        "world": [s for s in unique if s['category']=='world'][:8],
        "all": unique[:30],
    }
    
    # Morning: ensure coverage ALL categories
    morning_titles = []
    for cat in ["politics", "hyderabad", "telangana", "india", "world"]:
        for s in categorized.get(cat, [])[:3]:
            morning_titles.append(s['title'])
    
    # Fill remaining from all
    for s in unique:
        if s['title'] not in morning_titles and len(morning_titles) < 20:
            morning_titles.append(s['title'])
    
    raw_titles = morning_titles[:20]
    
    logger.info(f"Aggregated {len(unique)} fresh stories | Politics: {len(categorized['politics'])} | Hyderabad: {len(categorized['hyderabad'])} | Telangana: {len(categorized['telangana'])} | India: {len(categorized['india'])} | World: {len(categorized['world'])}")
    logger.info(f"Sources: Munsif {len(munsif)}, Etemaad {len(etemaad)}, IndiaToday {len(india_today)}, Express {len(express)}")
    
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
            "indian_express": len(express)
        }
    }

if __name__ == "__main__":
    data = aggregate_fresh_news()
    print(f"\nTotal: {data['total_count']} | Politics: {data['politics_count']}")
    for cat, stories in data['categorized'].items():
        if stories and cat != 'all':
            print(f"\n--- {cat.upper()} ({len(stories)}) ---")
            for s in stories[:3]:
                print(f" [{s['source']}] {s['title'][:80]}")
