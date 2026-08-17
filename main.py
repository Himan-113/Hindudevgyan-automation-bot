import os
import sys
import requests
import json
import random
import feedparser
import urllib.parse
from urllib.parse import urlparse, parse_qs
from google import genai
from bs4 import BeautifulSoup
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

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def safe_generate_content(prompt):
    """
    Robustly calls Gemini API using a fallback chain of models:
    gemini-2.5-flash -> gemini-2.5-flash-lite -> gemini-3.6-flash -> gemini-flash-latest.
    Automatically retries on 429 (quota/rate limit) and 503 (high demand) errors.
    """
    if not client:
        print("Error: Gemini client not initialized (GEMINI_API_KEY missing).")
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


RSS_FEEDS = [
    "https://www.abplive.com/lifestyle/religion/feed",
    "https://www.jagran.com/rss/spiritual",
    "https://zeenews.india.com/hindi/religion/rss"
]

ALLOWED_CATEGORIES = [
    "Festivals & Vrat",
    "Temples & Pilgrimage",
    "Astrology & Horoscope",
    "Vedic Wisdom",
    "Gita Wisdom",
    "Panchang",
    "Mantras & Chants",
    "Mythology",
    "Spiritual News"
]


# ==========================================
# CTA HTML BLOCKS
# ==========================================
def get_whatsapp_cta_html():
    return """
    <div style="background:linear-gradient(135deg,#25D366,#128C7E); border-radius:10px; padding:22px; margin:30px 0; text-align:center;">
        <h3 style="color:#fff; margin-top:0; font-size:18px;">📲 Join Our WhatsApp Channel</h3>
        <p style="color:#dcfce7; font-size:14px; margin-bottom:15px;">
            रोज़ सुबह पाएं — पंचांग, मंत्र, और आध्यात्मिक ज्ञान सीधे WhatsApp पर。<br>
            <em>Get daily Panchang, Mantras &amp; Spiritual Wisdom every morning.</em>
        </p>
        <a href="https://whatsapp.com/channel/0029Vb8RQLz545uzablvPF3x" target="_blank"
           style="display:inline-block; background:#fff; color:#128C7E; padding:11px 26px; border-radius:25px; font-weight:bold; text-decoration:none; font-size:14px;">
           📲 Join Free — HinduDevGyan Channel
        </a>
    </div>
    """


def get_kundli_upsell_html():
    return """
    <div style="background:#FDF0DB; border-left:4px solid #E8540A; padding:20px; border-radius:6px; margin-top:30px; margin-bottom:20px;">
        <h3 style="margin-top:0; color:#E8540A;">🔮 Curious About Your Birth Chart?</h3>
        <p style="font-size:15px; color:#333; margin-bottom:15px;">Discover your exact career path, marriage compatibility, and planetary dashas based on your exact birth time.</p>
        <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#10b981; color:#fff; padding:11px 20px; border-radius:4px; font-weight:bold; text-decoration:none; font-size:14px;">✨ Generate Free Vedic Kundli</a>
        <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#E8540A; color:#fff; padding:11px 20px; border-radius:4px; font-weight:bold; text-decoration:none; margin-left:8px; font-size:14px;">📄 Unlock 50-Page PDF (₹149)</a>
    </div>
    """


def get_ebook_upsell_html():
    return """
    <div style="background:#fffbeb; border:2px dashed #f59e0b; padding:22px; border-radius:8px; margin:30px 0; text-align:center;">
        <h3 style="margin-top:0; color:#b45309; font-size:20px;">Transform Your Home's Energy Today!</h3>
        <p style="font-size:15px; color:#78350f; margin-bottom:18px;">Discover the ancient secrets to attracting wealth, health, and harmony. Download our premium 5-chapter Vastu Shastra guide instantly.</p>
        <a href="https://rzp.io/rzp/VtX5q0e" target="_blank"
           style="display:inline-block; background:#f59e0b; color:#fff; padding:13px 28px; border-radius:30px; font-weight:bold; text-decoration:none; font-size:16px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
           📖 Unlock Vastu Shastra Mastery Guide (₹99)
        </a>
    </div>
    """


