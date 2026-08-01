import os
import requests
import json
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

client = genai.Client(api_key=GEMINI_API_KEY)

RSS_FEEDS = [
    "https://www.abplive.com/lifestyle/religion/feed",
    "https://www.jagran.com/rss/spiritual",
    "https://zeenews.india.com/hindi/religion/rss"
]


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


def get_affiliate_html(category="general"):
    if category.lower() == 'shiva':
        title = "5 Mukhi Rudraksha Mala — 108 Beads"
        desc = "Pure Nepali Rudraksha. Enhances focus and brings Lord Shiva's blessings."
        link = "https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21"
        price = "₹399 - Buy on Amazon"
    elif category.lower() in ('pooja', 'festival', 'gita', 'karma'):
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

        selected_topics = json.loads(text)
        return selected_topics
    except Exception as e:
        print(f"Failed AI deduplication: {e}")
        return []


def rewrite_article_and_image_prompt(original_title):
    print("Phase 3: Scholar AI & Marketing Editor writing article and designing visual image prompt...")
    prompt = f"""
    You are an elite Digital Marketing Manager, Vedic Scholar, and SEO Specialist for a top Hindu News Portal. Write a highly engaging, high-CTR, deeply respectful, and RankMath 100/100 SEO-optimized article in ENGLISH based on this news topic:
    "{original_title}"

    CRITICAL REQUIREMENTS:
    1. Language: The entire article MUST be written in high-quality, premium English.
    2. Headline (H1): Write a magnetic, click-tempting English headline like a Google News & Discover Editor. Trigger curiosity and awe (e.g., using strong hooks like "Sacred Dawn:", "Revealed:", "Why Thousands Gather For", "The Secret Of"). IT MUST BE 100% UNIQUE.
    3. Focus Keyword: Pick a clear 2-4 word focus phrase (e.g., "Ujjain Mahakal Bhasma Aarti" or "Nag Panchami Puja").
    4. URL Slug: Generate a 4-5 word English slug derived DIRECTLY from the Focus Keyword (e.g., ujjain-mahakal-bhasma-aarti).
    5. SEO Meta:
       - MetaTitle: Under 60 characters, keyword-front-loaded.
       - MetaDescription: Under 155 characters. IT MUST START WITH OR CONTAIN the exact Focus Keyword in the first sentence.
    6. Content First Paragraph: The VERY FIRST paragraph of `content_html` MUST contain the exact Focus Keyword bolded inside `<strong>` tags (e.g. `<p>Experience the divine power of <strong>Ujjain Mahakal Bhasma Aarti</strong>, one of the most sacred Vedic rituals...</p>`).
    7. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    8. Formatting: Use proper HTML headings (<h2>) like "Significance", "Mythology". Use short paragraphs, bold important names/facts, and include at least one bulleted list.
    9. BILINGUAL WHATSAPP OPTIMIZATION: At the very top of your HTML Content, before the English text, you MUST write a 2-3 sentence highly engaging Hindi summary titled '<h3>हिंदी सारांश:</h3>'. This will be pulled by WhatsApp for sharing previews.
    10. AI Image Prompt: Write a 100% LITERAL, VISUAL description in ENGLISH of the physical scene for a photorealistic featured image. Describe concrete physical objects (e.g. "A sacred black stone Shiva Lingam adorned with holy white ash, fresh orange marigold flower garlands, and glowing oil diya lamps in an ancient stone temple sanctum, 8k realistic photography, National Geographic style"). CRITICAL: NEVER use Hindi proper nouns (like 'Bhasma Aarti', 'Chhari Mubarak'), abstract terms, or chapter numbers. Describe real physical objects so the AI renders an authentic photo. Do NOT include text in the image.
    11. Image Alt Text: Also write a short, literal English description of that same image containing the Focus Keyword (for Google Image SEO).
    12. Category: Determine the ONE best category from this exact list: Mythology, Vedic Wisdom, Daily Sadhana, Festivals & Vrat, Astrology & Horoscope, Temples & Pilgrimage, Mantras & Chants, Spiritual News.
    13. Ecommerce Category: Choose ONE from: "shiva", "pooja", "gita", "general" — based on the article topic.

    Format the output EXACTLY like this:
    Headline: [Your High-CTR Unique English Headline]
    FocusKeyword: [2-4 word focus phrase]
    Slug: [your-english-url-slug]
    Category: [Just the category name, e.g. Temples & Pilgrimage]
    EcommerceCategory: [shiva|pooja|gita|general]
    ImagePrompt: [Literal visual English image generation prompt]
    ImageAltText: [Short description of image containing FocusKeyword]
    MetaTitle: [SEO title under 60 characters]
    MetaDescription: [SEO description under 155 characters starting with FocusKeyword]
    Content:
    <h3>हिंदी सारांश:</h3><p>Your Hindi summary...</p><p>First paragraph with <strong>FocusKeyword</strong>...</p><h2>Your Heading</h2>
    [Your HTML formatted content in English]
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt
        )
        text = response.text

        headline = text.split("Headline:")[1].split("FocusKeyword:")[0].strip()
        focus_keyword = text.split("FocusKeyword:")[1].split("Slug:")[0].strip()
        slug = text.split("Slug:")[1].split("Category:")[0].strip()
        category = text.split("Category:")[1].split("EcommerceCategory:")[0].strip()
        ecommerce_category = text.split("EcommerceCategory:")[1].split("ImagePrompt:")[0].strip()
        image_prompt = text.split("ImagePrompt:")[1].split("ImageAltText:")[0].strip()
        image_alt_text = text.split("ImageAltText:")[1].split("MetaTitle:")[0].strip()
        meta_title = text.split("MetaTitle:")[1].split("MetaDescription:")[0].strip()
        meta_description = text.split("MetaDescription:")[1].split("Content:")[0].strip()
        content = text.split("Content:")[1].strip()

        if content.startswith("```html"):
            content = content[7:-3].strip()

        return {
            "headline": headline,
            "focus_keyword": focus_keyword,
            "slug": slug,
            "category": category,
            "ecommerce_category": ecommerce_category,
            "image_prompt": image_prompt,
            "image_alt_text": image_alt_text,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "content": content
        }
    except Exception as e:
        print(f"Failed to generate AI response: {e}")
        return None


def generate_ai_image(prompt, topic_keyword="indian temple", filename="featured_image.webp"):
    print(f"Phase 4: Sourcing Real Authentic HD Photo or Smart AI Image... ({topic_keyword})")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    temp_jpg = "temp_bg.jpg"
    seed = random.randint(1, 999999)

    # Tier 1: Try Sourcing Real Authentic HD Photography
    clean_kw = topic_keyword.lower().replace(" ", "-")
    unsplash_url = f"https://images.unsplash.com/photo-1544717305-2782549b5136?w=1200&h=630&fit=crop"
    if "shiva" in clean_kw or "mahakal" in clean_kw:
        unsplash_url = f"https://images.unsplash.com/photo-1609840114035-3c981b782dfe?w=1200&h=630&fit=crop"
    elif "eclipse" in clean_kw or "grahan" in clean_kw:
        unsplash_url = f"https://images.unsplash.com/photo-1532693322450-2cb5c511067d?w=1200&h=630&fit=crop"
    elif "temple" in clean_kw or "pooja" in clean_kw:
        unsplash_url = f"https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=1200&h=630&fit=crop"

    try:
        res = requests.get(unsplash_url, headers=headers, timeout=8)
        if res.status_code == 200 and len(res.content) > 5000:
            with open(temp_jpg, "wb") as f:
                f.write(res.content)
            print(f"Successfully retrieved Real Authentic 4K Photography for {topic_keyword}!")
            return temp_jpg
    except Exception as e:
        print(f"Real photo engine notice ({e}), proceeding to AI engine...")

    # Tier 2: Smart Photorealistic AI Prompting
    high_quality_prompt = f"Professional realistic photography of {prompt}, shot on 35mm lens, f/1.8, natural golden hour lighting, 8k resolution, National Geographic style, highly detailed, photorealistic"
    encoded_prompt = urllib.parse.quote(high_quality_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true&enhance=true&seed={seed}"

    try:
        response = requests.get(url, stream=True, headers=headers, timeout=12)
        if response.status_code == 200 and len(response.content) > 5000:
            with open(temp_jpg, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print("Successfully generated fresh photorealistic AI background image!")
            return temp_jpg
    except Exception as e:
        print(f"Pollinations AI notice ({e}), using HD fallback background...")

    # Tier 3: High-Res Fallback
    try:
        fallback_url = f"https://picsum.photos/seed/{seed}/1200/630"
        res = requests.get(fallback_url, headers=headers, timeout=8)
        if res.status_code == 200:
            with open(temp_jpg, 'wb') as f:
                f.write(res.content)
            return temp_jpg
    except Exception as e:
        print(f"Fallback image error: {e}")

    return None


def compress_image(temp_filepath, output_filename="featured_image.webp", headline_text="", category_text="SPIRITUAL NEWS"):
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

        # 2. Font selection
        try:
            font_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 36)
            font_badge = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 20)
        except Exception:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()

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


def get_or_create_category(category_name):
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

    # Inject eBook upsell after 3rd paragraph
    paragraphs = data['content'].split('</p>')
    if len(paragraphs) > 3:
        paragraphs.insert(3, get_ebook_upsell_html())
    mid_content = '</p>'.join(paragraphs)

    # Inject WhatsApp CTA at mid-point
    paragraphs2 = mid_content.split('</p>')
    if len(paragraphs2) > 5:
        mid_idx = len(paragraphs2) // 2
        paragraphs2.insert(mid_idx, get_whatsapp_cta_html())
    full_content = '</p>'.join(paragraphs2)

    # Append end CTAs
    full_content += get_kundli_upsell_html()
    full_content += get_affiliate_html(data.get('ecommerce_category', 'general'))

    ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%dT%H:%M:%S')

    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
        "date": ist_now,
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
        print("Successfully published!")
    else:
        print(f"Failed to publish. Status code: {response.status_code}")
        print(response.text)


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
        print("Editor-in-Chief did not select any topics.")
        return

    print(f"Editor-in-Chief selected {len(selected_topics)} distinct topics for publication.")

    for news in selected_topics:
        print(f"\n--- Processing Master Topic: {news['title']} ---")

        rewritten = rewrite_article_and_image_prompt(news['title'])
        if not rewritten:
            continue

        if topic_already_covered_on_site(rewritten['headline']):
            mark_as_posted(news['link'])
            continue

        print(f"Final Headline: {rewritten['headline']}")
        print(f"AI Category: {rewritten['category']}")
        print(f"Focus Keyword: {rewritten.get('focus_keyword', 'N/A')}")

        temp_image = generate_ai_image(rewritten['image_prompt'], topic_keyword=rewritten.get('focus_keyword', rewritten['category']))
        media_id = None
        final_image = None
        if temp_image:
            output_webp = f"{rewritten['slug']}.webp"
            final_image = compress_image(temp_image, output_filename=output_webp, headline_text=rewritten['headline'], category_text=rewritten['category'])
            media_id = upload_image_to_wp(final_image, alt_text=rewritten.get('image_alt_text', rewritten['headline']))

        category_id = get_or_create_category(rewritten['category'])

        publish_wp_post(
            rewritten,
            media_id,
            category_id,
            rewritten['slug'],
            rewritten.get('meta_title'),
            rewritten.get('meta_description'),
            rewritten.get('focus_keyword')
        )

        mark_as_posted(news['link'])

        if final_image and os.path.exists(final_image):
            try:
                os.remove(final_image)
            except Exception:
                pass

        time.sleep(5)


if __name__ == "__main__":
    main()
