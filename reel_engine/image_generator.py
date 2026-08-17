"""
image_generator.py — HinduDevGyan Reel Engine
Generates one image per scene using multiple engines:
  Engine 1 → Pollinations AI (quick probe first — skip if down)
  Engine 2 → PIL stylized devotional placeholder (instant, always works)
Saves all scene images to temp/ directory.
"""

import os
import sys
import time
import random
import urllib.parse
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import (
    TEMP_DIR, REEL_WIDTH, REEL_HEIGHT,
    WINDOWS_FONTS, LINUX_FONTS,
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ──────────────────────────────────────────────
# Quick health-check: test if Pollinations is up
# ──────────────────────────────────────────────
_POLLINATIONS_ALIVE = None   # cached after first check


def _check_pollinations_alive() -> bool:
    global _POLLINATIONS_ALIVE
    if _POLLINATIONS_ALIVE is not None:
        return _POLLINATIONS_ALIVE
    try:
        r = requests.get(
            "https://image.pollinations.ai/prompt/test?width=64&height=64&nologo=true",
            headers=HEADERS, timeout=10
        )
        _POLLINATIONS_ALIVE = (r.status_code == 200 and len(r.content) > 500)
    except Exception:
        _POLLINATIONS_ALIVE = False
    status = "✅ online" if _POLLINATIONS_ALIVE else "❌ offline"
    print(f"  🔍 Pollinations check: {status}")
    return _POLLINATIONS_ALIVE


# ──────────────────────────────────────────────
# ENGINE 1: Pollinations AI
# ──────────────────────────────────────────────
def _generate_via_pollinations(prompt: str, output_path: Path, model: str = "flux") -> bool:
    clean_prompt = f"{prompt[:350]}, Indian devotional art, warm golden light, no text"
    encoded = urllib.parse.quote(clean_prompt)
    seed = random.randint(1, 999999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={REEL_WIDTH}&height={REEL_HEIGHT}"
        f"&nologo=true&seed={seed}&model={model}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 10000:
            output_path.write_bytes(resp.content)
            print(f"  ✅ Pollinations [{model}] → {output_path.name} ({len(resp.content)//1024}KB)")
            return True
        print(f"  ⚠️  Pollinations [{model}] status={resp.status_code}")
        return False
    except Exception as e:
        print(f"  ⚠️  Pollinations [{model}] error: {str(e)[:60]}")
        return False


# ──────────────────────────────────────────────
# ENGINE 2: Beautiful PIL Placeholder (instant)
# Styled divine devotional card — always works
# ──────────────────────────────────────────────

# Divine color palettes for variety across scenes
DIVINE_PALETTES = [
    {"bg_top": (15, 5, 30), "bg_bot": (80, 30, 5),   "accent": (212, 160, 23),  "name": "Shiva night"},
    {"bg_top": (20, 5, 0),  "bg_bot": (120, 50, 0),  "accent": (255, 200, 50),  "name": "Saffron dawn"},
    {"bg_top": (0, 10, 30), "bg_bot": (10, 60, 80),  "accent": (100, 200, 255), "name": "Ocean blue"},
    {"bg_top": (30, 0, 0),  "bg_bot": (100, 20, 60), "accent": (255, 150, 200), "name": "Shakti rose"},
    {"bg_top": (5, 20, 5),  "bg_bot": (20, 80, 30),  "accent": (100, 255, 150), "name": "Forest green"},
    {"bg_top": (20, 10, 0), "bg_bot": (90, 45, 10),  "accent": (255, 180, 80),  "name": "Temple gold"},
    {"bg_top": (10, 0, 30), "bg_bot": (60, 10, 90),  "accent": (200, 100, 255), "name": "Cosmic violet"},
]

DIVINE_SYMBOLS = ["🕉", "ॐ", "🙏", "⚡", "🌙", "🔱", "☀️"]


def _find_font(size: int = 40) -> ImageFont.ImageFont:
    for path in WINDOWS_FONTS + LINUX_FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_gradient(draw: ImageDraw.ImageDraw, palette: dict):
    """Draw a smooth top-to-bottom gradient."""
    top = palette["bg_top"]
    bot = palette["bg_bot"]
    for y in range(REEL_HEIGHT):
        t = y / REEL_HEIGHT
        r = int(top[0] + t * (bot[0] - top[0]))
        g = int(top[1] + t * (bot[1] - top[1]))
        b = int(top[2] + t * (bot[2] - top[2]))
        draw.line([(0, y), (REEL_WIDTH, y)], fill=(r, g, b))


def _wrap_text(text: str, max_chars: int = 28) -> list[str]:
    """Wrap text into lines of max_chars width."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current + " " + word) <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:6]


def _generate_stylized_placeholder(prompt: str, scene_id: int, output_path: Path) -> bool:
    """
    Generate a beautiful stylized devotional image using PIL.
    Rotates through 7 divine color palettes for visual variety.
    Never fails — guaranteed output.
    """
    try:
        palette = DIVINE_PALETTES[(scene_id - 1) % len(DIVINE_PALETTES)]
        symbol = DIVINE_SYMBOLS[(scene_id - 1) % len(DIVINE_SYMBOLS)]
        accent = palette["accent"]

        img = Image.new("RGB", (REEL_WIDTH, REEL_HEIGHT), palette["bg_top"])
        draw = ImageDraw.Draw(img)

        # Gradient background
        _draw_gradient(draw, palette)

        # Radial glow effect (concentric semi-transparent circles)
        cx, cy = REEL_WIDTH // 2, REEL_HEIGHT // 2 - 100
        for radius in range(350, 50, -30):
            alpha_ratio = (350 - radius) / 300
            r = int(accent[0] * alpha_ratio * 0.3)
            g = int(accent[1] * alpha_ratio * 0.3)
            b = int(accent[2] * alpha_ratio * 0.3)
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                outline=(r, g, b), width=1
            )

        # Decorative horizontal lines (top & bottom)
        for offset in [80, 90]:
            draw.line([(60, offset), (REEL_WIDTH - 60, offset)], fill=accent, width=2)
        for offset in [REEL_HEIGHT - 80, REEL_HEIGHT - 90]:
            draw.line([(60, offset), (REEL_WIDTH - 60, offset)], fill=accent, width=2)

        # Corner decorations
        corners = [(80, 60), (REEL_WIDTH - 80, 60),
                   (80, REEL_HEIGHT - 60), (REEL_WIDTH - 80, REEL_HEIGHT - 60)]
        for cx2, cy2 in corners:
            draw.ellipse([cx2 - 8, cy2 - 8, cx2 + 8, cy2 + 8], fill=accent)

        # Large central symbol
        font_xl = _find_font(180)
        draw.text((REEL_WIDTH // 2, REEL_HEIGHT // 2 - 280),
                  symbol, font=font_xl, fill=accent, anchor="mm")

        # Divider line
        draw.line([(120, REEL_HEIGHT // 2 - 80), (REEL_WIDTH - 120, REEL_HEIGHT // 2 - 80)],
                  fill=accent, width=2)

        # Scene narration text (wrapped, centered)
        font_body = _find_font(44)
        lines = _wrap_text(prompt[:160], max_chars=24)
        y_text = REEL_HEIGHT // 2 - 30
        for line in lines:
            draw.text((REEL_WIDTH // 2, y_text), line,
                      font=font_body, fill=(255, 245, 220), anchor="mm",
                      stroke_width=2, stroke_fill=(0, 0, 0))
            y_text += 56

        # Brand bar at bottom
        bar_y = REEL_HEIGHT - 140
        draw.rectangle([(0, bar_y), (REEL_WIDTH, REEL_HEIGHT)],
                        fill=(10, 4, 0))
        font_brand = _find_font(50)
        draw.text((REEL_WIDTH // 2, bar_y + 50), "🕉  HinduDevGyan",
                  font=font_brand, fill=accent, anchor="mm")
        font_small = _find_font(32)
        draw.text((REEL_WIDTH // 2, bar_y + 100), "hindudevgyan.in",
                  font=font_small, fill=(180, 160, 120), anchor="mm")

        # Slight blur for depth
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

        img.save(str(output_path), "JPEG", quality=88)
        print(f"  ✅ Stylized card [Scene {scene_id}] → {output_path.name}", flush=True)
        return True

    except Exception as e:
        print(f"  ❌ Placeholder failed: {e}", flush=True)
        return False


# ──────────────────────────────────────────────
# MAIN PUBLIC FUNCTIONS
# ──────────────────────────────────────────────

def generate_scene_image(scene_id: int, image_prompt: str, reel_id: str) -> "Path | None":
    """Generate a single scene image. Returns Path or None."""
    filename = f"{reel_id}_scene_{scene_id:02d}.jpg"
    output_path = TEMP_DIR / filename

    # Resume support
    if output_path.exists() and output_path.stat().st_size > 5000:
        print(f"  ♻️  Reusing cached: {filename}", flush=True)
        return output_path

    print(f"  🎨 Scene {scene_id}...", flush=True)

    # Try Pollinations only if it's alive (quick probe on first call)
    if _check_pollinations_alive():
        for model in ("flux-pro", "flux"):
            if _generate_via_pollinations(image_prompt, output_path, model):
                return output_path

    # Always-available fallback
    if _generate_stylized_placeholder(image_prompt, scene_id, output_path):
        return output_path

    return None


def generate_all_scene_images(scenes: list, reel_id: str) -> list:
    """Generate images for all scenes. Returns list of Paths."""
    print(f"\n🖼️  Generating {len(scenes)} scene images...", flush=True)
    image_paths = []
    for scene in scenes:
        path = generate_scene_image(
            scene_id=scene["id"],
            image_prompt=scene["image_prompt"],
            reel_id=reel_id
        )
        image_paths.append(path)

    success = sum(1 for p in image_paths if p is not None)
    print(f"  📊 {success}/{len(scenes)} images ready", flush=True)
    return image_paths
