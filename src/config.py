"""
National Reporter - Configuration V4
- Large fonts, Politics, Munsif/Etemaad Only
- Breaking News: immediate coverage as it happens + routine every 2h
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
        "red_breaking": "#FF0000",  # For breaking badge
    }
}

# Scraping Sources - Munsif & Etemaad ONLY for Urdu News
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
    }
}

# Content Preferences
CONTENT_PREFS = {
    "preferred_category": "politics",
    "bullets_count": "3-5",
    "morning_hours": [6, 7, 8, 9, 10, 11],
    "verification_required": True,
    "focus": "Munsif & Etemaad Only, Politics First, Verified Only",
    "breaking_enabled": True,
}

# Breaking News Detection
BREAKING_NEWS = {
    "enabled": True,
    "check_interval_minutes": 15,  # Check every 15 min for breaking news
    "routine_interval_hours": 2,  # Routine every 2 hours
    "keywords": [
        'breaking', 'urgent', 'just in', 'big breaking', 'flash', 'alert',
        'major', 'important', 'big news', 'exclusive', 'live',
        'resigns', 'arrested', 'accident', 'blast', 'firing', 'protest',
        'election', 'result', 'wins', 'loses', 'announces', 'declares',
        'cm', 'pm', 'minister', 'governor', 'high court', 'supreme court',
        'kcr', 'ktr', 'revanth', 'owaisi', 'modi', 'rahul', 'bjp', 'congress', 'brs'
    ],
    "importance_threshold": 8,  # Score 8-10 is breaking
    "immediate_post": True,  # Post immediately when breaking detected
}

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Facebook Graph API
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "239472476226069")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
FACEBOOK_GRAPH_VERSION = "v20.0"

# Scheduling
SCHEDULE_INTERVAL_HOURS = 2
BREAKING_CHECK_MINUTES = 15

# Image Generation
IMAGE_SIZE = (1080, 1080)
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
    "section_title": 30,
    "date_time": 18,
    "footer": 16,
    "category_badge": 22,
}

PREFERRED_SOURCES = ["Munsif Daily", "Etemaad Daily"]
URDU_NEWS_SOURCES_ONLY = True

# Constraints
NO_LINKS = True
NO_FAKE_NEWS = True
VERIFIED_ONLY = True
BREAKING_NEWS_ENABLED = True

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
