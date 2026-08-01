import os
import requests
import json
import random
import re
import urllib.parse
from google import genai
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import time
from datetime import datetime
import pytz

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

DAY_NAMES = {
    1: "Monday (ruling deity: Lord Shiva)",
    2: "Tuesday (ruling deity: Lord Hanuman / Mangal)",
    3: "Wednesday (ruling deity: Lord Ganesha / Budh)",
    4: "Thursday (ruling deity: Guru Brihaspati / Lord Vishnu)",
    5: "Friday (ruling deity: Goddess Lakshmi / Devi / Shukra)",
    6: "Saturday (ruling deity: Lord Shani)",
    7: "Sunday (ruling deity: Surya, the Sun God)",
}


# ==========================================
# CTA HTML BLOCKS
# ==========================================
def get_whatsapp_cta_html():
    return """
    <div style="background:linear-gradient(135deg,#25D366,#128C7E); border-radius:10px; padding:18px 14px; margin:25px 0; text-align:center; box-sizing:border-box; max-width:100%;">
        <h3 style="color:#fff; margin-top:0; font-size:17px;">📲 Join Our WhatsApp Channel</h3>
        <p style="color:#dcfce7; font-size:13px; margin-bottom:14px;">
            रोज़ सुबह पाएं — पंचांग, मंत्र, और आध्यात्मिक ज्ञान सीधे WhatsApp पर।<br>
            <em>Get daily Panchang, Mantras &amp; Spiritual Wisdom every morning.</em>
        </p>
        <a href="https://whatsapp.com/channel/0029Vb8RQLz545uzablvPF3x" target="_blank"
           style="display:inline-block; background:#fff; color:#128C7E; padding:10px 20px; border-radius:25px; font-weight:bold; text-decoration:none; font-size:13px; max-width:100%; box-sizing:border-box;">
           📲 Join Free — HinduDevGyan Channel
        </a>
    </div>
    """


def get_kundli_upsell_html():
    return """
    <div style="background:#FDF0DB; border-left:4px solid #E8540A; padding:16px; border-radius:6px; margin:25px 0; box-sizing:border-box; max-width:100%;">
        <h3 style="margin-top:0; color:#E8540A; font-size:18px;">🔮 Curious About Your Birth Chart?</h3>
        <p style="font-size:14px; color:#333; margin-bottom:14px;">Discover your exact career path, marriage compatibility, and planetary dashas based on your exact birth time.</p>
        <div style="display:flex; flex-wrap:wrap; gap:10px;">
            <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#10b981; color:#fff; padding:10px 16px; border-radius:4px; font-weight:bold; text-decoration:none; font-size:13px; text-align:center; flex:1; min-width:160px; box-sizing:border-box;">✨ Generate Free Vedic Kundli</a>
            <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#E8540A; color:#fff; padding:10px 16px; border-radius:4px; font-weight:bold; text-decoration:none; font-size:13px; text-align:center; flex:1; min-width:160px; box-sizing:border-box;">📄 Unlock 50-Page PDF (₹149)</a>
        </div>
    </div>
    """


def get_ebook_upsell_html():
    return """
    <div style="background:#fffbeb; border:2px dashed #f59e0b; padding:18px 12px; border-radius:8px; margin:25px 0; text-align:center; box-sizing:border-box; max-width:100%;">
        <h3 style="margin-top:0; color:#b45309; font-size:18px;">Transform Your Home's Energy Today!</h3>
        <p style="font-size:14px; color:#78350f; margin-bottom:15px;">Discover the ancient secrets to attracting wealth, health, and harmony. Download our premium 5-chapter Vastu Shastra guide instantly.</p>
        <a href="https://rzp.io/rzp/VtX5q0e" target="_blank"
           style="display:inline-block; background:#f59e0b; color:#fff; padding:11px 20px; border-radius:30px; font-weight:bold; text-decoration:none; font-size:14px; box-shadow:0 4px 6px rgba(0,0,0,0.1); max-width:100%; box-sizing:border-box;">
           📖 Unlock Vastu Shastra Mastery Guide (₹99)
        </a>
    </div>
    """


