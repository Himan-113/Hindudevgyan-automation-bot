# -*- coding: utf-8 -*-
"""
main_reel.py — HinduDevGyan Reel Engine
Entry point. Run this daily to generate today's reels.

Usage:
    python main_reel.py                     # Auto-select topic from Content Brain
    python main_reel.py --topic "custom topic here"
    python main_reel.py --count 2           # Generate 2 reels (default)
    python main_reel.py --test              # Generate 1 reel for testing
"""

import sys
import io
# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import argparse
import os
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path

# ── Set up path so all reel_engine modules can be imported ──
sys.path.insert(0, str(Path(__file__).parent))

from config import REELS_PER_DAY, LOGS_DIR, OUTPUT_DIR
from content_brain import (
    init_db, select_topic_for_today, mark_topic_used,
    log_reel, get_stats
)
from script_generator import generate_script, print_script_summary
from image_generator import generate_all_scene_images
from voice_generator import generate_scene_voices, get_audio_duration
from video_creator import create_reel, cleanup_temp


# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────
log_file = LOGS_DIR / f"reel_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)


# ──────────────────────────────────────────────
# SINGLE REEL PIPELINE
# ──────────────────────────────────────────────
def generate_one_reel(topic_data: dict) -> dict:
    """
    Full pipeline for one reel. Returns result dict with status and file path.
    """
    reel_id = uuid.uuid4().hex[:8]
    topic = topic_data["topic"]
    category = topic_data.get("category", "General")
    deity = topic_data.get("deity", "General")
    source = topic_data.get("source", "Manual")

    print("\n" + "═" * 65)
    print(f"🎬 REEL PIPELINE START")
    print(f"   ID       : {reel_id}")
    print(f"   Topic    : {topic[:70]}")
    print(f"   Category : {category} | Deity: {deity}")
    print(f"   Source   : {source}")
    print("═" * 65)

    result = {
        "reel_id": reel_id,
        "topic": topic,
        "status": "failed",
        "file": None,
        "duration": 0
    }

    start_time = time.time()

    # ── Step 1: Generate Script ──
    print("\n📝 Step 1/4 — Generating Script...")
    script = generate_script(topic, category, deity)
    if not script:
        print("❌ Script generation failed. Skipping reel.")
        return result
    print_script_summary(script)

    # ── Step 2: Generate Scene Images ──
    print("\n🖼️  Step 2/4 — Generating Scene Images...")
    scenes = script.get("scenes", [])
    image_paths = generate_all_scene_images(scenes, reel_id)

    valid_images = [p for p in image_paths if p and p.exists()]
    if len(valid_images) < 3:
        print(f"❌ Too few images generated ({len(valid_images)}). Skipping reel.")
        cleanup_temp(reel_id)
        return result

    # ── Step 3: Generate Voice Narration ──
    print("\n🎙️  Step 3/4 — Generating Hindi Voice Narration...")
    voice_paths = generate_scene_voices(scenes, reel_id)

    # ── Step 4: Assemble Video ──
    print("\n🎞️  Step 4/4 — Assembling Reel with FFmpeg...")
    final_mp4 = create_reel(script, image_paths, voice_paths, reel_id)

    elapsed = time.time() - start_time

    if final_mp4 and final_mp4.exists():
        duration = get_audio_duration(final_mp4)
        result["status"] = "success"
        result["file"] = str(final_mp4)
        result["duration"] = duration

        print("\n" + "🎉" * 32)
        print(f"✅ REEL READY!")
        print(f"   File     : {final_mp4.name}")
        print(f"   Duration : {duration:.1f} seconds")
        print(f"   Size     : {final_mp4.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"   Time     : {elapsed:.0f}s to generate")
        print(f"\n📌 Social Media Copy:")
        print(f"   YT Title : {script.get('youtube_title', '')}")
        print(f"   Caption  : {script.get('instagram_caption', '')[:100]}...")
        print(f"   Hashtags : {script.get('hashtags', '')[:80]}")
        print("🎉" * 32 + "\n")

        # Update Content Brain
        if "id" in topic_data:
            mark_topic_used(topic_data["id"], str(final_mp4))
            log_reel(topic_data["id"], topic, str(final_mp4), duration)

        # Save social media metadata alongside the video
        meta_path = OUTPUT_DIR / f"{final_mp4.stem}_meta.txt"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"TITLE: {script.get('youtube_title', '')}\n\n")
            f.write(f"DESCRIPTION:\n{script.get('youtube_description', '')}\n\n")
            f.write(f"INSTAGRAM CAPTION:\n{script.get('instagram_caption', '')}\n\n")
            f.write(f"HASHTAGS: {script.get('hashtags', '')}\n")
        print(f"📄 Metadata saved: {meta_path.name}")
    else:
        print(f"\n❌ Reel assembly failed after {elapsed:.0f}s")

    # Cleanup temp files
    cleanup_temp(reel_id)
    return result


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="HinduDevGyan Reel Engine — Generate viral Hindu devotional reels"
    )
    parser.add_argument("--topic", type=str, help="Custom topic override")
    parser.add_argument("--count", type=int, default=REELS_PER_DAY,
                        help=f"Number of reels to generate (default: {REELS_PER_DAY})")
    parser.add_argument("--test", action="store_true",
                        help="Generate 1 reel for testing")
    parser.add_argument("--stats", action="store_true",
                        help="Show Content Brain stats and exit")
    args = parser.parse_args()

    print("\n" + "🕉️  " * 20)
    print("      HinduDevGyan REEL ENGINE")
    print(f"      {datetime.now().strftime('%A, %d %B %Y — %I:%M %p IST')}")
    print("🕉️  " * 20 + "\n")

    # Init Content Brain DB
    init_db()

    # Show stats only
    if args.stats:
        stats = get_stats()
        print("📊 Content Brain Stats:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
        return

    count = 1 if args.test else args.count
    results = []

    for i in range(count):
        print(f"\n{'─' * 65}")
        print(f"  📹 Reel {i+1} of {count}")
        print(f"{'─' * 65}")

        # Topic selection
        if args.topic:
            topic_data = {
                "topic": args.topic,
                "category": "General",
                "deity": "General",
                "source": "Manual Override"
            }
        else:
            topic_data = select_topic_for_today()
            print(f"\n📅 Topic selected: {topic_data['topic'][:70]}")
            print(f"   Source: {topic_data.get('source', 'Content Brain')}")

        result = generate_one_reel(topic_data)
        results.append(result)

        if i < count - 1:
            print("\n⏳ Waiting 10 seconds before next reel...")
            time.sleep(10)

    # Final summary
    print("\n" + "═" * 65)
    print("📊 SESSION SUMMARY")
    print("═" * 65)
    success = [r for r in results if r["status"] == "success"]
    print(f"  ✅ Successful: {len(success)}/{len(results)}")
    for r in success:
        print(f"     → {Path(r['file']).name} ({r['duration']:.0f}s)")
    print(f"\n  📁 Output folder: {OUTPUT_DIR}")
    print("═" * 65 + "\n")


if __name__ == "__main__":
    main()
