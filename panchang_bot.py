import os
import requests
import json
import urllib.parse
from google import genai
from dotenv import load_dotenv
import time
from datetime import datetime
import pytz

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Prokerala Credentials (from your PHP snippet)
PROKERALA_CLIENT_ID = 'ee4667d9-435d-448c-b846-cf266945e020'
PROKERALA_CLIENT_SECRET = 'll7jobOolDnuqMkQsDaqPfBCuQ1BThHD1xlHUZIM'

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
                <a href="#" style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">₹399 - Buy on Amazon</a>
            </div>
        </div>
        """
    elif category.lower() == 'pooja' or category.lower() == 'festival':
        return """
        <div style="background:#fff8f0; border:1px solid #FF9800; padding:20px; border-radius:8px; margin-top:30px;">
            <h4 style="margin-top:0; color:#E65100;">⭐ Recommended for You</h4>
            <p style="font-size:0.9em; color:#666;"><em>Contains affiliate links. We earn a small commission at no extra cost to you.</em></p>
            <div style="display:flex; align-items:center; gap:15px;">
                <div style="flex:1;">
                    <strong style="color:#d97706;">Brass Puja Thali Set — 7 Piece</strong>
                    <p style="font-size:14px;">Complete brass thali with diya, incense holder, bell and more for daily puja.</p>
                </div>
                <a href="#" style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">₹599 - Buy on Amazon</a>
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
                <a href="#" style="background:#FF9800; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">₹349 - Buy on Amazon</a>
            </div>
        </div>
        """

def get_kundli_upsell_html():
    """Astrological Upsell Funnel to Premium PDF"""
    return """
    <div style="background:#FDF0DB; border-left:4px solid #E8540A; padding:20px; border-radius:6px; margin-top:30px; margin-bottom:20px;">
        <h3 style="margin-top:0; color:#E8540A;">Curious how today's Nakshatra affects you?</h3>
        <p style="font-size:15px; color:#333; margin-bottom:15px;">Discover your exact career path, marriage compatibility, and planetary dashas based on your exact birth time.</p>
        <a href="/free-kundli" style="display:inline-block; background:#10b981; color:#fff; padding:12px 20px; border-radius:4px; font-weight:bold; text-decoration:none;">Generate Free Vedic Kundli</a>
        <a href="#" style="display:inline-block; background:#E8540A; color:#fff; padding:12px 20px; border-radius:4px; font-weight:bold; text-decoration:none; margin-left:10px;">Unlock 50-Page Premium PDF (₹149)</a>
    </div>
    """

# ==========================================
# CORE BOT LOGIC
# ==========================================
def get_prokerala_panchang():
    print("Authenticating with Prokerala API...")
    token_url = "https://api.prokerala.com/token"
    token_payload = {
        'grant_type': 'client_credentials',
        'client_id': PROKERALA_CLIENT_ID,
        'client_secret': PROKERALA_CLIENT_SECRET
    }
    
    try:
        token_res = requests.post(token_url, data=token_payload)
        token_res.raise_for_status()
        access_token = token_res.json().get('access_token')
        
        # New Delhi Coordinates
        lat, lon = "28.6139", "77.2090"
        ist_now = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        
        panchang_url = f"https://api.prokerala.com/v2/astrology/panchang?datetime={urllib.parse.quote(ist_now)}&coordinates={lat},{lon}&ayanamsa=1"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        print("Fetching Exact Daily Panchang...")
        astro_res = requests.get(panchang_url, headers=headers)
        astro_res.raise_for_status()
        return astro_res.json()
    except Exception as e:
        print(f"Failed to fetch Prokerala data: {e}")
        return None

def generate_panchang_article(astro_data):
    print("Passing precise astronomical data to AI Editor...")
    
    nakshatra = astro_data['data']['nakshatra'][0]['name']
    tithi = astro_data['data']['tithi'][0]['name']
    karana = astro_data['data']['karana'][0]['name']
    yoga = astro_data['data']['yoga'][0]['name']
    
    prompt = f"""
    You are an enlightened Vedic Astrologer. 
    Write a 500-word daily horoscope/panchang article for today.
    
    Here is the exact mathematical astrological data for today:
    - Nakshatra: {nakshatra}
    - Tithi: {tithi}
    - Karana: {karana}
    - Yoga: {yoga}
    
    CRITICAL REQUIREMENTS:
    1. Write a beautiful, inspiring daily guidance article based on this specific Nakshatra and Tithi.
    2. Provide an SEO optimized, highly clickable Headline.
    3. Provide a 5-6 word URL Slug.
    4. Categorize the article for ecommerce. Choose one: "shiva", "pooja", or "general".
    5. Generate a highly descriptive English prompt for an AI Image Generator representing today's astrological energy (e.g. "Cinematic painting of cosmic planets, mystical glowing aura..."). Do NOT include any text in the image prompt.
    
    Format EXACTLY as valid JSON:
    {{
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "ecommerce_category": "general",
        "content_html": "<h2>Today's Astrological Significance</h2><p>...</p>",
        "image_prompt": "Your image prompt here"
    }}
    """
    
    try:
        # NOTE: Keeping gemini-flash-latest because gemini-2.0-flash failed with quota 0 in tests earlier.
        # Ensure you use your newly generated API key!
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

def generate_ai_image(prompt, filename="panchang_image.jpg"):
    print(f"Generating Astrological AI Image... ({prompt})")
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    try:
        response = requests.get(url, stream=True)
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

def get_or_create_category(category_name="Daily Panchang"):
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

def publish_wp_post(data, astro_data, media_id, category_id):
    print("Publishing to WordPress with E-Commerce & Kundli Upsells...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    
    nakshatra = astro_data['data']['nakshatra'][0]['name']
    tithi = astro_data['data']['tithi'][0]['name']
    
    # 1. The Core AI Content
    full_content = f"""
    <div style="background:#f8f9fa; border-left:5px solid #2563eb; padding:25px; margin-bottom:30px;">
        <h3 style="color:#1d4ed8; margin-top:0;">Exact Planetary Positions Today</h3>
        <p><strong>Tithi:</strong> {tithi}</p>
        <p><strong>Nakshatra:</strong> {nakshatra}</p>
    </div>
    {data['content_html']}
    """
    
    # 2. Inject The E-Commerce Block
    full_content += get_affiliate_html(data['ecommerce_category'])
    
    # 3. Inject The Kundli Upsell Funnel
    full_content += get_kundli_upsell_html()
    
    # 4. Inject The EEAT Disclaimer
    full_content += """
    <hr style="margin-top:30px;">
    <p style="font-size:12px; color:#888;"><em><strong>Disclaimer:</strong> This daily astrological forecast is algorithmically generated based on precise astronomical calculations and traditional Vedic Astrology principles. It is for spiritual guidance and entertainment purposes only.</em></p>
    """
    
    payload = {
        "title": data['headline'],
        "content": full_content,
        "status": "publish",
        "slug": data['slug'],
        "categories": [category_id]
    }
    if media_id:
        payload["featured_media"] = media_id
        
    response = requests.post(post_url, json=payload, auth=auth)
    if response.status_code == 201:
        print(f"Successfully published: {data['headline']}!")
    else:
        print(f"Failed to publish. Status code: {response.status_code}")

def main():
    print("Starting Daily Panchang & Monetization Bot...")
    
    astro_data = get_prokerala_panchang()
    if not astro_data:
        return
        
    article_data = generate_panchang_article(astro_data)
    if not article_data:
        return
        
    print(f"AI Editor selected headline: {article_data['headline']}")
    
    image_path = generate_ai_image(article_data['image_prompt'])
    media_id = upload_image_to_wp(image_path) if image_path else None
        
    category_id = get_or_create_category()
    
    publish_wp_post(article_data, astro_data, media_id, category_id)
    
    if image_path and os.path.exists(image_path):
        os.remove(image_path)

if __name__ == "__main__":
    main()
