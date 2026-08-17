"""
config.py — HinduDevGyan Reel Engine
Central configuration: API keys, paths, brand settings, reel parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in reel_engine dir first, then parent dir
_this_dir = Path(__file__).parent
load_dotenv(dotenv_path=_this_dir / ".env")           # reel_engine/.env
load_dotenv(dotenv_path=_this_dir.parent / ".env")    # project root .env (fallback)

# ──────────────────────────────────────────────
# API KEYS
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_CLIENT_SECRET_PATH = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent   # project root (alongside main.py)
REEL_ENGINE_DIR = Path(__file__).parent

ASSETS_DIR      = REEL_ENGINE_DIR / "assets"
MUSIC_DIR       = ASSETS_DIR / "music"
FONTS_DIR       = ASSETS_DIR / "fonts"
OUTPUT_DIR      = REEL_ENGINE_DIR / "output"
TEMP_DIR        = REEL_ENGINE_DIR / "temp"
LOGS_DIR        = REEL_ENGINE_DIR / "logs"
DB_PATH         = REEL_ENGINE_DIR / "content_brain.db"
LOGO_PATH       = BASE_DIR / "logo.png"

# Create dirs on import
for d in [ASSETS_DIR, MUSIC_DIR, FONTS_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# REEL SETTINGS
# ──────────────────────────────────────────────
REEL_WIDTH      = 1080
REEL_HEIGHT     = 1920
REEL_FPS        = 30
REELS_PER_DAY   = 2

# Scene timing
SCENE_DURATION_SEC   = 5      # seconds each scene image is shown
TRANSITION_DURATION  = 0.5    # cross-fade seconds between scenes
HOOK_DURATION_SEC    = 3      # first hook text hold

# Audio
BGM_VOLUME_DB        = -22    # background music level (quiet)
VOICE_VOLUME_DB      = 0      # narration level

# ──────────────────────────────────────────────
# VOICE SETTINGS
# ──────────────────────────────────────────────
# Edge-TTS Hindi voices (free, high quality)
VOICE_HINDI_MALE     = "hi-IN-MadhurNeural"    # calm, devotional
VOICE_HINDI_FEMALE   = "hi-IN-SwaraNeural"     # soft, expressive
VOICE_DEFAULT        = VOICE_HINDI_MALE

# ──────────────────────────────────────────────
# BRAND
# ──────────────────────────────────────────────
BRAND_NAME           = "HinduDevGyan"
BRAND_WEBSITE        = "hindudevgyan.in"
BRAND_COLOR_PRIMARY  = "#E8540A"   # saffron-orange
BRAND_COLOR_DARK     = "#1A0A00"   # deep dark
BRAND_COLOR_GOLD     = "#D4A017"   # divine gold

# ──────────────────────────────────────────────
# IMAGE GENERATION
# ──────────────────────────────────────────────
IMAGE_ASPECT_RATIO   = "1:1"   # we crop to 9:16 in video_creator
IMAGE_MODEL_PRIMARY  = "imagen-3.0-generate-002"
IMAGE_MODEL_FALLBACK = "pollinations"   # free fallback

# ──────────────────────────────────────────────
# FONTS (Windows paths)
# ──────────────────────────────────────────────
WINDOWS_FONTS = [
    r"C:\Windows\Fonts\NotoSansDevanagari-Bold.ttf",
    r"C:\Windows\Fonts\mangal.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]
LINUX_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

# ──────────────────────────────────────────────
# GOOGLE TRENDS SETTINGS
# ──────────────────────────────────────────────
TRENDS_GEO           = "IN"     # India
TRENDS_LANGUAGE      = "hi"
TRENDS_CATEGORY      = 0        # All categories (we filter by topic)
