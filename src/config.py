"""
National Reporter - Configuration
Premium Black & Gold Theme - Updated for Larger Fonts & Politics Focus
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
        "background": "#0A0A0A",  # Premium Black
        "gold_primary": "#D4AF37",  # Classic Gold
        "gold_light": "#F4E4BC",
        "gold_dark": "#B8941F",
        "gold_gradient_start": "#F9E076",
        "gold_gradient_end": "#8B6914",
        "silver": "#C0C0C0",
        "white": "#FFFFFF",
        "gray": "#E0E0E0",  # Lighter gray for better readability
        "card_bg": "#121212"
    }
}

# Scraping Sources - Enhanced for Politics
NEWS_SOURCES = {
    "munsif": {
        "name": "Munsif Daily",
        "url": "https://munsifdaily.com/",
        "urdu_url": "https://urdu.munsifdaily.com/",
        "rss": "https://munsifdaily.com/feed/",
        "categories": {
            "politics": "https://munsifdaily.com/category/political-news/",
            "hyderabad": "https://munsifdaily.com/category/hyderabad-news/",
            "telangana": "https://munsifdaily.com/category/telangana-news/",
            "national": "https://munsifdaily.com/category/india-news/",
            "world": "https://munsifdaily.com/category/world-news/",
            "telangana_politics": "https://munsifdaily.com/category/telangana-news/",
        }
    },
    "etemaad": {
        "name": "Etemaad Daily",
        "url": "https://www.etemaaddaily.com/",
        "english_url": "https://www.en.etemaaddaily.com/",
        "categories": {
            "politics": "https://www.en.etemaaddaily.com/world/national",
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
    "preferred_category": "politics",  # Prioritize politics
    "bullets_count": "3-5",  # 3 to 5 bullets
    "morning_hours": [6, 7, 8, 9, 10, 11],  # 6 AM to 11 AM - cover all categories
    "verification_required": True,  # No fake/unverified news
    "focus": "Only verified, important political news + major breaking from Hyderabad/Telangana/India/World"
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

# Image Generation - LARGER FONTS FOR READABILITY
IMAGE_SIZE = (1080, 1080)
IMAGE_SIZE_ALT = (1200, 630)
FONTS = {
    "urdu_nastaliq": str(FONTS_DIR / "NotoNastaliqUrdu-Regular.ttf"),
    "urdu_naskh": str(FONTS_DIR / "NotoNaskhArabic-Regular.ttf"),
    "poppins_bold": str(FONTS_DIR / "Poppins-Bold.ttf"),
    "poppins_semibold": str(FONTS_DIR / "Poppins-SemiBold.ttf"),
    "poppins_regular": str(FONTS_DIR / "Poppins-Regular.ttf"),
}

# Font Sizes - INCREASED FOR READABILITY - Roman Urdu now equally large
FONT_SIZES = {
    "headline_urdu": 58,  # Much larger
    "headline_english": 44,  # Increased
    "urdu_bullet": 36,  # Increased from 34 to 36
    "roman_bullet": 28,  # INCREASED from 24 to 28 - now equally readable
    "roman_bullet_bold": 28,  # For better readability
    "section_title": 30,  # Increased
    "date_time": 18,
    "footer": 16,
    "category_badge": 22,
}

# Preferred Sources - Munsif Daily and Etemaad Daily ONLY for Urdu news
PREFERRED_SOURCES = ["Munsif Daily", "Etemaad Daily"]
URDU_NEWS_SOURCES_ONLY = True  # Only Munsif and Etemaad for Urdu news

# Constraints
NO_LINKS = True
NO_FAKE_NEWS = True
VERIFIED_ONLY = True

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
