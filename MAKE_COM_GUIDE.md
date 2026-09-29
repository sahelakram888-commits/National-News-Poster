# Make.com Blueprint - National Reporter Automation

This guide shows step-by-step how to build the bot in Make.com without code.

## Scenario Overview (Every 2 Hours)

```
[Scheduling] -> [HTTP Fetch Munsif] -> [HTTP Fetch Etemaad] -> [HTTP Hyderabad] -> [HTTP Telangana]
       |
       v
[Text Aggregator - Combine Titles]
       |
       v
[OpenAI - GPT-4o-mini - Summarize to Urdu + Roman Urdu - NO LINKS]
       |
       v
[Bannerbear / APITemplate.io - Generate Black & Gold Card 1080x1080]
       |
       v
[Facebook Pages - Create Photo Post to National Reporter Page]
```

## Step 1: Create Scenario

1. Go to Make.com > Create new scenario
2. Name: "National Reporter - Every 2 Hours"

## Step 2: Trigger - Schedule

- Module: **Schedule** > **Every 2 hours**
- Or: **Schedule** > **At regular intervals** > 120 minutes
- First run: Immediately

## Step 3: Fetch News

Add 4x **HTTP > Make a request** modules in parallel:

### Module A: Munsif Home
- URL: `https://munsifdaily.com/`
- Method: GET
- Headers: User-Agent: Mozilla/5.0

### Module B: Etemaad English
- URL: `https://www.en.etemaaddaily.com/`
- Method: GET

### Module C: Hyderabad News
- URL: `https://munsifdaily.com/category/hyderabad-news/`

### Module D: Telangana News
- URL: `https://www.en.etemaaddaily.com/world/telangana`

For each, add **Text Parser > HTML to Text** or use regex to extract `<h2>, <h3>, <h4>` titles.

## Step 4: Aggregate & Clean (NO LINKS)

Add **Text Aggregator** or **Array Aggregator**:

- Combine all titles into one array
- Add **Text Parser > Replace** to enforce NO LINKS:
  - Pattern: `https?://\S+|www\.\S+|\[.*?\]\(.*?\)`
  - Replace with: empty string

Add **Array > Deduplicate** to remove duplicates.

## Step 5: OpenAI - AI Brain

Module: **OpenAI > Create a Chat Completion**

- Model: `gpt-4o-mini` or `gpt-4o`
- System prompt:

```
You are an expert Urdu news editor for 'National Reporter' - premium black & gold brand.

From provided news titles, select TOP 1-2 most important breaking news (prefer Hyderabad, Telangana, then India).

Output JSON only:
{
  "headline": "Brief impactful headline in Urdu (max 12 words)",
  "headline_roman": "Same headline in Roman Urdu",
  "urdu_bullets": ["3-5 bullets pure Urdu script Nastaliq, each 12-20 words"],
  "roman_urdu_bullets": ["Exact same 3-5 bullets but in Roman Urdu (Urdu in English alphabets, e.g., 'Hyderabad mein...')"],
  "category": "Hyderabad/Telangana/India/World/Regional"
}

STRICT:
- Absolutely NO hyperlinks, URLs, links
- Urdu bullets pure Urdu script (اردو)
- Roman Urdu is Urdu written in English letters, NOT English translation
- Professional, concise, informative
- No emojis in JSON
```

- User prompt: `Summarize these news into Urdu + Roman Urdu JSON (NO LINKS): {{titles}}`

- Response format: JSON Object

## Step 6: Card Creator - Bannerbear

### Setup Bannerbear Template (One-time)

1. Go to Bannerbear.com > Create Template > 1080x1080
2. Design:
   - Background: #0A0A0A
   - Border: 8px #D4AF37 outer, 2px #B8941F inner
   - Upload NR logo (silver/gold) to top-left corner
   - Add text layers:
     - `headline` - Noto Nastaliq Urdu Bold 42px, color #D4AF37, center
     - `headline_roman` - Poppins SemiBold 18px, #F4E4BC
     - `urdu_bullets` - Noto Nastaliq Urdu Regular 26px, white, right-aligned
     - `roman_bullets` - Poppins Regular 19px, #A0A0A0, left-aligned
     - `date_time` - Poppins Regular 15px, #A0A0A0, top-right
     - `category` - Poppins Bold 16px, black on gold badge
   - Add corner accents: small L shapes #F4E4BC at inner border corners
   - Add footer: #0F0F0F with gold top line, text "© National Reporter | Premium News"
