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


def get_affiliate_html(category="general"):
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
                <a href="https://www.amazon.in/s?k=5+mukhi+rudraksha+mala&tag=hindudevgyan-21" target="_blank"
                   style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; white-space:nowrap;">₹399 - Buy on Amazon</a>
            </div>
        </div>
        """
    elif category.lower() in ('pooja', 'festival', 'gita', 'karma'):
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
    print("Phase 3: Scholar AI writing article and designing image prompt...")
    prompt = f"""
    You are an elite Hindu Religious Scholar, Vedic Expert, and SEO Specialist. Write a highly engaging, deeply respectful, and SEO-optimized article in ENGLISH based on this Hindi news/topic:
    "{original_title}"

    CRITICAL REQUIREMENTS:
    1. Language: The entire article MUST be written in high-quality, premium English.
    2. Headline (H1): Write a highly clickable, English headline. IT MUST BE 100% UNIQUE. Find a creative, spiritual angle.
    3. URL Slug: Generate a 5-6 word English translation of the headline, formatted with hyphens (e.g., significance-of-chhaya-someswara-temple).
    4. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    5. Formatting: Use proper HTML headings (<h2>) like "Significance", "Mythology". Use short paragraphs, bold important names/facts, and include at least one bulleted list.
    6. BILINGUAL WHATSAPP OPTIMIZATION: At the very top of your HTML Content, before the English text, you MUST write a 2-3 sentence highly engaging Hindi summary titled '<h3>हिंदी सारांश:</h3>'. This will be pulled by WhatsApp for sharing previews.
    7. Category: Determine the ONE best category from this exact list: Mythology, Vedic Wisdom, Daily Sadhana, Festivals & Vrat, Astrology & Horoscope, Temples & Pilgrimage, Mantras & Chants, Spiritual News.
    8. AI Image Prompt: Write a short, highly-descriptive English prompt for an AI Image Generator to create a featured image for this article (e.g. "Cinematic realistic image of Lord Shiva meditating in the Himalayas, golden hour lighting"). Do NOT use text in the image.
    9. Image Alt Text: Also write a short, literal English description of that same image, for accessibility and image SEO (different from the creative prompt).
    10. SEO Meta: Provide "meta_title" (under 60 characters, keyword-front-loaded, can differ slightly from the headline), "meta_description" (a click-worthy summary under 155 characters), and "focus_keyword" (the single 2-4 word phrase this article should rank for).
    11. Ecommerce Category: Choose ONE from: "shiva", "pooja", "gita", "general" — based on the article topic.

    Format the output EXACTLY like this:
    Headline: [Your 100% Unique English Headline]
    Slug: [your-english-url-slug]
    Category: [Just the category name, e.g. Temples & Pilgrimage]
    EcommerceCategory: [shiva|pooja|gita|general]
    ImagePrompt: [The English image generation prompt]
    ImageAltText: [Short literal description of the image]
    MetaTitle: [SEO title under 60 characters]
    MetaDescription: [SEO description under 155 characters]
    FocusKeyword: [2-4 word focus phrase]
    Content:
    <h3>हिंदी सारांश:</h3><p>Your Hindi summary...</p><h2>Your First Heading</h2>
    [Your HTML formatted content in English with <h2>, <p>, <ul>, <li>, <strong>, and <a> tags. Do not include <html> or <body> tags]
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt
        )
        text = response.text

        headline = text.split("Headline:")[1].split("Slug:")[0].strip()
        slug = text.split("Slug:")[1].split("Category:")[0].strip()
        category = text.split("Category:")[1].split("EcommerceCategory:")[0].strip()
        ecommerce_category = text.split("EcommerceCategory:")[1].split("ImagePrompt:")[0].strip()
        image_prompt = text.split("ImagePrompt:")[1].split("ImageAltText:")[0].strip()
        image_alt_text = text.split("ImageAltText:")[1].split("MetaTitle:")[0].strip()
        meta_title = text.split("MetaTitle:")[1].split("MetaDescription:")[0].strip()
        meta_description = text.split("MetaDescription:")[1].split("FocusKeyword:")[0].strip()
        focus_keyword = text.split("FocusKeyword:")[1].split("Content:")[0].strip()
        content = text.split("Content:")[1].strip()

        if content.startswith("```html"):
            content = content[7:-3].strip()

        return {
            "headline": headline,
            "slug": slug,
            "category": category,
            "ecommerce_category": ecommerce_category,
            "image_prompt": image_prompt,
            "image_alt_text": image_alt_text,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "focus_keyword": focus_keyword,
            "content": content
        }
    except Exception as e:
        print(f"Failed to generate AI response: {e}")
        return None


def generate_ai_image(prompt, filename="featured_image.jpg"):
    print(f"Phase 4: Generating HD AI Image... ({prompt})")
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
    print("Uploading AI image to WordPress Media Library...")
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

        image_path = generate_ai_image(rewritten['image_prompt'])
        media_id = None
        if image_path:
            compress_image(image_path)
            media_id = upload_image_to_wp(image_path, alt_text=rewritten.get('image_alt_text', rewritten['headline']))

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

        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        time.sleep(5)


if __name__ == "__main__":
    main()
