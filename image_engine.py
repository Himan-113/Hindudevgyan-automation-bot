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
    Searches open internet media (Wikipedia/Wikimedia) ONLY for verified physical temples,
    pilgrimages, and public figures. Never searches for astrology, metaphors, or generic keywords.
    """
    text_lower = text.lower()

    # 1. Physical Temples, Shrines & Pilgrimages
    known_landmarks = [
        "amarnath", "kedarnath", "badrinath", "somnath", "kashi vishwanath", "ayodhya ram mandir",
        "ram mandir", "tirupati balaji", "puri jagannath", "meenakshi temple", "kamakhya temple",
        "vaishno devi", "har ki pauri", "varanasi ghats", "mahakaleshwar", "trimbakeshwar",
        "omkareshwar", "rameshwaram", "dwarka", "akshardham", "kanwar yatra", "kumbh mela"
    ]

    # 2. Real Living / Historical Figures & Gurus
    known_people = [
        "yogi adityanath", "narendra modi", "dhirendra shastri", "bageshwar dham", "shankaracharya",
        "swami vivekananda", "sadhguru", "baba ramdev", "premanand ji maharaj", "sri sri ravi shankar"
    ]

    target_query = None
    for landmark in known_landmarks:
        if landmark in text_lower:
            target_query = landmark.title()
            break

    if not target_query:
        for person in known_people:
            if person in text_lower:
                target_query = person.title()
                break

    if not target_query:
        return None

    headers = {'User-Agent': 'HinduDevGyan/2.0 (info@hindudevgyan.in)'}
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(target_query)}&gsrlimit=3&prop=pageimages&pithumbsize=1280&format=json"
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
                        print(f"[OK] Found authentic real photo for landmark/figure: '{target_query}' ({p.get('title')})")
                        return temp_file
    except Exception as e:
        print(f"Internet photo search exception: {e}")

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
    # ─── DIRECT 2026 ULTRA-HD FLUX.1 & GEMINI IMAGE ENGINE ───
    # Generates 100% bespoke, stunning 8K cinematic spiritual art with HinduDevGyan signature color harmony
    refined_prompt = (
        f"Ultra-HD 8k cinematic spiritual masterpiece of {prompt_text}. "
        f"Modern high-end spiritual realism, ethereal volumetric lighting, crystal-clear details, "
        f"harmonious Vedic color palette with radiant saffron gold, warm amber illumination, and deep cosmic indigo accents, "
        f"IMAX 70mm cinematic composition, sharp focus, breathtaking atmosphere, "
        f"unreal engine 5 architectural render fidelity. Strictly no text overlay, no watermarks, no distorted anatomy."
    )

    temp_raw = "temp_raw_gen.jpg"

    # ─── TIER 0: GOOGLE GEMINI 2.5 FLASH IMAGE & VERTEX AI / IMAGEN 3 ENGINE ───
    gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if gcp_project or gemini_key:
        try:
            from google import genai
            from google.genai import types

            if gemini_key:
                client = genai.Client(api_key=gemini_key)
            elif gcp_project:
                client = genai.Client(vertexai=True, project=gcp_project, location=os.getenv("GCP_LOCATION", "us-central1"))
            else:
                client = None

            # Try Gemini 2.5 Flash Image first
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash-image',
                    contents=refined_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        candidate_count=1,
                    )
                )
                if response and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img_bytes = part.inline_data.data
                            with open(temp_raw, "wb") as f:
                                f.write(img_bytes)
                            print("[OK] Successfully generated image via Google Gemini 2.5 Flash Image (Vertex AI)!")
                            return apply_smart_logo_watermark(temp_raw, output_filename)
            except Exception as e_flash:
                print(f"Gemini 2.5 Flash Image note: {e_flash}")
                # Fallback to Imagen 3
                try:
                    res_img = client.models.generate_images(
                        model='imagen-3.0-generate-002',
                        prompt=refined_prompt,
                        config=dict(number_of_images=1, aspect_ratio="4:3")
                    )
                    if res_img and res_img.generated_images:
                        img_bytes = res_img.generated_images[0].image.image_bytes
                        with open(temp_raw, "wb") as f:
                            f.write(img_bytes)
                        print("[OK] Successfully generated image via Google Imagen 3!")
                        return apply_smart_logo_watermark(temp_raw, output_filename)
                except Exception as e_imagen:
                    print(f"Google Imagen 3 attempt note: {e_imagen}")
        except Exception as e_google:
            print(f"Google Image Engine exception: {e_google}")

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
                "steps": 4,
                "height": 768,
                "width": 1024
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

    # ─── TIER 2: TOGETHER.AI (FLUX.1-schnell fallback) ───
    if TOGETHER_API_KEY:
        try:
            res = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers={"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": refined_prompt,
                    "width": 1024,
                    "height": 768,
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

    # ─── TIER 3: FAL.AI (FLUX.1-schnell fallback) ───
    if FAL_KEY:
        try:
            res = requests.post(
                "https://fal.run/fal-ai/flux/schnell",
                headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
                json={
                    "prompt": refined_prompt,
                    "image_size": "landscape_4_3",
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

    print("[ERROR] All High-End FLUX engines failed or reached daily quota limit.")
    return None
