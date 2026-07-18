import os
import sys
import requests
import feedparser
import urllib.parse
from urllib.parse import urlparse, parse_qs
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Fix for Windows console crashing when printing Hindi characters
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Hindu Religion & Spirituality RSS Feed (ABP Live Religion)
RSS_FEED_URL = "https://www.abplive.com/lifestyle/religion/feed"

def fetch_latest_news():
    print("Fetching latest National Hindi news...")
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        print("No news found.")
        return []
    
    news_list = []
    # Get the top 10 entries
    for entry in feed.entries[:10]:
        title = entry.title
        bing_link = entry.link
        
        # Extract the original direct URL from the Bing URL
        try:
            original_url = parse_qs(urlparse(bing_link).query)['url'][0]
        except Exception:
            original_url = bing_link
            
        news_list.append({"title": title, "link": original_url})
        
    print(f"Found {len(news_list)} recent articles in the feed.")
    return news_list

def is_duplicate(original_url):
    print("Checking if this news was already posted today...")
    url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=15"
    response = requests.get(url, auth=(WP_USERNAME, WP_APP_PASSWORD))
    if response.status_code == 200:
        posts = response.json()
        for post in posts:
            content = post.get('content', {}).get('rendered', '')
            if original_url in content:
                print("Duplicate found! Skipping to save AI credits and avoid spam.")
                return True
    return False

def get_or_create_category(category_name):
    # Search for the category
    url = f"{WP_URL}/wp-json/wp/v2/categories?search={category_name}"
    response = requests.get(url, auth=(WP_USERNAME, WP_APP_PASSWORD))
    if response.status_code == 200 and response.json():
        return response.json()[0]['id']
    
    # Create it if it doesn't exist
    create_url = f"{WP_URL}/wp-json/wp/v2/categories"
    data = {"name": category_name}
    create_response = requests.post(create_url, json=data, auth=(WP_USERNAME, WP_APP_PASSWORD))
    if create_response.status_code == 201:
        return create_response.json()['id']
    return None

