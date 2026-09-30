"""
National Reporter - Premium News Card Generator V3
- LARGER FONTS for readability (58px headline, 34px Urdu bullets, 24px Roman)
- Politics focused
- Better spacing, high contrast
"""
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import BRAND, FONTS, IMAGE_SIZE, ASSETS_DIR, OUTPUT_DIR, FONT_SIZES, CREDIT

logger = logging.getLogger(__name__)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception as e:
        logger.warning(f"Font load failed {path}: {e}")
        return ImageFont.load_default()

def reshape_for_naskh(text: str) -> str:
    if not HAS_BIDI:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def process_logo():
    logo_path = BRAND["logo_path"]
    try:
        logo = Image.open(logo_path).convert("RGBA")
        datas = logo.getdata()
        new_data = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        logo.putdata(new_data)
        return logo
    except Exception as e:
        logger.warning(f"Logo processing failed: {e}")
        return Image.open(logo_path).convert("RGBA")

def draw_borders(draw, w, h):
    gold = "#D4AF37"
    gold_dark = "#B8941F"
    gold_light = "#F4E4BC"
    draw.rectangle([(0,0),(w-1,h-1)], outline=gold, width=8)
    m = 20
    draw.rectangle([(m,m),(w-m-1,h-m-1)], outline=gold_dark, width=2)
    cl = 40
    ct = 4
    draw.line([(m,m),(m+cl,m)], fill=gold_light, width=ct)
    draw.line([(m,m),(m,m+cl)], fill=gold_light, width=ct)
    draw.line([(w-m-cl,m),(w-m,m)], fill=gold_light, width=ct)
    draw.line([(w-m,m),(w-m,m+cl)], fill=gold_light, width=ct)
    draw.line([(m,h-m),(m+cl,h-m)], fill=gold_light, width=ct)
    draw.line([(m,h-m-cl),(m,h-m)], fill=gold_light, width=ct)
    draw.line([(w-m-cl,h-m),(w-m,h-m)], fill=gold_light, width=ct)
    draw.line([(w-m,h-m-cl),(w-m,h-m)], fill=gold_light, width=ct)
    draw.rectangle([(30,30),(w-30,34)], fill=gold)

