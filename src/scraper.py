"""
National Reporter - News Scraper V2 - Politics Focus + Verified Only
- Prioritizes politics news
- Morning: covers all categories
- Filters unverified/fake news
- NO links
"""
import re
import time
import logging
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

from config import NEWS_SOURCES, NO_LINKS, CONTENT_PREFS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ur;q=0.8"
}

# Keywords for politics preference
POLITICS_KEYWORDS = [
    'bjp', 'congress', 'brs', 'trs', 'aimim', 'mim', 'assembly', 'election', 'minister', 
    'cm', 'chief minister', 'mla', 'mp', 'government', 'politics', 'political', 'revanth', 
    'ktr', 'kcr', 'owaisi', 'modi', 'rahul', 'telangana', 'mayor', 'corporation', 'council',
    'parliament', 'lok sabha', 'rajya sabha', 'vidhan', 'election commission', 'campaign',
    'manifesto', 'alliance', 'coalition', 'opposition', 'ruling', 'governance'
]

# Fake/unverified indicators to filter out
FAKE_NEWS_INDICATORS = [
    'shocking', 'you won\'t believe', 'viral', 'rumor', 'unconfirmed', 'allegedly fake',
    'hoax', 'clickbait', 'forwarded as received', 'whatsapp forward'
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    if NO_LINKS:
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_politics_news(title: str) -> bool:
    lower = title.lower()
    return any(kw in lower for kw in POLITICS_KEYWORDS)

def is_verified_news(title: str) -> bool:
    """Filter out potentially fake/unverified news"""
    lower = title.lower()
    # Check for fake indicators
    if any(indicator in lower for indicator in FAKE_NEWS_INDICATORS):
        return False
    # Too short or too sensational might be unverified
    if len(title) < 15 or len(title) > 280:
        return False
    # Must have some credible structure
    if title.count('!') > 1 or title.count('?') > 1:
        return False
    return True

def fetch_page(url: str, timeout=8):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, 'html.parser')
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e} (timeout {timeout}s)")
        return None

def scrape_munsif_home() -> List[Dict]:
    stories = []
    soup = fetch_page(NEWS_SOURCES["munsif"]["url"])
    if not soup:
        return stories

    articles = soup.find_all(['h2','h3'], limit=25)
    for el in articles[:20]:
        title = clean_text(el.get_text())
        if not is_verified_news(title):
            continue
        is_pol = is_politics_news(title)
        stories.append({
            "source": "Munsif Daily",
            "title": title,
            "category": "politics" if is_pol else "general",
            "is_politics": is_pol,
            "verified": True,
            "timestamp": datetime.now().isoformat(),
        })
    return stories

def scrape_munsif_category(category_url: str, category_name: str) -> List[Dict]:
    stories = []
    soup = fetch_page(category_url)
    if not soup:
        return stories
    headlines = soup.find_all(['h2','h3'], limit=12)
    for h in headlines:
        title = clean_text(h.get_text())
        if not is_verified_news(title):
            continue
        is_pol = is_politics_news(title) or category_name in ['politics', 'national']
        stories.append({
            "source": f"Munsif - {category_name}",
            "title": title,
            "category": category_name,
            "is_politics": is_pol,
            "verified": True,
            "timestamp": datetime.now().isoformat(),
        })
    return stories

def scrape_etemaad_home() -> List[Dict]:
    stories = []
    soup = fetch_page(NEWS_SOURCES["etemaad"]["english_url"])
    if not soup:
        return stories
    
    for selector in ['h4','h3','h2']:
        elements = soup.find_all(selector, limit=25)
        for el in elements:
            title = clean_text(el.get_text())
            if not is_verified_news(title):
                continue
            is_pol = is_politics_news(title)
            stories.append({
                "source": "Etemaad Daily",
                "title": title,
                "category": "politics" if is_pol else "general",
                "is_politics": is_pol,
                "verified": True,
                "timestamp": datetime.now().isoformat()
            })
        if stories:
            break
    return stories[:15]

