"""
National Reporter - Configuration V23 FINAL
- Reference card: English + Roman Urdu, red LATEST NEWS banner
- Permanent fix Tabassum 5x + Gemini API support
- Hourly + Breaking 15min
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

# Brand Identity
BRAND = {
    "name": "National Reporter",
    "short": "NR",
    "logo_path": str(ASSETS_DIR / "logo.png"),
    "credit": "Abu Aimal & Aimal Akram",
    "theme": {
        "background": "#0A0A0A",
        "gold_primary": "#D4AF37",
        "gold_light": "#F4E4BC",
        "gold_dark": "#B8941F",
        "gold_gradient_start": "#F9E076",
        "gold_gradient_end": "#8B6914",
        "silver": "#C0C0C0",
        "white": "#FFFFFF",
        "gray": "#E0E0E0",
        "card_bg": "#121212",
        "red_breaking": "#C41E2F",
    }
}

# Permanent Credit
CREDIT = {
    "name": "Abu Aimal & Aimal Akram",
    "show_in_image": True,
    "show_in_footer": True,
    "show_in_caption": True,
}

# Scraping Sources - Munsif + Etemaad Priority + India Today + Indian Express Fresh Morning
NEWS_SOURCES = {
    "munsif": {
        "name": "Munsif Daily",
        "url": "https://munsifdaily.com/",
        "urdu_url": "https://urdu.munsifdaily.com/",
        "rss": "https://munsifdaily.com/feed/",
        "priority": 1,
        "categories": {
            "politics": "https://munsifdaily.com/category/political-news/",
            "breaking": "https://munsifdaily.com/",
            "hyderabad": "https://munsifdaily.com/category/hyderabad-news/",
            "telangana": "https://munsifdaily.com/category/telangana-news/",
            "national": "https://munsifdaily.com/category/india-news/",
            "world": "https://munsifdaily.com/category/world-news/",
        }
    },
    "etemaad": {
        "name": "Etemaad Daily",
        "url": "https://www.etemaaddaily.com/",
        "english_url": "https://www.en.etemaaddaily.com/",
        "urdu_url": "https://www.etemaaddaily.com/",
        "priority": 1,
        "categories": {
            "politics": "https://www.en.etemaaddaily.com/world/national",
            "breaking": "https://www.en.etemaaddaily.com/",
            "hyderabad": "https://www.en.etemaaddaily.com/world/hyderabad",
            "telangana": "https://www.en.etemaaddaily.com/world/telangana",
            "national": "https://www.en.etemaaddaily.com/world/national",
            "world": "https://www.en.etemaaddaily.com/world/international",
            "regional": "https://www.en.etemaaddaily.com/world"
        }
    },
    "india_today": {
        "name": "India Today",
        "url": "https://www.indiatoday.in/",
        "rss": "https://www.indiatoday.in/rss/1206578",
        "priority": 2,
        "categories": {
            "politics": "https://www.indiatoday.in/politics",
            "breaking": "https://www.indiatoday.in/",
            "hyderabad": "https://www.indiatoday.in/cities",
            "telangana": "https://www.indiatoday.in/cities",
            "national": "https://www.indiatoday.in/india",
            "world": "https://www.indiatoday.in/world",
        }
    },
    "indian_express": {
        "name": "Indian Express",
        "url": "https://indianexpress.com/",
        "rss": "https://indianexpress.com/feed/",
        "priority": 2,
        "categories": {
            "politics": "https://indianexpress.com/section/political-pulse/",
            "breaking": "https://indianexpress.com/latest-news/",
            "hyderabad": "https://indianexpress.com/section/cities/hyderabad/",
            "telangana": "https://indianexpress.com/section/cities/",
            "national": "https://indianexpress.com/section/india/",
            "world": "https://indianexpress.com/section/world/",
        }
    },
    "ndtv": {
        "name": "NDTV",
        "url": "https://www.ndtv.com/",
        "rss": "https://feeds.feedburner.com/ndtvnews-india-news",
        "priority": 3,
        "categories": {
            "politics": "https://www.ndtv.com/india-news",
            "national": "https://www.ndtv.com/india-news",
            "world": "https://www.ndtv.com/world-news",
        }
    }
}

# Content Preferences
CONTENT_PREFS = {
    "preferred_category": "politics",
    "bullets_count": "3-5",
    "morning_hours": [6, 7, 8, 9, 10, 11],
    "verification_required": True,
    "focus": "Munsif & Etemaad Only, Politics First, Verified Only, English+Roman Card Reference",
    "breaking_enabled": True,
}

# Breaking News Detection
BREAKING_NEWS = {
    "enabled": True,
    "check_interval_minutes": 15,
    "routine_interval_hours": 1,  # Hourly now per user request
    "keywords": [
        'breaking', 'urgent', 'just in', 'big breaking', 'flash', 'alert',
        'major', 'important', 'big news', 'exclusive', 'live',
        'resigns', 'arrested', 'accident', 'blast', 'firing', 'protest',
        'election', 'result', 'wins', 'loses', 'announces', 'declares',
        'cm', 'pm', 'minister', 'governor', 'high court', 'supreme court',
        'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'bjp', 'congress', 'brs',
        'slams', 'heats up', 'disrupts', 'killed', 'murdered', 'attack', 'raid', 'seized'
    ],
    "importance_threshold": 8,
    "immediate_post": True,
}

# AI Configuration - OpenAI + Gemini (user added Gemini API)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Facebook Graph API
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "239472476226069")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
FACEBOOK_GRAPH_VERSION = "v20.0"

# Scheduling - Hourly per user
SCHEDULE_INTERVAL_HOURS = 1
BREAKING_CHECK_MINUTES = 15

# Image Generation V23 - Reference card 1080x1350 vertical
IMAGE_SIZE = (1080, 1350)  # Reference image is vertical
FONTS = {
    "urdu_nastaliq": str(FONTS_DIR / "NotoNastaliqUrdu-Regular.ttf"),
    "urdu_naskh": str(FONTS_DIR / "NotoNaskhArabic-Regular.ttf"),
    "poppins_bold": str(FONTS_DIR / "Poppins-Bold.ttf"),
    "poppins_semibold": str(FONTS_DIR / "Poppins-SemiBold.ttf"),
    "poppins_regular": str(FONTS_DIR / "Poppins-Regular.ttf"),
}

FONT_SIZES = {
    "headline_urdu": 58,
    "headline_english": 44,
    "urdu_bullet": 36,
    "roman_bullet": 28,
    "roman_bullet_bold": 28,
    "section_title": 28,
    "date_time": 22,
    "footer": 18,
    "category_badge": 48,  # LATEST NEWS banner 48px
    "english_bullet": 26,  # English bullet white bold 26px like reference
}

PREFERRED_SOURCES = ["Munsif Daily", "Etemaad Daily"]
URDU_NEWS_SOURCES_ONLY = True

# Constraints
NO_LINKS = True
NO_FAKE_NEWS = True
VERIFIED_ONLY = True
BREAKING_NEWS_ENABLED = True

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
