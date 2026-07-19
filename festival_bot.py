import os
import requests
import json
import urllib.parse
from google import genai
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# E-COMMERCE & UPSELL INJECTION
# ==========================================
def get_affiliate_html(category):
    """Contextual Affiliate Product Injection"""
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
    """Digital Product E-Book Mid-Article Injection"""
    return """
    <div style="background:#fffbeb; border:2px dashed #f59e0b; padding:25px; border-radius:8px; margin:30px 0; text-align:center;">
        <h3 style="margin-top:0; color:#b45309; font-size:22px;">Transform Your Home's Energy Today!</h3>
        <p style="font-size:16px; color:#78350f; margin-bottom:20px;">Discover the ancient secrets to attracting wealth, health, and absolute harmony. Download our premium 5-chapter Vastu Shastra guide instantly.</p>
        <a href="https://rzp.io/rzp/VtX5q0e" target="_blank" style="display:inline-block; background:#f59e0b; color:#fff; padding:15px 30px; border-radius:30px; font-weight:bold; text-decoration:none; font-size:18px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">Unlock The Vastu Shastra Mastery Guide (₹99)</a>
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
    Write a 600-word comprehensive guide about the upcoming Hindu Festivals and Vrats (like Ekadashi, Pradosh, or major festivals) for the week of: {date_range}.
    
    If there are no major well-known festivals, focus on the significance of the upcoming Ekadashi or Purnima/Amavasya, or discuss the spiritual significance of the current Hindu month.
    
    CRITICAL REQUIREMENTS:
    1. Write an SEO optimized, highly clickable Headline.
    2. Provide a 5-6 word URL Slug.
    3. Categorize the article for ecommerce. Choose one: "shiva" or "pooja".
    4. Provide the main article content in beautiful HTML format (using <h2>, <h3>, <p>, and <ul>).
    5. Internal Linking: You MUST naturally weave at least 3 internal HTML links into the article text to build SEO authority. Use this mapping:
       - Mentions of "Kundli", "Birth Chart", or "Horoscope" -> <a href="https://hindudevgyan.in/free-kundli/">
       - Mentions of "Vastu" -> <a href="https://hindudevgyan.in/category/vastu/">
       - Mentions of "Panchang" or "Muhurat" -> <a href="https://hindudevgyan.in/category/panchang/">
       - Mentions of "Bhagavad Gita" or "Karma" -> <a href="https://hindudevgyan.in/category/gita-wisdom/">
       - Mentions of "HinduDevGyan" -> <a href="https://hindudevgyan.in/">
    6. Generate a highly descriptive English prompt for an AI Image Generator representing the festival or spiritual mood (e.g. "Cinematic vibrant painting of Indian temple celebration, glowing lights, festive atmosphere..."). Do NOT include any text in the image prompt.
    
    Format EXACTLY as valid JSON:
    {{
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "ecommerce_category": "pooja",
        "content_html": "<h2>Upcoming Vrats and Festivals</h2><p>...</p>",
        "image_prompt": "Your image prompt here"
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
        print(f"Failed to generate AI article: {e}")
        return None

def generate_ai_image(prompt, filename="festival_image.jpg"):
    print(f"Generating Festival AI Image... ({prompt})")
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
            return None
    except:
        return None

def upload_image_to_wp(image_path):
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
            return response.json()['id']
    return None

def get_or_create_category(category_name="Festivals & Vrats"):
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
    
    # 1. The Core AI Content
    # Inject E-Book CTA directly into the middle of the AI article
    paragraphs = data['content_html'].split('</p>')
    if len(paragraphs) > 2:
        mid_idx = len(paragraphs) // 2
        paragraphs.insert(mid_idx, get_ebook_upsell_html())
    full_content = '</p>'.join(paragraphs)
    
    # 2. Inject The Contextual E-Commerce Block
    full_content += get_affiliate_html(data['ecommerce_category'])
    
    # 3. Inject The EEAT Disclaimer
    full_content += """
    <hr style="margin-top:30px;">
    <p style="font-size:12px; color:#888;"><em><strong>Disclaimer:</strong> Festival dates and timings can vary by geographical location and specific local panchang. Please consult with your local temple or pandit for exact fasting Muhurats in your timezone.</em></p>
    """
    
    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
        "slug": data['slug'],
        "categories": [category_id] if category_id else []
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
    
    # Only run on Sundays (0 = Monday, 6 = Sunday)
    if datetime.now().weekday() != 6:
        print("Today is not Sunday. The Weekly Festival Bot will sleep.")
        return
        
    article_data = generate_weekly_festivals()
    if not article_data:
        return
        
    print(f"AI Editor selected headline: {article_data['headline']}")
    
    image_path = generate_ai_image(article_data['image_prompt'])
    media_id = upload_image_to_wp(image_path) if image_path else None
        
    category_id = get_or_create_category()
    
    publish_wp_post(article_data, media_id, category_id)
    
    if image_path and os.path.exists(image_path):
        os.remove(image_path)

if __name__ == "__main__":
    main()