def get_affiliate_html(day):
    """Returns contextual affiliate product based on the day's ruling deity."""
    if day in (1, 6):  # Monday=Shiva, Saturday=Shani
        title = "5 Mukhi Rudraksha Mala — 108 Beads"
        desc = "Pure Nepali Rudraksha. Enhances focus and brings Lord Shiva's blessings."
        link = "https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21"
        price = "₹399 - Buy on Amazon"
    elif day == 5:  # Friday=Lakshmi
        title = "Brass Lakshmi Idol — 6 inch"
        desc = "Beautifully crafted brass Lakshmi idol for home puja and wealth attraction."
        link = "https://www.amazon.in/s?k=brass+lakshmi+idol+for+home&tag=hindudevgyan-21"
        price = "₹449 - Buy on Amazon"
    else:
        title = "Pure Copper Kalash with Lid"
        desc = "Auspicious copper vessel for Puja, Kalash Sthapana and daily water offerings."
        link = "https://www.amazon.in/s?k=pure+copper+kalash&tag=hindudevgyan-21"
        price = "₹349 - Buy on Amazon"

    return f"""
    <div style="background:#fff8f0; border:1px solid #FF9800; padding:16px; border-radius:8px; margin-top:25px; box-sizing:border-box; max-width:100%;">
        <h4 style="margin-top:0; color:#E65100; font-size:16px;">⭐ Recommended for You</h4>
        <p style="font-size:12px; color:#666; margin-bottom:10px;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:12px;">
            <div style="flex:1; min-width:180px;">
                <strong style="color:#d97706; font-size:14px;">{title}</strong>
                <p style="font-size:13px; color:#444; margin:4px 0 0 0;">{desc}</p>
            </div>
            <a href="{link}" target="_blank"
               style="background:#FF9800; color:#fff; padding:9px 16px; text-decoration:none; border-radius:4px; font-weight:bold; font-size:13px; display:inline-block; box-sizing:border-box;">{price}</a>
        </div>
    </div>
    """


# ==========================================
# CORE BOT LOGIC
# ==========================================
def get_current_pool():
    print("Fetching current mantra pool from WordPress...")
    try:
        res = requests.get(f"{WP_URL}/wp-json/hdg/v1/mantras")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Failed to fetch pool: {e}")
    return []


def find_neediest_day(pool):
    counts = {d: 0 for d in range(1, 8)}
    for m in pool:
        day = m.get('day')
        if day in counts:
            counts[day] += 1

    neediest_day = min(counts, key=counts.get)
    print(f"Current counts per day: {counts}")
    print(f"Neediest day: {neediest_day} - {DAY_NAMES[neediest_day]}")
    return neediest_day


