"""
National Reporter - Facebook Graph API Publisher V23
- Supports new English + Roman Urdu reference card format
- Permanent credit Abu Aimal & Aimal Akram
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
        if self.access_token:
            self.access_token = self._resolve_page_token_if_system_user(self.access_token)

    def _resolve_page_token_if_system_user(self, token: str) -> str:
        try:
            me_url = f"{self.base_url}/me?access_token={token}"
            r = requests.get(me_url, timeout=10)
            if r.status_code == 200:
                me_data = r.json()
                if me_data.get('id') == '122098613787496439' or 'nr_api_bot' in me_data.get('name','').lower():
                    logger.info(f"Detected system user token (never expiring) - {me_data.get('name')} - getting Page token")
                    accounts_url = f"{self.base_url}/me/accounts?access_token={token}"
                    r2 = requests.get(accounts_url, timeout=10)
                    if r2.status_code == 200:
                        accounts_data = r2.json()
                        for page in accounts_data.get('data', []):
                            if page['id'] == self.page_id:
                                page_token = page['access_token']
                                logger.info(f"Got never-expiring Page token from system user - length {len(page_token)} - tasks {page.get('tasks', [])}")
                                return page_token
                        logger.warning(f"Page {self.page_id} not found in system user accounts")
        except Exception as e:
            logger.warning(f"Failed to resolve system user Page token: {e}")
        return token

    def get_credit_name(self) -> str:
        try:
            from config import CREDIT
            return CREDIT.get('name', 'Abu Aimal & Aimal Akram')
        except:
            return "Abu Aimal & Aimal Akram"

    def is_configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    def format_post_text(self, news_data: Dict) -> str:
        """
        V23 Format: English + Roman Urdu (like reference image)
        Also supports legacy Urdu + Roman for compatibility
        """
        # New V23 format: English bullets + Roman Urdu
        english_bullets = news_data.get('english_bullets', []) or news_data.get('urdu_bullets', [])
        roman_bullets = news_data.get('roman_urdu_bullets', []) or news_data.get('roman_bullets', [])
        headline = news_data.get('headline', '')
        headline_roman = news_data.get('headline_roman', '')
        category = news_data.get('category', 'Latest News')
        date_str = news_data.get('date_str', '')
        time_str = news_data.get('time_str', '')

        # Detect if headline is Urdu script (legacy) or English (new V23)
        is_headline_urdu = any('\u0600' <= c <= '\u06FF' for c in headline) if headline else False

        text = ""
        if is_headline_urdu:
            # Legacy Urdu format
            text += f"📰 {headline}\n"
            if headline_roman and headline_roman != headline:
                text += f"{headline_roman}\n"
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📍 اردو میں اہم نکات:\n"
            for bullet in english_bullets[:5]:
                text += f"• {bullet}\n"
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📍 Roman Urdu Summary:\n"
            for bullet in roman_bullets[:5]:
                text += f"• {bullet}\n"
        else:
            # V23 New Reference Format: English + Roman Urdu
            text += f"📰 {headline}\n"
            if headline_roman and headline_roman.lower() != headline.lower():
                text += f"{headline_roman}\n"
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📍 ENGLISH - Latest News:\n"
            for bullet in english_bullets[:3]:
                text += f"• {bullet}\n"
            text += "\n━━━━━━━━━━━━━━━━━━━━\n"
            text += "📍 ROMAN URDU - Taza Khabar:\n"
            for bullet in roman_bullets[:3]:
                text += f"• {bullet}\n"

        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🏷️ Category: {category}\n"
        text += f"🕒 {date_str} | {time_str}\n"
        text += f"\n#NationalReporter #NR #Hyderabad #Telangana #EnglishNews #RomanUrdu #BreakingNews #LatestNews"
        text += f"\n\n-- {self.get_credit_name()} | National Reporter Team"

        import re
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        return text.strip()

    def publish_photo(self, image_path: str, news_data: Dict) -> Dict:
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
                files = {'source': img_file}
                data = {'caption': caption, 'access_token': self.access_token}
                logger.info(f"Publishing V23 to Facebook Page {self.page_id}... English+Roman card")
                response = requests.post(url, files=files, data=data, timeout=60)
                result = response.json()

                if response.status_code == 200 and 'id' in result:
                    logger.info(f"Successfully published V23! Post ID: {result['id']}")
                    return {
                        "success": True,
                        "post_id": result.get('id'),
                        "post_url": f"https://www.facebook.com/{result.get('id')}",
                        "response": result
                    }
                else:
                    logger.error(f"Facebook API error V23: {result}")
                    return {
                        "success": False,
                        "error": result,
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.exception(f"Exception during Facebook publish V23: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def publish_to_facebook(image_path: str, news_data: Dict) -> Dict:
    publisher = FacebookPublisher()
    return publisher.publish_photo(image_path, news_data)
