"""
National Reporter - Delete Old Cards - FIXED RACE CONDITION
- Deletes old duplicate empty posts and old card 'تلنگانہ کی سیاست میں بڑی ہلچل'
- FIX: Does NOT delete recent posts (created within last 24h) to avoid race where fresh posts have empty message temporarily
- Only deletes posts older than 1 day OR with ID < 1620000000000000 (old)
"""
import os
import requests
import time
from datetime import datetime, timedelta, timezone

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "239472476226069")
TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")

def get_all_posts(limit=100):
    url = f"https://graph.facebook.com/v20.0/{FACEBOOK_PAGE_ID}/posts?limit={limit}&fields=id,message,created_time&access_token={TOKEN}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get('data', [])
        else:
            print(f"Failed to get posts: {r.text[:500]}")
            return []
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

def delete_post(post_id):
    url = f"https://graph.facebook.com/v20.0/{post_id}?access_token={TOKEN}"
    try:
        r = requests.delete(url, timeout=15)
        print(f"Delete {post_id}: {r.status_code} - {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error deleting {post_id}: {e}")
        return False

def is_recent_post(created_time_str, hours=24):
    """Check if post is recent (within last N hours) - don't delete recent to avoid race"""
    try:
        # Parse ISO time like 2026-10-01T12:10:38+0000
        dt = datetime.fromisoformat(created_time_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now - dt
        return age < timedelta(hours=hours)
    except Exception as e:
        print(f"Failed to parse time {created_time_str}: {e}")
        # If can't parse, assume recent to be safe
        return True

def clean_old_posts():
    print("=== CLEANING OLD DUPLICATE CARDS - FIXED RACE CONDITION ===")
    print("Will NOT delete recent posts (within 24h) to avoid deleting fresh posts with temporary empty message")
    posts = get_all_posts(limit=100)
    print(f"Found {len(posts)} posts")
    
    old_ids = []
    skipped_recent = 0
    for p in posts:
        msg = p.get('message','') or ""
        pid = p.get('id','')
        ct = p.get('created_time','')
        
        # FIX: Skip recent posts to avoid race condition
        if is_recent_post(ct, hours=24):
            if msg.strip() == "":
                print(f"SKIP RECENT EMPTY (race protection): {pid} | {ct} | Age <24h - NOT deleting, will have message soon")
                skipped_recent += 1
            continue
        
        # Also skip if post ID is recent (greater than 1620000000000000 is recent Oct 2026)
        # Old posts have ID < 1620000000000000
        try:
            # Extract numeric ID part after _
            numeric_id = pid.split('_')[-1] if '_' in pid else pid
            if numeric_id.isdigit() and int(numeric_id) > 1629000000000000:
                # Recent post (Oct 1 2026 IDs are ~16291...), skip
                if msg.strip() == "":
                    print(f"SKIP RECENT ID (race protection): {pid} | {ct} | ID {numeric_id} > 1629e12 - NOT deleting")
                    skipped_recent += 1
                continue
        except:
            pass
        
        # Identify old cards: empty messages or old 'تلنگانہ کی سیاست میں بڑی ہلچل' - ONLY OLD
        is_old = False
        reason = ""
        if msg.strip() == "":
            is_old = True
            reason = "EMPTY MESSAGE OLD (duplicate failure) - OLDER THAN 24H"
        elif "تلنگانہ کی سیاست میں بڑی ہلچل" in msg:
            is_old = True
            reason = "OLD CARD TEMPLATE"
        elif len(msg) < 10 and "📰" in msg and not is_recent_post(ct, hours=24):
            is_old = True
            reason = "TOO SHORT / OLD"
        elif "Tabassum Begum" in msg and "Ball Badminton" in msg:
            is_old = True
            reason = "TABASSUM BEGUM 5x BUG - BLACKLISTED"
        elif "TSA Felicitates" in msg and "Swimmers" in msg:
            is_old = True
            reason = "TSA SWIMMERS OVERUSE - BLACKLISTED"
        
        if is_old:
            old_ids.append((pid, reason, msg[:50], ct))
    
    print(f"\nFound {len(old_ids)} OLD cards to delete (older than 24h):")
    for pid, reason, msg, ct in old_ids:
        print(f" - {pid} | {reason} | {ct} | {msg}")
    print(f"Skipped {skipped_recent} recent empty posts (race protection)")
    
    if old_ids:
        print(f"\nDeleting {len(old_ids)} old posts...")
        deleted = 0
        for pid, reason, msg, ct in old_ids:
            if delete_post(pid):
                deleted += 1
            time.sleep(1)
        print(f"\nDeleted {deleted}/{len(old_ids)} old posts")
    else:
        print("No old posts found to delete (all recent protected)")
    
    return old_ids

if __name__ == "__main__":
    clean_old_posts()
