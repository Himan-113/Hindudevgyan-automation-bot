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

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


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
        'gemini-1.5-flash',
        'gemini-1.5-pro',
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
                    time.sleep(6 * (attempt + 1))
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
    10. AI Image Prompt: Write a 100% LITERAL visual scene description in ENGLISH focusing on traditional Hindu iconography and scriptures. Describe physical objects cleanly (e.g., "An ancient Sanskrit manuscript resting on a sacred wooden altar in a peaceful temple inner sanctum, surrounded by glowing brass oil lamps and orange lotus flowers"). CRITICAL STYLE RESTRICTIONS: Do NOT include abstract words. NEVER include chapter numbers, verse numbers, or alphabetic text of any kind in the image prompt. Never use words like "photography", "photorealistic", "3D render", or "digital game art". Describe only real, classic, physical objects.
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
    """
    Calls centralized image_engine with Cloudflare FLUX.1 [schnell] & tight watermark badge.
    """
    from image_engine import generate_hd_featured_image
    return generate_hd_featured_image(prompt, category="Gita Wisdom", output_filename=filename)


def compress_image(temp_filepath, output_filename="gita_image.webp", headline_text="", category_text="GITA WISDOM"):
    """
    Applies smart watermark if not already applied.
    """
    from image_engine import apply_smart_logo_watermark
    return apply_smart_logo_watermark(temp_filepath, output_filename)


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
