"""
National Reporter - Main AI Agent V3
- Larger fonts
- Politics preferred
- Morning: cover all categories
- Verified only, no fake news
- 3-5 bullets
"""
import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SCHEDULE_INTERVAL_HOURS, OUTPUT_DIR, BRAND, CONTENT_PREFS
from scraper import aggregate_news
from processor import process_news
from image_generator import generate_news_card
from facebook_publisher import publish_to_facebook

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

def run_once() -> dict:
    logger.info("="*70)
    logger.info(f"Starting National Reporter cycle at {datetime.now()}")
    greeting, is_morning = get_time_greeting()
    logger.info(f"{greeting}! Morning Mode: {is_morning} | Politics Focus | Verified Only | Large Fonts")
    logger.info("="*70)

    result = {
        "started_at": datetime.now().isoformat(),
        "is_morning": is_morning,
        "steps": {}
    }

    try:
        # Step 1: Scrape
        logger.info("Step 1/4: Scraping (Politics Preferred, Verified Only, NO Fake News)")
        aggregated = aggregate_news()
        result["steps"]["scraping"] = {
            "status": "success",
            "total": aggregated.get('total_count', 0),
            "politics": aggregated.get('politics_count', 0),
            "is_morning": aggregated.get('is_morning'),
            "hour": aggregated.get('hour'),
            "fetched_at": aggregated.get('fetched_at')
        }
        logger.info(f"✓ Scraped {aggregated.get('total_count')} verified stories | Politics: {aggregated.get('politics_count')} | Morning: {aggregated.get('is_morning')}")

        if aggregated.get('total_count', 0) == 0:
            logger.warning("No verified stories found, using fallback")
            return {
                "status": "no_news",
                "message": "No verified news available - skipping to avoid fake news",
                "finished_at": datetime.now().isoformat()
            }

        # Step 2: AI Processing
        logger.info("Step 2/4: AI Processing (GPT-4 - Politics + 3-5 Bullets + Verified Only)")
        processed = process_news(aggregated)
        result["steps"]["processing"] = {
            "status": "success",
            "headline": processed.get('headline'),
            "category": processed.get('category'),
            "bullets_count": len(processed.get('urdu_bullets', [])),
            "verified": processed.get('verified', True)
        }
        logger.info(f"✓ Processed: {processed.get('headline')} | Category: {processed.get('category')} | Bullets: {len(processed.get('urdu_bullets', []))} | Verified: {processed.get('verified')}")

        # Step 3: Image Generation - Larger Fonts
        logger.info("Step 3/4: Image Generation (Premium Black & Gold 1080x1080 - LARGE FONTS)")
        image_path = generate_news_card(processed)
        result["steps"]["image_generation"] = {
            "status": "success",
            "path": image_path,
            "font_sizes": "Headline 58px, Urdu Bullets 34px, Roman 24px - High Readability"
        }
        logger.info(f"✓ Image generated (Large Fonts): {image_path}")

        # Step 4: Facebook Publishing
        logger.info(f"Step 4/4: Publishing to Facebook Page (ID: {os.getenv('FACEBOOK_PAGE_ID', '239472476226069')}) - Verified Only")
        publish_result = publish_to_facebook(image_path, processed)
        result["steps"]["publishing"] = publish_result

        if publish_result.get('success'):
            logger.info(f"✓ Published to Facebook: {publish_result.get('post_id')} | {publish_result.get('post_url')}")
        else:
            if publish_result.get('simulated'):
                logger.warning("Facebook credentials not configured - simulated publish")
                post_text_path = Path(image_path).with_suffix('.txt')
                from facebook_publisher import FacebookPublisher
                pub = FacebookPublisher()
                with open(post_text_path, 'w', encoding='utf-8') as f:
                    f.write(pub.format_post_text(processed))
                logger.info(f"Post text saved to: {post_text_path}")
            else:
                logger.error(f"Failed to publish: {publish_result.get('error')}")

        result["finished_at"] = datetime.now().isoformat()
        result["status"] = "success"
        result["processed_data"] = processed
        result["image_path"] = image_path

        logger.info("="*70)
        logger.info(f"Cycle completed! {greeting} - Politics: {processed.get('category')} - Verified: {processed.get('verified')} - Large Fonts")
        logger.info("="*70)
        return result

    except Exception as e:
        logger.exception(f"Cycle failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["finished_at"] = datetime.now().isoformat()
        return result

def run_scheduler():
    logger.info(f"Starting National Reporter Scheduler - Every {SCHEDULE_INTERVAL_HOURS} hours")
    logger.info(f"Brand: {BRAND['name']} | Theme: Premium Black & Gold | Large Fonts | Politics First | Verified Only")
    logger.info(f"Page: https://www.facebook.com/239472476226069")
    logger.info(f"Features: 3-5 bullets, Morning covers all categories, No fake news, Larger fonts for readability")
    
    run_once()

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(run_once, 'interval', hours=SCHEDULE_INTERVAL_HOURS, next_run_time=None)
        logger.info(f"Scheduler started. Next run in {SCHEDULE_INTERVAL_HOURS} hours. Press Ctrl+C to exit.")
        logger.info("Morning (6-11 AM): Covers Politics + Hyderabad + Telangana + India + World")
        logger.info("Day/Night: Focus on Politics (verified only)")
        scheduler.start()
    except ImportError:
        logger.warning("APScheduler not installed, using simple loop")
        while True:
            logger.info(f"Sleeping for {SCHEDULE_INTERVAL_HOURS} hours...")
            time.sleep(SCHEDULE_INTERVAL_HOURS * 3600)
            run_once()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="National Reporter AI Agent V3 - Large Fonts, Politics, Verified")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler every 2 hours')
    parser.add_argument('--test-image', action='store_true', help='Test image generation only with large fonts')
    args = parser.parse_args()

    if args.test_image:
        from image_generator import NewsCardV3
        from datetime import datetime
        test_data = {
            "headline": "تلنگانہ کی سیاست میں بڑی ہلچل، اہم فیصلے متوقع",
            "urdu_bullets": [
                "حیدرآباد میں سیاسی جماعتوں کے درمیان اہم ملاقاتیں جاری ہیں، بڑے فیصلے متوقع ہیں",
                "تلنگانہ اسمبلی میں اپوزیشن نے حکومت کے خلاف تحریک پیش کرنے کا اعلان کیا ہے",
                "وزیر اعلیٰ نے عوامی مسائل کے حل کے لیے نئے اقدامات کا اعلان کیا ہے",
                "الیکشن کمیشن نے آنے والے بلدیاتی انتخابات کی تیاریاں تیز کر دی ہیں",
                "عوام نے سیاسی صورتحال پر تشویش کا اظہار کرتے ہوئے امن کی اپیل کی ہے"
            ],
            "roman_urdu_bullets": [
                "Hyderabad mein siyasi jamaaton ke darmiyan aham mulaqatein jaari hain, bade faisle mutawaqqa hain",
                "Telangana Assembly mein opposition ne hukumat ke khilaf tehreek pesh karne ka elaan kiya hai",
                "Wazir-e-Aala ne awami masail ke hal ke liye naye iqdamaat ka elaan kiya hai",
                "Election Commission ne aane wale baldiyati intekhabat ki tayyariyan tez kar di hain",
                "Awaam ne siyasi surat-e-haal par tashweesh ka izhaar karte hue aman ki appeal ki hai"
            ],
            "category": "Politics",
            "date_str": datetime.now().strftime("%d %B %Y"),
            "time_str": datetime.now().strftime("%I:%M %p")
        }
        gen = NewsCardV3()
        path = gen.generate(test_data)
        print(f"Test image (Large Fonts): {path}")
    elif args.schedule:
        run_scheduler()
    else:
        result = run_once()
        print("\nResult:", result.get('status'))
        if result.get('image_path'):
            print(f"Image: {result['image_path']}")
            print(f"Category: {result.get('processed_data', {}).get('category')}")
            print(f"Bullets: {len(result.get('processed_data', {}).get('urdu_bullets', []))}")
