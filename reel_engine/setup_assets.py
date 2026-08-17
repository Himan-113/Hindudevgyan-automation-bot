"""
setup_assets.py — One-time setup script
Downloads a royalty-free devotional BGM track for the reel engine.
Run once before using main_reel.py

Usage:
    python reel_engine/setup_assets.py
"""

import urllib.request
import os
from pathlib import Path

MUSIC_DIR = Path(__file__).parent / "assets" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# Royalty-free Om chanting / devotional ambient tracks
# These are from archive.org and pixabay (public domain / CC0)
BGM_SOURCES = [
    {
        "name": "om_ambient_devotional.mp3",
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "desc": "Ambient devotional background (placeholder — replace with your own)"
    }
]

print("🎵 Setting up BGM assets for HinduDevGyan Reel Engine...")
print()
print("=" * 60)
print("IMPORTANT: For best results, please add your own royalty-free")
print("devotional/ambient BGM tracks to:")
print(f"  {MUSIC_DIR}")
print()
print("Recommended sources:")
print("  1. https://pixabay.com/music/ (search 'meditation' or 'om')")
print("  2. https://archive.org/details/audio (public domain)")
print("  3. YouTube Audio Library (free for creators)")
print("=" * 60)
print()

for track in BGM_SOURCES:
    output = MUSIC_DIR / track["name"]
    if output.exists():
        print(f"  ♻️  Already exists: {track['name']}")
        continue
    print(f"  ⬇️  Downloading placeholder BGM: {track['name']}...")
    try:
        urllib.request.urlretrieve(track["url"], output)
        print(f"  ✅ Saved: {output}")
        print(f"     ⚠️  Replace this with a proper devotional BGM track!")
    except Exception as e:
        print(f"  ⚠️  Could not download: {e}")
        print(f"     Manually place an MP3 file in: {MUSIC_DIR}")

print()
print("✅ Asset setup complete!")
print("   Next: python reel_engine/main_reel.py --test")
