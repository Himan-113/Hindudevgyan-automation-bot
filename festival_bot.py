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
from datetime import datetime, timedelta
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
        'gemini-3.6-flash',
        'gemini-2.5-flash-lite',
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


def get_affiliate_html(category="general"):
    if category.lower() == 'shiva':
        title = "5 Mukhi Rudraksha Mala — 108 Beads"
        desc = "Pure Nepali Rudraksha. Enhances focus and brings Lord Shiva's blessings."
        link = "https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21"
        price = "₹399 - Buy on Amazon"
    else:
        title = "Brass Puja Thali Set — 7 Piece"
        desc = "Complete brass thali with diya, incense holder, bell and more for daily puja."
        link = "https://www.amazon.in/s?k=brass+puja+thali+set&tag=hindudevgyan-21"
        price = "₹599 - Buy on Amazon"

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


def get_ebook_upsell_html():
    return """
    <div style="background:#fffbeb; border:2px dashed #f59e0b; padding:18px 12px; border-radius:8px; margin:25px 0; text-align:center; box-sizing:border-box; max-width:100%;">
        <h3 style="margin-top:0; color:#b45309; font-size:18px;">Transform Your Home's Energy Today!</h3>
        <p style="font-size:14px; color:#78350f; margin-bottom:15px;">Discover the ancient secrets to attracting wealth, health, and absolute harmony. Download our premium 5-chapter Vastu Shastra guide instantly.</p>
        <a href="https://rzp.io/rzp/VtX5q0e" target="_blank" style="display:inline-block; background:#f59e0b; color:#fff; padding:11px 20px; border-radius:30px; font-weight:bold; text-decoration:none; font-size:14px; box-shadow:0 4px 6px rgba(0,0,0,0.1); max-width:100%; box-sizing:border-box;">Unlock The Vastu Shastra Mastery Guide (₹99)</a>
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

# ==========================================
# CORE BOT LOGIC
# ==========================================
def generate_weekly_festivals():
    print("AI Astrologer is calculating upcoming festivals for the week...")

    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    next_week = today + timedelta(days=7)
    date_range = f"{today.strftime('%B %d, %Y')} to {next_week.strftime('%B %d, %Y')}"

    prompt = f"""
    You are an enlightened Vedic Astrologer, Senior Marketing Editor, and RankMath SEO Specialist.
    Write a 600-word comprehensive, high-CTR guide about the upcoming Hindu Festivals and Vrats for the week of: {date_range}.

    CRITICAL REQUIREMENTS:
    1. Focus Keyword: Generate a clear 3-4 word focus phrase (e.g. "Upcoming Hindu Festivals This Week" or "Hindu Vrat Dates").
    2. Headline (H1): Write a magnetic, click-tempting English headline like a Google News & Discover Editor. Trigger curiosity and awe (e.g. "Sacred Calendar: Upcoming Hindu Festivals & Vrat Dates This Week").
    3. URL Slug: A 4-5 word English slug derived DIRECTLY from the Focus Keyword (e.g. upcoming-hindu-festivals-this-week).
    4. Content First Paragraph: The VERY FIRST paragraph of `content_html` (after Hindi summary) MUST contain the exact Focus Keyword bolded inside `<strong>` tags (e.g., `<p>Discover the sacred dates and rituals of <strong>Upcoming Hindu Festivals This Week</strong>...</p>`).
    5. Categorize the article for ecommerce. Choose one: "shiva" or "pooja".
    6. Internal Linking rules:
       - Mentions of Kundli/Birth Chart/Horoscope -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of Vastu -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of Panchang/Muhurat -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of Bhagavad Gita/Karma -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
    7. BILINGUAL: At the very top of content_html write a Hindi summary titled '<h3>हिंदी सारांश:</h3>'.
    8. AI Image Prompt: Write a 100% LITERAL visual scene description in ENGLISH of the physical scene for a photorealistic featured image. Describe concrete physical objects (e.g. "A traditional Indian temple altar decorated with fresh orange marigold garlands, burning brass diya lamps, and sacred festival puja thali, 8k realistic photography, National Geographic style"). CRITICAL: NEVER use abstract terms, anime, or Hindi words in the prompt. Describe real physical objects so the AI renders an authentic photo. Do NOT include text.
    9. Image Alt Text: A short literal description of that image containing the Focus Keyword (for Image SEO).
    10. SEO META:
        - meta_title: Under 60 characters, keyword-front-loaded.
        - meta_description: Under 155 characters. IT MUST START WITH OR CONTAIN the exact Focus Keyword in the first sentence.

    Format EXACTLY as valid JSON:
    {{"headline": "...", "focus_keyword": "...", "slug": "...", "ecommerce_category": "pooja", "content_html": "...", "image_prompt": "...", "image_alt_text": "...", "meta_title": "...", "meta_description": "..."}}
    """

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed to generate AI article: Could not get response from Gemini API.")
        return None
    text = raw_text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    elif text.startswith("```"): text = text[3:-3].strip()

    try:
        return json.loads(text)
    except Exception as e:
        print(f"Failed to parse AI article JSON: {e}")
        return None

def generate_ai_image(prompt, topic_keyword="festival", filename="festival_image.webp"):
    print(f"Generating 100% Relevant HD Artwork... ({topic_keyword})")
    temp_jpg = "temp_festival_bg.jpg"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(2):
        seed = random.randint(1, 999999)
        encoded_prompt = urllib.parse.quote(f"Photorealistic 8k artwork of {prompt}, divine golden lighting, National Geographic style")
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1200&height=630&nologo=true&enhance=true&seed={seed}"

        try:
            response = requests.get(pollinations_url, stream=True, headers=headers, timeout=25)
            if response.status_code == 200 and len(response.content) > 10000:
                with open(temp_jpg, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print("Successfully generated fresh photorealistic AI background image!")
                return temp_jpg
        except Exception as e:
            print(f"Image engine attempt {attempt+1} notice ({e})")
            time.sleep(2)

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


def compress_image(temp_filepath, output_filename="festival_image.webp", headline_text="", category_text="FESTIVAL & VRAT"):
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
        headers = {'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"', 'Content-Type': mime_type}
        response = requests.post(media_url, headers=headers, data=file, auth=auth)
    if response.status_code == 201:
        media_id = response.json()['id']
        if alt_text:
            try:
                requests.post(f"{WP_URL}/wp-json/wp/v2/media/{media_id}", json={"alt_text": alt_text, "title": alt_text}, auth=auth)
            except Exception as e:
                print(f"Could not set alt text: {e}")
        return media_id
    return None

def get_or_create_category(category_name="Festivals & Vrat"):
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

def publish_wp_post(data, media_id, category_id):
    print("Publishing Weekly Festival Guide to WordPress...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    paragraphs = data['content_html'].split('</p>')
    if len(paragraphs) > 3:
        paragraphs.insert(3, get_ebook_upsell_html())
    if len(paragraphs) > 5:
        mid_idx = len(paragraphs) // 2
        paragraphs.insert(mid_idx, get_whatsapp_cta_html())
    full_content = '</p>'.join(paragraphs)
    full_content += get_kundli_upsell_html()
    full_content += get_affiliate_html(data['ecommerce_category'])
    full_content += """<hr style="margin-top:30px;"><p style="font-size:12px; color:#888;"><em><strong>Disclaimer:</strong> Festival dates and timings can vary by geographical location. Please consult your local temple or pandit for exact Muhurats.</em></p>"""

    ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%dT%H:%M:%S')

    payload = {
        "title": data['headline'], "content": full_content, "status": "publish",
        "date": ist_now,
        "slug": data['slug'], "categories": [category_id] if category_id else [],
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
        return None

def main():
    print("Starting Weekly Festival & Commerce Bot...")
    if datetime.now().weekday() != 6:
        print("Today is not Sunday. The Weekly Festival Bot will sleep.")
        return
    article_data = generate_weekly_festivals()
    if not article_data:
        print("ERROR: Failed to generate weekly festival article. Exiting with failure code 1.")
        sys.exit(1)
    print(f"AI Editor selected headline: {article_data['headline']}")
    print(f"Focus Keyword: {article_data.get('focus_keyword', 'N/A')}")
    temp_image = generate_ai_image(article_data['image_prompt'], topic_keyword=article_data.get('focus_keyword', 'festival'))
    media_id = None
    final_image = None
    if temp_image:
        output_webp = f"{article_data['slug']}.webp"
        final_image = compress_image(temp_image, output_filename=output_webp, headline_text=article_data['headline'], category_text="FESTIVAL & VRAT")
        media_id = upload_image_to_wp(final_image, alt_text=article_data.get('image_alt_text', article_data['headline']))
    category_id = get_or_create_category()
    post_link = publish_wp_post(article_data, media_id, category_id)

    if final_image and os.path.exists(final_image):
        try:
            os.remove(final_image)
        except Exception:
            pass


if __name__ == "__main__":
    main()
