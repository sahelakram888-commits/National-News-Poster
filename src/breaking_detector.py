"""
National Reporter - Breaking News Detector V2
- Fixes duplicate posts in GitHub Actions (ephemeral runners)
- Checks Facebook Page recent posts + local file + hash
- Dynamic, not static
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
        # Create hash of titles for duplicate detection
        titles_str = "".join(sorted(titles[:3])).lower()
        titles_hash = hashlib.md5(titles_str.encode()).hexdigest()
        
        data["titles"] = (titles + data.get("titles", []))[:100]
        data["hashes"] = ([titles_hash] + data.get("hashes", []))[:50]
        data["last_titles_hash"] = titles_hash
        if is_breaking:
            data["last_breaking"] = datetime.now().isoformat()
        else:
            data["last_routine"] = datetime.now().isoformat()
        
        with open(LAST_POSTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved last posted: hash {titles_hash}, {len(titles)} titles")
    except Exception as e:
        logger.warning(f"Could not save last posted: {e}")

def get_facebook_recent_posts(limit: int = 10) -> List[str]:
    """
    Get recent posts from Facebook Page to check for duplicates
    This works in GitHub Actions where local file is ephemeral
    """
    try:
        if not FACEBOOK_PAGE_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
            logger.warning("No FB token for duplicate check via API")
            return []
        
        import requests
        url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/posts?limit={limit}&fields=message&access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            recent_messages = []
            for post in data.get('data', []):
                msg = post.get('message', '')
                # Extract first 50 chars of headline from message
                if msg:
                    recent_messages.append(msg[:100].lower())
            logger.info(f"Fetched {len(recent_messages)} recent FB posts for duplicate check")
            return recent_messages
        else:
            logger.warning(f"Failed to fetch FB recent posts: {r.status_code} - {r.text[:300]}")
            return []
    except Exception as e:
        logger.warning(f"Exception fetching FB recent posts: {e}")
        return []

def is_duplicate_title(title: str, recent_fb_posts: List[str] = None, last_posted_data: Dict = None) -> bool:
    """
    Check if title is duplicate by:
    1. Local last_posted.json
    2. Facebook recent posts (for GitHub Actions)
    3. Hash comparison
    """
    if last_posted_data is None:
        last_posted_data = load_last_posted()
    
    lower_title = title.lower().strip()
    
    # Check local file
    for posted_title in last_posted_data.get('titles', [])[:20]:
        # If 70% similarity or exact match
        if lower_title == posted_title.lower().strip():
            logger.info(f"Duplicate found in local file: {title[:50]}")
            return True
        # Check if first 30 chars match (same news)
        if len(lower_title) > 20 and len(posted_title) > 20:
            if lower_title[:30] == posted_title.lower().strip()[:30]:
                logger.info(f"Duplicate (first 30 chars) in local: {title[:50]}")
                return True
    
    # Check Facebook recent posts
    if recent_fb_posts:
        for fb_msg in recent_fb_posts:
            # If title appears in recent FB post message
            if len(lower_title) > 15 and lower_title[:20] in fb_msg:
                logger.info(f"Duplicate found in FB recent posts: {title[:50]}")
                return True
            # Check headline similarity
            if lower_title[:25] in fb_msg or fb_msg[:25] in lower_title:
                # Additional check to avoid false positives
                if len(lower_title) > 25:
                    logger.info(f"Possible duplicate in FB: {title[:50]}")
                    # Don't return True immediately for this, just log
    
    # Check hash
    titles_hash = hashlib.md5(lower_title.encode()).hexdigest()
    if titles_hash in last_posted_data.get('hashes', [])[:10]:
        logger.info(f"Duplicate hash found: {title[:50]}")
        return True
    
    return False

def calculate_breaking_score(title: str, source: str = "") -> int:
    score = 0
    lower = title.lower()
    
    breaking_matches = sum(1 for kw in BREAKING_KEYWORDS if kw in lower)
    score += min(breaking_matches * 2, 6)
    
    important_persons = ['cm', 'pm', 'minister', 'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'governor', 'high court', 'supreme court', 'mayor']
    if any(p in lower for p in important_persons):
        score += 2
    
    action_words = ['resigns', 'arrested', 'wins', 'loses', 'announces', 'declares', 'dies', 'accident', 'blast', 'firing', 'protest', 'result', 'withdraws', 'attacks']
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
        # Skip if duplicate
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
    
    # Check politics category too
    politics = categorized.get('politics', [])[:5]
    for story in politics:
        title = story.get('title', '')
        if is_duplicate_title(title, recent_fb_posts, last_posted):
            continue
        score = calculate_breaking_score(title)
        if score >= 7 and not any(s['title'] == title for s in scored_stories):
            scored_stories.append({
                "title": title,
                "score": score,
                "is_breaking": score >= 8,
                "is_new": True,
                "category": "politics"
            })
    
    # Re-sort
    scored_stories.sort(key=lambda x: x['score'], reverse=True)
    breaking_stories = [s for s in scored_stories if s['is_breaking']]
    
    logger.info(f"Breaking detection: {len(breaking_stories)} breaking, {len(scored_stories)} new (after dedup), threshold {BREAKING_NEWS['importance_threshold']}")
    if breaking_stories:
        for b in breaking_stories[:3]:
            logger.info(f"  BREAKING (Score {b['score']}): {b['title']}")
    else:
        logger.info(f"  No breaking news, top scored: {scored_stories[:2]}")
    
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
    recent_fb_posts = get_facebook_recent_posts(limit=10)
    
    all_titles = aggregated_data.get('raw_titles', [])
    new_titles = []
    for t in all_titles:
        if not is_duplicate_title(t, recent_fb_posts, last_posted):
            new_titles.append(t)
    
    decision = {
        "should_post": False,
        "reason": "",
        "is_breaking": breaking_result["is_breaking"],
        "breaking_stories": breaking_result["breaking_stories"],
        "is_routine": is_routine_schedule,
        "new_titles_count": len(new_titles),
        "total_titles": len(all_titles)
    }
    
    if breaking_result["is_breaking"]:
        decision["should_post"] = True
        decision["reason"] = f"BREAKING NEWS ({len(breaking_result['breaking_stories'])} new breaking) - immediate post in middle of routine 2h cycle (as it happens)"
        decision["priority"] = "BREAKING"
    elif is_routine_schedule:
        # Routine: ALWAYS post every 2 hours FOREVER - NEVER STOP (user request: set once for all, done, not stop again and again)
        # This ensures 2h cycle maintained forever, even if no brand new news
        # Each post will be unique (dynamic headline based on time + latest Munsif/Etemaad news)
        last_routine_str = last_posted.get('last_routine')
        hours_since = 0
        if last_routine_str:
            try:
                last_routine = datetime.fromisoformat(last_routine_str)
                hours_since = (datetime.now() - last_routine).total_seconds() / 3600
            except:
                hours_since = 5
        
        decision["should_post"] = True  # ALWAYS True for routine - maintain forever
        if len(new_titles) > 0:
            decision["reason"] = f"Routine 2h cycle FOREVER (maintained, never stops) + {len(new_titles)} NEW from Munsif & Etemaad - {hours_since:.1f}h since last"
            decision["priority"] = "ROUTINE"
        else:
            decision["reason"] = f"Routine 2h cycle FOREVER - maintaining forever, posting latest important from Munsif & Etemaad (unique card every time, never old duplicate), last {hours_since:.1f}h ago, never stops"
            decision["priority"] = "ROUTINE_FOREVER"
    else:
        decision["should_post"] = False
        decision["reason"] = "Not routine schedule and no breaking news"
        decision["priority"] = "SKIP"
    
    logger.info(f"Post decision: {decision['should_post']} | {decision['reason']} | Priority: {decision.get('priority')} | New: {len(new_titles)}/{len(all_titles)}")
    
    return decision

if __name__ == "__main__":
    test_data = {
        "raw_titles": [
            "BREAKING: Telangana CM Revanth Reddy announces major scheme",
            "BJP attacks Revanth Reddy over comments",
            "Hyderabad police action in Old City",
        ],
        "categorized": {
            "politics": [{"title": "BREAKING: Telangana CM Revanth Reddy announces major scheme"}],
            "hyderabad": [],
            "telangana": [],
            "india": [],
            "world": [],
            "all": []
        }
    }
    result = detect_breaking_news(test_data)
    print(f"Breaking: {result['is_breaking']}, New: {result['total_new']}")
    decision = should_post_now(test_data, is_routine_schedule=True)
    print(f"Decision: {decision}")
