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


def fetch_real_temple_photo(query_text):
    """
    Searches official open media repositories (Wikipedia/Wikimedia) for authentic,
    high-resolution photographs of famous Indian temples & pilgrimage sites.
    """
    # Clean temple query
    clean_query = query_text.replace(" ", "_").strip()
    candidate_titles = [
        f"{clean_query}_Temple",
        f"{clean_query}_Mandir",
        clean_query
    ]

    headers = {'User-Agent': 'HinduDevGyan/2.0 (info@hindudevgyan.in)'}

    for title in candidate_titles:
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pithumbsize=1280"
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                pages = res.json().get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    if "thumbnail" in p and "source" in p["thumbnail"]:
                        img_url = p["thumbnail"]["source"]
                        img_data = requests.get(img_url, headers=headers, timeout=20).content
                        if len(img_data) > 20000:
                            temp_file = "temp_real_temple.jpg"
                            with open(temp_file, "wb") as f:
                                f.write(img_data)
                            print(f"[OK] Fetched authentic real photo for '{title}' from official repository")
                            return temp_file
        except Exception:
            continue

    return None


def generate_hd_featured_image(prompt_text, category="Spiritual News", output_filename="featured_image.webp", temple_keyword=""):
    """
    Smart Hybrid Visual Engine:
    1. If article is about a real physical temple (Kedarnath, Badrinath, Somnath, etc.),
       fetches the authentic real high-res photograph.
    2. Otherwise, generates 8K photorealistic Vedic artwork via Cloudflare FLUX.1.
    3. Applies snug HinduDevGyan logo watermark and converts to WebP.
    """
    print(f"\n[Image Engine] Processing Visual for: '{prompt_text[:60]}...'")
    temp_raw = "temp_raw_gen.jpg"

    # Step 1: Check for real physical temple photo if applicable
    search_terms = []
    if temple_keyword:
        search_terms.append(temple_keyword)

    # Detect famous physical temples and sacred geographic landmarks
    famous_temples = [
        "Amarnath", "Kedarnath", "Badrinath", "Kashi Vishwanath", "Mahakaleshwar", "Somnath",
        "Ayodhya", "Ram Mandir", "Tirupati", "Puri Jagannath", "Rameshwaram", "Vaishno Devi",
        "Banke Bihari", "Vrindavan", "Mathura", "Meenakshi", "Brihadisvara", "Kamakhya",
        "Dwarkadhish", "Trimbakeshwar", "Bhimashankar", "Omkareshwar", "Grishneshwar",
        "Mallikarjuna", "Nageshwar", "Baidyanath", "Varanasi", "Haridwar", "Rishikesh",
        "Gangotri", "Yamunotri", "Siddhivinayak", "Akshardham", "Belur Math"
    ]
    for temple in famous_temples:
        if temple.lower() in prompt_text.lower() and temple not in search_terms:
            search_terms.append(temple)

    # Step 1: If real physical temple/place is identified, fetch authentic real photograph
    for term in search_terms:
        real_photo = fetch_real_temple_photo(term)
        if real_photo:
            watermarked = apply_smart_logo_watermark(real_photo, output_filename)
            if os.path.exists(real_photo) and real_photo != output_filename:
                try: os.remove(real_photo)
                except Exception: pass
            return watermarked

    # Step 2: DYNAMIC FLUX.1 Prompt Generation (Varying composition by topic category)
    cat_lower = str(category).lower()
    if any(k in cat_lower for k in ["panchang", "astrology", "horoscope", "nakshatra"]):
        refined_prompt = (
            f"Cinematic 8k authentic Vedic astrology photography of {prompt_text}, "
            f"ancient Sanskrit palm-leaf manuscript, brass astrological yantra, "
            f"serene night sky with glowing crescent moon and stars, soft sacred lighting, Hasselblad 8k"
        )
    elif any(k in cat_lower for k in ["festival", "vrat", "celebration"]):
        refined_prompt = (
            f"Vibrant cinematic 8k Indian festival photography of {prompt_text}, "
            f"joyful celebration atmosphere, fresh marigold and lotus flower decorations, "
            f"traditional brass puja thali, glowing earthen diyas, Hasselblad 8k"
        )
    elif any(k in cat_lower for k in ["gita", "wisdom", "philosophy"]):
        refined_prompt = (
            f"Cinematic 8k spiritual Vedic photography of {prompt_text}, "
            f"serene Himalayan meditative atmosphere, soft divine light rays, sacred ancient setting, masterpiece"
        )
    else:
        refined_prompt = (
            f"Cinematic 8k photorealistic devotional photography of {prompt_text}, "
            f"sacred Indian spiritual atmosphere, warm volumetric golden lighting, "
            f"authentic traditional iconography, sharp focus, 35mm photograph"
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
