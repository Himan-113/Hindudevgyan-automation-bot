import os
import requests
import json
import base64
import random
import urllib.parse
from PIL import Image, ImageDraw, ImageFilter
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
FAL_KEY = os.getenv("FAL_KEY")

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")


def _crop_logo_tight(logo_img):
    """
    Finds the exact non-white and non-transparent graphic bounds
    using pure Pillow (no numpy required).
    """
    img = logo_img.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    found = False

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 20 and not (r > 240 and g > 240 and b > 240):
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                found = True

    if found and max_x > min_x and max_y > min_y:
        return img.crop((min_x, min_y, max_x + 1, max_y + 1))
    return logo_img


def apply_smart_logo_watermark(image_path, output_path=None):
    """
    Overlays a snug, premium frosted-glass HinduDevGyan logo badge
    in the top-right corner without blocking central subject matter.
    """
    if output_path is None:
        output_path = image_path

    try:
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        if os.path.exists(LOGO_PATH):
            logo_raw = Image.open(LOGO_PATH).convert("RGBA")
            logo_cropped = _crop_logo_tight(logo_raw)

            # Target logo width relative to image width (around 140-150px)
            target_w = min(150, int(width * 0.15))
            w_percent = target_w / float(logo_cropped.size[0])
            target_h = int(float(logo_cropped.size[1]) * float(w_percent))
            logo_resized = logo_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # Snug padding
            padding_x = 10
            padding_y = 6
            badge_w = target_w + (padding_x * 2)
            badge_h = target_h + (padding_y * 2)

            margin = 22
            x1 = width - margin - badge_w
            y1 = margin
            x2 = width - margin
            y2 = margin + badge_h

            badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(badge_layer)

            # Subtle drop shadow
            draw.rounded_rectangle([x1 + 1, y1 + 1, x2 + 1, y2 + 1], radius=8, fill=(0, 0, 0, 50))
            # Clean frosted white pill with saffron accent border
            draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(255, 255, 255, 235), outline=(232, 84, 10, 220), width=1)

            img = Image.alpha_composite(img, badge_layer)
            img.paste(logo_resized, (x1 + padding_x, y1 + padding_y), logo_resized)

        # Apply subtle sharpening and export as WebP
        final_img = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.0, percent=110, threshold=2))
        final_img.save(output_path, "WEBP", quality=88)
        return output_path
    except Exception as e:
        print(f"Warning: Watermarking failed ({e}), continuing with base image.")
        return image_path


def generate_hd_featured_image(prompt_text, category="Spiritual News", output_filename="featured_image.webp"):
    """
    Generates an 8K photorealistic Vedic/devotional image using Cloudflare FLUX.1 [schnell]
    with failover chains and watermarking.
    """
    print(f"\n[Image Engine] Generating 8K FLUX.1 Artwork for: '{prompt_text[:60]}...'")
    temp_raw = "temp_raw_gen.jpg"

    # Master prompt tuning for Indian Devotional & Vedic aesthetics
    refined_prompt = (
        f"Cinematic 8k photorealistic devotional photography of {prompt_text}, "
        f"sacred Indian Vedic atmosphere, warm golden hour lighting, glowing oil diyas, "
        f"intricate temple carvings, photorealistic textures, Hasselblad camera masterpiece"
    )

    # ─── TIER 1: CLOUDFLARE WORKERS AI (FLUX.1-schnell) ───
    if CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN:
        try:
            cf_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
            headers = {
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": refined_prompt,
                "steps": 4
            }
            res = requests.post(cf_url, headers=headers, json=payload, timeout=45)
            if res.status_code == 200:
                data = res.json()
                if "result" in data and "image" in data["result"]:
                    img_bytes = base64.b64decode(data["result"]["image"])
                    with open(temp_raw, "wb") as f:
                        f.write(img_bytes)
                    print("[OK] Successfully generated image via Cloudflare FLUX.1 [schnell] (Free Tier)")
                    watermarked = apply_smart_logo_watermark(temp_raw, output_filename)
                    if os.path.exists(temp_raw) and temp_raw != output_filename:
                        try: os.remove(temp_raw)
                        except Exception: pass
                    return watermarked
            else:
                print(f"Cloudflare FLUX error ({res.status_code}): {res.text[:120]}")
        except Exception as e:
            print(f"Cloudflare FLUX attempt exception: {e}")

    # ─── TIER 2: TOGETHER.AI (FLUX.1-schnell) ───
    if TOGETHER_API_KEY:
        try:
            res = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": refined_prompt,
                    "width": 1024,
                    "height": 1024,
                    "steps": 4,
                    "n": 1
                },
                timeout=30
            )
            if res.status_code == 200:
                img_url = res.json()["data"][0]["url"]
                img_bytes = requests.get(img_url, timeout=20).content
                with open(temp_raw, "wb") as f:
                    f.write(img_bytes)
                print("[OK] Successfully generated image via Together.ai FLUX.1!")
                return apply_smart_logo_watermark(temp_raw, output_filename)
        except Exception as e:
            print(f"Together.ai fallback exception: {e}")

    # ─── TIER 3: FAL.AI (FLUX.1-schnell) ───
    if FAL_KEY:
        try:
            res = requests.post(
                "https://fal.run/fal-ai/flux/schnell",
                headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
                json={
                    "prompt": refined_prompt,
                    "image_size": "square_hd",
                    "num_images": 1
                },
                timeout=30
            )
            if res.status_code == 200:
                img_url = res.json()["images"][0]["url"]
                img_bytes = requests.get(img_url, timeout=20).content
                with open(temp_raw, "wb") as f:
                    f.write(img_bytes)
                print("[OK] Successfully generated image via Fal.ai FLUX.1!")
                return apply_smart_logo_watermark(temp_raw, output_filename)
        except Exception as e:
            print(f"Fal.ai fallback exception: {e}")

    # ─── TIER 4: POLLINATIONS FLUX FALLBACK ───
    try:
        seed = random.randint(1000, 999999)
        encoded_prompt = urllib.parse.quote(refined_prompt)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"
        res = requests.get(pollinations_url, stream=True, timeout=30)
        if res.status_code == 200 and len(res.content) > 10000:
            with open(temp_raw, "wb") as f:
                f.write(res.content)
            print("[OK] Generated image via Pollinations FLUX fallback.")
            return apply_smart_logo_watermark(temp_raw, output_filename)
    except Exception as e:
        print(f"Pollinations fallback exception: {e}")

    return None
