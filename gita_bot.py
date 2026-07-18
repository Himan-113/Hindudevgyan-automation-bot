import os
import requests
import json
import urllib.parse
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_gita_wisdom():
    print("AI Guru is selecting a profound verse and generating wisdom...")
    
    prompt = """
    You are an enlightened Vedic Scholar and SEO Expert. 
    Your task is to randomly select a deeply profound and inspiring verse from the Bhagavad Gita and write a beautiful article about it in English.
    Ensure you pick a different verse than the most famous ones so the daily content stays fresh.
    
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
    7. Generate a highly descriptive English prompt for an AI Image Generator (e.g. "Cinematic realistic painting of Arjuna looking at Krishna, divine golden light, beautiful details, 4k"). Do NOT include any text in the image prompt.
    
    Format EXACTLY as valid JSON, with no markdown formatting around it, just raw JSON:
    {
        "headline": "Your English Headline Here",
        "slug": "your-english-slug-here",
        "sanskrit": "Sanskrit text here",
        "translation": "English translation here",
        "content_html": "<h2>Meaning</h2><p>...</p>",
        "image_prompt": "Your image prompt here"
    }
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

def generate_ai_image(prompt, filename="gita_image.jpg"):
    print(f"Generating Copyright-Free Spiritual AI Image... ({prompt})")
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
            print("Failed to generate AI image.")
            return None
    except Exception as e:
        print(f"Image generation error: {e}")
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
    
    # Format the beautiful Sloka box
    full_content = f"""
    <div style="background:#fffcf0; border-left:5px solid #FF9800; padding:25px; margin-bottom:30px;">
        <h3 style="color:#E65100; margin-top:0;">{data['sanskrit']}</h3>
        <p><em>"{data['translation']}"</em></p>
    </div>
    {data['content_html']}
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
        print(response.text)

def main():
    print("Starting Gita Wisdom Engine 2.0...")
    
    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables.")
        return
        
    wisdom_data = generate_gita_wisdom()
    if not wisdom_data:
        print("Failed to generate wisdom. Exiting.")
        return
        
    print(f"Verse Selected! Headline: {wisdom_data['headline']}")
    
    image_path = generate_ai_image(wisdom_data['image_prompt'])
    media_id = None
    if image_path:
        media_id = upload_image_to_wp(image_path)
        
    category_id = get_or_create_category()
    
    publish_wp_post(wisdom_data, media_id, category_id)
    
    if image_path and os.path.exists(image_path):
        os.remove(image_path)

if __name__ == "__main__":
    main()
