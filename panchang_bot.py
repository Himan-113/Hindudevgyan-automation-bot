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
PROKERALA_CLIENT_ID = os.getenv("PROKERALA_CLIENT_ID")
PROKERALA_CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET")

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
# DUPLICATE PROTECTION
# ==========================================
def already_published_today():
    print("Checking WordPress for today's panchang post...")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    start_of_day_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc_iso = start_of_day_ist.astimezone(pytz.utc).isoformat()
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    params = {"after": start_of_day_utc_iso, "per_page": 30, "_fields": "title"}
    try:
        res = requests.get(url, params=params, auth=auth)
        if res.status_code == 200:
            keywords = ["panchang", "horoscope", "nakshatra", "tithi"]
            for post in res.json():
                title = post.get("title", {}).get("rendered", "").lower()
                if any(k in title for k in keywords):
                    print(f"Found existing post today: {post.get('title', {}).get('rendered')}")
                    return True
    except Exception as e:
        print(f"Could not check WordPress for existing posts (continuing cautiously): {e}")
        return True
    return False


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
    elif category.lower() in ('pooja', 'festival'):
        title = "Brass Puja Thali Set — 7 Piece"
        desc = "Complete brass thali with diya, incense holder, bell and more for daily puja."
        link = "https://www.amazon.in/s?k=brass+puja+thali+set&tag=hindudevgyan-21"
        price = "₹599 - Buy on Amazon"
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
        <h3 style="margin-top:0; color:#E8540A; font-size:18px;">Curious how today's Nakshatra affects you?</h3>
        <p style="font-size:14px; color:#333; margin-bottom:14px;">Discover your exact career path, marriage compatibility, and planetary dashas based on your exact birth time.</p>
        <div style="display:flex; flex-wrap:wrap; gap:10px;">
            <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#10b981; color:#fff; padding:10px 16px; border-radius:4px; font-weight:bold; text-decoration:none; font-size:13px; text-align:center; flex:1; min-width:160px; box-sizing:border-box;">Generate Free Vedic Kundli</a>
            <a href="https://hindudevgyan.in/free-kundli/" style="display:inline-block; background:#E8540A; color:#fff; padding:10px 16px; border-radius:4px; font-weight:bold; text-decoration:none; font-size:13px; text-align:center; flex:1; min-width:160px; box-sizing:border-box;">Unlock 50-Page Premium PDF (₹149)</a>
        </div>
    </div>
    """


# ==========================================
# CORE BOT LOGIC
# ==========================================
def get_prokerala_panchang():
    print("Authenticating with Prokerala API...")
    token_url = "https://api.prokerala.com/token"
    token_payload = {'grant_type': 'client_credentials', 'client_id': PROKERALA_CLIENT_ID, 'client_secret': PROKERALA_CLIENT_SECRET}
    try:
        token_res = requests.post(token_url, data=token_payload)
        token_res.raise_for_status()
        access_token = token_res.json().get('access_token')
        lat, lon = "28.6139", "77.2090"
        ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        panchang_url = f"https://api.prokerala.com/v2/astrology/panchang?datetime={urllib.parse.quote(ist_now)}&coordinates={lat},{lon}&ayanamsa=1"
        headers = {'Authorization': f'Bearer {access_token}'}
        print("Fetching Exact Daily Panchang...")
        astro_res = requests.get(panchang_url, headers=headers)
        astro_res.raise_for_status()
        return astro_res.json()
    except Exception as e:
        print(f"Failed to fetch Prokerala data: {e}")
        return None


def generate_panchang_article(astro_data):
    print("Passing precise astronomical data to AI Editor...")
    nakshatra = astro_data['data']['nakshatra'][0]['name']
    tithi = astro_data['data']['tithi'][0]['name']
    karana = astro_data['data']['karana'][0]['name']
    yoga = astro_data['data']['yoga'][0]['name']

    prompt = f"""
    You are an enlightened Vedic Astrologer, Senior Marketing Editor, and RankMath SEO Specialist. Write a high-CTR 500-word daily panchang article for today.
    Nakshatra: {nakshatra}, Tithi: {tithi}, Karana: {karana}, Yoga: {yoga}

    CRITICAL REQUIREMENTS:
    1. Focus Keyword: Generate a clear 3-4 word focus phrase (e.g. "Today Panchang Shubh Muhurat" or "Daily Vedic Panchang").
    2. Headline (H1): Write a magnetic, click-tempting English headline like a Google News & Discover Editor. Trigger curiosity and awe (e.g. "Sacred Panchang Today: Auspicious Muhurat & Daily Nakshatra Wisdom").
    3. URL Slug: A 4-5 word English slug derived DIRECTLY from the Focus Keyword (e.g. today-panchang-shubh-muhurat).
    4. Content First Paragraph: The VERY FIRST paragraph of `content_html` (after Hindi summary) MUST contain the exact Focus Keyword bolded inside `<strong>` tags (e.g., `<p>According to <strong>Today Panchang Shubh Muhurat</strong>, the celestial alignments bring immense spiritual energy...</p>`).
    5. Internal linking: Kundli -> https://hindudevgyan.in/free-kundli/, Vastu -> /category/vastu/, Panchang -> /category/panchang/, Gita/Karma -> /category/gita-wisdom/
    6. BILINGUAL: At the very top of content_html write a Hindi summary titled '<h3>हिंदी सारांश:</h3>'.
    7. AI Image Prompt: Write a 100% LITERAL visual scene description in ENGLISH of the physical scene for a photorealistic featured image. Describe concrete physical objects (e.g. "A traditional brass Panchang calendar manuscript resting on a sacred marble altar, surrounded by orange marigold flowers and glowing oil diya lamps, warm golden morning light, 8k realistic photography, National Geographic style"). CRITICAL: NEVER use abstract astrological symbols, anime, or Hindi words in the prompt. Describe real physical objects so the AI renders an authentic photo. Do NOT include text.
    8. Image Alt Text: A short literal description of that image containing the Focus Keyword (for Image SEO).
    9. SEO META:
       - meta_title: Under 60 characters, keyword-front-loaded.
       - meta_description: Under 155 characters. IT MUST START WITH OR CONTAIN the exact Focus Keyword in the first sentence.
    10. Ecommerce category: "shiva", "pooja", or "general".

    Format as valid JSON:
    {{"headline": "...", "focus_keyword": "...", "slug": "...", "ecommerce_category": "general", "content_html": "...", "image_prompt": "...", "image_alt_text": "...", "meta_title": "...", "meta_description": "..."}}
    """

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed to generate AI article: Could not get response from Gemini API.")
        return None
    text = raw_text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    elif text.startswith("```"): text = text[3:-3].strip()

    try:
def generate_ai_image(prompt, topic_keyword="panchang", filename="panchang_image.webp"):
    """
    Calls centralized image_engine with Cloudflare FLUX.1 [schnell] & tight watermark badge.
    """
    from image_engine import generate_hd_featured_image
    return generate_hd_featured_image(prompt, category="Panchang", output_filename=filename)


def compress_image(temp_filepath, output_filename="panchang_image.webp", headline_text="", category_text="PANCHANG"):
    """
    Applies smart watermark if not already applied.
    """
    from image_engine import apply_smart_logo_watermark
    return apply_smart_logo_watermark(temp_filepath, output_filename)_filename
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


def get_or_create_category(category_name="Daily Panchang"):
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


def publish_wp_post(data, astro_data, media_id, category_id):
    print("Publishing to WordPress with E-Commerce & Kundli Upsells...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    nakshatra = astro_data['data']['nakshatra'][0]['name']
    tithi = astro_data['data']['tithi'][0]['name']

    panchang_box = f"""
    <div style="background:#f8f9fa; border-left:5px solid #2563eb; padding:25px; margin-bottom:30px;">
        <h3 style="color:#1d4ed8; margin-top:0;">Exact Planetary Positions Today</h3>
        <p><strong>Tithi:</strong> {tithi}</p>
        <p><strong>Nakshatra:</strong> {nakshatra}</p>
    </div>
    """

    paragraphs = data['content_html'].split('</p>')
    if len(paragraphs) > 3:
        paragraphs.insert(3, get_ebook_upsell_html())
    if len(paragraphs) > 5:
        mid_idx = len(paragraphs) // 2
        paragraphs.insert(mid_idx, get_whatsapp_cta_html())
    mid_injected_html = '</p>'.join(paragraphs)

    full_content = panchang_box + mid_injected_html
    full_content += get_kundli_upsell_html()
    full_content += get_affiliate_html(data['ecommerce_category'])
    full_content += """<hr style="margin-top:30px;"><p style="font-size:12px; color:#888;"><em><strong>Disclaimer:</strong> This daily astrological forecast is algorithmically generated based on precise astronomical calculations. It is for spiritual guidance and entertainment purposes only.</em></p>"""

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
    print("Starting Daily Panchang & Monetization Bot...")
    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD, PROKERALA_CLIENT_ID, PROKERALA_CLIENT_SECRET]):
        print("ERROR: Missing environment variables.")
        return
    if already_published_today():
        print("A panchang/horoscope post already exists for today. Skipping to avoid a duplicate.")
        return
    astro_data = get_prokerala_panchang()
    if not astro_data:
        print("ERROR: Failed to fetch Prokerala Panchang data. Exiting with failure code 1.")
        sys.exit(1)
    article_data = generate_panchang_article(astro_data)
    if not article_data:
        print("ERROR: Failed to generate Panchang article. Exiting with failure code 1.")
        sys.exit(1)
    print(f"AI Editor selected headline: {article_data['headline']}")
    print(f"Focus Keyword: {article_data.get('focus_keyword', 'N/A')}")
    temp_image = generate_ai_image(article_data['image_prompt'], topic_keyword=article_data.get('focus_keyword', 'panchang'))
    media_id = None
    final_image = None
    if temp_image:
        output_webp = f"{article_data['slug']}.webp"
        final_image = compress_image(temp_image, output_filename=output_webp, headline_text=article_data['headline'], category_text="PANCHANG")
        media_id = upload_image_to_wp(final_image, alt_text=article_data.get('image_alt_text', article_data['headline']))
    category_id = get_or_create_category()
    post_link = publish_wp_post(article_data, astro_data, media_id, category_id)

    if final_image and os.path.exists(final_image):
        try:
            os.remove(final_image)
        except Exception:
            pass


if __name__ == "__main__":
    main()
