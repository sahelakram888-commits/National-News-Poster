"""
National Reporter - Image Generator Wrapper V23
Uses V4 reference-perfect card: English + Roman Urdu, red LATEST NEWS banner
"""
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from image_generator_v4 import NewsCardV4, generate_news_card as gen_v4, wrap_text, load_font, process_logo
    HAS_V4 = True
    logger.info("Using V4 reference-perfect generator")
except ImportError as e:
    logger.warning(f"V4 import failed {e}, fallback to V3")
    HAS_V4 = False
    try:
        from image_generator_v2 import NewsCardV2 as NewsCardV3
    except:
        from image_generator_v4 import NewsCardV4 as NewsCardV3

if HAS_V4:
    class NewsCardV3(NewsCardV4):
        """Compatibility wrapper for main.py that expects NewsCardV3"""
        pass
    
    def generate_news_card(news_data, output_path=None):
        gen = NewsCardV4()
        return gen.generate(news_data, output_path)
else:
    def generate_news_card(news_data, output_path=None):
        from config import OUTPUT_DIR
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # Fallback simple
        gen = NewsCardV3()
        return gen.generate(news_data, output_path)

if __name__ == "__main__":
    test_data = {
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
        "date_str": "30 SEP 2026",
        "time_str": "09:56 PM",
        "category": "Latest News"
    }
    path = generate_news_card(test_data)
    print(f"Test card V23: {path}")
