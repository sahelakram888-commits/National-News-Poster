"""
Final Processor Wrapper V24 FINAL - URDU + Reference Perfect Design
User clarification: English card was FOR REFERENCE ONLY for design/layout
Actual needed: URDU cards (Urdu script + Roman Urdu) with reference perfect design
- Tabassum Begum 5x fix + TSA overuse + Fresh news + Reference perfect design
"""
import logging
logger = logging.getLogger(__name__)

try:
    from final_processor_v24 import (
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
    logger.info("Using V24 FINAL - URDU + Reference Perfect Design - User wants Urdu, English was reference only")
except ImportError as e:
    logger.warning(f"V24 import failed {e}, fallback to V23")
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
    except:
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
