import os
import sys
import requests
import json
import random
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


def safe_generate_content(prompt):
    """
    Robustly calls Gemini API using a fallback chain of models:
    gemini-2.5-flash -> gemini-2.5-flash-lite -> gemini-3.6-flash -> gemini-flash-latest.
    Automatically retries on 429 (quota/rate limit) and 503 (high demand) errors.
    """
    if not client:
        print("Error: Gemini client not initialized.")
        return None

    models_to_try = [
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-3.6-flash',
        'gemini-flash-latest'
    ]
    last_error = None

    for model in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_msg = str(e)
                last_error = e
                print(f"Warning: Model {model} attempt {attempt+1} failed: {err_msg[:120]}")
                if any(k in err_msg for k in ['429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'quota']):
                    time.sleep(3 * (attempt + 1))
                else:
                    break

    print(f"Error: All Gemini model attempts failed. Last error: {last_error}")
    return None



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


def get_affiliate_html():
    return """
    <div style="background:#fff8f0; border:1px solid #FF9800; padding:16px; border-radius:8px; margin-top:25px; box-sizing:border-box; max-width:100%;">
        <h4 style="margin-top:0; color:#E65100; font-size:16px;">⭐ Recommended for You</h4>
        <p style="font-size:12px; color:#666; margin-bottom:10px;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:12px;">
            <div style="flex:1; min-width:180px;">
                <strong style="color:#d97706; font-size:14px;">Bhagavad Gita As It Is — Hardcover</strong>
                <p style="font-size:13px; color:#444; margin:4px 0 0 0;">The world's most widely read edition of the Gita with original Sanskrit, transliteration, and commentary.</p>
            </div>
            <a href="https://www.amazon.in/s?k=bhagavad+gita+as+it+is+hardcover&tag=hindudevgyan-21" target="_blank"
               style="background:#FF9800; color:#fff; padding:9px 16px; text-decoration:none; border-radius:4px; font-weight:bold; font-size:13px; display:inline-block; box-sizing:border-box;">₹299 - Buy on Amazon</a>
        </div>
    </div>
    """


# ==========================================
# CORE BOT LOGIC
# ==========================================
def generate_gita_wisdom(avoid_list=None):
    print("AI Guru is selecting a profound verse and generating wisdom...")

    avoid_text = ""
    if avoid_list:
        avoid_text = (
            "\n\nIMPORTANT: Do NOT use any of these verses again, they have already been covered:\n"
            + "\n".join(f"- {v}" for v in avoid_list)
        )

    prompt = f"""
    You are an enlightened Vedic Scholar, Senior Digital Marketing Manager, and RankMath SEO Specialist.
    Your task is to randomly select a deeply profound and inspiring verse from the Bhagavad Gita and write a high-CTR, RankMath 100/100 SEO-optimized article about it in English.
    Ensure you pick a different verse than the most famous ones so the daily content stays fresh.
    {avoid_text}

    CRITICAL REQUIREMENTS:
    1. Provide the original Sanskrit Sloka.
    2. Provide the exact English translation.
    3. Focus Keyword: Generate a 3-4 word phrase representing this verse (e.g., "Bhagavad Gita Chapter 3 Verse 19").
    4. Headline (H1): Write a magnetic, click-tempting English headline like a Google News & Discover Editor. Trigger curiosity and awe (e.g., "The Secret to True Peace: Bhagavad Gita Chapter 3 Verse 19").
    5. URL Slug: A 4-5 word English slug derived DIRECTLY from the Focus Keyword (e.g., bhagavad-gita-chapter-3-verse-19).
    6. Content First Paragraph: The VERY FIRST paragraph of `content_html` (after Hindi summary) MUST contain the exact Focus Keyword bolded inside `<strong>` tags (e.g., `<p>In <strong>Bhagavad Gita Chapter 3 Verse 19</strong>, Lord Krishna reveals the profound secret...</p>`).
    7. Write a 400-word philosophical explanation of how this applies to modern daily life. Use headings (<h2>) and short paragraphs.
    8. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    9. BILINGUAL WHATSAPP OPTIMIZATION: At the very top of `content_html`, before the English text, you MUST write a 2-3 sentence highly engaging Hindi summary titled '<h3>हिंदी सारांश:</h3>'.
    10. AI Image Prompt: Write a 100% LITERAL visual scene description in ENGLISH of the physical scene for a photorealistic featured image. Describe concrete physical objects (e.g., "An ancient Sanskrit manuscript resting on a sacred wooden altar in a peaceful temple, surrounded by glowing brass oil lamps and orange lotus flowers, warm golden morning light, 8k realistic photography, National Geographic style"). CRITICAL: NEVER use abstract terms, anime style, or chapter numbers in the image prompt. Describe real physical objects so the AI renders an authentic photo. Do NOT include text.
    11. Image Alt Text: A short literal description of that image containing the Focus Keyword (for Image SEO).
    12. SEO META:
        - meta_title: Under 60 characters, keyword-front-loaded.
        - meta_description: Under 155 characters. IT MUST START WITH OR CONTAIN the exact Focus Keyword in the first sentence.

    Format EXACTLY as valid JSON, with no markdown formatting around it, just raw JSON:
    {{
        "headline": "Your English Headline Here",
        "focus_keyword": "Bhagavad Gita Chapter X Verse Y",
        "slug": "bhagavad-gita-chapter-x-verse-y",
        "sanskrit": "Sanskrit text here",
        "translation": "English translation here",
        "content_html": "<h3>हिंदी सारांश:</h3><p>Your Hindi summary...</p><p>First paragraph with <strong>FocusKeyword</strong>...</p><h2>Meaning</h2><p>Your English text...</p>",
        "image_prompt": "Literal visual English image generation prompt",
        "image_alt_text": "Short description containing FocusKeyword",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars starting with FocusKeyword"
    }}
    """

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed to generate AI wisdom: Could not get response from Gemini API.")
        return None
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    try:
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Failed to parse AI wisdom JSON: {e}")
        return None


def get_recent_slokas(limit=30):
    """Pull recent Gita Wisdom post content from WordPress so we know what NOT to repeat."""
    print("Checking WordPress for previously used verses...")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    used = []
    try:
        cat_res = requests.get(f"{WP_URL}/wp-json/wp/v2/categories",
                                params={"search": "Gita Wisdom"}, auth=auth)
        category_id = None
        if cat_res.status_code == 200 and cat_res.json():
            category_id = cat_res.json()[0]["id"]

        params = {"per_page": limit, "_fields": "content"}
        if category_id:
            params["categories"] = category_id

        res = requests.get(f"{WP_URL}/wp-json/wp/v2/posts", params=params, auth=auth)
        if res.status_code == 200:
            for post in res.json():
                raw_html = post.get("content", {}).get("rendered", "")
                used.append(raw_html[:400])
    except Exception as e:
        print(f"Could not fetch recent posts (continuing without history): {e}")

    return used


def sloka_already_used(sanskrit_text, recent_content_blobs):
    snippet = sanskrit_text.strip()[:20]
    if not snippet:
        return False
    for blob in recent_content_blobs:
        if snippet in blob:
            return True
    return False


def generate_ai_image(prompt, topic_keyword="gita wisdom", filename="gita_image.webp"):
    print(f"Generating 100% Relevant Artwork via Google Imagen 3 API... ({topic_keyword})")
    temp_jpg = "temp_gita_bg.jpg"
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


def compress_image(temp_filepath, output_filename="gita_image.webp", headline_text="", category_text="GITA WISDOM"):
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


def get_or_create_category(category_name="Gita Wisdom"):
    categories_url = f"{WP_URL}/wp-json/wp/v2/categories"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    response = requests.get(categories_url, params={"search": category_name}, auth=auth)
    if response.status_code == 200:
        categories = response.json()
        for cat in categories:
            if cat['name'].lower() == category_name.lower():
                return cat['id']

    post_data = {"name": category_name}
    response = requests.post(categories_url, json=post_data, auth=auth)
    if response.status_code == 201:
        return response.json()['id']
    return None


def publish_wp_post(data, media_id, category_id):
    print("Publishing final Gita Wisdom to WordPress...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    # Sanskrit verse box at the top
    verse_box = f"""
    <div style="background:#fffcf0; border-left:5px solid #FF9800; padding:25px; margin-bottom:30px;">
        <h3 style="color:#E65100; margin-top:0;">{data['sanskrit']}</h3>
        <p><em>"{data['translation']}"</em></p>
    </div>
    """

    # Inject eBook upsell after 3rd paragraph
    paragraphs = data['content_html'].split('</p>')
    if len(paragraphs) > 3:
        paragraphs.insert(3, get_ebook_upsell_html())
    mid_content = '</p>'.join(paragraphs)

    # Inject WhatsApp CTA at mid-point
    paragraphs2 = mid_content.split('</p>')
    if len(paragraphs2) > 5:
        mid_idx = len(paragraphs2) // 2
        paragraphs2.insert(mid_idx, get_whatsapp_cta_html())
    body_content = '</p>'.join(paragraphs2)

    full_content = verse_box + body_content
    full_content += get_kundli_upsell_html()
    full_content += get_affiliate_html()

    ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%dT%H:%M:%S')

    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
        "date": ist_now,
        "slug": data['slug'],
        "categories": [category_id] if category_id else [],
        "meta": {
            "rank_math_title": data.get('meta_title', data['headline'])[:60],
            "rank_math_description": data.get('meta_description', '')[:160],
            "rank_math_focus_keyword": data.get('focus_keyword', '')
        }
    }
    if media_id:
        payload["featured_media"] = media_id

    response = requests.post(post_url, json=payload, auth=auth)

    if response.status_code == 201:
        post_data = response.json()
        permalink = post_data.get('link', f"{WP_URL}/{data['slug']}/")
        print(f"Successfully published: {permalink}!")
        return permalink
    else:
        print(f"Failed to publish. Status code: {response.status_code}")
        print(response.text)
        return None


def main():
    print("Starting Gita Wisdom Engine 3.0 (dedup + RankMath SEO + image optimization)...")

    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables.")
        return

    recent_blobs = get_recent_slokas()

    wisdom_data = None
    attempted_slokas = []

    for attempt in range(4):
        candidate = generate_gita_wisdom(avoid_list=attempted_slokas)
        if not candidate:
            continue

        if sloka_already_used(candidate['sanskrit'], recent_blobs):
            print(f"Attempt {attempt + 1}: verse already covered recently, retrying...")
            attempted_slokas.append(candidate['sanskrit'][:60])
            continue

        wisdom_data = candidate
        break

    if not wisdom_data:
        print("ERROR: Could not generate or find a fresh Gita verse. Exiting with failure code 1.")
        sys.exit(1)

    print(f"Verse Selected! Headline: {wisdom_data['headline']}")
    print(f"Focus Keyword: {wisdom_data.get('focus_keyword', 'N/A')}")

    temp_image = generate_ai_image(wisdom_data['image_prompt'], topic_keyword=wisdom_data.get('focus_keyword', 'gita wisdom'))
    media_id = None
    final_image = None
    if temp_image:
        output_webp = f"{wisdom_data['slug']}.webp"
        final_image = compress_image(temp_image, output_filename=output_webp, headline_text=wisdom_data['headline'], category_text="GITA WISDOM")
        media_id = upload_image_to_wp(final_image, alt_text=wisdom_data.get('image_alt_text', wisdom_data['headline']))

    category_id = get_or_create_category()

    post_link = publish_wp_post(wisdom_data, media_id, category_id)

    if final_image and os.path.exists(final_image):
        try:
            os.remove(final_image)
        except Exception:
            pass


if __name__ == "__main__":
    main()
