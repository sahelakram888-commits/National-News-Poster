"""
National Reporter - Breaking News Detector
Detects breaking/important news as it happens, not just routine
"""
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config import BREAKING_NEWS, OUTPUT_DIR

logger = logging.getLogger(__name__)

BREAKING_KEYWORDS = BREAKING_NEWS["keywords"]

# File to store last posted news to avoid duplicates
LAST_POSTED_FILE = OUTPUT_DIR / "last_posted.json"

def load_last_posted() -> Dict:
    try:
        if LAST_POSTED_FILE.exists():
            with open(LAST_POSTED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load last posted: {e}")
    return {"titles": [], "last_breaking": None, "last_routine": None}

def save_last_posted(titles: List[str], is_breaking: bool = False):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        data = load_last_posted()
        # Keep last 50 titles to avoid duplicates
        data["titles"] = (titles + data.get("titles", []))[:50]
        if is_breaking:
            data["last_breaking"] = datetime.now().isoformat()
        else:
            data["last_routine"] = datetime.now().isoformat()
        with open(LAST_POSTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not save last posted: {e}")

def calculate_breaking_score(title: str, source: str = "") -> int:
    """
    Calculate breaking news score 0-10
    8-10 = Breaking, immediate post
    5-7 = Important, routine
    0-4 = Normal
    """
    score = 0
    lower = title.lower()
    
    # Keyword matching
    breaking_matches = sum(1 for kw in BREAKING_KEYWORDS if kw in lower)
    score += min(breaking_matches * 2, 6)  # Up to 6 points for keywords
    
    # Politics + important persons
    important_persons = ['cm', 'pm', 'minister', 'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'governor', 'high court', 'supreme court']
    if any(p in lower for p in important_persons):
        score += 2
    
    # Action words indicating breaking
    action_words = ['resigns', 'arrested', 'wins', 'loses', 'announces', 'declares', 'dies', 'accident', 'blast', 'firing', 'protest', 'result']
    if any(a in lower for a in action_words):
        score += 2
    
    # Recency bonus - if title has time indicators like "just in", "live", "today"
    recency_words = ['just in', 'live', 'today', 'now', 'breaking']
    if any(r in lower for r in recency_words):
        score += 1
    
    # Length check - very short or very long less likely breaking
    if 20 <= len(title) <= 150:
        score += 1
    
    return min(score, 10)

def is_breaking_news(title: str, score: int = None) -> bool:
    if score is None:
        score = calculate_breaking_score(title)
    return score >= BREAKING_NEWS["importance_threshold"]

def detect_breaking_news(aggregated_data: Dict) -> Dict:
    """
    Detect breaking news from aggregated data
    Returns: {is_breaking: bool, breaking_stories: [], all_scores: []}
    """
    all_titles = aggregated_data.get('raw_titles', [])
    categorized = aggregated_data.get('categorized', {})
    
    last_posted = load_last_posted()
    last_titles = [t.lower() for t in last_posted.get('titles', [])]
    
    scored_stories = []
    for title in all_titles:
        # Skip if already posted recently
        if title.lower() in last_titles:
            continue
        
        score = calculate_breaking_score(title)
        scored_stories.append({
            "title": title,
            "score": score,
            "is_breaking": is_breaking_news(title, score),
            "is_new": True
        })
    
    # Sort by score descending
    scored_stories.sort(key=lambda x: x['score'], reverse=True)
    
    breaking_stories = [s for s in scored_stories if s['is_breaking']]
    
    # Also check categorized politics for breaking
    politics = categorized.get('politics', [])[:5]
    for story in politics:
        title = story.get('title', '')
        if title.lower() in last_titles:
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
    
    is_breaking = len(breaking_stories) > 0
    
    logger.info(f"Breaking detection: {len(breaking_stories)} breaking, {len(scored_stories)} total scored, threshold {BREAKING_NEWS['importance_threshold']}")
    if breaking_stories:
        for b in breaking_stories[:3]:
            logger.info(f"  BREAKING (Score {b['score']}): {b['title']}")
    
    return {
        "is_breaking": is_breaking,
        "breaking_stories": breaking_stories,
        "all_scored": scored_stories[:10],
        "should_post_immediately": is_breaking and BREAKING_NEWS["immediate_post"],
        "routine_should_post": True,  # Always post routine every 2h, but breaking takes priority
        "checked_at": datetime.now().isoformat()
    }

def should_post_now(aggregated_data: Dict, is_routine_schedule: bool = False) -> Dict:
    """
    Decide if we should post now
    - If breaking news detected: post immediately
    - If routine schedule (every 2h): post routine
    - If no new news: skip to avoid duplicates
    """
    breaking_result = detect_breaking_news(aggregated_data)
    
    last_posted = load_last_posted()
    
    # Check if we have new titles
    all_titles = aggregated_data.get('raw_titles', [])
    new_titles = [t for t in all_titles if t.lower() not in [x.lower() for x in last_posted.get('titles', [])]]
    
    decision = {
        "should_post": False,
        "reason": "",
        "is_breaking": breaking_result["is_breaking"],
        "breaking_stories": breaking_result["breaking_stories"],
        "is_routine": is_routine_schedule,
        "new_titles_count": len(new_titles)
    }
    
    if breaking_result["is_breaking"]:
        decision["should_post"] = True
        decision["reason"] = f"BREAKING NEWS detected ({len(breaking_result['breaking_stories'])} stories) - immediate post"
        decision["priority"] = "BREAKING"
    elif is_routine_schedule and len(new_titles) > 0:
        decision["should_post"] = True
        decision["reason"] = f"Routine schedule (every 2h) + {len(new_titles)} new verified stories"
        decision["priority"] = "ROUTINE"
    elif is_routine_schedule and len(new_titles) == 0:
        # Even if no new titles, post in morning to cover all categories, or if politics important
        hour = datetime.now().hour
        if hour in [6,7,8,9,10,11]:  # Morning - always post
            decision["should_post"] = True
            decision["reason"] = f"Morning routine (6-11 AM) - covering all categories even if no brand new titles"
            decision["priority"] = "MORNING_ROUTINE"
        else:
            decision["should_post"] = False
            decision["reason"] = f"No new verified news, skipping to avoid duplicate (last posted {len(last_posted.get('titles', []))} titles)"
            decision["priority"] = "SKIP"
    else:
        decision["should_post"] = False
        decision["reason"] = "Not routine schedule and no breaking news"
        decision["priority"] = "SKIP"
    
    logger.info(f"Post decision: {decision['should_post']} | Reason: {decision['reason']} | Priority: {decision.get('priority')}")
    
    return decision

if __name__ == "__main__":
    # Test
    test_data = {
        "raw_titles": [
            "BREAKING: Telangana CM Revanth Reddy announces major scheme",
            "BJP attacks Revanth Reddy over comments",
            "Hyderabad police action in Old City",
            "Normal news about weather"
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
    print(f"Breaking: {result['is_breaking']}")
    print(f"Stories: {result['breaking_stories']}")
    
    decision = should_post_now(test_data, is_routine_schedule=True)
    print(f"Decision: {decision}")
