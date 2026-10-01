"""
National Reporter - Main AI Agent V23 FINAL
- Permanent fix Tabassum Begum 5x + TSA overuse
- Reference-perfect English + Roman Urdu card
- Gemini API support + OpenAI optional
- Hourly posting + Breaking 15min
- Saves ALL bullet titles to avoid repeat
"""
import os
import sys
import logging
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SCHEDULE_INTERVAL_HOURS, BREAKING_CHECK_MINUTES, OUTPUT_DIR, BRAND, CONTENT_PREFS, BREAKING_NEWS

# V23 - Use latest scraper and processor
try:
    from morning_fresh_scraper import aggregate_fresh_morning as aggregate_news
    from final_processor import process_fresh_news as process_news, process_breaking_news
    print("Using V23 FINAL: Tabassum 5x fix, English+Roman reference card, Gemini support, Hourly unique")
except ImportError as e:
    print(f"Import failed {e}, fallback")
    from scraper import aggregate_news
    from processor import process_news
    process_breaking_news = process_news

from image_generator import generate_news_card
from facebook_publisher import publish_to_facebook
from breaking_detector import detect_breaking_news, should_post_now, save_last_posted, is_permanently_blacklisted

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

def save_today_all_titles(processed_data: dict, raw_titles: list):
    """V23 FIX: Save ALL bullet titles + headline to avoid Tabassum 5x repeat"""
    try:
        from final_processor import save_today_posted
        # Collect ALL titles that were used
        all_titles_to_save = []
        
        # Headline source
        headline_source = processed_data.get('headline_source', '')
        if headline_source:
            all_titles_to_save.append(headline_source)
        
        # English bullets (actual English titles)
        for b in processed_data.get('english_bullets', [])[:5]:
            if b and len(b) > 15:
                all_titles_to_save.append(b)
        
        # Roman bullets
        for b in processed_data.get('roman_urdu_bullets', [])[:5]:
            if b and len(b) > 15:
                all_titles_to_save.append(b)
        
        # Legacy compatibility
        for b in processed_data.get('urdu_bullets', [])[:5]:
            if b and len(b) > 10 and b not in all_titles_to_save:
                all_titles_to_save.append(b)
        
        # Raw titles from scraper
        for t in raw_titles[:10]:
            if t and t not in all_titles_to_save:
                all_titles_to_save.append(t)
        
        # Clean blacklisted
        all_titles_to_save = [t for t in all_titles_to_save if not is_permanently_blacklisted(t)]
        
        # Save with headline
        save_today_posted(all_titles_to_save, headline_source)
        logger.info(f"Saved V23 today ALL titles: {len(all_titles_to_save)} titles including bullets | Avoids Tabassum 5x")
        logger.info(f"  Headline source: {headline_source[:60]}")
        for i, t in enumerate(all_titles_to_save[:5]):
            logger.info(f"  Title {i+1}: {t[:60]}")
            
    except Exception as e:
        logger.warning(f"Could not save today ALL titles V23: {e}")

