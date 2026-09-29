# National Reporter - AI News Poster (24/7 Automated)

Premium Black & Gold news poster that auto-publishes to Facebook every 2 hours.

**Page:** https://www.facebook.com/239472476226069 (502K followers)

## Features
- ✅ Scrapes Munsif Daily & Etemaad Daily ONLY (Urdu dailies)
- ✅ Politics preferred, 3-5 bullets, Verified only, No fake news
- ✅ Larger fonts: Headline 58px, Urdu 36px, Roman 28px Bold White
- ✅ Premium 1080x1080 black & gold cards with NR logo
- ✅ Morning 6-11 AM covers all categories, day/night politics focus
- ✅ Posts every 2 hours via GitHub Actions (24/7)

## Setup Secrets in GitHub
Go to Repo → Settings → Secrets and variables → Actions → New repository secret:

- `FACEBOOK_PAGE_ID` = `239472476226069`
- `FACEBOOK_PAGE_ACCESS_TOKEN` = Your Page Access Token (long-lived)
- `OPENAI_API_KEY` = Your OpenAI key (optional, uses mock if empty)

Then enable Actions - it will run every 2 hours automatically!

## Local Run
```bash
cp .env.example .env
# Edit .env
pip install -r requirements.txt
python src/main.py --once
python src/main.py --schedule  # Every 2 hours
```

## Workflow
Schedule (2h) → Scrape Munsif/Etemaad → GPT-4 Urdu+Roman → Generate Card → Facebook Graph API
