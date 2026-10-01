"""
National Reporter - Cleaner V19 - Deletes old duplicate/empty cards permanently
- Fixes "same cards 4-5 times which is very disturbing"
- Deletes empty messages, old templates, duplicates
"""

import os
import requests
import time
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "239472476226069")
SYS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")

def get_page_token():
    token = SYS_TOKEN
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
                        if page['id'] == PAGE_ID:
                            return page['access_token']
    except Exception as e:
        print(f"Token resolve failed: {e}")
    return token

def get_all_posts(limit=100):
    token = get_page_token()
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/posts?limit={limit}&fields=id,message,created_time,story&access_token={token}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get('data', []), token
        else:
            print(f"Failed to get posts: {r.text[:500]}")
            return [], token
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return [], token

def delete_post(post_id, token):
    url = f"https://graph.facebook.com/v20.0/{post_id}?access_token={token}"
    try:
        r = requests.delete(url, timeout=15)
        print(f"Delete {post_id}: {r.status_code} - {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error deleting {post_id}: {e}")
        return False

def clean_old_posts(dry_run=False):
    print("=== CLEANING OLD DUPLICATE/EMPTY CARDS V19 ===")
    posts, token = get_all_posts(limit=100)
    print(f"Found {len(posts)} posts")
    
    # Identify old cards
    old_ids = []
    messages = []
    for p in posts:
        msg = p.get('message','')
        pid = p.get('id','')
        ct = p.get('created_time','')
        messages.append(msg[:100] if msg else "")
    
    # Count duplicates
    cnt = Counter(messages)
    duplicates = {k:v for k,v in cnt.items() if v>1 and k.strip() != ""}
    print(f"Duplicate messages found: {len(duplicates)}")
    for msg, count in list(duplicates.items())[:5]:
        print(f"  Duplicate x{count}: {msg[:80]}")
    
    # Empty count
    empty_count = sum(1 for m in messages if m.strip() == "")
    print(f"Empty messages: {empty_count}")
    
    for p in posts:
        msg = p.get('message','')
        pid = p.get('id','')
        ct = p.get('created_time','')
        
        is_old = False
        reason = ""
        
        # Empty
        if msg.strip() == "":
            is_old = True
            reason = "EMPTY MESSAGE (failed post)"
        # Old template
        elif "تلنگانہ کی سیاست میں بڑی ہلچل" in msg:
            is_old = True
            reason = "OLD CARD TEMPLATE blacklisted"
        elif "حیدرآباد اور تلنگانہ سے تازہ ترین اہم خبر سامنے آئی ہے" in msg and len(msg) < 200:
            # If generic and short, it's old generic fallback
            is_old = True
            reason = "GENERIC FALLBACK not news"
        elif len(msg) < 20 and "📰" in msg:
            is_old = True
            reason = "TOO SHORT / OLD"
        # Duplicate: keep first occurrence, delete rest
        # We'll handle duplicate deletion separately
    
    # For duplicates, keep first, delete rest
    seen_messages = {}
    for p in posts:
        msg = p.get('message','')
        pid = p.get('id','')
        if not msg or msg.strip() == "":
            continue
        key = msg[:100]
        if key in seen_messages:
            # Duplicate
            old_ids.append((pid, f"DUPLICATE x{cnt[key]}", msg[:50], p.get('created_time','')))
        else:
            seen_messages[key] = pid
    
    # Also add empty
    for p in posts:
        msg = p.get('message','')
        pid = p.get('id','')
        if msg.strip() == "":
            old_ids.append((pid, "EMPTY MESSAGE", "", p.get('created_time','')))
    
    print(f"\nFound {len(old_ids)} OLD/DUPLICATE cards to delete:")
    for pid, reason, msg, ct in old_ids[:20]:
        print(f" - {pid} | {reason} | {ct} | {msg[:50]}")
    
    if dry_run:
        print("\nDRY RUN - not deleting")
        return old_ids
    
    if old_ids:
        print(f"\nDeleting {len(old_ids)} old posts...")
        deleted = 0
        for pid, reason, msg, ct in old_ids:
            if delete_post(pid, token):
                deleted += 1
            time.sleep(1.2)  # Avoid rate limit
        print(f"\nDeleted {deleted}/{len(old_ids)} old posts - PERMANENTLY")
    else:
        print("No old posts found to delete")
    
    return old_ids

if __name__ == "__main__":
    import sys
    dry = "--dry" in sys.argv
    clean_old_posts(dry_run=dry)