def get_affiliate_html(category="general"):
    cat_str = str(category).lower()
    if 'shiva' in cat_str:
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">5 Mukhi Rudraksha Mala — 108 Beads</strong>
                    <p style="font-size:14px;">Pure Nepali Rudraksha. Enhances focus and brings Lord Shiva's blessings.</p>
                </div>
                <a href="https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21" target="_blank"
                   style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹399 - Buy on Amazon</a>
            </div>
        </div>
        """
    elif any(k in cat_str for k in ['pooja', 'festival', 'gita', 'karma']):
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">Brass Puja Thali Set — 7 Piece</strong>
                    <p style="font-size:14px;">Complete brass thali with diya, incense holder, bell and more for daily puja.</p>
                </div>
                <a href="https://www.amazon.in/s?k=brass+puja+thali+set&tag=hindudevgyan-21" target="_blank"
                   style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹599 - Buy on Amazon</a>
            </div>
        </div>
        """
    else:
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">Pure Copper Kalash with Lid</strong>
                    <p style="font-size:14px;">Auspicious copper vessel for Puja, Kalash Sthapana and daily water offerings.</p>
                </div>
                <a href="https://www.amazon.in/s?k=pure+copper+kalash&tag=hindudevgyan-21" target="_blank"
                   style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹349 - Buy on Amazon</a>
            </div>
        </div>
        """


# ==========================================
# CORE BOT LOGIC
# ==========================================
def fetch_raw_headlines():
    print("Phase 1: Aggregating raw headlines from multiple networks...")
    all_news = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                all_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": urlparse(feed_url).netloc.replace('www.', '')
                })
        except Exception as e:
            print(f"Failed to parse {feed_url}: {e}")
    return all_news


def is_duplicate(url):
    file_path = "posted_links.txt"
    if not os.path.exists(file_path):
        return False
    with open(file_path, "r") as file:
        posted = file.read().splitlines()
    return url in posted


def mark_as_posted(url):
    file_path = "posted_links.txt"
    with open(file_path, "a") as file:
        file.write(url + "\n")


def topic_already_covered_on_site(headline):
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    stopwords = {"the", "a", "an", "of", "in", "on", "and", "to", "for", "is", "why", "how"}
    significant_words = [w for w in headline.split() if len(w) > 3 and w.lower() not in stopwords]
    query = " ".join(significant_words[:5])

    if not query:
        return False

    try:
        url = f"{WP_URL}/wp-json/wp/v2/posts"
        res = requests.get(url, params={"search": query, "per_page": 5}, auth=auth)
        if res.status_code == 200 and len(res.json()) > 0:
            print(f"  -> Topic already covered on site (matched search: '{query}'). Skipping.")
            return True
    except Exception as e:
        print(f"  -> Could not verify topic uniqueness against WordPress: {e}")

    return False


def deduplicate_and_select(raw_news):
    print(f"Phase 2: Editor-in-Chief AI analyzing {len(raw_news)} raw headlines for semantic deduplication...")

    headlines_text = ""
    for i, news in enumerate(raw_news):
        headlines_text += f"{i}. {news['title']} (Source: {news['source']})\n"

    prompt = f"""
    You are the elite Editor-in-Chief of a premium Hindu Spirituality news portal.
    Below are trending headlines from various Indian news networks. Many cover the EXACT SAME EVENT.

    Your Task:
    1. Semantically group all duplicates (e.g., if Zee and ABP both report on a specific temple, count it as one story).
    2. Select the 3 most distinct, high-impact, and trending religious/spiritual topics from this list.
    3. Return ONLY a JSON array of 3 objects containing the original title and link of the chosen stories.

    Raw Headlines:
    {headlines_text}

    Format EXACTLY as valid JSON, with no other text or formatting:
    [
        {{"title": "original title 1", "link": "original link 1"}},
        {{"title": "original title 2", "link": "original link 2"}},
        {{"title": "original title 3", "link": "original link 3"}}
    ]
    """

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed AI deduplication: Could not get response from Gemini API.")
        return []
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    try:
        selected_topics = json.loads(text)
        return selected_topics
    except Exception as e:
        print(f"Failed AI deduplication JSON parsing: {e}")
        return []


def clean_category_name(raw_category):
    """Cleans up raw category string from Gemini output so it NEVER contains 'Ecommerce' or invalid text."""
    if not raw_category:
        return "Spiritual News"
    clean = str(raw_category).replace("Ecommerce", "").replace("Category:", "").strip()
    for cat in ALLOWED_CATEGORIES:
        if cat.lower() in clean.lower():
            return cat
    return "Spiritual News"


def rewrite_article_and_image_prompt(original_title):
    print("Phase 3: Scholar AI & Marketing Editor writing article and designing visual image prompt...")
    prompt = f"""
    You are an elite Hindu Religious Scholar, Vedic Expert, and SEO Specialist. Write a highly engaging, deeply respectful, and SEO-optimized article in ENGLISH based on this Hindi news/topic:
    "{original_title}"

    CRITICAL REQUIREMENTS:
    1. Language: The entire article MUST be written in high-quality, premium English.
    2. Headline (H1): Write a highly clickable, English headline. IT MUST BE 100% UNIQUE. Find a creative, spiritual angle.
    3. URL Slug: Generate a 5-6 word English translation of the headline, formatted with hyphens (e.g., significance-of-kashi-vishwanath-sawan).
    4. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    5. Formatting: Use proper HTML headings (<h2>) like "Significance", "Mythology". Use short paragraphs, bold important names/facts, and include at least one bulleted list.
    6. BILINGUAL WHATSAPP OPTIMIZATION: At the very top of your HTML Content, before the English text, you MUST write a 2-3 sentence highly engaging Hindi summary titled '<h3>हिंदी सारांश:</h3>'.
    7. Category: Choose ONE category from this exact list: Festivals & Vrat, Temples & Pilgrimage, Astrology & Horoscope, Vedic Wisdom, Gita Wisdom, Panchang, Mantras & Chants, Mythology, Spiritual News.
    8. Ecommerce Tag: Choose ONE keyword from: "shiva", "pooja", "gita", "general".
    9. Visual AI Image Prompt: Write a detailed, concrete visual description in English for Google Imagen 3 API (e.g., "Photorealistic painting of Lord Shiva meditating at Kashi Vishwanath temple during sunrise, glowing oil diyas, divine golden aura, 8k resolution"). Do NOT put text in this image prompt.
    10. Image Alt Text: Write a short, literal English description of that image.
    11. Short Image Banner Text: Provide a SHORT 3-5 WORD visual headline for the image text banner (e.g. "KASHI VISHWANATH: SAWAN GUIDELINES" or "SURYA GRAHAN 2026: COSMIC WARNING"). DO NOT copy the full long article title!
    12. SEO Meta: Provide "meta_title" (under 60 chars), "meta_description" (under 155 chars), and "focus_keyword" (2-4 word phrase).

    Format output EXACTLY as valid JSON:
    {{
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "category": "Temples & Pilgrimage",
        "ecommerce_tag": "shiva",
        "image_prompt": "Detailed concrete visual prompt for Imagen 3",
        "image_alt_text": "Short literal alt description",
        "image_banner_text": "SHORT 3-5 WORD BANNER TITLE",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars",
        "focus_keyword": "Focus keyword phrase",
        "content": "<h3>हिंदी सारांश:</h3><p>Your Hindi summary...</p><h2>First Heading</h2><p>Article body...</p>"
    }}
    """

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed to generate AI article response: Could not get response from Gemini API.")
        return None
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()

    try:
        data = json.loads(text)
        data['category'] = clean_category_name(data.get('category'))
        return data
    except Exception as e:
        print(f"Failed to parse AI article JSON: {e}")
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


def generate_ai_image(prompt, banner_text="", category_text="Spiritual News", filename="featured_image.webp"):
    print(f"Phase 4: Generating 100% Relevant HD Artwork... ({banner_text})")
    temp_jpg = "temp_bg.jpg"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(2):
        seed = random.randint(1, 999999)
        encoded_prompt = urllib.parse.quote(f"Photorealistic 8k artwork of {prompt}, divine golden lighting, National Geographic style")
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true&seed={seed}"

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


def compress_image(temp_filepath, output_filename="featured_image.webp", headline_text="", category_text="SPIRITUAL NEWS"):
    """
    Overlays a high-CTR news thumbnail text banner at bottom (260px height),
    insets logo.png at top-right, applies UnsharpMask sharpening filter for HD crispness,
    and compresses to ultra-fast WebP format (25-45 KB).
    """
    try:
        img = Image.open(temp_filepath).convert("RGBA")
        width, height = img.size

        # 1. Extended Dark Gradient Banner at bottom (260px height for breathing room)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        banner_height = 260
        for y in range(height - banner_height, height):
            alpha = int(230 * ((y - (height - banner_height)) / banner_height))
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
        badge_y1 = height - 190
        badge_x2 = badge_x1 + badge_w
        badge_y2 = badge_y1 + badge_h

        draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=6, fill=(232, 84, 10, 240))
        draw.text((badge_x1 + 12, badge_y1 + 5), badge_text, font=font_badge, fill=(255, 255, 255))

        # 4. Short Visual Banner Title Overlay (Max 45 chars, smart 3-5 word heading)
        clean_title = headline_text.upper()[:45]
        draw.text((38, height - 120), clean_title, font=font_title, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))

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


def get_or_create_category(category_name):
    clean_name = clean_category_name(category_name)
    categories_url = f"{WP_URL}/wp-json/wp/v2/categories"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    response = requests.get(categories_url, params={"search": clean_name}, auth=auth)
    if response.status_code == 200:
        categories = response.json()
        for cat in categories:
            if cat['name'].lower() == clean_name.lower():
                return cat['id']

    post_data = {"name": clean_name}
    response = requests.post(categories_url, json=post_data, auth=auth)
    if response.status_code == 201:
        return response.json()['id']
    return None


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


def publish_wp_post(data, media_id, category_id, slug, meta_title, meta_description, focus_keyword):
    print("Phase 5: Publishing flawless AI post to WordPress...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    # Inject eBook upsell mid-article (after 3rd paragraph)
    paragraphs = data['content'].split('</p>')
    if len(paragraphs) > 3:
        paragraphs.insert(3, get_ebook_upsell_html())
    mid_content = '</p>'.join(paragraphs)

    # Inject WhatsApp CTA after mid-point
    paragraphs2 = mid_content.split('</p>')
    if len(paragraphs2) > 5:
        mid_idx = len(paragraphs2) // 2
        paragraphs2.insert(mid_idx, get_whatsapp_cta_html())
    full_content = '</p>'.join(paragraphs2)

    # Append Kundli upsell + Affiliate at the end
    full_content += get_kundli_upsell_html()
    full_content += get_affiliate_html(data.get('ecommerce_tag', 'general'))

    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
        "slug": slug,
        "categories": [category_id] if category_id else [],
        "meta": {
            "rank_math_title": (meta_title or data['headline'])[:60],
            "rank_math_description": (meta_description or '')[:160],
            "rank_math_focus_keyword": focus_keyword or ''
        }
    }
    if media_id:
        payload["featured_media"] = media_id

    response = requests.post(post_url, json=payload, auth=auth)

    if response.status_code == 201:
        post_data = response.json()
        permalink = post_data.get('link', f"{WP_URL}/{slug}/")
        print(f"Successfully published: {permalink}")
        return permalink
    else:
        print(f"Failed to publish. Status code: {response.status_code}")
        print(response.text)
        return None


def main():
    print("Starting Ultimate HinduDevGyan Editor-in-Chief Bot...")

    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables.")
        return

    all_raw_news = fetch_raw_headlines()
    fresh_news = [news for news in all_raw_news if not is_duplicate(news['link'])]

    if not fresh_news:
        print("No fresh news found across any network.")
        return

    selected_topics = deduplicate_and_select(fresh_news)

    if not selected_topics:
        print("ERROR: Editor-in-Chief did not select any topics (API failure or invalid response).")
        sys.exit(1)

    print(f"Editor-in-Chief selected {len(selected_topics)} distinct topics for publication.")
    published_count = 0
    published_posts = []

    for news in selected_topics:
        print(f"\n--- Processing Master Topic: {news['title']} ---")

        rewritten = rewrite_article_and_image_prompt(news['title'])
        if not rewritten:
            continue

        if topic_already_covered_on_site(rewritten['headline']):
            mark_as_posted(news['link'])
            continue

        clean_cat = clean_category_name(rewritten.get('category'))

        print(f"Final Headline: {rewritten['headline']}")
        print(f"Clean Category: {clean_cat}")
        print(f"Focus Keyword: {rewritten.get('focus_keyword', 'N/A')}")

        banner_heading = rewritten.get('image_banner_text', rewritten['headline'][:45])
        temp_image = generate_ai_image(rewritten['image_prompt'], banner_text=banner_heading, category_text=clean_cat)
        media_id = None
        final_image = None
        if temp_image:
            output_webp = f"{rewritten['slug']}.webp"
            final_image = compress_image(temp_image, output_filename=output_webp, headline_text=banner_heading, category_text=clean_cat)
            media_id = upload_image_to_wp(final_image, alt_text=rewritten.get('image_alt_text', rewritten['headline']))

        category_id = get_or_create_category(clean_cat)

        post_link = publish_wp_post(
            rewritten,
            media_id,
            category_id,
            rewritten['slug'],
            rewritten.get('meta_title'),
            rewritten.get('meta_description'),
            rewritten.get('focus_keyword')
        )

        if post_link:
            published_posts.append({
                "title": rewritten['headline'],
                "link": post_link,
                "category": clean_cat
            })
            mark_as_posted(news['link'])
            published_count += 1

        if final_image and os.path.exists(final_image):
            try:
                os.remove(final_image)
            except Exception:
                pass

        time.sleep(5)

    if published_count == 0:
        print("ERROR: 0 articles were published despite topics being selected. Triggering failure alert.")
        sys.exit(1)


if __name__ == "__main__":
    main()