def generate_new_mantra(target_day, existing_sanskrit_openers):
    day_description = DAY_NAMES[target_day]

    avoid_text = ""
    if existing_sanskrit_openers:
        avoid_text = (
            "\n\nDo NOT repeat any of these mantras already in our pool (matching by opening words):\n"
            + "\n".join(f"- {s}" for s in existing_sanskrit_openers)
        )

    prompt = f"""
    You are an enlightened Vedic Scholar, Senior Marketing Editor, and RankMath SEO Specialist.
    Your task is to craft a high-CTR, RankMath 100/100 SEO-optimized daily mantra post for {day_description}.

    CRITICAL REQUIREMENTS:
    1. Select a powerful, authentic Sanskrit mantra dedicated to the deity/planet of {day_description},
       widely recognized and commonly recited.
    2. Keep it short - 1 to 2 lines of Sanskrit, suitable for a small card display.
    3. Provide an accurate Hindi meaning (2-3 sentences).
    4. Provide an accurate English translation (2-3 sentences).
    5. Provide a short title in English and in Hindi.
    6. Focus Keyword: Generate a 3-4 word focus phrase (e.g., "Shani Mantra Meaning & Benefits").
    7. Headline (H1): Write a magnetic, click-tempting English headline like a Google News & Discover Editor. Trigger curiosity and awe (e.g., "Sacred Shani Mantra: Powerful Chants for Protection & Peace").
    8. URL Slug: A 4-5 word English slug derived DIRECTLY from the Focus Keyword (e.g., shani-mantra-meaning-benefits).
    9. Explanation: Write a 150-word English explanation. The VERY FIRST sentence MUST contain the exact Focus Keyword bolded inside `<strong>` tags (e.g., `<p>Reciting the <strong>Shani Mantra Meaning & Benefits</strong> brings immense cosmic harmony...</p>`).
    10. SEO META:
        - meta_title: Under 60 characters, keyword-front-loaded.
        - meta_description: Under 155 characters. IT MUST START WITH OR CONTAIN the exact Focus Keyword in the first sentence.
    11. AI Image Prompt: Write a 100% LITERAL visual scene description in ENGLISH of the physical scene for a photorealistic featured image. Describe concrete physical objects (e.g., "A sacred brass deity idol placed on a black marble altar with lit mustard oil diya lamps and dark lotus flowers, warm golden morning light, 8k realistic photography, National Geographic style"). CRITICAL: NEVER use abstract terms, anime, or Hindi words in the prompt. Describe real physical objects so the AI renders an authentic photo. Do NOT include text.
    12. Image Alt Text: A short literal description of that image containing the Focus Keyword (for Image SEO).

    Format EXACTLY as valid JSON, no markdown, no extra text:
    {{
        "title_en": "Short English Title",
        "title_hi": "संक्षिप्त हिंदी शीर्षक",
        "focus_keyword": "Focus Keyword Here",
        "headline": "Magnetic High-CTR Headline",
        "slug": "url-slug-here",
        "sanskrit": "The Sanskrit mantra text",
        "hindi": "Hindi meaning",
        "english": "English translation",
        "explanation": "Explanation with <strong>FocusKeyword</strong> in first sentence",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description starting with FocusKeyword",
        "image_prompt": "Literal visual English image generation prompt",
        "image_alt_text": "Short description containing FocusKeyword"
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt
        )
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"Failed to generate mantra: {e}")
        return None


def generate_ai_image(prompt, topic_keyword="mantras", filename="mantra_image.webp"):
    print(f"Generating 100% Relevant Artwork via Google Imagen 3 API... ({topic_keyword})")
    temp_jpg = "temp_mantra_bg.jpg"
    seed = random.randint(1, 999999)

    # Tier 1: Primary Engine - Google Imagen 3 API (`imagen-3.0-generate-002`)
    try:
        res = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=f"Photorealistic 8k artwork of {prompt}, divine lighting, highly detailed, 35mm lens, masterpiece",
            config=dict(
                number_of_images=1,
                output_mime_type='image/jpeg',
                aspect_ratio='16:9'
            )
        )
        if res and res.generated_images and len(res.generated_images[0].image.image_bytes) > 20000:
            with open(temp_jpg, "wb") as f:
                f.write(res.generated_images[0].image.image_bytes)
            print("Successfully generated 100% relevant HD artwork via Google Imagen 3 API!")
            return temp_jpg
    except Exception as e:
        print(f"Google Imagen 3 API notice ({e}), failing over to Pollinations AI engine...")

    # Tier 2: Secondary Engine - Pollinations AI
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    encoded_prompt = urllib.parse.quote(f"Photorealistic 8k artwork of {prompt}, divine golden lighting, National Geographic style")
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true&seed={seed}"

    try:
        response = requests.get(pollinations_url, stream=True, headers=headers, timeout=14)
        if response.status_code == 200 and len(response.content) > 10000:
            with open(temp_jpg, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print("Successfully generated fresh photorealistic AI background image via Pollinations engine!")
            return temp_jpg
    except Exception as e:
        print(f"Pollinations AI backup notice ({e})")

    return None


def get_cross_platform_fonts(size_title=34, size_badge=18):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf"
    ]
    font_title, font_badge = None, None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_title = ImageFont.truetype(path, size_title)
                font_badge = ImageFont.truetype(path, size_badge)
                break
            except Exception:
                pass
    if not font_title:
        try:
            font_title = ImageFont.load_default(size=size_title)
            font_badge = ImageFont.load_default(size=size_badge)
        except Exception:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()

    return font_title, font_badge


def compress_image(temp_filepath, output_filename="mantra_image.webp", headline_text="", category_text="MANTRAS & CHANTS"):
    """
    Overlays a high-CTR news thumbnail text banner at bottom,
    insets logo.png at top-right, applies UnsharpMask sharpening filter for HD crispness,
    and compresses to ultra-fast WebP format (25-45 KB).
    """
    try:
        img = Image.open(temp_filepath).convert("RGBA")
        width, height = img.size

        # 1. Dark Gradient Banner at bottom
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        banner_height = 220
        for y in range(height - banner_height, height):
            alpha = int(220 * ((y - (height - banner_height)) / banner_height))
            draw_ov.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)

        # 2. Cross-platform Font Selection (Linux + Windows bold font support)
        font_title, font_badge = get_cross_platform_fonts(size_title=34, size_badge=18)

        # 3. Category Pill Badge
        badge_text = category_text.upper()[:25]
        try:
            badge_bbox = font_badge.getbbox(badge_text)
            badge_w = (badge_bbox[2] - badge_bbox[0]) + 24
            badge_h = (badge_bbox[3] - badge_bbox[1]) + 14
        except Exception:
            badge_w, badge_h = 160, 32

        badge_x1 = 38
        badge_y1 = height - 165
        badge_x2 = badge_x1 + badge_w
        badge_y2 = badge_y1 + badge_h

        draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=6, fill=(232, 84, 10, 240))
        draw.text((badge_x1 + 12, badge_y1 + 5), badge_text, font=font_badge, fill=(255, 255, 255))

        # 4. Main Title Overlay
        clean_title = headline_text.upper()[:52]
        draw.text((38, height - 105), clean_title, font=font_title, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))

        # 5. Inset Top-Right Logo Badge
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")

            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)

            target_w = 110
            w_percent = (target_w / float(logo.size[0]))
            target_h = int((float(logo.size[1]) * float(w_percent)))
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

            margin_right = 38
            margin_top = 22
            padding = 6
            card_w = target_w + (padding * 2)
            card_h = target_h + (padding * 2)

            card_x1 = width - margin_right - card_w
            card_y1 = margin_top
            card_x2 = width - margin_right
            card_y2 = margin_top + card_h

            card_ov = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            card_draw = ImageDraw.Draw(card_ov)
            card_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=6, fill=(255, 255, 255, 235), outline=(232, 84, 10, 240), width=1)
            img = Image.alpha_composite(img, card_ov)
            img.paste(logo, (card_x1 + padding, card_y1 + padding), logo)

        # 6. Apply UnsharpMask & Save WebP
        combined = img.convert("RGB")
        sharpened = combined.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=2))
        sharpened.save(output_filename, "WEBP", quality=85)
        print(f"Compressed & News Banner Watermarked image (WebP, Sharpness enhanced, File: {output_filename})")

        if os.path.exists(temp_filepath) and temp_filepath != output_filename:
            try:
                os.remove(temp_filepath)
            except Exception:
                pass
        return output_filename
    except Exception as e:
        print(f"Could not process image (continuing with original): {e}")
        return temp_filepath


def upload_image_to_wp(image_path, alt_text=""):
    print(f"Uploading WebP AI image ({image_path}) to WordPress Media Library...")
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    mime_type = "image/webp" if image_path.endswith(".webp") else "image/jpeg"

    with open(image_path, 'rb') as file:
        headers = {
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"',
            'Content-Type': mime_type
        }
        response = requests.post(media_url, headers=headers, data=file, auth=auth)

    if response.status_code == 201:
        media_id = response.json()['id']
        if alt_text:
            try:
                requests.post(
                    f"{WP_URL}/wp-json/wp/v2/media/{media_id}",
                    json={"alt_text": alt_text, "title": alt_text},
                    auth=auth
                )
            except Exception as e:
                print(f"Could not set alt text (image still uploaded fine): {e}")
        return media_id
    else:
        print(f"Failed to upload image. Status code: {response.status_code}")
        return None


def get_or_create_category(category_name="Mantras & Chants"):
    categories_url = f"{WP_URL}/wp-json/wp/v2/categories"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    response = requests.get(categories_url, params={"search": category_name}, auth=auth)
    if response.status_code == 200:
        for cat in response.json():
            if cat['name'].lower() == category_name.lower():
                return cat['id']

    response = requests.post(categories_url, json={"name": category_name}, auth=auth)
    if response.status_code == 201:
        return response.json()['id']
    return None


def publish_mantra_post(mantra_data, category_id, media_id=None, target_day=1):
    """Publishes the mantra as its own real WordPress post, so it gets a
    genuine, unique, indexable URL - not just an anchor on a shared page."""
    print(f"Publishing '{mantra_data['title_en']}' as its own post...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    content = f"""
    <div style="background:#fffcf0; border-left:5px solid #FF9800; padding:25px; margin-bottom:30px;">
        <h3 style="color:#E65100; margin-top:0;">{mantra_data['sanskrit']}</h3>
        <p><em>"{mantra_data['english']}"</em></p>
    </div>
    <h2>हिंदी अर्थ (Hindi Meaning)</h2>
    <p>{mantra_data['hindi']}</p>
    {get_whatsapp_cta_html()}
    <h2>Significance</h2>
    <p>{mantra_data['explanation']}</p>
    {get_ebook_upsell_html()}
    {get_kundli_upsell_html()}
    {get_affiliate_html(target_day)}
    """

    ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%dT%H:%M:%S')

    payload = {
        "title": mantra_data['title_en'],
        "content": content,
        "status": "publish",
        "date": ist_now,
        "slug": mantra_data.get('slug', ''),
        "categories": [category_id] if category_id else [],
        "meta": {
            "rank_math_title": mantra_data.get('meta_title', mantra_data['title_en'])[:60],
            "rank_math_description": mantra_data.get('meta_description', '')[:160],
            "rank_math_focus_keyword": mantra_data.get('focus_keyword', '')
        }
    }
    if media_id:
        payload["featured_media"] = media_id

    response = requests.post(post_url, json=payload, auth=auth)
    if response.status_code == 201:
        post_data = response.json()
        permalink = post_data.get('link', '')
        print(f"Post published: {permalink}")
        return permalink
    else:
        print(f"Failed to publish post. Status: {response.status_code}")
        print(response.text)
        return None


def add_mantra_to_pool(mantra_data, day, post_url):
    print("Adding mantra to the sidebar widget pool...")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    payload = {
        "day": day,
        "title_en": mantra_data['title_en'],
        "title_hi": mantra_data['title_hi'],
        "sanskrit": mantra_data['sanskrit'],
        "hindi": mantra_data['hindi'],
        "english": mantra_data['english'],
        "url": post_url or ""
    }
    res = requests.post(f"{WP_URL}/wp-json/hdg/v1/mantras", json=payload, auth=auth)
    if res.status_code == 201:
        print(f"Success! Pool now has {res.json().get('total_pool_size')} mantras total.")
    else:
        print(f"Failed to add mantra to pool. Status: {res.status_code}")
        print(res.text)


def main():
    print("Starting Mantra Pool Growth Bot...")

    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables.")
        return

    pool = get_current_pool()
    target_day = find_neediest_day(pool)
    existing_openers = [m['sanskrit'][:25] for m in pool if 'sanskrit' in m]

    new_mantra = None
    for attempt in range(3):
        candidate = generate_new_mantra(target_day, existing_openers)
        if not candidate:
            continue
        if any(candidate['sanskrit'][:25] == opener for opener in existing_openers):
            print(f"Attempt {attempt + 1}: duplicate detected, retrying...")
            continue
        new_mantra = candidate
        break

    if not new_mantra:
        print("Could not generate a fresh, non-duplicate mantra after several attempts. Skipping this run.")
        return

    temp_image = generate_ai_image(new_mantra.get('image_prompt', new_mantra['title_en']), topic_keyword=new_mantra.get('slug', 'mantra'))
    media_id = None
    final_image = None
    if temp_image:
        output_webp = f"{new_mantra.get('slug', 'mantra')}.webp"
        final_image = compress_image(temp_image, output_filename=output_webp, headline_text=new_mantra.get('headline', new_mantra['title_en']), category_text="MANTRAS & CHANTS")
        media_id = upload_image_to_wp(final_image, alt_text=new_mantra.get('image_alt_text', new_mantra['title_en']))

    category_id = get_or_create_category()
    post_url = publish_mantra_post(new_mantra, category_id, media_id, target_day)

    add_mantra_to_pool(new_mantra, target_day, post_url)

    if final_image and os.path.exists(final_image):
        try:
            os.remove(final_image)
        except Exception:
            pass


if __name__ == "__main__":
    main()
