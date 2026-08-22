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


def _trim_black_bars(img):
    """
    Scans and automatically crops any letterbox or pillarbox dark borders.
    """
    rgb = img.convert('RGB')
    width, height = rgb.size
    pixels = rgb.load()
    
    # Top & Bottom scan
    min_y, max_y = 0, height - 1
    for y in range(height):
        is_black = True
        for x in range(int(width * 0.1), int(width * 0.9), 10):
            r, g, b = pixels[x, y]
            if r > 28 or g > 28 or b > 28:
                is_black = False
                break
        if not is_black:
            min_y = y
            break
            
    for y in range(height - 1, -1, -1):
        is_black = True
        for x in range(int(width * 0.1), int(width * 0.9), 10):
            r, g, b = pixels[x, y]
            if r > 28 or g > 28 or b > 28:
                is_black = False
                break
        if not is_black:
            max_y = y
            break
            
    # Left & Right scan
    min_x, max_x = 0, width - 1
    for x in range(width):
        is_black = True
        for y in range(int(height * 0.1), int(height * 0.9), 10):
            r, g, b = pixels[x, y]
            if r > 28 or g > 28 or b > 28:
                is_black = False
                break
        if not is_black:
            min_x = x
            break
            
    for x in range(width - 1, -1, -1):
        is_black = True
        for y in range(int(height * 0.1), int(height * 0.9), 10):
            r, g, b = pixels[x, y]
            if r > 28 or g > 28 or b > 28:
                is_black = False
                break
        if not is_black:
            max_x = x
            break
            
    if max_y > min_y + 100 and max_x > min_x + 100:
        return img.crop((min_x, min_y, max_x + 1, max_y + 1))
    return img


def apply_smart_logo_watermark(image_path, output_path=None):
    """
    1. Trims all black letterbox borders completely.
    2. Scales to 16:9 Widescreen (1600x900) full edge-to-edge artwork.
    3. Overlays logo badge directly inside the top-right corner of the artwork.
    4. Exports to high-quality 8K WebP.
    """
    if output_path is None:
        output_path = image_path

    try:
        raw_img = Image.open(image_path).convert("RGBA")
        trimmed_img = _trim_black_bars(raw_img)
        
        # Enforce full edge-to-edge 16:9 widescreen canvas
        target_w = 1600
        target_h = 900
        img = trimmed_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        width, height = target_w, target_h

        if os.path.exists(LOGO_PATH):
            logo_raw = Image.open(LOGO_PATH).convert("RGBA")
            logo_cropped = _crop_logo_tight(logo_raw)

            # Target logo width relative to image width (around 150px)
            target_logo_w = 150
            w_percent = target_logo_w / float(logo_cropped.size[0])
            target_logo_h = int(float(logo_cropped.size[1]) * float(w_percent))
            logo_resized = logo_cropped.resize((target_logo_w, target_logo_h), Image.Resampling.LANCZOS)

            # Snug padding
            padding_x = 10
            padding_y = 6
            badge_w = target_logo_w + (padding_x * 2)
            badge_h = target_logo_h + (padding_y * 2)

            margin = 24
            x1 = width - margin - badge_w
            y1 = margin
            x2 = width - margin
            y2 = margin + badge_h

            badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(badge_layer)

            # Subtle drop shadow & frosted white badge with saffron border
            draw.rounded_rectangle([x1 + 1, y1 + 1, x2 + 1, y2 + 1], radius=8, fill=(0, 0, 0, 60))
            draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(255, 255, 255, 240), outline=(232, 84, 10, 220), width=1)

            img = Image.alpha_composite(img, badge_layer)
            img.paste(logo_resized, (x1 + padding_x, y1 + padding_y), logo_resized)

        # Apply subtle sharpening and export as WebP
        final_img = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.0, percent=110, threshold=2))
        final_img.save(output_path, "WEBP", quality=90)
        return output_path
    except Exception as e:
        print(f"Warning: Watermarking failed ({e}), continuing with base image.")
        return image_path


def generate_hd_featured_image(prompt_text, category="Spiritual News", output_filename="featured_image.webp", temple_keyword=""):
    """
    Direct clean prompt to Google Vertex AI Gemini / Imagen (Uses ₹28,000 credit balance)
    """
    print(f"\n[Vertex AI Image Engine] Generating 16:9 rich visual for: '{prompt_text}'")
    
    # Rich, detailed, 16:9 widescreen spiritual infographic & divine art prompt
    clean_prompt = (
        f"A rich, highly-detailed 16:9 wide landscape spiritual featured banner and infographic for Hindu article: '{prompt_text}'. "
        f"Wide 16:9 panoramic composition with central divine Hindu deity, sacred golden temple atmosphere, ornate Vedic decorative elements, "
        f"warm ambient diya illumination, fresh marigold flowers, crystal clear 8k resolution. Wide landscape 16:9 format."
    )

    temp_raw = "temp_raw_gen.jpg"

    gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not (gcp_project or gemini_key):
        print("[ERROR] Neither GCP_PROJECT_ID nor GEMINI_API_KEY is configured for image generation.")
        return None

    try:
        from google import genai
        from google.genai import types
        import time

        # Prioritize Account B Vertex AI for Image Generation (Uses the ₹28,000 Credit Balance)
        if gcp_project and (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_SA_KEY")):
            client = genai.Client(vertexai=True, project=gcp_project, location=os.getenv("GCP_LOCATION", "us-central1"))
        elif gemini_key:
            client = genai.Client(api_key=gemini_key)
        elif gcp_project:
            client = genai.Client(vertexai=True, project=gcp_project, location=os.getenv("GCP_LOCATION", "us-central1"))
        else:
            client = None

        if client:
            # 1. Primary: Google Gemini 2.5 Flash Image with retry handling
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash-image',
                        contents=clean_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
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
                    print(f"[Vertex AI Gemini 2.5 Flash Image Attempt {attempt+1} Note]: {e_flash}")
                    time.sleep(3)

            # 2. Secondary: Google Imagen 3 fallback
            try:
                res_img = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=clean_prompt,
                    config=dict(number_of_images=1, aspect_ratio="16:9")
                )
                if res_img and res_img.generated_images:
                    img_bytes = res_img.generated_images[0].image.image_bytes
                    with open(temp_raw, "wb") as f:
                        f.write(img_bytes)
                    print("[OK] Successfully generated 2026 Ultra-HD image via Google Imagen 3 (Vertex AI)!")
                    return apply_smart_logo_watermark(temp_raw, output_filename)
            except Exception as e_imagen:
                print(f"[Vertex AI Imagen 3 Attempt Note]: {e_imagen}")
    except Exception as e_google:
        print(f"[Vertex AI Exception]: {e_google}")

    print("[ERROR] Vertex AI Image Generation failed. No external fallbacks enabled.")
    return None