3. Save Template ID

### In Make.com

Module: **Bannerbear > Create an Image**

- Template: Your template ID
- Modifications:
  - `headline`: `{{openai.headline}}`
  - `headline_roman`: `{{openai.headline_roman}}`
  - `urdu_bullets`: `{{join(openai.urdu_bullets, newline + "• ")}}`
  - `roman_bullets`: `{{join(openai.roman_urdu_bullets, newline + "• ")}}`
  - `date_time`: `{{formatDate(now; "DD MMMM YYYY | hh:mm A")}}`
  - `category`: `{{openai.category}}`
  - `logo`: URL to hosted NR logo (upload to Imgur or Bannerbear)

Wait for image generation (use Sleep module 5 sec if needed).

### Alternative: APITemplate.io

Similar, use HTML template from `templates/news_card.html`:
- Create template in APITemplate.io
- Paste HTML, add dynamic fields `{{headline}}`, etc.
- Upload logo
- API will return image URL

### Alternative: Self-hosted Puppeteer (Free)

Use **Make.com > HTTP > Make a request** to your own server:
- Server runs Puppeteer that renders `templates/news_card.html` with data
- Returns image URL

## Step 7: Facebook Poster

Module: **Facebook Pages > Create a Post** or **Upload a Photo**

Option A: **Create a Post with Photo** (preferred)
- Connection: Connect your Facebook account, select Page "National Reporter" (100085918100245)
- Photo: Map image URL from Bannerbear (`image_url`)
- Message:

```
📰 {{headline}}
{{headline_roman}}

━━━━━━━━━━━━━━━━━━━━
📍 اردو میں اہم نکات:
• {{join(urdu_bullets; "\n• ")}}

━━━━━━━━━━━━━━━━━━━━
📍 Roman Urdu Summary:
• {{join(roman_urdu_bullets; "\n• ")}}

━━━━━━━━━━━━━━━━━━━━
🏷️ Category: {{category}}
🕒 {{date_time}}

#NationalReporter #NR #Hyderabad #Telangana #UrduNews #BreakingNews
```

- **Important:** Ensure message has NO `http` or `www` - double check with Text Parser Replace before.

Option B: **Facebook Pages > Upload a Photo**
- Same mapping, but upload binary if you downloaded image

## Step 8: Error Handling & Filters

- Add **Error Handler** > Ignore or Resume for scraping failures
- Add **Filter** after OpenAI: only continue if `headline` exists
- Add **Data Store** in Make.com to avoid duplicate posts (store last 10 headlines, check if new headline already posted)

## Step 9: Activate

- Set scheduling to every 2 hours
- Save and activate scenario
- Test with "Run once"

## Hosting Logo

Upload NR logo to:
- Imgur, or
- Your website, or
- Bannerbear media library
- Use direct URL: `https://i.imgur.com/xxxx.png`

## Cost Estimate (Make.com)

- Operations per run: ~10-12
- Runs per day: 12 (every 2 hours)
- Per month: ~360-432 ops
- Make.com Free: 1000 ops/month → enough
- OpenAI: ~$0.01 per run (gpt-4o-mini)
- Bannerbear: Free 30 images/month, then $49/month - alternative use APITemplate.io free tier or self-hosted

## Self-hosted Free Alternative

Instead of Bannerbear, host Python image generator on:
- Render.com (free tier)
- Railway
- Your VPS

Create simple Flask API:

```python
@app.route('/generate', methods=['POST'])
def generate():
  data = request.json
  path = generate_news_card(data)
  return send_file(path)
```

Then in Make.com, HTTP POST to your API with JSON, get image URL.

---

Done! Your bot will post every 2 hours automatically.