def rewrite_article_with_ai(original_title):
    print("Rewriting and Translating article with Gemini AI for HinduDevGyan...")
    prompt = f"""
    You are an elite Hindu Religious Scholar, Vedic Expert, and SEO Specialist. Write a highly engaging, deeply respectful, and SEO-optimized article in ENGLISH based on this Hindi news/topic:
    "{original_title}"
    
    CRITICAL SEO & EDITORIAL REQUIREMENTS:
    1. Language: The entire article MUST be written in high-quality, premium English.
    2. Headline (H1): Write a highly clickable, English headline. IT MUST BE 100% UNIQUE. Find a creative, spiritual angle.
    3. URL Slug: Generate a 5-6 word English translation of the headline, formatted with hyphens (e.g., significance-of-chhaya-someswara-temple).
    4. The Hook (First Paragraph): The first 150-160 characters MUST perfectly summarize the topic.
    5. Internal Linking: Naturally embed an HTML link to the homepage (https://hindudevgyan.in) somewhere INSIDE the paragraphs (e.g., according to <a href="https://hindudevgyan.in">Hindu Dev Gyan</a>...). DO NOT put it at the very end.
    6. Formatting: Use proper HTML headings (<h2>) like "Significance", "Mythology", or "Puja Vidhi". Use short paragraphs, bold important names/facts, and include at least one bulleted list. 
    7. Category: Determine the ONE best category from this exact list: Mythology, Vedic Wisdom, Daily Sadhana, Festivals & Vrat, Astrology & Horoscope, Temples & Pilgrimage, Mantras & Chants, Spiritual News.
    
    Format the output EXACTLY like this:
    Headline: [Your 100% Unique English Headline]
    Slug: [your-english-url-slug]
    Category: [Just the category name, e.g. Temples & Pilgrimage]
    Content:
    [Your HTML formatted content in English with <h2>, <p>, <ul>, <li>, <strong>, and <a> tags. Do not include <html> or <body> tags]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Parse the response
        headline = text.split("Headline:")[1].split("Slug:")[0].strip()
        slug = text.split("Slug:")[1].split("Category:")[0].strip()
        category = text.split("Category:")[1].split("Content:")[0].strip()
        content = text.split("Content:")[1].strip()
        
        # Clean markdown formatting if present
        if content.startswith("```html"):
            content = content[7:-3].strip()
            
        return {"headline": headline, "slug": slug, "category": category, "content": content}
    except Exception as e:
        print(f"Failed to generate or parse AI response: {e}")
        return None

def download_source_image(link):
    print("Extracting original image from news source...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(link, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            print(f"Found original image: {image_url}")
            
            # Download the image
            img_data = requests.get(image_url, headers=headers, timeout=10).content
            with open('temp_image.jpg', 'wb') as handler:
                handler.write(img_data)
            return 'temp_image.jpg'
        else:
            print("No original image found in the source article.")
            return None
    except Exception as e:
        print(f"Failed to extract original image: {e}")
        return None

def upload_image_to_wp(image_path):
    print("Uploading image to WordPress...")
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    
    headers = {
        "Content-Disposition": f"attachment; filename={os.path.basename(image_path)}",
        "Content-Type": "image/jpeg"
    }
    
    with open(image_path, "rb") as img:
        response = requests.post(media_url, headers=headers, data=img, auth=(WP_USERNAME, WP_APP_PASSWORD))
        
    if response.status_code == 201:
        print("Image uploaded successfully!")
        return response.json()['id']
    else:
        print(f"Failed to upload image. Status code: {response.status_code}")
        print(response.text)
        return None

def publish_wp_post(headline, content, media_id, original_url, category_id, slug):
    print("Publishing to WordPress...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    # Extract the domain name for the image credit
    domain = urlparse(original_url).netloc.replace('www.', '')
    
    # Append the image credit and hidden tracking URL
    final_content = content + f"\n\n<p style='font-size: 0.9em; color: gray;'><em>(Image Credit: {domain})</em></p>"
    final_content += f"\n\n<!-- SOURCE: {original_url} -->"
    
    data = {
        "title": headline,
        "content": final_content,
        "status": "publish",
        "slug": slug,
        "categories": [category_id] if category_id else []
    }
    if media_id:
        data["featured_media"] = media_id
    
    response = requests.post(post_url, json=data, auth=(WP_USERNAME, WP_APP_PASSWORD))
    
    if response.status_code == 201:
        print(f"Success! Post created: {response.json().get('link')}")
    else:
        print(f"Failed to publish. Status code: {response.status_code}")
        print(response.text)

def main():
    print("Starting Advanced HinduDevGyan Bot (Batch Processing Mode)...")
    
    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables. Please check your .env file.")
        return
    
    # 1. Fetch News List
    news_list = fetch_latest_news()
    if not news_list:
        return
        
    posts_created_this_run = 0
    MAX_POSTS_PER_RUN = 5
    
    for news in news_list:
        if posts_created_this_run >= MAX_POSTS_PER_RUN:
            print(f"\nReached safety cap of {MAX_POSTS_PER_RUN} posts per run. Stopping for now.")
            break
            
        print(f"\n--- Processing: {news['title']} ---")
        
        # 2. Check for Duplicates
        if is_duplicate(news['link']):
            continue # Skip to the next article
            
        # 3. Rewrite with AI & Categorize
        rewritten = rewrite_article_with_ai(news['title'])
        if not rewritten:
            continue
        
        print(f"New Headline: {rewritten['headline']}")
        print(f"New URL Slug: {rewritten['slug']}")
        print(f"AI Category Decision: {rewritten['category']}")
        
        # 4. Get/Create WP Category ID
        category_id = get_or_create_category(rewritten['category'])
        
        # 5. Extract Original Image
        image_path = download_source_image(news['link'])
        media_id = None
        if image_path:
            # 6. Upload Image
            media_id = upload_image_to_wp(image_path)
        
        # 7. Publish Post
        publish_wp_post(rewritten['headline'], rewritten['content'], media_id, news['link'], category_id, rewritten['slug'])
        
        # Cleanup temp image
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            
        posts_created_this_run += 1
    
    print("\nAutomation batch complete!")

if __name__ == "__main__":
    main()