def wrap_text_simple(text, font, max_w, draw):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        test = f"{cur} {word}".strip()
        bbox = draw.textbbox((0,0), test, font=font)
        if bbox[2]-bbox[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

class NewsCardV3:
    def __init__(self):
        self.w, self.h = IMAGE_SIZE
        self.gold = "#D4AF37"
        self.gold_light = "#F4E4BC"
        self.gold_dark = "#B8941F"
        self.white = "#FFFFFF"
        self.gray = "#E0E0E0"  # Lighter for readability
        
        # LARGER FONTS - Updated for readability - Roman Urdu now equally large
        self.font_urdu_head = load_font(FONTS["urdu_nastaliq"], FONT_SIZES["headline_urdu"])  # 58px
        self.font_urdu_bullet = load_font(FONTS["urdu_naskh"], FONT_SIZES["urdu_bullet"])  # 36px - even larger
        self.font_poppins_bold = load_font(FONTS["poppins_bold"], FONT_SIZES["headline_english"])  # 44px
        self.font_poppins_semi = load_font(FONTS["poppins_semibold"], FONT_SIZES["section_title"])  # 30px
        self.font_poppins_reg = load_font(FONTS["poppins_regular"], FONT_SIZES["roman_bullet"])  # 28px - INCREASED
        self.font_poppins_roman_bold = load_font(FONTS["poppins_semibold"], FONT_SIZES["roman_bullet"])  # 28px SemiBold for Roman readability
        self.font_small = load_font(FONTS["poppins_regular"], FONT_SIZES["date_time"])  # 18px
        self.font_badge = load_font(FONTS["poppins_semibold"], FONT_SIZES["category_badge"])  # 22px
        self.font_footer = load_font(FONTS["poppins_regular"], FONT_SIZES["footer"])

    def generate(self, news_data, output_path=None):
        if output_path is None:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(OUTPUT_DIR / f"NR_News_{ts}.png")

        img = Image.new('RGB', (self.w, self.h), "#0A0A0A")
        draw = ImageDraw.Draw(img)
        draw_borders(draw, self.w, self.h)

        # Logo - larger and more premium + Permanent Credit after small logo
        try:
            logo = process_logo()
            logo.thumbnail((150,150), Image.LANCZOS)
            lx, ly = 50, 50
            draw.rounded_rectangle([(lx-5, ly-5), (lx+logo.width+5, ly+logo.height+5)], radius=10, fill="#1A1A1A", outline=self.gold_dark, width=1)
            img.paste(logo, (lx, ly), logo)
            draw.text((lx, ly+logo.height+10), "NATIONAL REPORTER", font=self.font_small, fill=self.gold_light)
            # Permanent Credit after small logo - Abu Aimak & Aimal Akram
            if CREDIT["show_in_image"]:
                credit_text = f"-- {CREDIT['name']}"
                draw.text((lx, ly+logo.height+30), credit_text, font=self.font_small, fill="#FFD700")  # Gold credit
        except Exception as e:
            logger.warning(f"Logo failed: {e}")
            draw.text((50,50), "NR", font=self.font_poppins_bold, fill=self.gold)
            if CREDIT["show_in_image"]:
                draw.text((50,95), f"-- {CREDIT['name']}", font=self.font_small, fill="#FFD700")

        # Date/Time - larger, top right
        date_str = news_data.get('date_str', datetime.now().strftime("%d %B %Y"))
        time_str = news_data.get('time_str', datetime.now().strftime("%I:%M %p"))
        dt_text = f"{date_str} | {time_str}"
        bbox = draw.textbbox((0,0), dt_text, font=self.font_small)
        draw.text((self.w-50-(bbox[2]-bbox[0]), 55), dt_text, font=self.font_small, fill=self.gray)

        # Category badge - larger, more prominent
        cat = news_data.get('category','Politics').upper()
        badge = f" {cat} • BREAKING "
        bbox = draw.textbbox((0,0), badge, font=self.font_badge)
        bw = bbox[2]-bbox[0]+24
        bh = bbox[3]-bbox[1]+14
        bx = self.w-50-bw
        by = 82
        draw.rounded_rectangle([(bx,by),(bx+bw,by+bh)], radius=8, fill=self.gold)
        draw.text((bx+12, by+6), badge.strip(), font=self.font_badge, fill="#000000")

        # Headline - MUCH LARGER, centered, gold, with better spacing
        headline = news_data.get('headline','اہم سیاسی خبر')
        is_urdu = any('\u0600' <= c <= '\u06FF' for c in headline)
        y = 230  # More space from logo
        max_w = self.w-100

        if is_urdu:
            lines = wrap_text_simple(headline, self.font_urdu_head, max_w, draw)
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=self.font_urdu_head)
                w = bbox[2]-bbox[0]
                x = (self.w-w)//2
                # Stronger shadow for readability
                draw.text((x+3, y+3), line, font=self.font_urdu_head, fill="#000000")
                draw.text((x, y), line, font=self.font_urdu_head, fill=self.gold)
                y += 70  # More line spacing
        else:
            lines = wrap_text_simple(headline, self.font_poppins_bold, max_w, draw)
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=self.font_poppins_bold)
                w = bbox[2]-bbox[0]
                x = (self.w-w)//2
                draw.text((x+3, y+3), line, font=self.font_poppins_bold, fill="#000000")
                draw.text((x, y), line, font=self.font_poppins_bold, fill=self.gold)
                y += 56

        # Divider
        dy = y+15
        draw.line([(80,dy),(self.w-80,dy)], fill="#444444", width=1)
        draw.line([(self.w//2-60,dy),(self.w//2+60,dy)], fill=self.gold_dark, width=3)
        y = dy+30

        # Urdu bullets - LARGER FONT, better readability - Show 3 max in image for readability, 3-5 in caption
        urdu_bullets = news_data.get('urdu_bullets',[])[:3]  # Show 3 in image for large font readability (3-5 in FB caption)
        title_urdu = "اہم نکات"
        bbox = draw.textbbox((0,0), title_urdu, font=self.font_poppins_semi)
        draw.text((self.w-80-(bbox[2]-bbox[0]), y), title_urdu, font=self.font_urdu_bullet, fill=self.gold_light)
        y += 48

        for bullet in urdu_bullets:
            if y > self.h-340:
                break
            dot_x = self.w-75
            draw.ellipse([(dot_x-5,y+16-5),(dot_x+5,y+16+5)], fill=self.gold)  # Larger dot
            max_text_w = self.w-170
            words = bullet.split()
            cur_line = ""
            lines = []
            for word in words:
                test = f"{cur_line} {word}".strip()
                bbox = draw.textbbox((0,0), reshape_for_naskh(test) if HAS_BIDI else test, font=self.font_urdu_bullet)
                if bbox[2]-bbox[0] <= max_text_w:
                    cur_line = test
                else:
                    if cur_line:
                        lines.append(cur_line)
                    cur_line = word
            if cur_line:
                lines.append(cur_line)

            for line in lines:
                reshaped_line = reshape_for_naskh(line) if HAS_BIDI else line
                bbox = draw.textbbox((0,0), reshaped_line, font=self.font_urdu_bullet)
                w = bbox[2]-bbox[0]
                x = self.w-100-w
                draw.text((x, y), reshaped_line, font=self.font_urdu_bullet, fill=self.white)
                y += 44  # More spacing for larger font
            y += 12

        y += 12
        draw.line([(80,y),(self.w-80,y)], fill="#333333", width=1)
        y += 18

        # Roman Urdu - LARGER & BOLDER for readability (28px SemiBold)
        draw.text((80,y), "ROMAN URDU SUMMARY", font=self.font_poppins_semi, fill=self.gold_light)
        y += 36

        roman_bullets = news_data.get('roman_urdu_bullets',[])[:3]  # Show 3 in image, 3-5 in caption for readability
        for bullet in roman_bullets:
            if y > self.h-90:
                break
            draw.text((80,y), "•", font=self.font_poppins_semi, fill=self.gold)
            max_w_roman = self.w-180
            words = bullet.split()
            cur = ""
            lines = []
            for w in words:
                test = f"{cur} {w}".strip()
                bbox = draw.textbbox((0,0), test, font=self.font_poppins_roman_bold)
                if bbox[2]-bbox[0] <= max_w_roman:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            
            for idx, line in enumerate(lines):
                if y > self.h-90:
                    break
                # Use SemiBold for better readability - 28px
                draw.text((108,y), line, font=self.font_poppins_roman_bold, fill="#FFFFFF")  # White for better contrast, not gray
                y += 32  # More spacing for larger font
            y += 10

        # Footer - Permanent Credit at end
        fy = self.h-65
        draw.rectangle([(0,fy),(self.w,self.h)], fill="#0F0F0F")
        draw.line([(0,fy),(self.w,fy)], fill=self.gold_dark, width=1)
        # Main footer with credit at end - Abu Aimak & Aimal Akram
        if CREDIT["show_in_footer"]:
            footer = f"© National Reporter | Verified News | {CREDIT['name']} | Hyderabad"
        else:
            footer = "© National Reporter | Verified News | Hyderabad, Telangana | Politics First"
        bbox = draw.textbbox((0,0), footer, font=self.font_footer)
        fx = (self.w-(bbox[2]-bbox[0]))//2
        draw.text((fx, fy+12), footer, font=self.font_footer, fill="#888888")
        # Small NR + Credit
        draw.text((50,fy+12), "NR", font=self.font_poppins_semi, fill=self.gold_dark)
        # Extra credit line at bottom for permanence
        credit_footer = f"-- {CREDIT['name']} | National Reporter Team"
        bbox2 = draw.textbbox((0,0), credit_footer, font=self.font_footer)
        fx2 = (self.w-(bbox2[2]-bbox2[0]))//2
        draw.text((fx2, fy+32), credit_footer, font=self.font_footer, fill=self.gold_dark)

        img.save(output_path, "PNG", quality=95, optimize=True)
        logger.info(f"Generated (Large Fonts): {output_path}")
        return output_path

def generate_news_card(news_data, output_path=None):
    gen = NewsCardV3()
    return gen.generate(news_data, output_path)

if __name__ == "__main__":
    test = {
        "headline": "تلنگانہ کی سیاست میں بڑی ہلچل، اہم فیصلے متوقع",
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
        "date_str": datetime.now().strftime("%d %B %Y"),
        "time_str": datetime.now().strftime("%I:%M %p")
    }
    print(generate_news_card(test))
