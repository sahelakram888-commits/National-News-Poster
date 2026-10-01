"""
National Reporter - Main AI Agent V17 Final - SET AND FORGET, NEVER STOPS
- Hourly posting, Latest News (not Breaking unless actual breaking)
- No old cards, no fake news, no mistakes
- Politics first, then regional (Hyderabad/Telangana), then national, then world
- Wide coverage: Munsif, Etemaad, India Today, Indian Express, NDTV
- Auto-delete old card if posted
- Never expiring token, set once for all
"""
import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SCHEDULE_INTERVAL_HOURS, BREAKING_CHECK_MINUTES, OUTPUT_DIR, BRAND, CONTENT_PREFS, BREAKING_NEWS
# V17 Final - SET AND FORGET, NEVER STOPS, Hourly, Latest News, Important First, No Old Cards
try:
    from morning_fresh_scraper import aggregate_fresh_morning as aggregate_news
    from final_processor import process_fresh_news as process_news, process_breaking_news
    print("Using V17 FINAL: SET AND FORGET, Hourly, Latest News, Important First, No Old Cards, Never Stops")
except ImportError:
    try:
        from morning_fresh_scraper import aggregate_fresh_morning as aggregate_news
        from important_first_processor import process_fresh_news as process_news
        print("Using V15 IMPORTANT FIRST: Politics > Regional > National > World, Hourly, 55 fresh")
    except ImportError:
        from scraper import aggregate_news
        from processor import process_news
        print("Fallback to old scraper")

