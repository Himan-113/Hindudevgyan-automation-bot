import os
import requests
import json
import urllib.parse
from google import genai
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import time
from datetime import datetime, timedelta

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


def get_affiliate_html(category):
    if category.lower() == 'shiva':
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">5 Mukhi Rudraksha Mala — 108 Beads</strong>
                    <p style="font-size:14px;">Pure Nepali Rudraksha. Enhances focus and brings Lord Shiva's blessings.</p>
                </div>
                <a href="https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21" target="_blank" style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">₹399 - Buy on Amazon</a>
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
                    <strong style="color:#d97706;">Brass Puja Thali Set — 7 Piece</strong>
                    <p style="font-size:14px;">Complete brass thali with diya, incense holder, bell and more for daily puja.</p>
                </div>
                <a href="https://www.amazon.in/s?k=brass+puja+thali+set&tag=hindudevgyan-21" target="_blank" style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">₹599 - Buy on Amazon</a>
            </div>
        </div>
        """

def get_ebook_upsell_html():
    return """
    <div style="background:#fffbeb; border:2px dashed #f59e0b; padding:25px; border-radius:8px; margin:30px 0; text-align:center;">
        <h3 style="margin-top:0; color:#b45309; font-size:22px;">Transform Your Home's Energy Today!</h3>
        <p style="font-size:16px; color:#78350f; margin-bottom:20px;">Discover the ancient secrets to attracting wealth, health, and absolute harmony. Download our premium 5-chapter Vastu Shastra guide instantly.</p>
        <a href="https://rzp.io/rzp/VtX5q0e" target="_blank" style="display:inline-block; background:#f59e0b; color:#fff; padding:15px 30px; border-radius:30px; font-weight:bold; text-decoration:none; font-size:18px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">Unlock The Vastu Shastra Mastery Guide (₹99)</a>
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

# ==========================================
# CORE BOT LOGIC
# ==========================================
def generate_weekly_festivals():
    print("AI Astrologer is calculating upcoming festivals for the week...")

    today = datetime.now()
    next_week = today + timedelta(days=7)
    date_range = f"{today.strftime('%B %d, %Y')} to {next_week.strftime('%B %d, %Y')}"

    prompt = f"""
    You are an enlightened Vedic Astrologer and Historian.
    Write a 600-word comprehensive guide about the upcoming Hindu Festivals and Vrats for the week of: {date_range}.

    CRITICAL REQUIREMENTS:
    1. Write an SEO optimized, highly clickable Headline.
    2. Provide a 5-6 word URL Slug.
    3. Categorize the article for ecommerce. Choose one: "shiva" or "pooja".
    4. Provide the main article content in beautiful HTML format.
    5. Internal Linking rules:
       - Mentions of Kundli/Birth Chart/Horoscope -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of Vastu -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of Panchang/Muhurat -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of Bhagavad Gita/Karma -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
    6. BILINGUAL: At the very top of content_html write a Hindi summary titled '<h3>हिंदी सारांश:</h3>'.
    7. Generate an AI image prompt for the festival mood.

    Format EXACTLY as valid JSON:
    {{"headline": "...", "slug": "...", "ecommerce_category": "pooja", "content_html": "...", "image_prompt": "..."}}
    """

    try:
        response = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
        text = response.text
        if text.startswith("```json"): text = text[7:-3].strip()
        elif text.startswith("```"): text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"Failed to generate AI article: {e}")
        return None

def generate_ai_image(prompt, filename="festival_image.jpg"):
    print(f"Generating HD Festival AI Image... ({prompt})")
    high_quality_prompt = f"{prompt}, 8k resolution, highly detailed, sharp focus, vivid colors, festive lighting, masterwork"
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
        return None
    except Exception:
        return None


def compress_image(filepath, quality=82):
    """
    Overlays the actual HinduDevGyan logo (logo.png) in the top-right corner,
    applies UnsharpMask sharpening filter for HD crispness,
    and compresses with web-optimized JPEG settings.
    """
    try:
        img = Image.open(filepath).convert("RGBA")
        width, height = img.size

        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")

            # Convert near-white background pixels to transparent
            datas = logo.getdata()
            new_data = []
            for item in datas:
                if item[0] > 230 and item[1] > 230 and item[2] > 230:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            logo.putdata(new_data)

            # Resize logo to width = 210px (maintaining aspect ratio)
            target_w = 210
            w_percent = (target_w / float(logo.size[0]))
            target_h = int((float(logo.size[1]) * float(w_percent)))
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

            # White semi-transparent rounded backing card for high visibility
            margin = 18
            padding = 8
            card_w = target_w + (padding * 2)
            card_h = target_h + (padding * 2)

            card_x1 = width - margin - card_w
            card_y1 = margin
            card_x2 = width - margin
            card_y2 = margin + card_h

            overlay = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=8, fill=(255, 255, 255, 225), outline=(232, 84, 10, 240), width=2)

            # Composite card onto image
            img = Image.alpha_composite(img, overlay)

            # Paste logo inside card
            logo_x = card_x1 + padding
            logo_y = card_y1 + padding
            img.paste(logo, (logo_x, logo_y), logo)

        # Apply UnsharpMask sharpening filter
        combined = img.convert("RGB")
        sharpened = combined.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))

        # Save with web-optimized JPEG compression
        sharpened.save(filepath, "JPEG", quality=quality, optimize=True, progressive=True)
        print(f"Compressed & Logo Watermarked image (Sharpness enhanced, Quality={quality})")
    except Exception as e:
        print(f"Could not process image (continuing with original): {e}")
    return filepath

def upload_image_to_wp(image_path):
    print("Uploading image to WordPress...")
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    with open(image_path, 'rb') as file:
        headers = {'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"', 'Content-Type': 'image/jpeg'}
        response = requests.post(media_url, headers=headers, data=file, auth=auth)
        if response.status_code == 201:
            return response.json()['id']
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

    payload = {
        "title": data['headline'], "content": full_content, "status": "publish",
        "slug": data['slug'], "categories": [category_id] if category_id else []
    }
    if media_id:
        payload["featured_media"] = media_id

    response = requests.post(post_url, json=payload, auth=auth)
    if response.status_code == 201:
        print(f"Successfully published: {data['headline']}!")
    else:
        print(f"Failed to publish. Status code: {response.status_code}")

def main():
    print("Starting Weekly Festival & Commerce Bot...")
    if datetime.now().weekday() != 6:
        print("Today is not Sunday. The Weekly Festival Bot will sleep.")
        return
    article_data = generate_weekly_festivals()
    if not article_data:
        return
    print(f"AI Editor selected headline: {article_data['headline']}")
    image_path = generate_ai_image(article_data['image_prompt'])
    media_id = None
    if image_path:
        compress_image(image_path)
        media_id = upload_image_to_wp(image_path)
    category_id = get_or_create_category()
    publish_wp_post(article_data, media_id, category_id)
    if image_path and os.path.exists(image_path):
        os.remove(image_path)


if __name__ == "__main__":
    main()
