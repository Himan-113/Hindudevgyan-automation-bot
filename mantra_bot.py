import os
import requests
import json
import re
import urllib.parse
from google import genai
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


def get_affiliate_html(day):
    """Returns contextual affiliate product based on the day's ruling deity."""
    if day in (1, 6):  # Monday=Shiva, Saturday=Shani
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
    elif day == 5:  # Friday=Lakshmi
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">Brass Lakshmi Idol — 6 inch</strong>
                    <p style="font-size:14px;">Beautifully crafted brass Lakshmi idol for home puja and wealth attraction.</p>
                </div>
                <a href="https://www.amazon.in/s?k=brass+lakshmi+idol+for+home&tag=hindudevgyan-21" target="_blank"
                   style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹449 - Buy on Amazon</a>
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
    You are an enlightened Vedic Scholar and SEO Expert. Provide one short, well-known,
    authentic Sanskrit mantra or shloka appropriate for {day_description}.
    {avoid_text}

    Requirements:
    1. Must be a genuine, traditional Sanskrit mantra (not invented) - one that is
       widely recognized and commonly recited, appropriate for {day_description}.
    2. Keep it short - 1 to 2 lines of Sanskrit, suitable for a small card display.
    3. Provide an accurate Hindi meaning (2-3 sentences).
    4. Provide an accurate English translation (2-3 sentences).
    5. Provide a short title in English and in Hindi.
    6. Write a slightly longer (100-150 word) English explanation of the mantra's
       significance and when/how it is traditionally recited - this will be published
       as its own short article, so it needs enough substance to be a real page.
    7. SEO META: "meta_title" (under 60 characters, e.g. "Shani Mantra - Meaning & Benefits"),
       "meta_description" (under 155 characters), "focus_keyword" (2-4 words,
       e.g. "Shani mantra meaning").
    8. URL Slug: a 3-5 word English slug for this mantra, hyphenated (e.g. "shani-mantra-meaning-benefits").
    9. AI Image Prompt: Write a highly descriptive, cinematic English prompt for an AI Image
       Generator to create a featured image representing this mantra's deity/theme
       (e.g. "Cinematic realistic image of Lord Shiva meditating in the Himalayas, golden
       hour lighting, 8k, highly detailed"). Do NOT include any text in the image.
    10. Image Alt Text: A short, literal English description of that same image, for
        accessibility and image SEO (different from the creative prompt).

    Format EXACTLY as valid JSON, no markdown, no extra text:
    {{
        "title_en": "Short English Title",
        "title_hi": "संक्षिप्त हिंदी शीर्षक",
        "sanskrit": "The Sanskrit mantra text",
        "hindi": "Hindi meaning",
        "english": "English translation",
        "explanation": "100-150 word explanation of significance and how it's used",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars",
        "focus_keyword": "2-4 word focus phrase",
        "slug": "3-5-word-url-slug",
        "image_prompt": "Your image generation prompt here",
        "image_alt_text": "Short literal description of the image"
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


def generate_ai_image(prompt, filename="mantra_image.jpg"):
    print(f"Generating HD AI Image... ({prompt})")
    high_quality_prompt = f"{prompt}, 8k resolution, highly detailed, sharp focus, vivid colors, divine lighting, masterwork"
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
        print(response.text)
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

    image_path = generate_ai_image(new_mantra.get('image_prompt', new_mantra['title_en']))
    media_id = None
    if image_path:
        compress_image(image_path)
        media_id = upload_image_to_wp(image_path, alt_text=new_mantra.get('image_alt_text', new_mantra['title_en']))

    category_id = get_or_create_category()
    post_url = publish_mantra_post(new_mantra, category_id, media_id, target_day)

    add_mantra_to_pool(new_mantra, target_day, post_url)

    if image_path and os.path.exists(image_path):
        os.remove(image_path)


if __name__ == "__main__":
    main()
