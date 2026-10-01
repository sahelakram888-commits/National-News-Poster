"""
Breaking Detector V23 FINAL - Permanent fix Tabassum Begum 5x + TSA Swimmers
- Extended permanent blacklist: Woman Married OYO + Tabassum Begum Ball Badminton + TSA Swimmers overused
- Hourly rotation + today dedup saves ALL bullet titles
"""
import json, logging, hashlib, os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from config import BREAKING_NEWS, OUTPUT_DIR, FACEBOOK_PAGE_ID

logger = logging.getLogger(__name__)
BREAKING_KEYWORDS = BREAKING_NEWS["keywords"]
LAST_POSTED_FILE = OUTPUT_DIR / "last_posted.json"
TODAY_POSTED_FILE = OUTPUT_DIR / "posted_today.json"

# V23 PERMANENT BLACKLIST - Fixes Tabassum 5x + 32 cards same news + TSA overuse
PERMANENT_BLACKLIST = [
    "Woman Who Married Lover in Temple Found Murdered at Hyderabad OYO",
    "woman who married lover in temple found murdered at hyderabad oyo",
    "mandir me premi se shaadi",
    "مندر میں پریمی سے شادی",
    "Nizamabad’s Tabassum Begum Shines at Senior National Ball Badminton Championship",
    "Nizamabad's Tabassum Begum Shines at Senior National Ball Badminton Championship",
    "tabassum begum shines at senior national ball badminton championship",
    "تبسم بیگم نے سینئر نیشنل بال بیڈمنٹن",
    "Tabassum Begum",
    "TSA Felicitates 15 Telangana Swimmers for National Masters Championship Participation",
    "tsa felicitates 15 telangana swimmers",
    "تلنگانہ کی سیاست میں بڑی ہلچل",
    "حیدرآباد اور تلنگانہ سے تازہ ترین اہم خبر سامنے آئی ہے",
]

def is_permanently_blacklisted(title: str) -> bool:
    if not title:
        return False
    lower = title.lower().strip()
    for black in PERMANENT_BLACKLIST:
        if black.lower() in lower or lower in black.lower():
            return True
    if "married lover in temple" in lower and "hyderabad oyo" in lower:
        return True
    if "tabassum begum" in lower and "ball badminton" in lower:
        return True
    if "tsa felicitates" in lower and "telangana swimmers" in lower:
        return True
    if "پریمی سے شادی" in title:
        return True
    if "تبسم بیگم" in title:
        return True
    return False

def load_last_posted() -> Dict:
    try:
        if LAST_POSTED_FILE.exists():
            with open(LAST_POSTED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"titles": [], "hashes": []}

