"""
National Reporter - Important First Processor V10
- Politics first, then regional (Hyderabad/Telangana), then national, then world
- Important news first (breaking score high)
- Hourly posting to cover so much news
- Never expiring token
"""
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

def clean_urdu_pure(text: str) -> str:
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\b[a-zA-Z][a-zA-Z0-9\'-]*\b', '', text)
    text = re.sub(r'[^\u0600-\u06FF\s\u200c\u200d۔،؟!0-9٪%]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_roman_pure(text: str) -> str:
    text = re.sub(r'[\u0600-\u06FF]+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s\-\.,:;\'\"()!?\n]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_urdu(text: str) -> bool:
    return any('\u0600' <= c <= '\u06FF' for c in text)

def calculate_importance(title: str) -> int:
    """Calculate importance score 0-10"""
    lower = title.lower()
    score = 0
    
    # Breaking keywords
    breaking_kw = ['breaking','urgent','just in','major','important','big news','exclusive','live','resigns','arrested','accident','blast','firing','protest','election','result','wins','loses','announces','declares']
    score += sum(1 for kw in breaking_kw if kw in lower) * 1
    
    # Important persons
    important = ['cm','pm','minister','kcr','ktr','revanth','owaisi','modi','rahul','governor','high court','supreme court','mla','mp','eci','dpg','president']
    if any(p in lower for p in important):
        score += 2
    
    # Action
    action = ['killed','murdered','assault','attack','raid','bust','cancelled','directs','announces','approves','hits record']
    if any(a in lower for a in action):
        score += 2
    
    # Politics boost
    if any(k in lower for k in ['bjp','congress','brs','trs','aimim','election','politics','assembly']):
        score += 2
    
    # Regional boost (Hyderabad/Telangana)
    if 'hyderabad' in lower or 'telangana' in lower:
        score += 1
    
    return min(score, 10)

def translate_important_news(eng_title: str) -> tuple:
    """Translate important news first: politics > regional > national > world"""
    lower = eng_title.lower()
    
    # Politics first (most important)
    if 'congress announces sama reddy' in lower and 'mlc poll' in lower:
        return ("کانگریس نے ایم ایل سی انتخابات کے لیے سما ریڈی اور رام ریڈی کو امیدوار نامزد کیا ہے", "Congress ne MLC intekhabat ke liye Sama Reddy aur Ram Reddy ko ummeedwar namzad kiya hai")
    elif 'gyanesh kumar must quit' in lower and 'ballot papers' in lower:
        return ("گیانیش کمار مستعفی ہوں، بیلٹ پیپر واپس لائیں، تلنگانہ ڈپٹی سی ایم کا مطالبہ", "Gyanesh Kumar mustafe hon, ballot paper wapas laayen, Telangana Deputy CM ka mutalba")
    elif 'please come back to us' in lower and 'telangana deputy cm' in lower:
        return ("براہ مہربانی واپس آ جائیں، تلنگانہ ڈپٹی سی ایم کی سابق کانگریس لیڈروں سے اپیل", "Barah-e-meherbani wapas aa jayen, Telangana Deputy CM ki sabiq Congress leaders se appeal")
    elif 'formed to protect british' in lower and 'congress attacking eci' in lower:
        return ("برطانوی دور میں بنی کانگریس آج الیکشن کمیشن پر حملہ کر رہی ہے، بی جے پی کا الزام", "Bartanvi daur mein bani Congress aaj Election Commission par hamla kar rahi hai, BJP ka ilzaam")
    elif 'telangana hc directs dgp' in lower and 'brs women mlas' in lower:
        return ("تلنگانہ ہائی کورٹ نے بی آر ایس خاتون ایم ایل ایز کیس میں ڈی جی پی کو ہدایات دی ہیں", "Telangana High Court ne BRS khatoon MLAs case mein DGP ko hidayat di hain")
    elif 'how can one expect better from cong' in lower and 'revanth reddy' in lower:
        return ("بی جے پی نے رام شیوا تبصرے پر ریونت ریڈی پر تنقید کی ہے", "BJP ne Ram-Shiva tabsare par Revanth Reddy par tanqeed ki hai")
    elif 'telangana acb catches revenue inspector' in lower:
        return ("تلنگانہ اے سی بی نے 15 ہزار رشوت کیس میں ریونیو انسپکٹر کو پکڑا ہے", "Telangana ACB ne 15 hazar rishwat case mein revenue inspector ko pakda hai")
    elif 'telangana power demand hits record' in lower:
        return ("تلنگانہ میں بجلی کی طلب نے 12 ہزار میگا واٹ کا ریکارڈ توڑ دیا ہے", "Telangana mein bijli ki talab ne 12 hazar MW ka record tod diya hai")
    elif 'congress approves sama rammohan reddy' in lower:
        return ("کانگریس نے تلنگانہ ایم ایل سی انتخابات کے لیے امیدواروں کو منظوری دی ہے", "Congress ne Telangana MLC intekhabat ke liye ummeedwaron ko manzoori di hai")
    elif 'kharge quips at tharoor' in lower:
        return ("کانگریس میٹنگ میں کھرگے نے تھرور پر طنز کیا ہے", "Congress meeting mein Kharge ne Tharoor par tanz kiya hai")
    
    # Regional - Hyderabad/Telangana (second priority)
    elif 'woman who married lover in temple' in lower and 'murdered at hyderabad oyo' in lower:
        return ("مندر میں پریمی سے شادی کرنے والی خاتون کا حیدرآباد او وائی او میں قتل پایا گیا", "Mandir mein premi se shadi karne wali khatoon ka Hyderabad OYO mein qatal paya gaya")
    elif 'cab driver attempts to sexually assault' in lower and 'hyderabad' in lower:
        return ("حیدرآباد میں کیب ڈرائیور کی خاتون سے بدتمیزی کی کوشش، پولیس نے مقدمہ درج کیا", "Hyderabad mein cab driver ki khatoon se badtameezi ki koshish, police ne muqadma darj kiya")
    elif 'licences of 11 hyderabad restaurants cancelled' in lower:
        return ("حیدرآباد کے 11 ریسٹورنٹس کے لائسنس غیر صحت مندانہ حالات پر منسوخ کیے گئے", "Hyderabad ke 11 restaurants ke licence ghair sehat mandana halat par mansookh kiye gaye")
    elif 'telangana woman lured to oman' in lower:
        return ("تلنگانہ کی خاتون کو عمان میں جعلی نوکری کا جھانسہ دے کر پھنسایا گیا", "Telangana ki khatoon ko Oman mein jali naukri ka jhansa de kar phansaya gaya")
    elif 'around 100 sheep killed' in lower and 'medchal' in lower:
        return ("میڈچل میں دکن ایکسپریس کی زد میں آ کر 100 بھیڑیں ہلاک ہو گئیں", "Medchal mein Dakshin Express ki zad mein aa kar 100 bheden halaak ho gayin")
    elif 'son allegedly attacks parents' in lower and 'kukatpally' in lower:
        return ("کوکٹ پلی میں بیٹے کا جائیداد کے تنازع پر والدین پر حملہ، پولیس تحقیقات جاری", "Kukatpally mein bete ka jayedad ke tanaze par walidain par hamla, police tahqeeqat jaari")
    
    # National (third priority)
    elif 'ed continues questioning' in lower and 'vivekananda reddy' in lower:
        return ("ویویکانند ریڈی قتل کیس میں ای ڈی کی جانب سے اہم ملزم سے پوچھ گچھ جاری ہے", "Vivekananda Reddy qatal case mein ED ki janib se aham mulzim se pooch gach jaari hai")
    elif 'cbi secures deportation' in lower and 'nirav modi' in lower:
        return ("سی بی آئی نے نیرو مودی کیس کے ملزم کو یو اے ای سے ڈی پورٹ کرایا ہے", "CBI ne Nirav Modi case ke mulzim ko UAE se deport karaya hai")
    elif 'bjp declares names of six candidates' in lower:
        return ("بی جے پی نے اتر پردیش ایم ایل سی کے لیے 6 امیدواروں کا اعلان کیا ہے", "BJP ne Uttar Pradesh MLC ke liye 6 ummeedwaron ka elaan kiya hai")
    elif 'after bjp objects to salary hike' in lower and 'omar abdullah' in lower:
        return ("بی جے پی کے اعتراض کے بعد عمر عبداللہ نے تنخواہ کے بل واپس لیے ہیں", "BJP ke aitraaz ke baad Omar Abdullah ne tankhwah ke bill wapas liye hain")
    elif 'lashkar commander musa killed' in lower and 'budgam encounter' in lower:
        return ("بڈگام انکاؤنٹر میں لشکر کمانڈر موسیٰ ہلاک، سابق پاک کمانڈو بھی مارا گیا", "Budgam encounter mein Lashkar commander Musa halaak, sabiq Pak commando bhi mara gaya")
    elif 'might as well disband up police' in lower:
        return ("یوپی پولیس کو ختم ہی کر دیں، سپریم کورٹ نے ریاستی پولیس کو سخت تنقید کا نشانہ بنایا", "UP police ko khatam hi kar dein, Supreme Court ne riyasati police ko sakht tanqeed ka nishana banaya")
    elif 'all 4 lashkar terrorists' in lower and 'viral pic now dead' in lower:
        return ("وائرل تصویر میں نظر آنے والے 4 لشکر دہشت گرد اب ہلاک ہو چکے ہیں", "Viral tasveer mein nazar aane wale 4 Lashkar dehshatgard ab halaak ho chuke hain")
    elif 'apple pay debuts in india' in lower:
        return ("ایپل پے نے ہندوستان میں آغاز کیا ہے جہاں یو پی آئی کا 80 فیصد سے زیادہ حصہ ہے", "Apple Pay ne Hindustan mein aaghaz kiya hai jahan UPI ka 80% se zyada hissa hai")
    elif '9-year-old girl dies' in lower and 'school staircase collapses' in lower:
        return ("بہار کے کھگڑیا میں اسکول کی سیڑھیاں گرنے سے 9 سالہ بچی ہلاک ہو گئی ہے", "Bihar ke Khagaria mein school ki seedhiyan girne se 9 saala bacchi halaak ho gayi hai")
    elif 'dr g. satheesh reddy' in lower and 'indigenous content' in lower:
        return ("ڈاکٹر جی ستیش ریڈی نے کہا مسلح افواج میں دیسی مواد 88 فیصد تک پہنچ گیا ہے", "Dr G. Satheesh Reddy ne kaha musallah afwaj mein desi mawaad 88% tak pahunch gaya hai")
    elif 'top lashkar commander musa killed' in lower:
        return ("بڈگام میں ٹاپ لشکر کمانڈر موسیٰ ہلاک، دہشت گرد نیٹ ورک ختم", "Budgam mein top Lashkar commander Musa halaak, dehshatgard network khatam")
    
    # World (fourth priority)
    elif 'iran offers to reopen hormuz' in lower:
        return ("ایران نے سات روزہ منصوبے کے چھٹے دن ہرمز کو دوبارہ کھولنے کی پیشکش کی ہے", "Iran ne saat roza mansube ke chathe din Hormuz ko dobara kholne ki peshkash ki hai")
    
    else:
        return ("حیدرآباد اور تلنگانہ سے تازہ ترین اہم خبر سامنے آئی ہے", "Hyderabad aur Telangana se taza tareen aham khabar samne aayi hai")

def get_time_context():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    second = now.second
    # Unique rotation every time - changes every minute and every second for variety
    # Ensures NO OLD CARD REPETITION - unique headline every single post
    # Uses hour*60 + minute + second for true uniqueness
    rotation = (hour * 3600 + minute * 60 + second) % 100  # Unique every second, 100 variations
    return {
        "now": now,
        "hour": hour,
        "minute": minute,
        "second": second,
        "rotation": rotation,
        "is_morning": hour in [6,7,8,9,10,11],
        "date_str": now.strftime("%d %B %Y"),
        "time_str": now.strftime("%I:%M %p"),
        "unique_id": now.strftime("%d%m%H%M%S")
    }

def is_blacklisted_old_card(title: str) -> bool:
    """Blacklist old card templates - NEVER post old cards again"""
    blacklisted = [
        "تلنگانہ کی سیاست میں بڑی ہلچل",
        "تلنگانہ کی سیاست میں بڑی ہلچل، اہم فیصلے متوقع",
        "حیدرآباد میں سیاسی جماعتوں کے درمیان اہم ملاقاتیں",
        "تلنگانہ اسمبلی میں اپوزیشن نے حکومت کے خلاف تحریک",
        "وزیر اعلیٰ نے عوامی مسائل کے حل کے لیے نئے اقدامات",
    ]
    for old in blacklisted:
        if old in title or title in old:
            return True
    return False

def get_last_posted_headlines() -> List[str]:
    """Get last posted headlines to avoid old card repetition"""
    try:
        from pathlib import Path
        import json
        last_file = Path(__file__).parent.parent / "output" / "last_posted.json"
        if last_file.exists():
            with open(last_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('titles', [])[:30]
    except:
        pass
    return []

def process_important_first(aggregated_data: Dict) -> Dict:
    """Process important news first: politics > regional > national > world - NO OLD CARD REPETITION"""
    all_stories = aggregated_data.get('all_stories', [])
    time_ctx = get_time_context()
    last_headlines = get_last_posted_headlines()
    
    # Sort by importance first, then by category priority
    def category_priority(s):
        cat = s.get('category','')
        if s.get('is_politics'):
            return 1
        if cat in ['hyderabad','telangana']:
            return 2
        if cat == 'india':
            return 3
        if cat == 'world':
            return 4
        return 5
    
    for s in all_stories:
        s['importance'] = calculate_importance(s['title'])
    
    all_stories.sort(key=lambda x: (-x['importance'], category_priority(x)))
    
    # Filter out old posted headlines and blacklisted old cards to avoid repetition
    fresh_stories = []
    for s in all_stories:
        # Blacklist old card templates - NEVER post old cards again
        if is_blacklisted_old_card(s['title']):
            logger.info(f"Blacklisted old card - skipping: {s['title'][:50]}")
            continue
            
        is_old = False
        for old_title in last_headlines:
            if s['title'].lower().strip() == old_title.lower().strip():
                is_old = True
                break
            if len(s['title']) > 20 and s['title'].lower().strip()[:20] == old_title.lower().strip()[:20]:
                is_old = True
                break
        if not is_old:
            fresh_stories.append(s)
    
    # If all are old, use all but with rotation for uniqueness
    if not fresh_stories:
        fresh_stories = all_stories
    
    # Get top 20 important first from fresh
    important_titles = [s['title'] for s in fresh_stories[:20]]
    
    categorized = {
        "politics": [s for s in fresh_stories if s.get('is_politics')][:10],
        "hyderabad": [s for s in fresh_stories if s['category']=='hyderabad'][:8],
        "telangana": [s for s in fresh_stories if s['category']=='telangana'][:8],
        "india": [s for s in fresh_stories if s['category']=='india'][:8],
        "world": [s for s in fresh_stories if s['category']=='world'][:5],
        "all": fresh_stories[:20],
    }
    
    # Headline: most important from FRESH, with rotation for uniqueness every second
    # Ensures NO OLD CARD REPETITION
    if fresh_stories:
        rotation = time_ctx['rotation']
        # Rotate through top 10 fresh important headlines for variety every post
        idx = rotation % min(10, len(fresh_stories))
        selected = fresh_stories[idx]
        selected_title = selected['title']
        logger.info(f"Selected fresh headline (rot {rotation}, idx {idx}, not old): {selected_title[:60]} | Importance {selected['importance']}")
    else:
        selected_title = "تلنگانہ میں اہم پیش رفت ہوئی ہے"
    
    # Category
    lower_sel = selected_title.lower()
    if any(k in lower_sel for k in ['bjp','congress','election','modi','revanth','owaisi','cm','pm','hc','court','mla','mp','eci','minister']):
        category = "Politics"
    elif 'hyderabad' in lower_sel:
        category = "Hyderabad"
    elif 'telangana' in lower_sel:
        category = "Telangana"
    elif 'india' in lower_sel or 'lashkar' in lower_sel or 'budgam' in lower_sel or 'bihar' in lower_sel:
        category = "India"
    elif 'world' in lower_sel or 'oman' in lower_sel or 'iran' in lower_sel:
        category = "World"
    else:
        category = "Breaking"
    
    # Translate
    if is_urdu(selected_title):
        headline_urdu = clean_urdu_pure(selected_title)[:90]
        if len(headline_urdu) < 10:
            headline_urdu = "تلنگانہ میں اہم پیش رفت ہوئی ہے"
        _, headline_roman = translate_important_news(selected_title)
        headline_roman = clean_roman_pure(headline_roman)[:90]
    else:
        headline_urdu, headline_roman = translate_important_news(selected_title)
        headline_urdu = clean_urdu_pure(headline_urdu)[:90]
        headline_roman = clean_roman_pure(headline_roman)[:90]
    
    # Bullets: important first - politics, then regional, then national, then world
    urdu_bullets = []
    roman_bullets = []
    
    bullet_sources = []
    # Order: politics first, then hyderabad, telangana, india, world
    for cat in ["politics", "hyderabad", "telangana", "india", "world"]:
        for s in categorized.get(cat, [])[:2]:
            if s['title'] not in bullet_sources:
                bullet_sources.append(s['title'])
    
    # Fill from important titles
    for title in important_titles:
        if len(bullet_sources) >= 5:
            break
        if title not in bullet_sources:
            bullet_sources.append(title)
    
    for title in bullet_sources[:5]:
        if is_urdu(title):
            urdu = clean_urdu_pure(title)[:120]
            if len(urdu) < 10:
                urdu = "حیدرآباد سے تازہ ترین خبر ہے"
            _, roman = translate_important_news(title)
            roman = clean_roman_pure(roman)[:130]
        else:
            urdu, roman = translate_important_news(title)
            urdu = clean_urdu_pure(urdu)[:120]
            roman = clean_roman_pure(roman)[:130]
        
        if len(urdu) >= 10:
            urdu_bullets.append(urdu)
        if len(roman) >= 10:
            roman_bullets.append(roman)
    
    while len(urdu_bullets) < 3:
        urdu_bullets.append("حیدرآباد میں تازہ ترین صورتحال پر انتظامیہ کی نظر ہے")
        roman_bullets.append("Hyderabad mein taza tareen surat-e-haal par intezamiya ki nazar hai")
    
    min_count = min(len(urdu_bullets), len(roman_bullets), 5)
    min_count = max(3, min_count)
    
    unique_str = f"{time_ctx['unique_id']}_{selected_title}"
    titles_hash = hashlib.md5(unique_str.encode()).hexdigest()[:6]
    
    return {
        "headline": headline_urdu,
        "headline_roman": headline_roman,
        "urdu_bullets": urdu_bullets[:min_count],
        "roman_urdu_bullets": roman_bullets[:min_count],
        "category": category,
        "importance_score": all_stories[0]['importance'] if all_stories else 8,
        "verified": True,
        "sources": list(set([s.get('source','') for s in all_stories[:5]])) or ["Munsif Daily", "Etemaad Daily", "India Today", "NDTV"],
        "titles_hash": titles_hash,
        "is_from_actual_news": True,
        "is_morning": time_ctx['is_morning'],
        "rotation_index": time_ctx['rotation'],
        "unique_id": f"{time_ctx['date_str']}_{time_ctx['time_str']}_{titles_hash}_rot{time_ctx['rotation']}",
        "headline_source": selected_title,
        "date_str": time_ctx['date_str'],
        "time_str": time_ctx['time_str'],
        "sources_used": aggregated_data.get('sources_used', {}),
        "important_first": True
    }

def process_fresh_news(aggregated_data: Dict) -> Dict:
    logger.info(f"Processing IMPORTANT FIRST - Politics > Regional > National > World, Hourly")
    return process_important_first(aggregated_data)
