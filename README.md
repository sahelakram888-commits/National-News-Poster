# 📰 National Reporter - AI News Poster Agent

**Premium Black & Gold Theme | NR Logo | Automated Every 2 Hours**

Automated AI agent that publishes news updates to the **National Reporter** Facebook page:  
https://www.facebook.com/profile.php?id=100085918100245

![NR Logo](assets/logo.png)

---

## 🎯 Objective

Build an automated AI agent that:
1. Scrapes top stories from **Munsif Daily** & **Etemaad Daily** + Hyderabad, Telangana, India, World, Regional
2. Processes with **GPT-4** into Urdu + Roman Urdu bullets (NO LINKS)
3. Generates **1080x1080 premium black & gold news card** with NR logo
4. Publishes to Facebook Page via **Graph API** every 2 hours

---

## 🏛️ Brand Identity

- **Name:** National Reporter
- **Logo:** Silver & Gold NR (provided)
- **Theme:** Premium black `#0A0A0A` + gold `#D4AF37` + gold light `#F4E4BC`
- **Tone:** Professional, concise, informative

---

## 📁 Project Structure

```
national-reporter-agent/
├── src/
│   ├── config.py              # Brand, sources, API keys
│   ├── scraper.py             # Munsif + Etemaad + categories
│   ├── processor.py           # GPT-4 Urdu + Roman Urdu
│   ├── image_generator.py     # 1080x1080 black/gold card
│   ├── facebook_publisher.py  # Graph API poster
│   └── main.py                # Orchestrator + scheduler
├── templates/
│   └── news_card.html         # HTML template for Bannerbear/APITemplate.io
├── assets/
│   ├── logo.png               # NR logo
│   └── fonts/
│       ├── NotoNastaliqUrdu-Regular.ttf
│       ├── Poppins-Bold.ttf etc.
├── output/                    # Generated cards
├── n8n_workflow.json          # No-code workflow for n8n
├── requirements.txt
├── .env.example
├── run.sh
└── README.md
```

---

## 🚀 Quick Start (Python Agent)

### 1. Setup

```bash
git clone <repo>
cd national-reporter-agent
cp .env.example .env
# Edit .env with your keys
chmod +x run.sh
./run.sh once
```

### 2. Get API Keys

#### OpenAI (GPT-4)
- Go to https://platform.openai.com/api-keys
- Create key, set `OPENAI_API_KEY` in `.env`

#### Facebook Graph API
1. Go to https://developers.facebook.com/
2. Create App > Business > Connect Facebook Page
3. Add **Graph API Explorer**:
   - Permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`, `public_profile`
   - Select your Page: National Reporter (100085918100245)
   - Generate **Page Access Token** (long-lived)
4. Set in `.env`:
   ```
   FACEBOOK_PAGE_ID=100085918100245
   FACEBOOK_PAGE_ACCESS_TOKEN=EAAG...
   ```

### 3. Run Modes

```bash
./run.sh once          # Run one cycle now
./run.sh schedule      # Run every 2 hours forever
./run.sh test-image    # Test only card generation
./run.sh test-scrape   # Test only scraping
```

Or directly:

```bash
python src/main.py --once
python src/main.py --schedule
python src/main.py --test-image
```

---

## 🔄 Workflow Details

### 1. Scraping & Aggregation (Every 2 Hours)

**Sources:**
- `https://munsifdaily.com/` + categories: Hyderabad, Telangana, India, World
- `https://www.en.etemaaddaily.com/` + categories: Hyderabad, Telangana, National, International

**Implementation:** `src/scraper.py`
- Uses `requests` + `BeautifulSoup`
- Deduplicates by title
- **Constraint:** Strips ALL hyperlinks before output

### 2. Content Processing (AI Engine)

**Prompt used (GPT-4):**

```
You are an expert Urdu news editor for 'National Reporter'...
Select TOP 1-2 most important breaking news...
Output JSON:
{
  "headline": "Urdu headline max 12 words",
  "headline_roman": "Roman Urdu",
  "urdu_bullets": ["3-5 bullets pure Urdu script"],
  "roman_urdu_bullets": ["Same in Roman Urdu"],
  "category": "Hyderabad/Telangana/India/World"
}
STRICT: NO hyperlinks, NO URLs...
```

**Implementation:** `src/processor.py`

Output example:

```json
{
  "headline": "حیدرآباد میں بڑی کارروائی، پولیس کی اہم پیش رفت",
  "headline_roman": "Hyderabad Mein Badi Karwai, Police Ki Aham Pesh Raft",
  "urdu_bullets": [
    "حیدرآباد کے ایس آر نگر میں مشتبہ حالات میں خاتون کی لاش برآمد",
    "پولیس نے تحقیقات شروع کر دی ہیں",
    "مقامی لوگوں میں تشویش کی لہر"
  ],
  "roman_urdu_bullets": [
    "Hyderabad ke SR Nagar mein mushtaba halaat mein laash baramad",
    "Police ne tehqiqaat shuru kar di",
    "Maqami logon mein tashweesh ki leher"
  ]
}
```

### 3. Image Generation (The News Card)

