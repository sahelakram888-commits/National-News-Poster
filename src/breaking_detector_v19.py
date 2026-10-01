"""
National Reporter - Breaking Detector V19 - FIXES SAME CARD 4-5 TIMES
- Routine hourly FOREVER never stops, unique card every hour
- Breaking check 15min immediate post
- STRONG duplicate check for BOTH routine and breaking (fixes same cards 4-5 times)
- Checks FB recent 30 + last_posted.json + similarity
"""

import re
import json
import logging
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from config import BREAKING_NEWS, OUTPUT_DIR, FACEBOOK_PAGE_ID

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
        
        unique_titles = []
        seen = set()
        for t in titles + data.get("titles", []):
            if not t:
                continue
            tl = t.lower().strip()
            if tl not in seen and len(tl) > 10:
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

def get_facebook_recent_posts(limit: int = 30) -> List[str]:
    """Fetch recent FB posts to avoid duplicates - V19 uses system token auto-resolve"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    page_id = os.getenv("FACEBOOK_PAGE_ID", FACEBOOK_PAGE_ID)
    if not token:
        return []
    try:
        import requests
        # Auto-resolve system user token to page token
        try:
            me_url = f"https://graph.facebook.com/v20.0/me?access_token={token}"
            r = requests.get(me_url, timeout=8)
            if r.status_code == 200:
                me_data = r.json()
                if me_data.get('id') == '122098613787496439' or 'nr_api_bot' in me_data.get('name','').lower():
                    acc_url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={token}"
                    r2 = requests.get(acc_url, timeout=8)
                    if r2.status_code == 200:
                        for page in r2.json().get('data', []):
                            if page['id'] == page_id:
                                token = page['access_token']
                                break
        except:
            pass
        
        url = f"https://graph.facebook.com/v20.0/{page_id}/posts?limit={limit}&fields=message&access_token={token}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            recent_messages = []
            for post in data.get('data', []):
                msg = post.get('message', '')
                if msg:
                    recent_messages.append(msg[:200].lower())
            logger.info(f"Fetched {len(recent_messages)} recent FB posts for dedup")
            return recent_messages
        else:
            logger.warning(f"Failed to fetch FB recent: {r.status_code} {r.text[:200]}")
            return []
    except Exception as e:
        logger.warning(f"Exception fetching FB recent: {e}")
        return []

def is_duplicate_title_v19(title: str, recent_fb_posts: List[str] = None, last_posted_data: Dict = None) -> bool:
    """V19 STRONG duplicate check - prevents same card 4-5 times"""
    if last_posted_data is None:
        last_posted_data = load_last_posted()
    if recent_fb_posts is None:
        recent_fb_posts = []
    
    lower_title = title.lower().strip()
    if len(lower_title) < 10:
        return False
    
    # Check last_posted titles - exact and similarity
    for posted_title in last_posted_data.get('titles', [])[:30]:
        if not posted_title:
            continue
        pt_lower = posted_title.lower().strip()
        if lower_title == pt_lower:
            return True
        if len(lower_title) > 25 and len(pt_lower) > 25:
            if lower_title[:25] == pt_lower[:25]:
                return True
        # Word overlap 70%
        words1 = set(lower_title.split())
        words2 = set(pt_lower.split())
        if len(words1) > 3 and len(words2) > 3:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > 0.7:
                return True
    
    # Check FB recent
    for fb_msg in recent_fb_posts[:30]:
        if len(lower_title) > 20 and lower_title[:20] in fb_msg:
            return True
        # 3 key words overlap
        if len(lower_title.split()) > 4:
            key_words = [w for w in lower_title.split() if len(w) > 4][:3]
            if key_words and all(kw in fb_msg for kw in key_words):
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
    action_words = ['resigns', 'arrested', 'wins', 'loses', 'announces', 'declares', 'dies', 'accident', 'blast', 'firing', 'protest', 'result', 'withdraws', 'attacks', 'seeks', 'demands', 'detained', 'seized']
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
    last_posted = load_last_posted()
    recent_fb_posts = get_facebook_recent_posts(limit=30)
    
    scored_stories = []
    for title in all_titles:
        if is_duplicate_title_v19(title, recent_fb_posts, last_posted):
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
    
    logger.info(f"Breaking detection V19: {len(breaking_stories)} breaking, {len(scored_stories)} new (deduped), threshold {BREAKING_NEWS['importance_threshold']}")
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
    """V19: BOTH routine and breaking check duplicates - fixes same cards 4-5 times"""
    breaking_result = detect_breaking_news(aggregated_data)
    last_posted = load_last_posted()
    all_titles = aggregated_data.get('raw_titles', [])
    recent_fb = get_facebook_recent_posts(limit=30)
    
    # Count how many titles are truly new (not duplicate)
    new_count = 0
    for t in all_titles:
        if not is_duplicate_title_v19(t, recent_fb, last_posted):
            new_count += 1
    
    decision = {
        "should_post": False,
        "reason": "",
        "is_breaking": breaking_result["is_breaking"],
        "breaking_stories": breaking_result["breaking_stories"],
        "is_routine": is_routine_schedule,
        "new_titles_count": new_count,
        "total_titles": len(all_titles),
        "total_new_after_dedup": breaking_result["total_new"]
    }
    
    if breaking_result["is_breaking"]:
        decision["should_post"] = True
        decision["reason"] = f"BREAKING NEWS ({len(breaking_result['breaking_stories'])} new breaking, {new_count} new total) - immediate post as it happens"
        decision["priority"] = "BREAKING"
    elif is_routine_schedule:
        # ROUTINE HOURLY FOREVER - BUT only if we have new content, otherwise skip to avoid same card repetition
        last_routine_str = last_posted.get('last_routine')
        hours_since = 0
        if last_routine_str:
            try:
                last_routine = datetime.fromisoformat(last_routine_str)
                hours_since = (datetime.now() - last_routine).total_seconds() / 3600
            except:
                hours_since = 5
        
        if new_count == 0 and breaking_result["total_new"] == 0:
            decision["should_post"] = False
            decision["reason"] = f"No new titles after dedup (all {len(all_titles)} already posted) - skipping to avoid same card 4-5 times"
            decision["priority"] = "SKIP_DUPLICATE"
        else:
            decision["should_post"] = True
            decision["reason"] = f"Routine hourly FOREVER - {new_count} new titles after dedup, {hours_since:.1f}h since last, unique card rotation {datetime.now().hour}"
            decision["priority"] = "ROUTINE_FOREVER_UNIQUE_V19"
    else:
        decision["should_post"] = False
        decision["reason"] = "Not routine schedule and no breaking news"
        decision["priority"] = "SKIP"
    
    logger.info(f"Post decision V19: {decision['should_post']} | {decision['reason']} | Priority: {decision.get('priority')} | New: {new_count}/{len(all_titles)}")
    return decision
