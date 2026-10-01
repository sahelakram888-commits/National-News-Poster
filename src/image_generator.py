"""
National Reporter - Image Generator Wrapper V5 - URDU + Reference Perfect Design
User clarification: English card was FOR REFERENCE ONLY for design/layout
Actual needed: URDU cards (Urdu script + Roman Urdu) with reference perfect design
- Black #0A0A0A, Gold top 12px, NR logo 120px, Gold separator 3px
- Red banner #C41E2F LATEST NEWS white 48px bold warning icon
- URDU / ROMAN URDU gold headers with vertical bar, gold dots, white bullets
- 1080x1080 compact
"""
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from image_generator_v5 import NewsCardV5, generate_news_card as gen_v5, wrap_text, wrap_urdu_text, load_font, process_logo, reshape_urdu
    HAS_V5 = True
    logger.info("Using V5 URDU + Reference Perfect generator (user wants Urdu, English was reference only)")
except ImportError as e:
    logger.warning(f"V5 import failed {e}, fallback to V4")
    HAS_V5 = False
    try:
        from image_generator_v4 import NewsCardV4 as NewsCardV5
    except:
        from image_generator_v4 import NewsCardV4 as NewsCardV5

if HAS_V5:
    class NewsCardV3(NewsCardV5):
        """Compatibility wrapper for main.py that expects NewsCardV3"""
        pass
    
    def generate_news_card(news_data, output_path=None):
        gen = NewsCardV5()
        return gen.generate(news_data, output_path)
else:
    def generate_news_card(news_data, output_path=None):
        from config import OUTPUT_DIR
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        gen = NewsCardV5()
        return gen.generate(news_data, output_path)

if __name__ == "__main__":
    test_data = {
        "urdu_bullets": [
            "حیدرآباد میں پولیس کی بڑی کارروائی، منشیات کے خلاف سخت اقدامات",
            "تلنگانہ ہائی کورٹ نے بی آر ایس خاتون ایم ایل ایز کیس میں ڈی جی پی کو ہدایات دی ہیں",
            "کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے"
        ],
        "roman_urdu_bullets": [
            "Hyderabad mein police ki badi karwai, manshiyat ke khilaf sakht iqdamat",
            "Telangana High Court ne BRS khatoon MLAs case mein DGP ko hidayat di hain",
            "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai"
        ],
        "date_str": "01 OCT 2026",
        "time_str": "12:36 PM",
        "category": "Latest News"
    }
    path = generate_news_card(test_data)
    print(f"Test card V5 URDU Reference Perfect: {path}")
