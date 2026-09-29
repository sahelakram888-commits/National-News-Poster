"""
National Reporter - Premium News Card Generator V2
Fixed Urdu rendering: Noto Nastaliq without reshaping, Noto Naskh with reshaping
"""
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import BRAND, FONTS, IMAGE_SIZE, ASSETS_DIR, OUTPUT_DIR

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
    """Only for Naskh font - uses reshaper"""
    if not HAS_BIDI:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except:
        return text

def process_logo():
    """Process logo to remove white background and make premium"""
    logo_path = BRAND["logo_path"]
    try:
        logo = Image.open(logo_path).convert("RGBA")
        # Remove white background: make near-white pixels transparent
        datas = logo.getdata()
        new_data = []
        for item in datas:
            # If pixel is very light (white background), make transparent
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
    # Outer
    draw.rectangle([(0,0),(w-1,h-1)], outline=gold, width=8)
    # Inner
    m = 20
    draw.rectangle([(m,m),(w-m-1,h-m-1)], outline=gold_dark, width=2)
    # Corners
    cl = 40
    ct = 4
    # TL
    draw.line([(m,m),(m+cl,m)], fill=gold_light, width=ct)
    draw.line([(m,m),(m,m+cl)], fill=gold_light, width=ct)
    # TR
    draw.line([(w-m-cl,m),(w-m,m)], fill=gold_light, width=ct)
    draw.line([(w-m,m),(w-m,m+cl)], fill=gold_light, width=ct)
    # BL
    draw.line([(m,h-m),(m+cl,h-m)], fill=gold_light, width=ct)
    draw.line([(m,h-m-cl),(m,h-m)], fill=gold_light, width=ct)
    # BR
    draw.line([(w-m-cl,h-m),(w-m,h-m)], fill=gold_light, width=ct)
    draw.line([(w-m,h-m-cl),(w-m,h-m)], fill=gold_light, width=ct)
    # Top accent
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