def load_today_posted() -> Dict:
    try:
        if TODAY_POSTED_FILE.exists():
            with open(TODAY_POSTED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('date') == datetime.now().strftime("%Y-%m-%d"):
                    return data
    except:
        pass
    return {"date": datetime.now().strftime("%Y-%m-%d"), "titles": [], "headlines": []}

def save_last_posted(titles: List[str], is_breaking: bool = False):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        data = load_last_posted()
        titles_str = "".join(sorted([t for t in titles[:5] if t][:3])).lower()
        titles_hash = hashlib.md5(titles_str.encode()).hexdigest()
        unique_titles = []
        seen = set()
        for t in titles + data.get("titles", []):
            if not t:
                continue
            if is_permanently_blacklisted(t):
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
    except Exception as e:
        logger.warning(f"Could not save last posted: {e}")

def get_facebook_recent_posts(limit: int = 30) -> List[str]:
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
            return [p.get('message','')[:200].lower() for p in data.get('data', []) if p.get('message')]
    except:
        pass
    return []

def is_duplicate_title_v23(title: str, recent_fb_posts: List[str] = None, last_posted_data: Dict = None, today_posted: Dict = None) -> bool:
    if today_posted is None:
        today_posted = load_today_posted()
    if last_posted_data is None:
        last_posted_data = load_last_posted()
    if recent_fb_posts is None:
        recent_fb_posts = []
    
    if is_permanently_blacklisted(title):
        return True
    
    lower_title = title.lower().strip()
    # Check today posted - exact match only for today (less aggressive)
    for posted in today_posted.get('titles', [])[-100:]:
        if lower_title == posted.lower().strip():
            return True
        # Only check prefix if very similar and long (40 chars not 25) to allow fresh news
        if len(lower_title) > 40 and len(posted) > 40 and lower_title[:40] == posted.lower().strip()[:40]:
            return True
    
    # Check last posted - more lenient, only exact or high overlap 85% (not 70%)
    for posted_title in last_posted_data.get('titles', [])[:20]:  # Only last 20, not 30, to allow fresh
        if not posted_title:
            continue
        pt_lower = posted_title.lower().strip()
        if lower_title == pt_lower:
            return True
        if len(lower_title) > 40 and len(pt_lower) > 40 and lower_title[:40] == pt_lower[:40]:
            return True
        words1 = set(lower_title.split())
        words2 = set(pt_lower.split())
        if len(words1) > 4 and len(words2) > 4:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > 0.85:  # Increased from 0.7 to 0.85 to allow fresh news
                return True
    
    # Check FB recent - only exact substring 30 chars (not 20) to allow fresh
    for fb_msg in recent_fb_posts[:20]:  # Only 20, not 30
        if len(lower_title) > 30 and lower_title[:30] in fb_msg:
            return True
    
    return False

def calculate_breaking_score(title: str, source: str = "") -> int:
    if is_permanently_blacklisted(title):
        return -100
    score = 0
    lower = title.lower()
    breaking_matches = sum(1 for kw in BREAKING_KEYWORDS if kw in lower)
    score += min(breaking_matches * 2, 6)
    important_persons = ['cm', 'pm', 'minister', 'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'governor', 'high court', 'supreme court', 'mayor', 'mla', 'mp', 'eci']
    if any(p in lower for p in important_persons):
        score += 2
    action_words = ['resigns', 'arrested', 'wins', 'loses', 'announces', 'declares', 'dies', 'accident', 'blast', 'firing', 'protest', 'result', 'withdraws', 'attacks', 'seeks', 'demands', 'detained', 'seized', 'slams', 'heats up', 'disrupts']
    if any(a in lower for a in action_words):
        score += 2
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
    today_posted = load_today_posted()
    recent_fb_posts = get_facebook_recent_posts(limit=30)
    
    scored_stories = []
    for title in all_titles:
        if is_permanently_blacklisted(title):
            continue
        if is_duplicate_title_v23(title, recent_fb_posts, last_posted, today_posted):
            continue
        score = calculate_breaking_score(title)
        if score < -50:
            continue
        scored_stories.append({
            "title": title,
            "score": score,
            "is_breaking": is_breaking_news(title, score),
            "is_new": True
        })
    scored_stories.sort(key=lambda x: x['score'], reverse=True)
    breaking_stories = [s for s in scored_stories if s['is_breaking']]
    
    logger.info(f"Breaking detection V23: {len(breaking_stories)} breaking, {len(scored_stories)} new (deduped, blacklist), threshold {BREAKING_NEWS['importance_threshold']}")
    
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
    today_posted = load_today_posted()
    all_titles = aggregated_data.get('raw_titles', [])
    recent_fb = get_facebook_recent_posts(limit=30)
    
    new_count = 0
    for t in all_titles:
        if not is_permanently_blacklisted(t) and not is_duplicate_title_v23(t, recent_fb, last_posted, today_posted):
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
        decision["reason"] = f"BREAKING NEWS ({len(breaking_result['breaking_stories'])} new breaking, {new_count} new total) - immediate"
        decision["priority"] = "BREAKING"
    elif is_routine_schedule:
        if new_count == 0 and breaking_result["total_new"] == 0:
            decision["should_post"] = False
            decision["reason"] = f"No new titles after dedup+blacklist V23 (all {len(all_titles)} already posted or blacklisted) - skipping to avoid Tabassum 5x"
            decision["priority"] = "SKIP_DUPLICATE_BLACKLIST_V23"
        else:
            decision["should_post"] = True
            decision["reason"] = f"Routine hourly V23 - {new_count} new titles after dedup+blacklist, today {len(today_posted.get('titles',[]))} posted"
            decision["priority"] = "ROUTINE_V23_PERMANENT_FIX"
    else:
        decision["should_post"] = False
        decision["reason"] = "Not routine and no breaking"
        decision["priority"] = "SKIP"
    
    logger.info(f"Post decision V23: {decision['should_post']} | {decision['reason']} | Priority: {decision.get('priority')}")
    return decision
