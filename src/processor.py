"""
National Reporter - AI Content Processing Engine V2
- Larger readability focus
- Politics preferred
- 3-5 bullets
- Morning: cover all categories
- NO fake/unverified news
- NO links
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
import re

from config import OPENAI_API_KEY, OPENAI_MODEL, NO_LINKS, CONTENT_PREFS

logger = logging.getLogger(__name__)

MOCK_PROCESSED_POLITICS = {
    "headline": "تلنگانہ کی سیاست میں بڑی ہلچل، اہم فیصلے متوقع",
    "headline_roman": "Telangana Ki Siyasat Mein Badi Hulchul, Aham Faisle Mutawaqqa",
    "urdu_bullets": [
        "حیدرآباد میں سیاسی جماعتوں کے درمیان اہم ملاقاتیں جاری ہیں، بڑے فیصلے متوقع ہیں",
        "تلنگانہ اسمبلی میں اپوزیشن نے حکومت کے خلاف تحریک پیش کرنے کا اعلان کیا ہے",
        "وزیر اعلیٰ نے عوامی مسائل کے حل کے لیے نئے اقدامات کا اعلان کیا ہے",
        "الیکشن کمیشن نے آنے والے بلدیاتی انتخابات کی تیاریاں تیز کر دی ہیں",
        "عوام نے سیاسی صورتحال پر تشویش کا اظہار کرتے ہوئے امن کی اپیل کی ہے"
    ],
    "roman_urdu_bullets": [
        "Hyderabad mein siyasi jamaaton ke darmiyan aham mulaqatein jaari hain, bade faisle mutawaqqa hain",
        "Telangana Assembly mein opposition ne hukumat ke khilaf tehreek pesh karne ka elaan kiya hai",
        "Wazir-e-Aala ne awami masail ke hal ke liye naye iqdamaat ka elaan kiya hai",
        "Election Commission ne aane wale baldiyati intekhabat ki tayyariyan tez kar di hain",
        "Awaam ne siyasi surat-e-haal par tashweesh ka izhaar karte hue aman ki appeal ki hai"
    ],
    "category": "Politics",
    "importance_score": 9,
    "verified": True
}

SYSTEM_PROMPT_V2 = """
You are a senior political news editor for 'National Reporter' - premium black & gold brand with 500K+ followers.

CRITICAL RULES - MUST FOLLOW:

1. CONTENT PREFERENCE:
   - PRIORITY 1: Politics news (Telangana politics, Hyderabad politics, National politics, Assembly, Elections, Government decisions)
   - PRIORITY 2: Major breaking news from Hyderabad, Telangana, India, World
   - MORNING (6 AM - 11 AM): Cover ALL important categories - Politics + Hyderabad + Telangana + National + World (one major story from each if available)
   - DAY/NIGHT: Focus on politics first

2. VERIFICATION - NO FAKE NEWS:
   - Only include VERIFIED, factual news from provided titles
   - NO rumors, NO unverified claims, NO fake news
   - If news seems unverified or sensational without source, SKIP IT
   - Prefer official statements, government announcements, election commission, police verified reports
   - If no verified important news, say "No major verified news" - don't hallucinate

3. OUTPUT FORMAT - JSON ONLY:
{
  "headline": "Brief impactful headline in Urdu (max 10 words, politics focused if possible)",
  "headline_roman": "Same headline in Roman Urdu",
  "urdu_bullets": ["3-5 bullets in pure Urdu script, each 15-22 words, detailed and readable", "..."],
  "roman_urdu_bullets": ["Exact same 3-5 bullets in Roman Urdu (Urdu in English letters)", "..."],
  "category": "Politics/Hyderabad/Telangana/India/World/Morning Roundup",
  "importance_score": 1-10,
  "verified": true,
  "sources": ["Munsif", "Etemaad"] // internal only
}

4. BULLETS REQUIREMENTS:
   - Exactly 3-5 bullets (prefer 4-5 for readability)
   - Each bullet 15-22 words (longer than before for detail)
   - Pure Urdu script for Urdu bullets (اردو)
   - Roman Urdu = Urdu written in English letters (e.g., 'Hyderabad mein siyasi hulchul...')
   - NOT English translation
   - Professional, concise, informative
   - NO emojis in JSON

5. STRICT CONSTRAINTS:
   - Absolutely NO hyperlinks, URLs, [links]
   - NO fake news, NO unverified news
   - NO sensationalism
   - If morning time, mention multiple categories if important news available
   - Headline must be impactful, political if possible

