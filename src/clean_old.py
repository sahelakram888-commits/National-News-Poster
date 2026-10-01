"""
National Reporter - Delete Old Cards + Post Fresh Morning News
- Deletes old duplicate empty posts and old card 'تلنگانہ کی سیاست میں بڑی ہلچل'
- Fetches fresh morning news from India Today + Indian Express + Munsif + Etemaad
- Translates English to Urdu & Roman Urdu
"""
import os
import requests
import time
from datetime import datetime

FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "239472476226069")
TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "EABCx6O5eVE4BSorsXG6VPkjxx8svdqfJsBtXMtsYPP5HADCuP47FnC4mbiDeSmhZBchTuxQ1MZCkfU5XEsyYmqUFoPjqErInM3RutBtoYklXlZCNZB8VOS22r4ivaQzHcA5yRtuovC7HUFNSZBnJKXOa4LzbtnZC7sKHsJKHldlMIGbU76GtbwHb2J8pCvgj5bZBkLjNBND2tpfBumrUosspj0ZAsVMSOGo6KU5RKC0tktXDQEGBSYFDRQZDZD")

def get_all_posts(limit=50):
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

def clean_old_posts():
    print("=== CLEANING OLD DUPLICATE CARDS ===")
    posts = get_all_posts(limit=50)
    print(f"Found {len(posts)} posts")
    
    old_ids = []
    for p in posts:
        msg = p.get('message','')
        pid = p.get('id','')
        ct = p.get('created_time','')
        
        # Identify old cards: empty messages or old 'تلنگانہ کی سیاست میں بڑی ہلچل'
        is_old = False
        reason = ""
        if msg.strip() == "":
            is_old = True
            reason = "EMPTY MESSAGE (duplicate failure)"
        elif "تلنگانہ کی سیاست میں بڑی ہلچل" in msg:
            is_old = True
            reason = "OLD CARD TEMPLATE"
        elif len(msg) < 10 and "📰" in msg:
            is_old = True
            reason = "TOO SHORT / OLD"
        
        if is_old:
            old_ids.append((pid, reason, msg[:50], ct))
    
    print(f"\nFound {len(old_ids)} OLD cards to delete:")
    for pid, reason, msg, ct in old_ids:
        print(f" - {pid} | {reason} | {ct} | {msg}")
    
    if old_ids:
        print(f"\nDeleting {len(old_ids)} old posts...")
        deleted = 0
        for pid, reason, msg, ct in old_ids:
            if delete_post(pid):
                deleted += 1
            time.sleep(1)  # Avoid rate limit
        print(f"\nDeleted {deleted}/{len(old_ids)} old posts")
    else:
        print("No old posts found to delete")
    
    return old_ids

if __name__ == "__main__":
    clean_old_posts()