def run_once(is_routine: bool = True, force_post: bool = False) -> dict:
    logger.info("="*70)
    greeting, is_morning = get_time_greeting()
    mode = "ROUTINE HOURLY (1h) - Latest News English+Roman" if is_routine else "BREAKING CHECK (15min) - As it happens"
    logger.info(f"Starting National Reporter V23 at {datetime.now()} | Mode: {mode} | FIXES TABASSUM 5X + REFERENCE CARD")
    logger.info(f"{greeting}! V23: No duplicate, English+Roman reference perfect, Gemini support, Politics first, Hourly unique")
    logger.info("="*70)

    result = {
        "started_at": datetime.now().isoformat(),
        "is_morning": is_morning,
        "mode": mode,
        "is_routine": is_routine,
        "steps": {}
    }

    try:
        # Step 1: Scrape - V23
        logger.info("Step 1/4: Scraping V23 - Munsif + Etemaad + India Today + Indian Express + NDTV (Politics first, Dedup, Blacklist Tabassum)")
        aggregated = aggregate_news()
        result["steps"]["scraping"] = {
            "status": "success",
            "total": aggregated.get('total_count', 0),
            "politics": aggregated.get('politics_count', 0),
            "is_morning": aggregated.get('is_morning'),
            "hour": aggregated.get('hour'),
            "sources": aggregated.get('sources_used', {})
        }
        logger.info(f"✓ Scraped V23 {aggregated.get('total_count')} verified | Politics: {aggregated.get('politics_count')} | Sources: {aggregated.get('sources_used', {})}")

        if aggregated.get('total_count', 0) == 0:
            logger.warning("No verified stories, skipping to avoid fake news")
            return {"status": "no_news", "message": "No verified news", "finished_at": datetime.now().isoformat()}

        # Step 1.5: Breaking Detection V23 - Strong dedup + Tabassum blacklist
        logger.info(f"Step 1.5/4: Breaking Detection V23 (Threshold {BREAKING_NEWS['importance_threshold']}) - No Tabassum 5x, No duplicate")
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
        
        logger.info(f"Breaking check V23: {breaking_info['is_breaking']} | Breaking: {len(breaking_info['breaking_stories'])} | Decision: {decision['should_post']} | Reason: {decision['reason']} | New: {decision.get('new_titles_count')}")

        if not decision["should_post"] and not force_post:
            logger.info(f"⏭️ Skipping post V23 - {decision['reason']} - Avoids Tabassum 5x + same card repeat")
            result["status"] = "skipped"
            result["reason"] = decision["reason"]
            result["finished_at"] = datetime.now().isoformat()
            return result

        # Step 2: AI Processing V23 - English + Roman Urdu reference card
        logger.info(f"Step 2/4: AI Processing V23 - English+Roman reference perfect, Gemini support, No Tabassum, Politics first")
        if decision.get("priority") == "BREAKING":
            processed = process_breaking_news(aggregated)
            logger.info(f"BREAKING NEWS V23 - {processed.get('headline')}")
        else:
            processed = process_news(aggregated)
            if "BREAKING" in processed.get('category','').upper() and not decision["is_breaking"]:
                cat = processed.get('category','').replace('BREAKING','Latest News').replace('BREAKING -','').strip()
                if not cat or cat.lower() == "breaking":
                    cat = "Latest News"
                processed['category'] = cat
        
        result["steps"]["processing"] = {
            "status": "success",
            "headline": processed.get('headline'),
            "headline_roman": processed.get('headline_roman'),
            "category": processed.get('category'),
            "english_count": len(processed.get('english_bullets', [])),
            "roman_count": len(processed.get('roman_urdu_bullets', [])),
            "verified": processed.get('verified', True),
            "is_breaking": decision["is_breaking"],
            "is_latest_news": not decision["is_breaking"],
            "no_duplicate": processed.get('no_duplicate', True),
            "reference_design": True
        }
        logger.info(f"✓ Processed V23: {processed.get('headline')} | Cat: {processed.get('category')} | EN: {len(processed.get('english_bullets', []))} RO: {len(processed.get('roman_urdu_bullets', []))} | Reference: English+Roman")

        # Step 3: Image Generation V23 - Reference perfect 1080x1350
        logger.info("Step 3/4: Image Generation V23 Reference Perfect (1080x1350 - Red LATEST NEWS banner #C41E2F, Gold top #D4AF37, English 26px white bold + Roman 26px)")
        image_path = generate_news_card(processed)
        result["steps"]["image_generation"] = {
            "status": "success",
            "path": image_path,
            "font_sizes": "Banner 48px white bold, Date 22px gold, Section 28px gold, Bullets 26px white bold gold dot",
            "latest_news": not decision["is_breaking"],
            "reference_perfect": True,
            "size": "1080x1350"
        }
        logger.info(f"✓ Image generated V23 Reference Perfect: {image_path}")

        # Step 4: Facebook Publishing V23
        logger.info(f"Step 4/4: Publishing V23 Reference to Facebook Page {os.getenv('FACEBOOK_PAGE_ID', '239472476226069')} | Priority: {decision.get('priority')} | English+Roman | No Tabassum 5x")
        publish_result = publish_to_facebook(image_path, processed)
        result["steps"]["publishing"] = publish_result

        if publish_result.get('success'):
            post_id = publish_result.get('post_id')
            logger.info(f"✓ Published V23 to Facebook: {post_id} | Priority: {decision.get('priority')} | Reference card English+Roman | Permanent fix Tabassum 5x")
            
            # V23 FIX: Save ALL bullet titles + headline to avoid Tabassum 5x repeat
            save_last_posted([processed.get('headline_source','')] + aggregated.get('raw_titles', [])[:3], is_breaking=decision["is_breaking"])
            save_today_all_titles(processed, aggregated.get('raw_titles', []))
            logger.info(f"Saved V23 fresh headline + ALL bullets: {processed.get('headline_source','')[:50]}")
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
        logger.info(f"Cycle completed V23! {greeting} | {decision.get('priority')} | English+Roman Reference Perfect | Tabassum 5x Fixed | Gemini Support | SET AND FORGET, NEVER STOPS")
        logger.info("="*70)
        return result

    except Exception as e:
        logger.exception(f"Cycle failed V23: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        result["finished_at"] = datetime.now().isoformat()
        return result

def run_scheduler():
    logger.info(f"Starting National Reporter V23 Scheduler - FIXES TABASSUM 5X, Reference Perfect English+Roman, Gemini")
    logger.info(f"Brand: {BRAND['name']} | Page: https://www.facebook.com/239472476226069 (502K)")
    logger.info(f"Routine: Every 1 hour (hourly) | Breaking Check: Every 15 minutes | V23 Reference Perfect")
    
    run_once(is_routine=True)

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler()
        scheduler.add_job(lambda: run_once(is_routine=True), 'interval', hours=1, id='routine_hourly')
        scheduler.add_job(lambda: run_once(is_routine=False), 'interval', minutes=15, id='breaking_check')
        logger.info(f"Scheduler started V23:")
        logger.info(f"  - Routine: every 1h (hourly) - Latest News English+Roman Reference Perfect, No Tabassum 5x")
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
    parser = argparse.ArgumentParser(description="National Reporter V23 - Tabassum 5x fix, Reference card English+Roman")
    parser.add_argument('--once', action='store_true', help='Run once (hourly routine)')
    parser.add_argument('--breaking-check', action='store_true', help='Run breaking news check (15 min)')
    parser.add_argument('--schedule', action='store_true', help='Run scheduler: hourly + breaking 15min, never stops')
    parser.add_argument('--test-image', action='store_true', help='Test image generation reference perfect')
    parser.add_argument('--force', action='store_true', help='Force post even if duplicate')
    args = parser.parse_args()

    if args.test_image:
        from image_generator import NewsCardV3
        try:
            aggregated = aggregate_news()
            if aggregated.get('total_count', 0) > 0:
                test_data = process_news(aggregated)
                print(f"Using V23 Latest News: {test_data.get('headline')} | Source: {test_data.get('headline_source','')[:50]} | Rot: {test_data.get('rotation_index')} | Cat: {test_data.get('category')}")
            else:
                raise ValueError("No news aggregated")
        except Exception as e:
            print(f"Scrape failed {e}, using V23 fallback reference")
            test_data = {
                "headline": "What nonsense? KTR slams Revanth over Ram vs Shiva comment.",
                "headline_roman": "Kya bakwas hai? KTR ne Revanth ko Ram vs Shiva comment par kharij kharij suna di.",
                "english_bullets": [
                    "What nonsense? KTR slams Revanth over Ram vs Shiva comment.",
                    "Political Atmosphere Heats Up in Nalgonda Over MLA Elections.",
                    "Opposition protest disrupts council meeting at Pala municipality in Keralam's Kottayam."
                ],
                "roman_urdu_bullets": [
                    "Kya bakwas hai? KTR ne Revanth ko Ram vs Shiva comment par kharij kharij suna di.",
                    "Nalgonda mein MLA intikhabat par siyasi garmi barh gayi.",
                    "Keralam ke Kottayam mein Pala municipality mein muzahamati council meeting mein khalal."
                ],
                "category": "Latest News",
                "date_str": datetime.now().strftime("%d %b %Y").upper(),
                "time_str": datetime.now().strftime("%I:%M %p").upper(),
                "rotation_index": datetime.now().hour
            }
        gen = NewsCardV3()
        path = gen.generate(test_data)
        print(f"Test image V23 Reference Perfect: {path}")
    elif args.breaking_check:
        result = run_once(is_routine=False, force_post=args.force)
        print(f"Breaking check V23: {result.get('status')} | {result.get('decision', {}).get('reason')}")
    elif args.schedule:
        run_scheduler()
    else:
        result = run_once(is_routine=True, force_post=args.force)
        print(f"\nResult V23: {result.get('status')} | Priority: {result.get('decision', {}).get('priority')} | Category: {result.get('processed_data', {}).get('category')} | Reason: {result.get('decision', {}).get('reason')}")
        if result.get('image_path'):
            print(f"Image: {result['image_path']}")
            print(f"English bullets: {result.get('processed_data', {}).get('english_bullets')}")
            print(f"Roman bullets: {result.get('processed_data', {}).get('roman_urdu_bullets')}")
