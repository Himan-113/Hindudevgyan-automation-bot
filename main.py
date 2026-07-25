import os
import requests
import json
import feedparser
import urllib.parse
from urllib.parse import urlparse, parse_qs
from google import genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
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

    Format the output EXACTLY like this:
    Headline: [Your 100% Unique English Headline]
    Slug: [your-english-url-slug]
    Category: [Just the category name, e.g. Temples & Pilgrimage]
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
        category = text.split("Category:")[1].split("ImagePrompt:")[0].strip()
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
    print(f"Phase 4: Generating Copyright-Free AI Image... ({prompt})")
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"

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


def compress_image(filepath, quality=75):
    try:
        img = Image.open(filepath)
        img.convert("RGB").save(filepath, "JPEG", quality=quality, optimize=True)
        print(f"Compressed image at quality={quality}")
    except Exception as e:
        print(f"Could not compress image (continuing with original): {e}")
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

    payload = {
        "title": data['headline'],
        "content": data['content'],
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