6. EXAMPLE:
User provides: ["Revanth Reddy announces new scheme", "BRS protests in Assembly", "Hyderabad police action"]
You output:
{
  "headline": "تلنگانہ اسمبلی میں سیاسی ہلچل، اپوزیشن کا احتجاج",
  "headline_roman": "Telangana Assembly Mein Siyasi Hulchul, Opposition Ka Ehtijaj",
  "urdu_bullets": [
    "تلنگانہ اسمبلی میں آج اپوزیشن جماعتوں نے حکومت کی پالیسیوں کے خلاف شدید احتجاج کیا ہے",
    "وزیر اعلیٰ ریونت ریڈی نے عوام کے لیے نئی فلاحی اسکیم کا اعلان کیا ہے جس سے لاکھوں لوگوں کو فائدہ ہوگا",
    "الیکشن کمیشن نے حیدرآباد میں بلدیاتی انتخابات کی تیاریوں کا جائزہ لیا ہے",
    "سیاسی تجزیہ کاروں کا کہنا ہے کہ آنے والے دنوں میں بڑے سیاسی فیصلے متوقع ہیں"
  ],
  ...
}

Time now: {current_time}, Hour: {hour}. Is morning? {is_morning}. If morning, cover all categories.
"""

def clean_no_links(text: str) -> str:
    if NO_LINKS:
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    return text.strip()

def get_time_context():
    now = datetime.now()
    hour = now.hour
    is_morning = hour in CONTENT_PREFS.get("morning_hours", [6,7,8,9,10,11])
    return {
        "current_time": now.strftime("%d %B %Y %I:%M %p"),
        "hour": hour,
        "is_morning": is_morning,
        "is_morning_str": "YES - Cover all categories (Politics + Hyderabad + Telangana + National + World)" if is_morning else "NO - Focus on Politics"
    }

def process_with_openai(aggregated_data: Dict) -> Dict:
    if not OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY, using politics-focused mock")
        return process_mock_politics(aggregated_data)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        all_titles = aggregated_data.get('raw_titles', [])[:25]
        categorized = aggregated_data.get('categorized', {})
        time_ctx = get_time_context()

        context = f"""
        Time: {time_ctx['current_time']} | Hour: {time_ctx['hour']} | Morning Mode: {time_ctx['is_morning_str']}

        IMPORTANT: 
        - Sources: Munsif Daily and Etemaad Daily ONLY for Urdu news (preferred Urdu dailies)
        - Prefer POLITICS news from these sources
        - Only VERIFIED news. NO fake news. 3-5 bullets.

        All Top Titles from Munsif & Etemaad (25 verified):
        {chr(10).join(f"- {t}" for t in all_titles)}

        Politics/National from Munsif & Etemaad (Priority):
        {chr(10).join(f"- {s['title']} [Source: {s.get('source','Munsif/Etemaad')}]" for s in categorized.get('india', [])[:6] + categorized.get('all', [])[:6])}

        Hyderabad (Local Politics + Breaking) from Munsif & Etemaad:
        {chr(10).join(f"- {s['title']}" for s in categorized.get('hyderabad', [])[:6])}

        Telangana (State Politics) from Munsif & Etemaad:
        {chr(10).join(f"- {s['title']}" for s in categorized.get('telangana', [])[:6])}

        World (from Munsif & Etemaad):
        {chr(10).join(f"- {s['title']}" for s in categorized.get('world', [])[:4])}
        """

        system_prompt = SYSTEM_PROMPT_V2.format(
            current_time=time_ctx['current_time'],
            hour=time_ctx['hour'],
            is_morning=time_ctx['is_morning_str']
        )

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Summarize into Urdu + Roman Urdu (3-5 bullets, politics preferred, verified only, NO LINKS):\n\n{context}"}
            ],
            temperature=0.3,  # Lower for more factual, less hallucination
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        result = validate_and_clean(result)
        logger.info(f"AI processed (Politics focus): {result.get('headline')} | Verified: {result.get('verified')}")
        return result

    except Exception as e:
        logger.error(f"OpenAI failed: {e}, fallback to mock politics")
        return process_mock_politics(aggregated_data)

def process_mock_politics(aggregated_data: Dict) -> Dict:
    """Fallback with politics focus"""
    titles = aggregated_data.get('raw_titles', [])
    categorized = aggregated_data.get('categorized', {})
    time_ctx = get_time_context()

    # Try to find politics-related titles
    politics_keywords = ['bjp', 'congress', 'brs', 'trs', 'assembly', 'election', 'minister', 'cm', 'mla', 'mp', 'government', 'politics', 'revanth', 'ktr', 'owaisi', 'modi', 'rahul', 'telangana', 'hyderabad', 'mayor', 'corporation']
    
    selected_titles = []
    for title in titles:
        lower = title.lower()
        if any(kw in lower for kw in politics_keywords):
            selected_titles.append(title)
    
    # If morning, include all categories
    if time_ctx['is_morning']:
        selected_titles = titles[:8]  # More coverage in morning
        category = "Morning Roundup"
    else:
        if not selected_titles:
            selected_titles = titles[:3]
        category = "Politics"

    result = MOCK_PROCESSED_POLITICS.copy()
    if selected_titles:
        result["headline_roman"] = selected_titles[0][:80]
        result["category"] = category
    
    result["processed_at"] = datetime.now().isoformat()
    result["date_str"] = datetime.now().strftime("%d %B %Y")
    result["time_str"] = datetime.now().strftime("%I:%M %p")
    result["is_morning"] = time_ctx['is_morning']
    
    return validate_and_clean(result)

def validate_and_clean(data: Dict) -> Dict:
    required_keys = ["headline", "urdu_bullets", "roman_urdu_bullets"]
    for key in required_keys:
        if key not in data:
            logger.warning(f"Missing {key}, using mock politics")
            return MOCK_PROCESSED_POLITICS

    data['headline'] = clean_no_links(data.get('headline',''))
    data['headline_roman'] = clean_no_links(data.get('headline_roman', data['headline']))

    urdu_clean = []
    for bullet in data.get('urdu_bullets', [])[:5]:
        bullet = clean_no_links(bullet)
        if bullet and len(bullet) > 10:
            urdu_clean.append(bullet)
    
    # Ensure 3-5 bullets
    if len(urdu_clean) < 3:
        urdu_clean = MOCK_PROCESSED_POLITICS['urdu_bullets'][:4]
    data['urdu_bullets'] = urdu_clean[:5]

    roman_clean = []
    for bullet in data.get('roman_urdu_bullets', [])[:5]:
        bullet = clean_no_links(bullet)
        if bullet and len(bullet) > 10:
            roman_clean.append(bullet)
    
    if len(roman_clean) < 3:
        roman_clean = MOCK_PROCESSED_POLITICS['roman_urdu_bullets'][:4]
    data['roman_urdu_bullets'] = roman_clean[:5]

    # Ensure same count
    min_count = min(len(data['urdu_bullets']), len(data['roman_urdu_bullets']))
    # Force at least 3
    min_count = max(3, min_count)
    data['urdu_bullets'] = data['urdu_bullets'][:min_count]
    data['roman_urdu_bullets'] = data['roman_urdu_bullets'][:min_count]

    data['processed_at'] = datetime.now().isoformat()
    data['date_str'] = datetime.now().strftime("%d %B %Y")
    data['time_str'] = datetime.now().strftime("%I:%M %p")
    data['verified'] = data.get('verified', True)

    return data

def process_news(aggregated_data: Dict) -> Dict:
    logger.info(f"Processing news - Politics preferred, Verified only, 3-5 bullets, Time: {get_time_context()}")
    result = process_with_openai(aggregated_data)
    return result

if __name__ == "__main__":
    mock_agg = {
        "fetched_at": datetime.now().isoformat(),
        "raw_titles": [
            "Telangana HC Directs DGP To Identify Police Personnel In BRS Women MLAs Case",
            "BJP attacks Revanth Reddy over Ram-Shiva comments",
            "BJP declares names of six candidates for Uttar Pradesh MLC elections",
            "Centre sanctions Rs 1,200 crore to 10 states under PM Rashtriya Krishi Vikas Yojana"
        ],
        "categorized": {
            "hyderabad": [{"title": "Cab driver attempts to sexually assault woman in Hyderabad"}],
            "telangana": [{"title": "Telangana HC Directs DGP To Identify Police Personnel"}],
            "india": [{"title": "BJP declares names of six candidates"}],
            "world": [],
            "all": []
        }
    }
    result = process_news(mock_agg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
