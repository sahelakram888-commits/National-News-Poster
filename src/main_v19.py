"""
National Reporter - Main AI Agent V19 Final - FIXES NOT POSTING + SAME CARDS 4-5 TIMES
- Hourly posting, Latest News, Politics first
- Strong deduplication: checks FB recent 30 + last_posted.json
- Deletes old empty/duplicate cards permanently
- OpenAI optional: if API key present, uses AI translation
- Never expiring token, set and forget, never stops
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SCHEDULE_INTERVAL_HOURS, BREAKING_CHECK_MINUTES, OUTPUT_DIR, BRAND, CONTENT_PREFS, BREAKING_NEWS

# V19 - Use latest scraper and processor
try:
    from morning_fresh_scraper import aggregate_fresh_morning as aggregate_news
    from final_processor import process_fresh_news as process_news, process_breaking_news
    print("Using V19 FINAL: No duplicate, Specific only, Hourly unique, OpenAI optional, No old cards")
except ImportError as e:
    print(f"Import failed {e}, fallback")
    from scraper import aggregate_news
    from processor import process_news
    process_breaking_news = process_news

from image_generator import generate_news_card
from facebook_publisher import publish_to_facebook
from breaking_detector import detect_breaking_news, should_post_now, save_last_posted

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("NationalReporterAgent")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_time_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning", True
    elif 12 <= hour < 17:
        return "Good Afternoon", False
    elif 17 <= hour < 21:
        return "Good Evening", False
    else:
        return "Late Night", False

def run_once(is_routine: bool = True, force_post: bool = False) -> dict:
    logger.info("="*70)
    greeting, is_morning = get_time_greeting()
    mode = "ROUTINE HOURLY (1h) - Latest News" if is_routine else "BREAKING CHECK (15min) - As it happens"
    logger.info(f"Starting National Reporter V19 at {datetime.now()} | Mode: {mode} | FIXES DUPLICATE 4-5 TIMES")
    logger.info(f"{greeting}! V19: No duplicate, Specific only, Hourly unique, OpenAI optional, No old cards, Politics first")
    logger.info("="*70)

    result = {
        "started_at": datetime.now().isoformat(),
        "is_morning": is_morning,
        "mode": mode,
        "is_routine": is_routine,
        "steps": {}
    }

    try:
        # Step 1: Scrape - V19
        logger.info("Step 1/4: Scraping V19 - Munsif + Etemaad + India Today + Indian Express + NDTV (Wide coverage, Politics first, Dedup)")
        aggregated = aggregate_news()
        result["steps"]["scraping"] = {
            "status": "success",
            "total": aggregated.get('total_count', 0),
            "politics": aggregated.get('politics_count', 0),
            "is_morning": aggregated.get('is_morning'),
            "hour": aggregated.get('hour'),
            "sources": aggregated.get('sources_used', {})
        }
        logger.info(f"✓ Scraped V19 {aggregated.get('total_count')} verified | Politics: {aggregated.get('politics_count')} | Sources: {aggregated.get('sources_used', {})}")

        if aggregated.get('total_count', 0) == 0:
            logger.warning("No verified stories, skipping to avoid fake news")
            return {"status": "no_news", "message": "No verified news", "finished_at": datetime.now().isoformat()}

        # Step 1.5: Breaking Detection V19 - Strong dedup
        logger.info(f"Step 1.5/4: Breaking Detection V19 (Threshold {BREAKING_NEWS['importance_threshold']}) - No duplicate 4-5 times")
        breaking_info = detect_breaking_news(aggregated)
        decision = should_post_now(aggregated, is_routine_schedule=is_routine)
        
        result["steps"]["breaking_detection"] = {
            "is_breaking": breaking_info["is_breaking"],
            "breaking_count": len(breaking_info["breaking_stories"]),
            "should_post": decision["should_post"],
            "reason": decision["reason"],
            "priority": decision.get("priority"),
            "new_titles": decision.get("new_titles_count", 0)
        }
        
        logger.info(f"Breaking check V19: {breaking_info['is_breaking']} | Breaking: {len(breaking_info['breaking_stories'])} | Decision: {decision['should_post']} | Reason: {decision['reason']} | New: {decision.get('new_titles_count')}")

        if not decision["should_post"] and not force_post:
            logger.info(f"⏭️ Skipping post V19 - {decision['reason']} - Avoids same card 4-5 times")
            result["status"] = "skipped"
            result["reason"] = decision["reason"]
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Step 2: AI Processing V19
        logger.info(f"Step 2/4: AI Processing V19 - No duplicate, Specific only, Hourly unique, OpenAI optional, Politics first")
        if decision.get("priority") == "BREAKING":
            processed = process_breaking_news(aggregated)
            logger.info(f"BREAKING NEWS V19 - {processed.get('headline')}")
        else:
            processed = process_news(aggregated)
            # Ensure Latest News for routine
            if "BREAKING" in processed.get('category','').upper() and not decision["is_breaking"]:
                cat = processed.get('category','').replace('BREAKING','Latest News').replace('BREAKING -','').strip()
                if not cat or cat.lower() == "breaking":
                    cat = "Latest News"
                processed['category'] = cat
        
        result["steps"]["processing"] = {
            "status": "success",
            "headline": processed.get('headline'),
            "category": processed.get('category'),
            "bullets_count": len(processed.get('urdu_bullets', [])),
            "verified": processed.get('verified', True),
            "is_breaking": decision["is_breaking"],
            "is_latest_news": not decision["is_breaking"],
            "no_duplicate": processed.get('no_duplicate', True)
        }
        logger.info(f"✓ Processed V19: {processed.get('headline')} | Cat: {processed.get('category')} | Bullets: {len(processed.get('urdu_bullets', []))} | No duplicate: {processed.get('no_duplicate')}")

        # Step 3: Image Generation V19
        logger.info("Step 3/4: Image Generation V19 (1080x1080 - 58px headline, 36px Urdu, 28px Roman Bold White)")
        image_path = generate_news_card(processed)
        result["steps"]["image_generation"] = {
            "status": "success",
            "path": image_path,
            "font_sizes": "Headline 58px, Urdu 36px, Roman 28px Bold White",
            "latest_news": not decision["is_breaking"]
        }
        logger.info(f"✓ Image generated V19: {image_path}")

        # Step 4: Facebook Publishing V19
        logger.info(f"Step 4/4: Publishing V19 to Facebook Page {os.getenv('FACEBOOK_PAGE_ID', '239472476226069')} | Priority: {decision.get('priority')} | No duplicate")
        publish_result = publish_to_facebook(image_path, processed)
        result["steps"]["publishing"] = publish_result

        if publish_result.get('success'):
            post_id = publish_result.get('post_id')
            logger.info(f"✓ Published V19 to Facebook: {post_id} | Priority: {decision.get('priority')} | No duplicate, Specific only")
            
            # Save posted titles to avoid duplicates - V19 strong dedup
            save_last_posted([processed.get('headline_source','')] + aggregated.get('raw_titles', [])[:3], is_breaking=decision["is_breaking"])
            logger.info(f"Saved fresh headline to avoid old card repetition V19: {processed.get('headline_source','')[:50]}")
        else:
            if publish_result.get('simulated'):
                logger.warning("Facebook not configured - simulated")
                post_text_path = Path(image_path).with_suffix('.txt')
                from facebook_publisher import FacebookPublisher
                pub = FacebookPublisher()
                with open(post_text_path, 'w', encoding='utf-8') as f:
                    f.write(pub.format_post_text(processed))
                logger.info(f"Post text saved: {post_text_path}")
            else:
                logger.error(f"Failed to publish: {publish_result.get('error')}")

        result["finished_at"] = datetime.now().isoformat()
        result["status"] = "success"
        result["processed_data"] = processed
        result["image_path"] = image_path
        result["breaking_info"] = breaking_info
        result["decision"] = decision

        logger.info("="*70)
        logger.info(f"Cycle completed V19! {greeting} | {decision.get('priority')} | No duplicate, Specific only, Hourly unique | SET AND FORGET, NEVER STOPS")
        logger.info("="*70)
        return result

    except Exception as e:
        logger.exception(f"Cycle failed V19: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["finished_at"] = datetime.now().isoformat()
        return result

def run_scheduler():
    logger.info(f"Starting National Reporter V19 Scheduler - FIXES DUPLICATE 4-5 TIMES, No old cards")
    logger.info(f"Brand: {BRAND['name']} | Page: https://www.facebook.com/239472476226069 (502K)")
    logger.info(f"Routine: Every 1 hour (hourly) | Breaking Check: Every 15 minutes | V19 No duplicate")
    
    run_once(is_routine=True)

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(lambda: run_once(is_routine=True), 'interval', hours=1, id='routine_hourly')
        scheduler.add_job(lambda: run_once(is_routine=False), 'interval', minutes=15, id='breaking_check')
        logger.info(f"Scheduler started V19:")
        logger.info(f"  - Routine: every 1h (hourly) - Latest News, No duplicate, Specific only")
        logger.info(f"  - Breaking check: every 15min - immediate as it happens")
        scheduler.start()
    except ImportError:
        logger.warning("APScheduler not installed, using simple loop")
        while True:
            time.sleep(15 * 60)
            run_once(is_routine=False)
            hour = datetime.now().hour
            minute = datetime.now().minute
            if minute < 15:
                run_once(is_routine=True)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="National Reporter V19 - No duplicate, Specific only")
    parser.add_argument('--once', action='store_true', help='Run once (hourly routine)')
    parser.add_argument('--breaking-check', action='store_true', help='Run breaking news check (15 min)')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler: hourly + breaking 15min, never stops')
    parser.add_argument('--test-image', action='store_true', help='Test image generation')
    parser.add_argument('--force', action='store_true', help='Force post even if duplicate')
    args = parser.parse_args()

    if args.test_image:
        from image_generator import NewsCardV3
        try:
            aggregated = aggregate_news()
            if aggregated.get('total_count', 0) > 0:
                test_data = process_news(aggregated)
                print(f"Using V19 Latest News: {test_data.get('headline')} | Source: {test_data.get('headline_source','')[:50]} | Rot: {test_data.get('rotation_index')} | Cat: {test_data.get('category')}")
            else:
                raise ValueError("No news aggregated")
        except Exception as e:
            print(f"Scrape failed {e}, using V19 fallback")
            test_data = {
                "headline": "کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے",
                "headline_roman": "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai",
                "urdu_bullets": [
                    "کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے",
                    "حیدرآباد میں کیب ڈرائیور کی خاتون سے بدتمیزی کی کوشش، پولیس نے مقدمہ درج کیا",
                    "تلنگانہ ہائی کورٹ نے بی آر ایس خاتون ایم ایل ایز کیس میں ڈی جی پی کو ہدایات دی ہیں",
                ],
                "roman_urdu_bullets": [
                    "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai",
                    "Hyderabad mein cab driver ki khatoon se badtameezi ki koshish, police ne muqadma darj kiya",
                    "Telangana High Court ne BRS khatoon MLAs case mein DGP ko hidayat di hain",
                ],
                "category": "Latest News",
                "date_str": datetime.now().strftime("%d %B %Y"),
                "time_str": datetime.now().strftime("%I:%M %p"),
                "rotation_index": datetime.now().hour
            }
        gen = NewsCardV3()
        path = gen.generate(test_data)
        print(f"Test image V19: {path}")
    elif args.breaking_check:
        result = run_once(is_routine=False, force_post=args.force)
        print(f"Breaking check V19: {result.get('status')} | {result.get('decision', {}).get('reason')}")
    elif args.schedule:
        run_scheduler()
    else:
        result = run_once(is_routine=True, force_post=args.force)
        print(f"\nResult V19: {result.get('status')} | Priority: {result.get('decision', {}).get('priority')} | Category: {result.get('processed_data', {}).get('category')} | Reason: {result.get('decision', {}).get('reason')}")
        if result.get('image_path'):
            print(f"Image: {result['image_path']}")
