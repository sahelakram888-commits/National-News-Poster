"""
National Reporter - Main AI Agent V4
- Large fonts (Urdu 36px, Roman 28px Bold White)
- Politics preferred, Munsif & Etemaad Only
- Breaking News: immediate as it happens + routine every 2h
- Verified only, no fake
- 3-5 bullets
"""
import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SCHEDULE_INTERVAL_HOURS, BREAKING_CHECK_MINUTES, OUTPUT_DIR, BRAND, CONTENT_PREFS, BREAKING_NEWS
from scraper import aggregate_news
from processor import process_news
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
    """
    is_routine: True if called from 2h schedule, False if from breaking check (15 min)
    force_post: Force post even if no new news (for testing)
    """
    logger.info("="*70)
    greeting, is_morning = get_time_greeting()
    mode = "ROUTINE (2h)" if is_routine else f"BREAKING CHECK ({BREAKING_CHECK_MINUTES}min)"
    logger.info(f"Starting National Reporter cycle at {datetime.now()} | Mode: {mode}")
    logger.info(f"{greeting}! Morning: {is_morning} | Politics | Munsif/Etemaad Only | Large Fonts | Breaking Enabled")
    logger.info("="*70)

    result = {
        "started_at": datetime.now().isoformat(),
        "is_morning": is_morning,
        "mode": mode,
        "is_routine": is_routine,
        "steps": {}
    }

    try:
        # Step 1: Scrape
        logger.info("Step 1/4: Scraping Munsif & Etemaad Only (Politics, Verified, No Fake)")
        aggregated = aggregate_news()
        result["steps"]["scraping"] = {
            "status": "success",
            "total": aggregated.get('total_count', 0),
            "politics": aggregated.get('politics_count', 0),
            "is_morning": aggregated.get('is_morning'),
            "hour": aggregated.get('hour'),
        }
        logger.info(f"✓ Scraped {aggregated.get('total_count')} verified | Politics: {aggregated.get('politics_count')} | Morning: {aggregated.get('is_morning')}")

        if aggregated.get('total_count', 0) == 0:
            logger.warning("No verified stories, skipping to avoid fake news")
            return {"status": "no_news", "message": "No verified news", "finished_at": datetime.now().isoformat()}

        # Step 1.5: Breaking News Detection
        logger.info(f"Step 1.5/4: Breaking News Detection (Threshold {BREAKING_NEWS['importance_threshold']}, Keywords {len(BREAKING_NEWS['keywords'])})")
        breaking_info = detect_breaking_news(aggregated)
        decision = should_post_now(aggregated, is_routine_schedule=is_routine)
        
        result["steps"]["breaking_detection"] = {
            "is_breaking": breaking_info["is_breaking"],
            "breaking_count": len(breaking_info["breaking_stories"]),
            "should_post": decision["should_post"],
            "reason": decision["reason"],
            "priority": decision.get("priority")
        }
        
        logger.info(f"Breaking check: {breaking_info['is_breaking']} | Breaking stories: {len(breaking_info['breaking_stories'])} | Decision: {decision['should_post']} | Reason: {decision['reason']}")

        if not decision["should_post"] and not force_post:
            logger.info(f"⏭️ Skipping post - {decision['reason']}")
            result["status"] = "skipped"
            result["reason"] = decision["reason"]
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Step 2: AI Processing
        logger.info(f"Step 2/4: AI Processing (Politics + 3-5 Bullets + Verified + Breaking: {decision.get('priority')})")
        processed = process_news(aggregated)
        # If breaking, adjust headline to indicate breaking
        if decision.get("priority") == "BREAKING":
            if "BREAKING" not in processed.get('category',''):
                processed['category'] = f"BREAKING - {processed.get('category','Politics')}"
        
        result["steps"]["processing"] = {
            "status": "success",
            "headline": processed.get('headline'),
            "category": processed.get('category'),
            "bullets_count": len(processed.get('urdu_bullets', [])),
            "verified": processed.get('verified', True),
            "is_breaking": decision["is_breaking"]
        }
        logger.info(f"✓ Processed: {processed.get('headline')} | Cat: {processed.get('category')} | Bullets: {len(processed.get('urdu_bullets', []))} | Breaking: {decision['is_breaking']}")

        # Step 3: Image Generation
        logger.info("Step 3/4: Image Generation (1080x1080 - Large Fonts: Urdu 36px, Roman 28px Bold White)")
        image_path = generate_news_card(processed)
        result["steps"]["image_generation"] = {
            "status": "success",
            "path": image_path,
            "font_sizes": "Headline 58px, Urdu 36px, Roman 28px Bold White"
        }
        logger.info(f"✓ Image generated: {image_path}")

        # Step 4: Facebook Publishing
        logger.info(f"Step 4/4: Publishing to Facebook Page {os.getenv('FACEBOOK_PAGE_ID', '239472476226069')} | Priority: {decision.get('priority')} | Verified Only")
        publish_result = publish_to_facebook(image_path, processed)
        result["steps"]["publishing"] = publish_result

        if publish_result.get('success'):
            logger.info(f"✓ Published to Facebook: {publish_result.get('post_id')} | Priority: {decision.get('priority')}")
            # Save posted titles to avoid duplicates
            save_last_posted(aggregated.get('raw_titles', [])[:5], is_breaking=decision["is_breaking"])
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
        logger.info(f"Cycle completed! {greeting} | {decision.get('priority')} | Politics | Verified | Large Fonts | Munsif/Etemaad Only")
        logger.info("="*70)
        return result

    except Exception as e:
        logger.exception(f"Cycle failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["finished_at"] = datetime.now().isoformat()
        return result

def run_scheduler():
    logger.info(f"Starting National Reporter Scheduler")
    logger.info(f"Brand: {BRAND['name']} | Page: https://www.facebook.com/239472476226069 (502K)")
    logger.info(f"Routine: Every {SCHEDULE_INTERVAL_HOURS} hours | Breaking Check: Every {BREAKING_CHECK_MINUTES} minutes")
    logger.info(f"Features: Politics First, Munsif/Etemaad Only, Large Fonts, Verified Only, Breaking Immediate")
    
    # Initial run
    run_once(is_routine=True)

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        
        # Routine every 2 hours
        scheduler.add_job(lambda: run_once(is_routine=True), 'interval', hours=SCHEDULE_INTERVAL_HOURS, id='routine')
        
        # Breaking check every 15 minutes
        scheduler.add_job(lambda: run_once(is_routine=False), 'interval', minutes=BREAKING_CHECK_MINUTES, id='breaking_check')
        
        logger.info(f"Scheduler started:")
        logger.info(f"  - Routine: every {SCHEDULE_INTERVAL_HOURS}h")
        logger.info(f"  - Breaking check: every {BREAKING_CHECK_MINUTES}min (immediate post if breaking)")
        logger.info(f"Press Ctrl+C to exit.")
        scheduler.start()
    except ImportError:
        logger.warning("APScheduler not installed, using simple loop")
        while True:
            # Alternate between routine and breaking checks
            time.sleep(BREAKING_CHECK_MINUTES * 60)
            run_once(is_routine=False)
            # Every 8 breaking checks = 2 hours, do routine
            # Simplified: just check every 15 min with routine flag based on time
            hour = datetime.now().hour
            minute = datetime.now().minute
            if minute < BREAKING_CHECK_MINUTES:  # Top of every 2 hours
                if hour % SCHEDULE_INTERVAL_HOURS == 0:
                    run_once(is_routine=True)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="National Reporter V4 - Breaking + Routine")
    parser.add_argument('--once', action='store_true', help='Run once (routine)')
    parser.add_argument('--breaking-check', action='store_true', help='Run breaking news check (15 min)')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler: routine 2h + breaking 15min')
    parser.add_argument('--test-image', action='store_true', help='Test image generation')
    parser.add_argument('--force', action='store_true', help='Force post even if duplicate')
    args = parser.parse_args()

    if args.test_image:
        from image_generator import NewsCardV3
        test_data = {
            "headline": "تلنگانہ کی سیاست میں بڑی ہلچل، اہم فیصلے متوقع",
            "urdu_bullets": [
                "حیدرآباد میں سیاسی جماعتوں کے درمیان اہم ملاقاتیں جاری ہیں، بڑے فیصلے متوقع ہیں",
                "تلنگانہ اسمبلی میں اپوزیشن نے حکومت کے خلاف تحریک پیش کرنے کا اعلان کیا ہے",
                "وزیر اعلیٰ نے عوامی مسائل کے حل کے لیے نئے اقدامات کا اعلان کیا ہے",
            ],
            "roman_urdu_bullets": [
                "Hyderabad mein siyasi jamaaton ke darmiyan aham mulaqatein jaari hain, bade faisle mutawaqqa hain",
                "Telangana Assembly mein opposition ne hukumat ke khilaf tehreek pesh karne ka elaan kiya hai",
                "Wazir-e-Aala ne awami masail ke hal ke liye naye iqdamaat ka elaan kiya hai",
            ],
            "category": "Politics",
            "date_str": datetime.now().strftime("%d %B %Y"),
            "time_str": datetime.now().strftime("%I:%M %p")
        }
        gen = NewsCardV3()
        path = gen.generate(test_data)
        print(f"Test image (Large Fonts - Roman 28px Bold White): {path}")
    elif args.breaking_check:
        result = run_once(is_routine=False, force_post=args.force)
        print(f"Breaking check result: {result.get('status')} | {result.get('decision', {}).get('reason')}")
    elif args.schedule:
        run_scheduler()
    else:
        result = run_once(is_routine=True, force_post=args.force)
        print(f"\nResult: {result.get('status')} | Priority: {result.get('decision', {}).get('priority')} | Reason: {result.get('decision', {}).get('reason')}")
        if result.get('image_path'):
            print(f"Image: {result['image_path']}")
