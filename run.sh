#!/bin/bash
# National Reporter - Runner Script
set -e

echo "📰 National Reporter - AI Agent"
echo "Premium Black & Gold | NR Logo"
echo "=================================="

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Check python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found, creating from example..."
    cp .env.example .env
    echo "✏️  Please edit .env with your OPENAI_API_KEY and FACEBOOK tokens"
fi

# Ensure output dir
mkdir -p output
mkdir -p assets/fonts

# Parse args
MODE=${1:-once}

if [ "$MODE" == "once" ]; then
    echo "▶️  Running once..."
    python3 src/main.py --once
elif [ "$MODE" == "schedule" ]; then
    echo "⏰ Running scheduler every 2 hours..."
    python3 src/main.py --schedule
elif [ "$MODE" == "test-image" ]; then
    echo "🖼️  Testing image generation..."
    python3 src/main.py --test-image
    echo "✅ Check output/ folder"
elif [ "$MODE" == "test-scrape" ]; then
    echo "🔍 Testing scraper..."
    python3 src/scraper.py
elif [ "$MODE" == "install-fonts" ]; then
    echo "🔤 Fonts already in assets/fonts"
    ls -lh assets/fonts/
else
    echo "Usage: ./run.sh [once|schedule|test-image|test-scrape]"
    echo "  once        - Run one full cycle (default)"
    echo "  schedule    - Run every 2 hours infinitely"
    echo "  test-image  - Test only image generation"
    echo "  test-scrape - Test only scraping"
fi