from image_generator import generate_news_card
from facebook_publisher import publish_to_facebook
from breaking_detector import detect_breaking_news, should_post_now, save_last_posted

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / "agent.log") if OUTPUT_DIR.exists() else logging.StreamHandler()
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
    mode = "ROUTINE HOURLY (1h) - Latest News" if is_routine else f"BREAKING CHECK (15min) - As it happens"
    logger.info(f"Starting National Reporter V17 Final at {datetime.now()} | Mode: {mode} | SET AND FORGET, NEVER STOPS")
    logger.info(f"{greeting}! Important First: Politics > Regional > National > World | Latest News | No Old Cards | No Fake | Never Expiring Token")
    logger.info("="*70)

    result = {
        "started_at": datetime.now().isoformat(),
        "is_morning": is_morning,
        "mode": mode,
        "is_routine": is_routine,
        "steps": {}
    }

    try:
        # Step 1: Scrape - V17 Final - Wide coverage
        logger.info("Step 1/4: Scraping V17 Final - Munsif + Etemaad + India Today + Indian Express + NDTV (Wide coverage, Politics first, Regional then National World)")
        aggregated = aggregate_news()
        result["steps"]["scraping"] = {
            "status": "success",
            "total": aggregated.get('total_count', 0),
            "politics": aggregated.get('politics_count', 0),
            "is_morning": aggregated.get('is_morning'),
            "hour": aggregated.get('hour'),
            "sources": aggregated.get('sources_used', {})
        }
        logger.info(f"✓ Scraped V17 Final {aggregated.get('total_count')} verified | Politics: {aggregated.get('politics_count')} | Sources: {aggregated.get('sources_used', {})} | Important First")

        if aggregated.get('total_count', 0) == 0:
            logger.warning("No verified stories, skipping to avoid fake news")
            return {"status": "no_news", "message": "No verified news", "finished_at": datetime.now().isoformat()}

        # Step 1.5: Breaking News Detection - V17 Final
        logger.info(f"Step 1.5/4: Breaking Detection V17 Final (Threshold {BREAKING_NEWS['importance_threshold']}) - Breaking as it happens or hourly")
        breaking_info = detect_breaking_news(aggregated)
        decision = should_post_now(aggregated, is_routine_schedule=is_routine)
        
        result["steps"]["breaking_detection"] = {
            "is_breaking": breaking_info["is_breaking"],
            "breaking_count": len(breaking_info["breaking_stories"]),
            "should_post": decision["should_post"],
            "reason": decision["reason"],
            "priority": decision.get("priority")
        }
        
        logger.info(f"Breaking check V17: {breaking_info['is_breaking']} | Breaking: {len(breaking_info['breaking_stories'])} | Decision: {decision['should_post']} | Reason: {decision['reason']}")

        if not decision["should_post"] and not force_post:
            logger.info(f"⏭️ Skipping post - {decision['reason']}")
            result["status"] = "skipped"
            result["reason"] = decision["reason"]
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Step 2: AI Processing - V17 Final - SET AND FORGET, Latest News not Breaking unless actual breaking
        logger.info(f"Step 2/4: AI Processing V17 Final - SET AND FORGET, Latest News, Important First: Politics > Regional > National > World, No Old Cards, No Fake")
        try:
            from final_processor import process_breaking_news as process_breaking
            if decision.get("priority") == "BREAKING":
                processed = process_breaking(aggregated)
                logger.info(f"BREAKING NEWS as it happens - {processed.get('headline')}")
            else:
                processed = process_news(aggregated)
                # Ensure category says Latest News for routine hourly (not Breaking) as user requested
                if "BREAKING" in processed.get('category','').upper() and not decision["is_breaking"]:
                    cat = processed.get('category','').replace('BREAKING','Latest News').replace('BREAKING -','').strip()
                    if not cat or cat.lower() == "breaking":
                        cat = "Latest News"
                    processed['category'] = cat
        except ImportError:
            processed = process_news(aggregated)
            if decision.get("priority") == "BREAKING":
                if "BREAKING" not in processed.get('category',''):
                    processed['category'] = f\"BREAKING - {processed.get('category','Politics')}\"
            else:
                if "BREAKING" in processed.get('category',''):
                    processed['category'] = processed.get('category','').replace('BREAKING','Latest News').replace(' - ',' ').strip()
                    if not processed['category']:
                        processed['category'] = "Latest News"
        
        result["steps"]["processing"] = {
            "status": "success",
            "headline": processed.get('headline'),
            "category": processed.get('category'),
            "bullets_count": len(processed.get('urdu_bullets', [])),
            "verified": processed.get('verified', True),
            "is_breaking": decision["is_breaking"],
            "is_latest_news": not decision["is_breaking"],
            "important_first": True
        }
        logger.info(f"✓ Processed V17 Final: {processed.get('headline')} | Cat: {processed.get('category')} | Bullets: {len(processed.get('urdu_bullets', []))} | Breaking: {decision['is_breaking']} | Latest News: {not decision['is_breaking']} | Important First")

        # Step 3: Image Generation - V17 Final
        logger.info("Step 3/4: Image Generation V17 Final (1080x1080 - Large Fonts: Urdu 36px, Roman 28px Bold White, Latest News, No Old Cards)")
        image_path = generate_news_card(processed)
        result["steps"]["image_generation"] = {
            "status": "success",
            "path": image_path,
            "font_sizes": "Headline 58px, Urdu 36px, Roman 28px Bold White",
            "latest_news": not decision["is_breaking"]
        }
        logger.info(f"✓ Image generated V17 Final: {image_path} | Latest News: {not decision['is_breaking']}")

        # Step 4: Facebook Publishing - V17 Final - SET AND FORGET, NEVER STOPS, Auto-delete old cards
        logger.info(f"Step 4/4: Publishing V17 Final to Facebook Page {os.getenv('FACEBOOK_PAGE_ID', '239472476226069')} | Priority: {decision.get('priority')} | Latest News: {not decision['is_breaking']} | Never Stops | Never Expiring Token")
        publish_result = publish_to_facebook(image_path, processed)
        result["steps"]["publishing"] = publish_result

        if publish_result.get('success'):
            post_id = publish_result.get('post_id')
            logger.info(f"✓ Published V17 Final to Facebook: {post_id} | Priority: {decision.get('priority')} | Latest News: {not decision['is_breaking']} | SET AND FORGET, NEVER STOPS")
            
            # V17: Auto-delete old card if posted (if causing problem) - blacklisted check
            headline = processed.get('headline','')
            blacklisted_old = ["تلنگانہ کی سیاست میں بڑی ہلچل", "حیدرآباد میں سیاسی جماعتوں کے درمیان اہم ملاقاتیں", "تلنگانہ اسمبلی میں اپوزیشن نے حکومت کے خلاف تحریک", "وزیر اعلیٰ نے عوامی مسائل کے حل کے لیے نئے اقدامات"]
            is_old_card = any(old in headline for old in blacklisted_old)
            
            if is_old_card:
                logger.warning(f"⚠️ OLD CARD DETECTED AFTER POSTING - Auto-deleting immediately: {headline[:50]} - SET AND FORGET FIX")
                try:
                    import requests
                    token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
                    delete_url = f"https://graph.facebook.com/v20.0/{post_id}?access_token={token}"
                    del_resp = requests.delete(delete_url, timeout=10)
                    if del_resp.status_code == 200:
                        logger.info(f"✅ Auto-deleted old card immediately: {post_id} - No old cards again")
                        result["steps"]["publishing"]["auto_deleted_old"] = True
                    else:
                        logger.warning(f"Failed to auto-delete old card: {del_resp.text[:200]}")
                except Exception as e:
                    logger.warning(f"Exception auto-deleting old card: {e}")
            else:
                # Save posted titles to avoid duplicates - no old cards, no fake
                save_last_posted([processed.get('headline_source','')] + aggregated.get('raw_titles', [])[:3], is_breaking=decision["is_breaking"])
                logger.info(f"Saved fresh headline to avoid old card repetition: {processed.get('headline_source','')[:50]} | SET AND FORGET")
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
        logger.info(f"Cycle completed V17 Final! {greeting} | {decision.get('priority')} | Latest News: {not decision['is_breaking']} | Important First: Politics > Regional > National > World | No Old Cards | No Fake | Never Expiring Token | SET AND FORGET, NEVER STOPS")
        logger.info("="*70)
        return result

    except Exception as e:
        logger.exception(f"Cycle failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["finished_at"] = datetime.now().isoformat()
        return result

def run_scheduler():
    logger.info(f"Starting National Reporter V17 Final Scheduler - SET AND FORGET, NEVER STOPS")
    logger.info(f"Brand: {BRAND['name']} | Page: https://www.facebook.com/239472476226069 (502K)")
    logger.info(f"Routine: Every 1 hour (hourly) | Breaking Check: Every 15 minutes | Important First: Politics > Regional > National > World")
    logger.info(f"Features: Latest News (not Breaking unless actual breaking), No Old Cards, No Fake, Auto-delete old, Never Expiring Token, Wide Coverage")
    
    run_once(is_routine=True)

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(lambda: run_once(is_routine=True), 'interval', hours=1, id='routine_hourly')
        scheduler.add_job(lambda: run_once(is_routine=False), 'interval', minutes=15, id='breaking_check')
        logger.info(f"Scheduler started V17 Final:")
        logger.info(f"  - Routine: every 1h (hourly) - Latest News, Important First")
        logger.info(f"  - Breaking check: every 15min - immediate as it happens")
        logger.info(f"  - SET AND FORGET, NEVER STOPS until we did")
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
    parser = argparse.ArgumentParser(description="National Reporter V17 Final - SET AND FORGET, NEVER STOPS")
    parser.add_argument('--once', action='store_true', help='Run once (hourly routine)')
    parser.add_argument('--breaking-check', action='store_true', help='Run breaking news check (15 min)')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler: hourly + breaking 15min, never stops')
    parser.add_argument('--test-image', action='store_true', help='Test image generation - Latest News, No Old Cards')
    parser.add_argument('--force', action='store_true', help='Force post even if duplicate')
    args = parser.parse_args()

    if args.test_image:
        from image_generator import NewsCardV3
        # V17 Final - SET AND FORGET, Latest News, No Old Cards, Important First
        try:
            aggregated = aggregate_news()
            if aggregated.get('total_count', 0) > 0:
                test_data = process_news(aggregated)
                print(f"Using V17 Final Latest News: {test_data.get('headline')} | Source: {test_data.get('headline_source','')[:50]} | Rot: {test_data.get('rotation_index')} | Cat: {test_data.get('category')} | Sources: {test_data.get('sources_used')}")
            else:
                raise ValueError("No news aggregated")
        except Exception as e:
            print(f"Scrape failed {e}, using V17 Final fallback - Latest News, Important First, No Old Cards")
            test_data = {
                "headline": "کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے",
                "headline_roman": "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai",
                "urdu_bullets": [
                    "کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے",
                    "حیدرآباد میں کیب ڈرائیور کی خاتون سے بدتمیزی کی کوشش، پولیس نے مقدمہ درج کیا",
                    "تلنگانہ ہائی کورٹ نے بی آر ایس خاتون ایم ایل ایز کیس میں ڈی جی پی کو ہدایات دی ہیں",
                    "بڈگام انکاؤنٹر میں لشکر کمانڈر موسیٰ ہلاک، سابق پاک کمانڈو بھی مارا گیا",
                    "مندر میں پریمی سے شادی کرنے والی خاتون کا حیدرآباد او وائی او میں قتل پایا گیا"
                ],
                "roman_urdu_bullets": [
                    "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai",
                    "Hyderabad mein cab driver ki khatoon se badtameezi ki koshish, police ne muqadma darj kiya",
                    "Telangana High Court ne BRS khatoon MLAs case mein DGP ko hidayat di hain",
                    "Budgam encounter mein Lashkar commander Musa halaak, sabiq Pak commando bhi mara gaya",
                    "Mandir mein premi se shadi karne wali khatoon ka Hyderabad OYO mein qatal paya gaya"
                ],
                "category": "Latest News",
                "date_str": datetime.now().strftime("%d %B %Y"),
                "time_str": datetime.now().strftime("%I:%M %p"),
                "rotation_index": datetime.now().hour
            }
        gen = NewsCardV3()
        path = gen.generate(test_data)
        print(f"Test image V17 Final (Latest News, No Old Cards, Important First, Rot {test_data.get('rotation_index')}): {path}")
    elif args.breaking_check:
        result = run_once(is_routine=False, force_post=args.force)
        print(f"Breaking check V17 Final: {result.get('status')} | {result.get('decision', {}).get('reason')}")
    elif args.schedule:
        run_scheduler()
    else:
        result = run_once(is_routine=True, force_post=args.force)
        print(f"\nResult V17 Final: {result.get('status')} | Priority: {result.get('decision', {}).get('priority')} | Category: {result.get('processed_data', {}).get('category')} | Reason: {result.get('decision', {}).get('reason')}")
        if result.get('image_path'):
            print(f"Image: {result['image_path']} | Latest News: {not result.get('decision', {}).get('is_breaking', False)}")