def scrape_etemaad_categories() -> List[Dict]:
    all_stories = []
    for cat_name, cat_url in NEWS_SOURCES["etemaad"]["categories"].items():
        soup = fetch_page(cat_url)
        if not soup:
            continue
        headlines = soup.find_all(['h4','h3','h2'], limit=10)
        for h in headlines:
            title = clean_text(h.get_text())
            if not is_verified_news(title):
                continue
            is_pol = is_politics_news(title) or cat_name in ['politics', 'national']
            all_stories.append({
                "source": f"Etemaad - {cat_name}",
                "title": title,
                "category": cat_name,
                "is_politics": is_pol,
                "verified": True,
                "timestamp": datetime.now().isoformat()
            })
        time.sleep(0.3)
    return all_stories

def aggregate_news() -> Dict:
    logger.info("Starting news aggregation - Politics preferred, Verified only...")
    all_stories = []

    # 1. Munsif - Politics first
    logger.info("Scraping Munsif Daily (Politics priority)...")
    all_stories.extend(scrape_munsif_home())
    # Politics category first
    if "politics" in NEWS_SOURCES["munsif"]["categories"]:
        all_stories.extend(scrape_munsif_category(NEWS_SOURCES["munsif"]["categories"]["politics"], "politics"))
    for cat_name, cat_url in NEWS_SOURCES["munsif"]["categories"].items():
        if cat_name == "politics":
            continue
        all_stories.extend(scrape_munsif_category(cat_url, cat_name))
        time.sleep(0.3)

    # 2. Etemaad
    logger.info("Scraping Etemaad Daily...")
    all_stories.extend(scrape_etemaad_home())
    all_stories.extend(scrape_etemaad_categories())

    # Deduplicate
    seen = set()
    unique_stories = []
    for s in all_stories:
        key = s['title'].lower().strip()
        if key not in seen and len(key) > 10:
            seen.add(key)
            unique_stories.append(s)

    # Sort: politics first, then verified, then recent
    unique_stories.sort(key=lambda x: (not x.get('is_politics', False), x['title']), reverse=False)

    # Categorize with politics priority
    hour = datetime.now().hour
    is_morning = hour in CONTENT_PREFS.get("morning_hours", [6,7,8,9,10,11])
    
    categorized = {
        "politics": [s for s in unique_stories if s.get('is_politics')][:12],
        "hyderabad": [s for s in unique_stories if "hyderabad" in s['category'].lower()][:10],
        "telangana": [s for s in unique_stories if "telangana" in s['category'].lower()][:10],
        "india": [s for s in unique_stories if s['category'] in ["national","india"]][:10],
        "world": [s for s in unique_stories if s['category'] == "world"][:8],
        "regional": [s for s in unique_stories if s['category'] in ["regional","general"]][:8],
        "all": unique_stories[:30],
        "morning_roundup": unique_stories[:15] if is_morning else []
    }

    # For morning, ensure coverage of all categories
    if is_morning:
        logger.info(f"Morning mode ({hour}h) - covering all categories")
        # Ensure at least 2 from each major category in morning
        morning_titles = []
        for cat in ["politics", "hyderabad", "telangana", "india", "world"]:
            morning_titles.extend([s['title'] for s in categorized.get(cat, [])[:3]])
        raw_titles = morning_titles[:20]
    else:
        # Day/night: politics first
        politics_titles = [s['title'] for s in categorized.get('politics', [])[:10]]
        other_titles = [s['title'] for s in unique_stories if not s.get('is_politics')][:10]
        raw_titles = politics_titles + other_titles
        raw_titles = raw_titles[:20]

    logger.info(f"Aggregated {len(unique_stories)} verified stories | Politics: {len(categorized['politics'])} | Morning: {is_morning}")

    return {
        "fetched_at": datetime.now().isoformat(),
        "total_count": len(unique_stories),
        "politics_count": len(categorized['politics']),
        "is_morning": is_morning,
        "hour": hour,
        "categorized": categorized,
        "raw_titles": raw_titles,
        "verified_only": True
    }

if __name__ == "__main__":
    data = aggregate_news()
    print(f"Total: {data['total_count']} | Politics: {data['politics_count']} | Morning: {data['is_morning']}")
    for cat, stories in data['categorized'].items():
        if stories:
            print(f"\n--- {cat.upper()} ({len(stories)}) ---")
            for s in stories[:3]:
                print(f" - [{'POL' if s.get('is_politics') else 'GEN'}] {s['title']}")
