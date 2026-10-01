"""
Final Processor Wrapper V23 - Permanent fix Tabassum Begum 5x + Gemini + Reference card
"""
import logging
logger = logging.getLogger(__name__)

try:
    from final_processor_v23 import (
        process_fresh_news,
        process_breaking_news,
        process_final_news,
        save_today_posted,
        load_today_posted,
        load_last_posted,
        is_permanently_blacklisted,
        PERMANENT_BLACKLIST,
        translate_specific_news,
        calculate_importance
    )
    logger.info("Using V23 FINAL - Tabassum 5x fix + Gemini + Reference card")
except ImportError as e:
    logger.warning(f"V23 import failed {e}, fallback to V22")
    try:
        from final_processor_v22 import (
            process_fresh_news,
            process_breaking_news,
            process_final_news,
            save_today_posted,
            load_today_posted,
            load_last_posted,
            is_permanently_blacklisted,
            PERMANENT_BLACKLIST,
            translate_specific_news,
            calculate_importance
        )
    except:
        from final_processor_v21 import (
            process_fresh_news,
            process_breaking_news,
            process_final_news,
            save_today_posted,
            load_today_posted,
            load_last_posted,
            is_permanently_blacklisted,
            PERMANENT_BLACKLIST,
            translate_specific_news,
            calculate_importance
        )
