# ✅ Deployment Checklist - National Reporter

## What Was Built

✅ **Python AI Agent** - Fully working
- Scrapes Munsif Daily (https://munsifdaily.com/) + categories Hyderabad/Telangana/India/World
- Scrapes Etemaad Daily (https://www.en.etemaaddaily.com/) + categories
- Aggregated 58 unique stories in last test
- **NO LINKS** enforced at 3 levels

✅ **AI Processing Engine** (GPT-4)
- Selects top 1-2 important stories
- Outputs: Headline (Urdu), Urdu bullets 3-5, Roman Urdu bullets 3-5
- Prompt enforces NO LINKS, pure Urdu script + Roman Urdu

✅ **Image Generation - Premium Black & Gold**
- 1080x1080 card
- Black background #0A0A0A + gold border #D4AF37 double + corner accents #F4E4BC
- NR logo top-left with transparent background + gold border
- Date/Time top-right + Category badge BREAKING gold pill
- Headline centered gold Nastaliq 44px
- Urdu bullets right-aligned Naskh 26px white + gold dots (with arabic-reshaper + bidi)
- Roman Urdu left-aligned Poppins 19px gray
- Footer premium
- **Tested & Working** - see output/ folder

✅ **Facebook Publisher**
- Graph API v20.0 POST /{page-id}/photos
- Caption: Urdu + Roman Urdu + hashtags, NO LINKS
- Simulated mode if no token, saves .txt

✅ **Scheduler**
- Every 2 hours via APScheduler or cron
- `run.sh schedule` or systemd or Docker

✅ **No-Code Workflows**
- n8n_workflow.json ready to import
- MAKE_COM_GUIDE.md step-by-step
- templates/news_card.html for Bannerbear/APITemplate.io

## Files Ready

- src/main.py --once / --schedule / --test-image
- src/scraper.py, processor.py, image_generator.py, facebook_publisher.py, config.py
- templates/news_card.html
- assets/logo.png + fonts (Noto Nastaliq, Noto Naskh, Poppins)
- n8n_workflow.json
- requirements.txt, .env.example, run.sh, README.md, MAKE_COM_GUIDE.md
- Dockerfile, docker-compose.yml, systemd service

## Next Steps for You

1. **Add API Keys in .env**
```
OPENAI_API_KEY=sk-...
FACEBOOK_PAGE_ID=100085918100245
FACEBOOK_PAGE_ACCESS_TOKEN=EAAG...
```

2. **Get Facebook Token**
- developers.facebook.com > Your App > Graph API Explorer
- Permissions: pages_manage_posts, pages_read_engagement, pages_show_list
- Generate Page Token for National Reporter page
- Extend to long-lived (60 days) - or use system user token for permanent

3. **Test**
```
./run.sh once
```
Check output/ folder for PNG + TXT

4. **Deploy Scheduler**
- Option A: Local: `./run.sh schedule` (keeps running)
- Option B: Server: Use systemd service or Docker
```
sudo cp systemd/national-reporter.service /etc/systemd/system/
sudo systemctl enable national-reporter --now
```
- Option C: n8n/Make.com - import workflow, set credentials, activate

5. **Optional: Improve Urdu**
- Already using arabic-reshaper + bidi + Noto Naskh/Nastaliq
- If need even better Nastaliq, host HTML template with Puppeteer (renders in Chrome, perfect Urdu)

## Live Test Result (29 Sep 2026)

Scraped: 58 stories
Selected: Hyderabad - "Cab driver attempts to sexually assault woman in Hyderabad"
Generated: output/NR_News_20260929_114310.png (95KB)
Post Text: output/NR_News_20260929_114310.txt - NO LINKS verified

## Facebook Page

https://www.facebook.com/profile.php?id=100085918100245

Ready to post every 2 hours once token added.

## Support

- All code documented
- NO LINKS constraint enforced everywhere
- Brand: Premium Black & Gold, NR logo top corner, Nastaliq + sans-serif
