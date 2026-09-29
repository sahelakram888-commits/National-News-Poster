"""
National Reporter - Facebook Graph API Publisher
Posts generated image + Urdu + Roman Urdu text to Facebook Page
https://www.facebook.com/profile.php?id=100085918100245
"""
import os
import logging
import requests
from typing import Dict
from pathlib import Path

from config import FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_GRAPH_VERSION

logger = logging.getLogger(__name__)

GRAPH_BASE = f"https://graph.facebook.com/{FACEBOOK_GRAPH_VERSION}"

class FacebookPublisher:
    def __init__(self, page_id: str = None, access_token: str = None):
        self.page_id = page_id or FACEBOOK_PAGE_ID
        self.access_token = access_token or FACEBOOK_PAGE_ACCESS_TOKEN
        self.base_url = GRAPH_BASE

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def format_post_text(self, news_data: Dict) -> str:
        """
        Format text for Facebook post - NO LINKS constraint
        Includes Urdu bullets + Roman Urdu bullets
        """
        headline = news_data.get('headline', '')
        headline_roman = news_data.get('headline_roman', '')
        urdu_bullets = news_data.get('urdu_bullets', [])
        roman_bullets = news_data.get('roman_urdu_bullets', [])
        category = news_data.get('category', 'News')
        date_str = news_data.get('date_str', '')
        time_str = news_data.get('time_str', '')

        # Build post
        text = f"📰 {headline}\n"
        if headline_roman and headline_roman != headline:
            text += f"{headline_roman}\n"
        text += "\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "📍 اردو میں اہم نکات:\n"
        for bullet in urdu_bullets:
            text += f"• {bullet}\n"
        text += "\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "📍 Roman Urdu Summary:\n"
        for bullet in roman_bullets:
            text += f"• {bullet}\n"
        text += "\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🏷️ Category: {category}\n"
        text += f"🕒 {date_str} | {time_str}\n"
        text += f"\n#NationalReporter #NR #Hyderabad #Telangana #UrduNews #BreakingNews"
        # Note: hashtags are okay, NOT hyperlinks

        # Ensure no URLs slipped in
        # (double-check)
        import re
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        return text.strip()

    def publish_photo(self, image_path: str, news_data: Dict) -> Dict:
        """
        Publish photo post to Facebook Page
        Uses /{page-id}/photos endpoint
        """
        if not self.is_configured():
            logger.error("Facebook not configured - missing PAGE_ID or ACCESS_TOKEN")
            return {
                "success": False,
                "error": "Facebook credentials not configured. Set FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN in .env",
                "simulated": True,
                "post_text": self.format_post_text(news_data),
                "image_path": image_path
            }

        url = f"{self.base_url}/{self.page_id}/photos"
        
        caption = self.format_post_text(news_data)
        
        try:
            with open(image_path, 'rb') as img_file:
                files = {
                    'source': img_file
                }
                data = {
                    'caption': caption,
                    'access_token': self.access_token
                }
                logger.info(f"Publishing to Facebook Page {self.page_id}...")
                response = requests.post(url, files=files, data=data, timeout=60)
                result = response.json()

                if response.status_code == 200 and 'id' in result:
                    logger.info(f"Successfully published! Post ID: {result['id']}")
                    return {
                        "success": True,
                        "post_id": result.get('id'),
                        "post_url": f"https://www.facebook.com/{result.get('id')}",
                        "response": result
                    }
                else:
                    logger.error(f"Facebook API error: {result}")
                    return {
                        "success": False,
                        "error": result,
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.exception(f"Exception during Facebook publish: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def publish_feed_with_image_url(self, image_url: str, news_data: Dict) -> Dict:
        """
        Alternative method if image is hosted via URL (for Make.com/Bannerbear flow)
        """
        if not self.is_configured():
            return {"success": False, "error": "Not configured", "simulated": True}

        url = f"{self.base_url}/{self.page_id}/feed"
        message = self.format_post_text(news_data)

        data = {
            'message': message,
            'link': image_url,  # Note: we avoid links per constraint, but if using image URL hosting, this is the image itself
            'access_token': self.access_token
        }
        # Actually for photo URL, better to use picture param? But we use photos endpoint preferred.
        # This method kept for compatibility

        try:
            response = requests.post(url, data=data, timeout=30)
            result = response.json()
            if response.status_code == 200:
                return {"success": True, "post_id": result.get('id'), "response": result}
            else:
                return {"success": False, "error": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

def publish_to_facebook(image_path: str, news_data: Dict) -> Dict:
    publisher = FacebookPublisher()
    return publisher.publish_photo(image_path, news_data)

if __name__ == "__main__":
    # Test formatting without actual publish
    test_data = {
        "headline": "حیدرآباد میں بڑی کارروائی، پولیس کی اہم پیش رفت",
        "headline_roman": "Hyderabad Mein Badi Karwai, Police Ki Aham Pesh Raft",
        "urdu_bullets": [
            "حیدرآباد کے ایس آر نگر میں مشتبہ حالات میں خاتون کی لاش برآمد ہوئی ہے",
            "پولیس نے واقعے کی تحقیقات شروع کر دی ہیں"
        ],
        "roman_urdu_bullets": [
            "Hyderabad ke SR Nagar mein mushtaba halaat mein khatoon ki laash baramad hui hai",
            "Police ne waqiye ki tehqiqaat shuru kar di hain"
        ],
        "category": "Hyderabad",
        "date_str": "29 September 2026",
        "time_str": "05:30 PM"
    }
    pub = FacebookPublisher()
    text = pub.format_post_text(test_data)
    print(text)
    print("\n--- Configured:", pub.is_configured())
