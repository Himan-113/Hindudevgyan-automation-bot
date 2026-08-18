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
WP_URL = os.getenv("WP_URL") or "https://hindudevgyan.in"
WP_USERNAME = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USERNAME") or os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD") or os.getenv("WP_PASSWORD")

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
    You are an elite Hindu Religious Scholar, Vedic Astrologer, and SEO Editor-in-Chief. Write a deeply engaging, authoritative, and SEO-optimized article in ENGLISH based on this Hindi news/topic:
    "{original_title}"

    CRITICAL EDITORIAL & SEO REQUIREMENTS:
    1. Language: Premium, engaging English.
    2. Headline (H1) Formula: High-Search Intent + Trending Hook.
       - Structure: `[Deity/Festival/Rashi Name 2026]: [High-Search Intent - Muhurat / Vidhi / Predictions / Spiritual Meaning]`
       - Examples of GOOD titles: "Sawan Somwar & Nag Panchami 2026: Auspicious Shubh Muhurat, Puja Vidhi & Shiva Mantras", "Aquarius Weekly Horoscope (Aug 17–22, 2026): Kumbh Rashi Career Shifts & Shani Remedies", "Amarnath Yatra 2026: Chhari Mubarak Dates, Holy Cave Timings & Weather Guide".
       - BANNED ABSTRACT WORDS: NEVER use words like "Alchemy", "Triumph", "Crossroads", "Tapestry", "Symphony", "Delve". Keep titles clear, powerful, and directly matching what people search on Google & Discover.
    3. URL Slug: Clean 4-6 word hyphenated slug (e.g. sawan-somwar-nag-panchami-muhurat-vidhi).
    4. Internal Linking: Naturally embed at least 3 internal HTML links:
       - Kundli / Horoscope -> <a href="https://hindudevgyan.in/free-kundli/">
       - Vastu -> <a href="https://hindudevgyan.in/category/vastu/">
       - Panchang / Muhurat -> <a href="https://hindudevgyan.in/category/panchang/">
       - Bhagavad Gita / Karma -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - HinduDevGyan -> <a href="https://hindudevgyan.in/">
    5. High E-E-A-T Content Structure in HTML:
       - Top: <h3>हिंदी सारांश:</h3> with 3 clear bullet points summarizing the event for mobile/WhatsApp readers.
       - <h2>Significance & Vedic Context</h2>: Deep spiritual and mythological background.
       - <blockquote>: An authentic Sanskrit Shloka with English transliteration and word-by-word meaning.
       - <h2>Rituals, Vidhi & Muhurat</h2>: Step-by-step puja vidhi, timing table (if applicable), and Dos & Don'ts.
       - <h2>Frequently Asked Questions</h2>: 3 crisp Q&A pairs (<h3> and <p>) optimized for Google FAQ Rich Snippets.
    6. Category: Choose ONE from: Festivals & Vrat, Temples & Pilgrimage, Astrology & Horoscope, Vedic Wisdom, Gita Wisdom, Panchang, Mantras & Chants, Mythology, Spiritual News.
    7. Ecommerce Tag: Choose ONE: "shiva", "pooja", "gita", "general".
    8. Visual AI Image Prompt: A concrete, literal 20-30 word visual scene description focusing on traditional Hindu iconography and sacred subjects.
       - If a Deity (Shiva, Krishna, Rama, Ganesha, Hanuman, Durga): describe the deity in a classic calm posture with iconic physical symbols (flute, bow, trishul, lotus).
       - If Horoscope / Astrology: describe the classical Vedic celestial symbol (e.g. majestic lion in stars for Leo; sacred brass kalash for Aquarius).
       - If Temple / Ritual / Vrat: describe the physical stone architecture or traditional puja altar with brass diyas and fresh flowers.
       - CRITICAL STYLE RESTRICTIONS: Do NOT include abstract action words, emotional metaphors, or alphabetic text. NEVER use words like "photography", "3D render", "digital art", or "National Geographic". Describe only concrete physical subjects.
    9. Image Alt Text: Short descriptive alt text containing primary subject (e.g. "Lord Shiva and sacred Vasuki serpent in meditation").
    10. Short Image Banner Text: 3-5 word concise headline.
    11. SEO Meta: "meta_title" (<60 chars), "meta_description" (<155 chars), and "focus_keyword".

    Format output EXACTLY as valid JSON:
    {{
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "category": "Temples & Pilgrimage",
        "ecommerce_tag": "shiva",
        "image_prompt": "Detailed concrete visual scene for FLUX.1",
        "image_alt_text": "Short literal alt description",
        "image_banner_text": "SHORT 3-5 WORD BANNER TITLE",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars",
        "focus_keyword": "Focus keyword phrase",
        "content": "<h3>हिंदी सारांश:</h3><ul><li>Point 1</li><li>Point 2</li></ul><h2>Significance & Vedic Context</h2><p>...</p>"
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


def generate_ai_image(prompt, banner_text="", category_text="Spiritual News", filename="featured_image.webp"):
    """
    Calls centralized image_engine with Cloudflare FLUX.1 [schnell] & tight watermark badge.
    """
    from image_engine import generate_hd_featured_image
    return generate_hd_featured_image(prompt, category=category_text, output_filename=filename)


def compress_image(temp_filepath, output_filename="featured_image.webp", headline_text="", category_text="SPIRITUAL NEWS"):
    """
    Applies smart watermark if not already applied.
    """
    from image_engine import apply_smart_logo_watermark
    return apply_smart_logo_watermark(temp_filepath, output_filename)


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
