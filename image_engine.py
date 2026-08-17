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


def search_internet_for_real_photo(text):
    """
    Dynamically extracts key entities (persons, places, temples, real events)
    from ANY title or prompt and searches open internet media (Wikipedia/Wikimedia) FIRST.
    Returns local file path if a high-res real photo is found, else None.
    """
    import re
    boilerplate = {
        'news', 'today', '2026', '2025', 'sacred', 'divine', 'cosmic', 'unlocks',
        'revealed', 'begins', 'journey', 'final', 'phase', 'harness', 'power',
        'confluence', 'honors', 'secret', 'secrets', 'exclusive', 'special', 'updates'
    }
    words = text.replace(':', ' ').replace('-', ' ').replace(',', ' ').replace("'", "").split()
    candidates = []
    
    # 1. Capitalized multi-word entities (Persons, Places, Temples, Events)
    entities = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
    for ent in entities:
        clean_ent = ' '.join([w for w in ent.split() if w.lower() not in boilerplate])
        if clean_ent and clean_ent not in candidates:
            candidates.append(clean_ent)
            
    # 2. Main title clean multi-word queries
    clean_terms = [w for w in words if w.lower() not in boilerplate and len(w) > 3]
    if len(clean_terms) >= 2:
        candidates.append(' '.join(clean_terms[:3]))
        
    # 3. Individual significant capitalized names
    for w in words:
        if len(w) > 4 and w[0].isupper() and w.lower() not in boilerplate and w not in candidates:
            candidates.append(w)
            
    headers = {'User-Agent': 'HinduDevGyan/2.0 (info@hindudevgyan.in)'}
    for q in candidates:
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(q)}&gsrlimit=3&prop=pageimages&pithumbsize=1280&format=json"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                pages = res.json().get("query", {}).get("pages", {})
                for pid, p in sorted(pages.items(), key=lambda x: x[1].get('index', 99)):
                    if "thumbnail" in p and "source" in p["thumbnail"]:
                        img_url = p["thumbnail"]["source"]
                        img_data = requests.get(img_url, headers=headers, timeout=15).content
                        if len(img_data) > 20000:
                            temp_file = "temp_real_media.jpg"
                            with open(temp_file, "wb") as f:
                                f.write(img_data)
                            print(f"[OK] Found authentic real photo for '{q}' ({p.get('title')}) from internet repository")
                            return temp_file
        except Exception:
            continue
    return None


def generate_hd_featured_image(prompt_text, category="Spiritual News", output_filename="featured_image.webp", temple_keyword=""):
    """
    Enterprise Internet-First Visual Pipeline:
    1. Searches the internet FIRST for any real person, landmark, temple, or event in the text.
    2. If a real high-res photograph is found -> Applies watermark and returns it.
    3. If not found (or pure mythology / astrology / mantra) -> Generates via FLUX.1 with topic-tailored prompts.
    4. Applies snug HinduDevGyan logo watermark and converts to WebP.
    """
    print(f"\n[Image Engine] Processing Visual for: '{prompt_text[:60]}...'")
    temp_raw = "temp_raw_gen.jpg"

    # ─── STEP 1: SEARCH OPEN INTERNET MEDIA FIRST ───
    real_photo = search_internet_for_real_photo(prompt_text)
    if real_photo and os.path.exists(real_photo):
        watermarked = apply_smart_logo_watermark(real_photo, output_filename)
        if real_photo != output_filename:
            try: os.remove(real_photo)
            except Exception: pass
        return watermarked

    # ─── STEP 2: DYNAMIC FLUX.1 GENERATION (NATURAL AI RENDERING) ───
    # Passes Gemini's context-aware visual prompt directly with photorealistic quality anchors
    refined_prompt = (
        f"Cinematic 8k photorealistic photography of {prompt_text}, "
        f"warm sacred lighting, realistic textures, high detail, Hasselblad 8k masterpiece"
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
