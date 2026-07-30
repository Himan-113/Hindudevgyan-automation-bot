import os
import requests
import json
import urllib.parse
from google import genai
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import time

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================
# CTA HTML BLOCKS
# ==========================================
def get_whatsapp_cta_html():
    return """
    <div style="background:linear-gradient(135deg,#25D366,#128C7E); border-radius:10px; padding:22px; margin:30px 0; text-align:center;">
        <h3 style="color:#fff; margin-top:0; font-size:18px;">📲 Join Our WhatsApp Channel</h3>
        <p style="color:#dcfce7; font-size:14px; margin-bottom:15px;">
            रोज़ सुबह पाएं — पंचांग, मंत्र, और आध्यात्मिक ज्ञान सीधे WhatsApp पर।<br>
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


def get_affiliate_html():
    return """
    <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
        <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
        <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
        <div style="display:flex; align-items:center; gap:15px;">
            <div style="flex:1;">
                <strong style="color:#d97706;">Bhagavad Gita As It Is — Hardcover</strong>
                <p style="font-size:14px;">The world's most widely read edition of the Gita with original Sanskrit, transliteration, and commentary.</p>
            </div>
            <a href="https://www.amazon.in/s?k=bhagavad+gita+as+it+is+hardcover&tag=hindudevgyan-21" target="_blank"
               style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹299 - Buy on Amazon</a>
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
    You are an enlightened Vedic Scholar and SEO Expert.
    Your task is to randomly select a deeply profound and inspiring verse from the Bhagavad Gita and write a beautiful article about it in English.
    Ensure you pick a different verse than the most famous ones so the daily content stays fresh.
    {avoid_text}

    CRITICAL REQUIREMENTS:
    1. Provide the original Sanskrit Sloka.
    2. Provide the exact English translation.
    3. Write a 400-word philosophical explanation of how this applies to modern daily life. Use headings (<h2>) and short paragraphs.
    4. Provide an SEO optimized, highly clickable Headline.
    5. Provide a 5-6 word URL Slug.
    6. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    7. BILINGUAL WHATSAPP OPTIMIZATION: At the very top of `content_html`, before the English text, you MUST write a 2-3 sentence highly engaging Hindi summary titled '<h3>हिंदी सारांश:</h3>'. This will be pulled by WhatsApp for sharing previews.
    8. Generate a highly descriptive English prompt for an AI Image Generator (e.g. "Cinematic realistic painting of Arjuna looking at Krishna, divine golden light, beautiful details, 4k"). Do NOT include any text in the image prompt.
    9. Also generate a short, literal ALT TEXT description of that same image in plain English (e.g. "Arjuna and Krishna on a chariot at Kurukshetra with golden light") - this is for accessibility and image SEO, not the same as the creative prompt.
    10. SEO META: Provide "meta_title" (a compelling, keyword-front-loaded title under 60 characters, can differ slightly from the headline), "meta_description" (a click-worthy summary under 155 characters), and "focus_keyword" (the single 2-4 word phrase this article should rank for, e.g. "Bhagavad Gita chapter 6 verse 5").

    Format EXACTLY as valid JSON, with no markdown formatting around it, just raw JSON:
    {{
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "sanskrit": "Sanskrit text here",
        "translation": "English translation here",
        "content_html": "<h3>हिंदी सारांश:</h3><p>Your Hindi summary here...</p><h2>Meaning</h2><p>Your English text...</p>",
        "image_prompt": "Your image prompt here",
        "image_alt_text": "Short literal description of the image",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars",
        "focus_keyword": "2-4 word focus phrase"
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

        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Failed to generate AI wisdom: {e}")
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


def generate_ai_image(prompt, filename="gita_image.jpg"):
    print(f"Generating HD Spiritual AI Image... ({prompt})")
    high_quality_prompt = f"{prompt}, 8k resolution, highly detailed, sharp focus, vivid colors, cinematic lighting, masterwork"
    encoded_prompt = urllib.parse.quote(high_quality_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true&model=flux"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print("Successfully generated AI image!")
            return filename
        else:
            print("Failed to generate AI image.")
            return None
    except Exception as e:
        print(f"Image generation error: {e}")
        return None


def compress_image(filepath, quality=82):
    """
    Applies UnsharpMask filter for crispness, adds a semi-transparent 'HinduDevGyan'
    watermark badge in the top-right corner to protect image rights on Google Images,
    and compresses with web-optimized JPEG settings.
    """
    try:
        img = Image.open(filepath).convert("RGBA")
        width, height = img.size

        # Create transparent overlay for watermark badge
        overlay = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        text = "🚩 HinduDevGyan"
        margin = 20
        badge_width = 180
        badge_height = 36
        x1 = width - margin - badge_width
        y1 = margin
        x2 = width - margin
        y2 = margin + badge_height

        # Semi-transparent dark pill with saffron border
        draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(15, 23, 42, 175), outline=(232, 84, 10, 220), width=1)

        # Draw text centered in badge
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x1 + (badge_width - tw) / 2
        ty = y1 + (badge_height - th) / 2 - 1

        draw.text((tx, ty), text, fill=(255, 255, 255, 240), font=font)

        # Composite overlay
        combined = Image.alpha_composite(img, overlay).convert("RGB")

        # Apply UnsharpMask sharpening filter
        sharpened = combined.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))

        # Save with web-optimized JPEG compression
        sharpened.save(filepath, "JPEG", quality=quality, optimize=True, progressive=True)
        print(f"Compressed & Watermarked image (Sharpness enhanced, Quality={quality})")
    except Exception as e:
        print(f"Could not process image (continuing with original): {e}")
    return filepath


def upload_image_to_wp(image_path, alt_text=""):
    print("Uploading image to WordPress...")
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    with open(image_path, 'rb') as file:
        headers = {
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"',
            'Content-Type': 'image/jpeg'
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

    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
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
        print(f"Successfully published: {data['headline']}!")
    else:
        print(f"Failed to publish. Status code: {response.status_code}")
        print(response.text)


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
        print("Could not find a fresh, uncovered verse after several attempts. Skipping today's run.")
        return

    print(f"Verse Selected! Headline: {wisdom_data['headline']}")
    print(f"Focus Keyword: {wisdom_data.get('focus_keyword', 'N/A')}")

    image_path = generate_ai_image(wisdom_data['image_prompt'])
    media_id = None
    if image_path:
        compress_image(image_path)
        media_id = upload_image_to_wp(image_path, alt_text=wisdom_data.get('image_alt_text', wisdom_data['headline']))

    category_id = get_or_create_category()

    publish_wp_post(wisdom_data, media_id, category_id)

    if image_path and os.path.exists(image_path):
        os.remove(image_path)


if __name__ == "__main__":
    main()