**Design Specs:**
- Size: **1080x1080** (also supports 1200x630)
- Background: Premium black `#0A0A0A`
- Border: 8px outer gold `#D4AF37` + 2px inner `#B8941F` + corner accents `#F4E4BC`
- Top: 4px gold gradient bar
- **Elements:**
  - NR logo top-left (140px)
  - Date/Time top-right
  - Category badge gold pill top-right
  - Headline centered, gold, 42px Nastaliq/Bold
  - Divider with gold accent
  - Urdu bullets: right-aligned, Nastaliq 28px, white, gold dot
  - Roman Urdu bullets: left-aligned, Poppins 20px, gray, gold bullet
  - Footer: black `#0F0F0F` + gold line + copyright

**Implementation:**
- **Python:** `src/image_generator.py` uses Pillow + `arabic-reshaper` + `python-bidi` for perfect Urdu RTL
- **No-code alternative:** `templates/news_card.html` for Bannerbear / APITemplate.io / Puppeteer

**Fonts:**
- Urdu: Noto Nastaliq Urdu (Google Fonts)
- Roman Urdu: Poppins Regular/SemiBold/Bold

### 4. Publishing to Facebook

**Endpoint:** `POST /{page-id}/photos` with `caption` + `source` (image file)

**Implementation:** `src/facebook_publisher.py`

Post format:

```
📰 [Headline Urdu]
[Headline Roman]

━━━━━━━━━━━━━━━━━━━━
📍 اردو میں اہم نکات:
• [Urdu bullet 1]
• ...

━━━━━━━━━━━━━━━━━━━━
📍 Roman Urdu Summary:
• [Roman bullet 1]
• ...

━━━━━━━━━━━━━━━━━━━━
🏷️ Category: Hyderabad
🕒 29 September 2026 | 05:30 PM

#NationalReporter #NR #Hyderabad...
```

**NO LINKS** - enforced via regex cleaning.

---

## 🔧 No-Code Implementation (Make.com / n8n)

### Option A: n8n (Recommended, self-hosted)

1. Import `n8n_workflow.json` into n8n
2. Setup credentials:
   - OpenAI API
   - Facebook Graph API (Page Token)
   - Bannerbear API (or APITemplate.io)
3. Create Bannerbear template:
   - Background black, gold borders
   - Upload NR logo
   - Add fields: `headline`, `headline_roman`, `urdu_bullets`, `roman_bullets`, `date_time`, `category`
   - Fonts: Noto Nastaliq Urdu for Urdu, Poppins for Roman
4. Activate workflow - runs every 2 hours

**Nodes:**
Schedule (2h) → HTTP Munsif + Etemaad + Hyderabad + Telangana → Merge → Code Clean (NO LINKS) → OpenAI GPT-4 → Validate → Bannerbear Image → Facebook Graph API Post

### Option B: Make.com

Same flow visually:

1. **Trigger:** Schedule every 2 hours
2. **HTTP modules:** Fetch Munsif, Etemaad, categories
3. **Text Aggregator:** Combine titles
4. **OpenAI module:** Prompt as above
5. **Bannerbear / APITemplate.io module:** Fill template
6. **Facebook Pages module:** Create a Photo Post
   - Connect Page 100085918100245
   - Map image URL + caption
   - Ensure caption has NO links

**Make.com Blueprint Tips:**
- Use `replace(http://* ; empty)` to enforce NO LINKS
- For Urdu font in Bannerbear, upload Noto Nastaliq Urdu TTF
- Set image size 1080x1080

---

## 🛡️ Constraints Enforcement

- **NO LINKS** checked at 3 levels:
  1. `scraper.py` `clean_text()` removes URLs
  2. `processor.py` `clean_no_links()` + prompt instruction
  3. `facebook_publisher.py` `format_post_text()` final regex
- All output JSON validated

---

## 📸 Sample Output

Generated card includes:
- Black background, golden double border with corner L-accents
- NR logo top-left
- Date/time top-right
- Breaking badge
- Headline gold centered
- Urdu bullets (Nastaliq, white, right-aligned, gold dots)
- Roman bullets (Poppins, gray, left-aligned)
- Footer

Check `output/` folder after test run.

---

## 🔐 Environment Variables

See `.env.example` - required:

```
OPENAI_API_KEY
FACEBOOK_PAGE_ID=100085918100245
FACEBOOK_PAGE_ACCESS_TOKEN
```

Optional: `OPENAI_MODEL=gpt-4o-mini`

---

## 🐛 Troubleshooting

- **Urdu rendering boxes:** Install fonts in `assets/fonts/` and ensure `arabic-reshaper` + `python-bidi` installed
- **Facebook token expired:** Generate long-lived token (60 days) via Graph API Explorer > Extend
- **Scraping blocked:** Sites may change structure - update selectors in `scraper.py`
- **No stories:** Check internet, or fallback to mock data in processor

---

## 📅 Scheduling

- **Python:** APScheduler every 2 hours, or cron: `0 */2 * * * /path/to/run.sh once`
- **n8n/Make:** Built-in schedule node
- **Systemd:** Create service + timer

---

## 🤝 Credits

- Brand: National Reporter (NR)
- Logo: Silver & Gold NR
- Sources: Munsif Daily, Etemaad Daily
- Stack: Python, OpenAI GPT-4, Pillow, Facebook Graph API v20.0, n8n/Make.com

---

## 📄 License

Private for National Reporter Facebook Page.

**Page:** https://www.facebook.com/profile.php?id=100085918100245
