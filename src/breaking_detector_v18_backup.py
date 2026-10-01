"""
National Reporter - Breaking Detector V3 - FIXES OLD CARD PERMANENTLY
- Routine 2h FOREVER never stops, unique card every 2h via rotation
- Breaking check 15min immediate post
- Duplicate check ONLY for breaking (to avoid spam same breaking), NOT for routine
- Routine always posts unique card from latest Munsif & Etemaad
"""
import re
import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from config import BREAKING_NEWS, OUTPUT_DIR, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN

logger = logging.getLogger(__name__)

BREAKING_KEYWORDS = BREAKING_NEWS["keywords"]
LAST_POSTED_FILE = OUTPUT_DIR / "last_posted.json"

def load_last_posted() -> Dict:
    try:
        if LAST_POSTED_FILE.exists():
            with open(LAST_POSTED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load last posted: {e}")
    return {"titles": [], "hashes": [], "last_breaking": None, "last_routine": None, "last_titles_hash": ""}

def save_last_posted(titles: List[str], is_breaking: bool = False):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        data = load_last_posted()
        titles_str = "".join(sorted(titles[:3])).lower()
        titles_hash = hashlib.md5(titles_str.encode()).hexdigest()
        
        # Keep only recent 50, avoid bloating with repeats
        unique_titles = []
        seen = set()
        for t in titles + data.get("titles", []):
            tl = t.lower().strip()
            if tl not in seen:
                seen.add(tl)
                unique_titles.append(t)
        
        data["titles"] = unique_titles[:50]
        data["hashes"] = ([titles_hash] + data.get("hashes", []))[:20]
        data["last_titles_hash"] = titles_hash
        if is_breaking:
            data["last_breaking"] = datetime.now().isoformat()
        else:
            data["last_routine"] = datetime.now().isoformat()
        
        with open(LAST_POSTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved last posted: hash {titles_hash}, {len(titles)} titles, breaking={is_breaking}")
    except Exception as e:
        logger.warning(f"Could not save last posted: {e}")

def get_facebook_recent_posts(limit: int = 10) -> List[str]:
    try:
        if not FACEBOOK_PAGE_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
            return []
        import requests
        url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/posts?limit={limit}&fields=message&access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            recent_messages = []
            for post in data.get('data', []):
                msg = post.get('message', '')
                if msg:
                    recent_messages.append(msg[:100].lower())
            logger.info(f"Fetched {len(recent_messages)} recent FB posts")
            return recent_messages
        else:
            logger.warning(f"Failed to fetch FB recent: {r.status_code}")
            return []
    except Exception as e:
        logger.warning(f"Exception fetching FB recent: {e}")
        return []

def is_duplicate_title(title: str, recent_fb_posts: List[str] = None, last_posted_data: Dict = None) -> bool:
    """Only for breaking duplicate check, not for routine"""
    if last_posted_data is None:
        last_posted_data = load_last_posted()
    lower_title = title.lower().strip()
    for posted_title in last_posted_data.get('titles', [])[:15]:
        if lower_title == posted_title.lower().strip():
            return True
        if len(lower_title) > 25 and lower_title[:25] == posted_title.lower().strip()[:25]:
            return True
    if recent_fb_posts:
        for fb_msg in recent_fb_posts:
            if len(lower_title) > 20 and lower_title[:20] in fb_msg:
                return True
    return False

def calculate_breaking_score(title: str, source: str = "") -> int:
    score = 0
    lower = title.lower()
    breaking_matches = sum(1 for kw in BREAKING_KEYWORDS if kw in lower)
    score += min(breaking_matches * 2, 6)
    important_persons = ['cm', 'pm', 'minister', 'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'governor', 'high court', 'supreme court', 'mayor', 'mla', 'mp']
    if any(p in lower for p in important_persons):
        score += 2
    action_words = ['resigns', 'arrested', 'wins', 'loses', 'announces', 'declares', 'dies', 'accident', 'blast', 'firing', 'protest', 'result', 'withdraws', 'attacks', 'seeks', 'demands']
    if any(a in lower for a in action_words):
        score += 2
    recency_words = ['just in', 'live', 'today', 'now', 'breaking', 'urgent']
    if any(r in lower for r in recency_words):
        score += 1
    if 20 <= len(title) <= 180:
        score += 1
    return min(score, 10)

def is_breaking_news(title: str, score: int = None) -> bool:
    if score is None:
        score = calculate_breaking_score(title)
    return score >= BREAKING_NEWS["importance_threshold"]

def detect_breaking_news(aggregated_data: Dict) -> Dict:
    all_titles = aggregated_data.get('raw_titles', [])
    categorized = aggregated_data.get('categorized', {})
    last_posted = load_last_posted()
    recent_fb_posts = get_facebook_recent_posts(limit=15)
    
    scored_stories = []
    for title in all_titles:
        if is_duplicate_title(title, recent_fb_posts, last_posted):
            continue
        score = calculate_breaking_score(title)
        scored_stories.append({
            "title": title,
            "score": score,
            "is_breaking": is_breaking_news(title, score),
            "is_new": True
        })
    scored_stories.sort(key=lambda x: x['score'], reverse=True)
    breaking_stories = [s for s in scored_stories if s['is_breaking']]
    
    logger.info(f"Breaking detection: {len(breaking_stories)} breaking, {len(scored_stories)} new, threshold {BREAKING_NEWS['importance_threshold']}")
    if breaking_stories:
        for b in breaking_stories[:3]:
            logger.info(f"  BREAKING (Score {b['score']}): {b['title'][:80]}")
    
    return {
        "is_breaking": len(breaking_stories) > 0,
        "breaking_stories": breaking_stories,
        "all_scored": scored_stories[:10],
        "should_post_immediately": len(breaking_stories) > 0 and BREAKING_NEWS["immediate_post"],
        "checked_at": datetime.now().isoformat(),
        "total_new": len(scored_stories)
    }

def should_post_now(aggregated_data: Dict, is_routine_schedule: bool = False) -> Dict:
    breaking_result = detect_breaking_news(aggregated_data)
    last_posted = load_last_posted()
    all_titles = aggregated_data.get('raw_titles', [])
    
    decision = {
        "should_post": False,
        "reason": "",
        "is_breaking": breaking_result["is_breaking"],
        "breaking_stories": breaking_result["breaking_stories"],
        "is_routine": is_routine_schedule,
        "new_titles_count": breaking_result["total_new"],
        "total_titles": len(all_titles)
    }
    
    if breaking_result["is_breaking"]:
        decision["should_post"] = True
        decision["reason"] = f"BREAKING NEWS ({len(breaking_result['breaking_stories'])} new breaking) - immediate post as it happens"
        decision["priority"] = "BREAKING"
    elif is_routine_schedule:
        # ROUTINE 2H FOREVER - ALWAYS post, unique card every 2h via rotation, NEVER stops
        last_routine_str = last_posted.get('last_routine')
        hours_since = 0
        if last_routine_str:
            try:
                last_routine = datetime.fromisoformat(last_routine_str)
                hours_since = (datetime.now() - last_routine).total_seconds() / 3600
            except:
                hours_since = 5
        
        decision["should_post"] = True  # ALWAYS True - fixes old card by ensuring new unique card
        decision["reason"] = f"Routine 2h FOREVER (never stops) - unique card rotation {datetime.now().hour//2} from actual latest Munsif & Etemaad, {breaking_result['total_new']} new titles, {hours_since:.1f}h since last"
        decision["priority"] = "ROUTINE_FOREVER_UNIQUE"
    else:
        decision["should_post"] = False
        decision["reason"] = "Not routine schedule and no breaking news"
        decision["priority"] = "SKIP"
    
    logger.info(f"Post decision: {decision['should_post']} | {decision['reason']} | Priority: {decision.get('priority')}")
    return decision
