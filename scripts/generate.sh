#!/usr/bin/env bash
# Runs the tweet generation workflow locally.
# Scrapes RSS feeds, ranks items, generates drafts via Gemini, and sends them to Telegram.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✔ $*${NC}"; }
warn() { echo -e "${YELLOW}! $*${NC}"; }
fail() { echo -e "${RED}✘ $*${NC}"; exit 1; }

echo "=== generate workflow ==="

# 1. Must run from project root
[ -f "pyproject.toml" ] || fail "Run this script from the project root."

# 2. .env must exist
[ -f ".env" ] || fail ".env not found. Copy .env.example and fill in your credentials."

# 3. Load environment variables
set -a
# shellcheck source=/dev/null
source .env
set +a
ok ".env loaded"

# 4. Check required variables
REQUIRED=(GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID)
MISSING=()
for var in "${REQUIRED[@]}"; do
    [ -n "${!var:-}" ] || MISSING+=("$var")
done
[ ${#MISSING[@]} -eq 0 ] || fail "Missing env vars: ${MISSING[*]}"
ok "Environment variables present"

# 5. Check Python dependencies
python -c "from google import genai; import feedparser, httpx, pydantic, tweepy" 2>/dev/null \
    || fail "Python dependencies missing. Run: pip install -r requirements.txt"
ok "Python dependencies available"

# 6. Ensure data/state.json exists
if [ ! -f "data/state.json" ]; then
    warn "data/state.json not found — creating empty state"
    mkdir -p data
    echo '{}' > data/state.json
fi
ok "State file ready"

echo ""
python -m src.workflows.generate