class NewsCardV2:
    def __init__(self):
        self.w, self.h = IMAGE_SIZE
        self.gold = "#D4AF37"
        self.gold_light = "#F4E4BC"
        self.gold_dark = "#B8941F"
        self.white = "#FFFFFF"
        self.gray = "#A0A0A0"
        # Fonts - use Naskh for reliable Urdu with reshaper, Nastaliq for headline without reshaper
        self.font_urdu_head = load_font(FONTS["urdu_nastaliq"], 44)  # No reshaping
        self.font_urdu_bullet = load_font(FONTS["urdu_naskh"], 26)  # Will use reshaping
        self.font_poppins_bold = load_font(FONTS["poppins_bold"], 34)
        self.font_poppins_semi = load_font(FONTS["poppins_semibold"], 20)
        self.font_poppins_reg = load_font(FONTS["poppins_regular"], 19)
        self.font_small = load_font(FONTS["poppins_regular"], 15)

    def generate(self, news_data, output_path=None):
        if output_path is None:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(OUTPUT_DIR / f"NR_News_{ts}.png")

        img = Image.new('RGB', (self.w, self.h), "#0A0A0A")
        draw = ImageDraw.Draw(img)
        draw_borders(draw, self.w, self.h)

        # Logo
        try:
            logo = process_logo()
            logo.thumbnail((130,130), Image.LANCZOS)
            # Add subtle gold background circle behind logo for premium
            # Draw gold rounded rect behind logo
            lx, ly = 50, 50
            # Background for logo visibility
            draw.rounded_rectangle([(lx-5, ly-5), (lx+logo.width+5, ly+logo.height+5)], radius=8, fill="#1A1A1A", outline=self.gold_dark, width=1)
            img.paste(logo, (lx, ly), logo)
            draw.text((lx, ly+logo.height+8), "NATIONAL REPORTER", font=self.font_small, fill=self.gold_light)
        except Exception as e:
            logger.warning(f"Logo failed: {e}")
            draw.text((50,50), "NR", font=self.font_poppins_bold, fill=self.gold)

        # Date/Time top right
        date_str = news_data.get('date_str', datetime.now().strftime("%d %B %Y"))
        time_str = news_data.get('time_str', datetime.now().strftime("%I:%M %p"))
        dt_text = f"{date_str} | {time_str}"
        bbox = draw.textbbox((0,0), dt_text, font=self.font_small)
        draw.text((self.w-50-(bbox[2]-bbox[0]), 55), dt_text, font=self.font_small, fill=self.gray)

        # Category badge
        cat = news_data.get('category','Hyderabad').upper()
        badge = f" {cat} • BREAKING "
        bbox = draw.textbbox((0,0), badge, font=self.font_poppins_semi)
        bw = bbox[2]-bbox[0]+20
        bh = bbox[3]-bbox[1]+12
        bx = self.w-50-bw
        by = 78
        draw.rounded_rectangle([(bx,by),(bx+bw,by+bh)], radius=6, fill=self.gold)
        draw.text((bx+10, by+5), badge.strip(), font=self.font_poppins_semi, fill="#000000")

        # Headline - center, gold
        headline = news_data.get('headline','اہم خبر')
        is_urdu = any('\u0600' <= c <= '\u06FF' for c in headline)
        y = 210
        max_w = self.w-100

        if is_urdu:
            # For Nastaliq, DO NOT reshape, render as is, but right to left visual will be handled by font
            # We'll wrap without reshaping
            lines = wrap_text_simple(headline, self.font_urdu_head, max_w, draw)
            for line in lines:
                # For Nastaliq, keep original (no reshaping)
                bbox = draw.textbbox((0,0), line, font=self.font_urdu_head)
                w = bbox[2]-bbox[0]
                x = (self.w-w)//2
                draw.text((x+2, y+2), line, font=self.font_urdu_head, fill="#000000")
                draw.text((x, y), line, font=self.font_urdu_head, fill=self.gold)
                y += 58
        else:
            lines = wrap_text_simple(headline, self.font_poppins_bold, max_w, draw)
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=self.font_poppins_bold)
                w = bbox[2]-bbox[0]
                x = (self.w-w)//2
                draw.text((x+2, y+2), line, font=self.font_poppins_bold, fill="#000000")
                draw.text((x, y), line, font=self.font_poppins_bold, fill=self.gold)
                y += 46

        # Divider
        dy = y+10
        draw.line([(80,dy),(self.w-80,dy)], fill="#333333", width=1)
        draw.line([(self.w//2-50,dy),(self.w//2+50,dy)], fill=self.gold_dark, width=2)
        y = dy+25

        # Urdu bullets - use Naskh with reshaping for reliable rendering
        urdu_bullets = news_data.get('urdu_bullets',[])[:4]
        # Section title
        title_urdu = "اہم نکات"
        # For title, use Nastaliq without reshaping
        bbox = draw.textbbox((0,0), title_urdu, font=self.font_urdu_bullet)
        # Right align
        draw.text((self.w-80-(bbox[2]-bbox[0]), y), title_urdu, font=self.font_urdu_bullet, fill=self.gold_light)
        y += 38

        for bullet in urdu_bullets:
            if y > self.h-320:
                break
            # Gold dot right side
            dot_x = self.w-75
            draw.ellipse([(dot_x-4,y+12-4),(dot_x+4,y+12+4)], fill=self.gold)
            # Wrap and reshape each line for Naskh
            max_text_w = self.w-160
            # First wrap using original text measurement (approx)
            # For wrapping Urdu with reshaping, we need to wrap original then reshape lines
            words = bullet.split()
            cur_line = ""
            lines = []
            for word in words:
                test = f"{cur_line} {word}".strip()
                # Measure with Naskh font (use reshaped for accurate width? use original for simplicity)
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
                x = self.w-95-w
                draw.text((x, y), reshaped_line, font=self.font_urdu_bullet, fill=self.white)
                y += 34
            y += 8

        y += 8
        draw.line([(80,y),(self.w-80,y)], fill="#222222", width=1)
        y += 14

        # Roman Urdu
        draw.text((80,y), "ROMAN URDU SUMMARY", font=self.font_poppins_semi, fill=self.gold_light)
        y += 26

        roman_bullets = news_data.get('roman_urdu_bullets',[])[:4]
        for bullet in roman_bullets:
            if y > self.h-80:
                break
            draw.text((80,y), "•", font=self.font_poppins_semi, fill=self.gold)
            # Wrap
            max_w_roman = self.w-160
            words = bullet.split()
            cur = ""
            lines = []
            for w in words:
                test = f"{cur} {w}".strip()
                bbox = draw.textbbox((0,0), test, font=self.font_poppins_reg)
                if bbox[2]-bbox[0] <= max_w_roman:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            
            for idx, line in enumerate(lines):
                if y > self.h-80:
                    break
                if idx==0:
                    draw.text((100,y), line, font=self.font_poppins_reg, fill=self.gray)
                else:
                    draw.text((100,y), line, font=self.font_poppins_reg, fill=self.gray)
                y += 22
            y += 6

        # Footer
        fy = self.h-55
        draw.rectangle([(0,fy),(self.w,self.h)], fill="#0F0F0F")
        draw.line([(0,fy),(self.w,fy)], fill=self.gold_dark, width=1)
        footer = "© National Reporter | Premium News | Hyderabad, Telangana"
        bbox = draw.textbbox((0,0), footer, font=self.font_small)
        fx = (self.w-(bbox[2]-bbox[0]))//2
        draw.text((fx, fy+15), footer, font=self.font_small, fill="#666666")
        draw.text((50,fy+15), "NR", font=self.font_poppins_semi, fill=self.gold_dark)

        img.save(output_path, "PNG", quality=95, optimize=True)
        logger.info(f"Generated: {output_path}")
        return output_path

def generate_news_card(news_data, output_path=None):
    gen = NewsCardV2()
    return gen.generate(news_data, output_path)

if __name__ == "__main__":
    test = {
        "headline": "حیدرآباد میں بڑی کارروائی، پولیس کی اہم پیش رفت",
        "urdu_bullets": [
            "حیدرآباد کے ایس آر نگر میں مشتبہ حالات میں خاتون کی لاش برآمد ہوئی ہے",
            "پولیس نے واقعے کی تحقیقات شروع کر دی ہیں اور شواہد اکٹھے کیے جا رہے ہیں",
            "مقامی لوگوں میں اس واقعے کے بعد تشویش کی لہر دوڑ گئی ہے",
            "تلنگانہ میں انتظامیہ نے عوام سے امن برقرار رکھنے کی اپیل کی ہے"
        ],
        "roman_urdu_bullets": [
            "Hyderabad ke SR Nagar mein mushtaba halaat mein khatoon ki laash baramad hui hai",
            "Police ne waqiye ki tehqiqaat shuru kar di hain aur shawahid ikatthe kiye ja rahe hain",
            "Maqami logon mein is waqiye ke baad tashweesh ki leher daud gayi hai",
            "Telangana mein intezamiya ne awaam se aman barqarar rakhne ki appeal ki hai"
        ],
        "category": "Hyderabad",
        "date_str": datetime.now().strftime("%d %B %Y"),
        "time_str": datetime.now().strftime("%I:%M %p")
    }
    print(generate_news_card(test))
