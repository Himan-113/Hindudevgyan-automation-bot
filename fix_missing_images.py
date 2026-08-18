import os
import json
import time
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
load_dotenv('reel_engine/.env')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL") or "https://hindudevgyan.in"
WP_USERNAME = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USERNAME") or os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD") or os.getenv("WP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def safe_generate_content(prompt):
    """
    Robustly calls Gemini API using a fallback chain of models:
    gemini-2.5-flash-lite -> gemini-3.6-flash -> gemini-flash-latest.
    Automatically retries on 429 and 503 errors.
    """
    if not client:
        return None

    models_to_try = [
        'gemini-2.5-flash-lite',
        'gemini-3.6-flash',
        'gemini-flash-latest'
    ]
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
                if any(k in err_msg for k in ['429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'quota']):
                    time.sleep(2 * (attempt + 1))
                else:
                    break
    return None


def generate_high_quality_image_prompt(headline, article_text="", category_name=""):
    clean_context = ""
    if article_text:
        import re
        clean_context = re.sub(r'<[^>]+>', ' ', article_text)[:600].strip()

    prompt = f"""
    You are an expert AI Visual Director for a premium Vedic and Hindu media portal.
    Headline: "{headline}"
    Category: "{category_name}"
    Context: "{clean_context}"

    Task: Create a highly relevant, distinct 2026 cinematic visual scene prompt for this specific article.
    STRICT ICONOGRAPHY RULES:
    1. If a REAL PHYSICAL TEMPLE / LANDMARK is mentioned (e.g., Amarnath, Kedarnath, Badrinath, Somnath, Ayodhya, Kashi, Ujjain, Vrindavan, Tirupati, Puri):
       - State the majestic physical architecture clearly (e.g., "The majestic Himalayan Kedarnath temple facade with snow peaks").
    2. If PANCHANG, NAKSHATRA, or HOROSCOPE:
       - Describe glowing celestial nebulae, radiant cosmic constellations, and an ancient Sanskrit manuscript on a carved wooden altar.
    3. If FESTIVAL & VRAT (e.g. Janmashtami, Diwali, Navratri, Shivratri):
       - Describe vibrant festive elements: polished brass puja thali with fresh flowers, glowing oil diyas, and sacred offerings.
    4. If A SPECIFIC DEITY (Lord Shiva, Lord Krishna, Lord Rama, Hanuman, Ganesha, Maa Durga):
       - Describe that specific deity in a serene divine posture with glowing ethereal aura and iconic sacred symbols (flute, trishul, bow).
    5. CRITICAL RESTRICTIONS: Describe only concrete physical subjects and ethereal lighting. Strictly NO text, NO letters, NO watermarks.
    6. Keep prompt under 35 words. Return ONLY the prompt string.
    """
    res = safe_generate_content(prompt)
    if res:
        clean = res.strip().replace('"', '').replace('\n', ' ')
        return clean
    return f"{headline}"


def upload_image_to_wp(image_path, alt_text=""):
    print("  -> Uploading branded 8K WebP to WordPress Media Library...")
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    
    with open(image_path, 'rb') as file:
        headers = {
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"',
            'Content-Type': 'image/webp'
        }
        response = requests.post(media_url, headers=headers, data=file, auth=auth)
        if response.status_code == 201:
            media_data = response.json()
            media_id = media_data.get('id')
            if alt_text:
                try:
                    requests.post(f"{media_url}/{media_id}", json={"alt_text": alt_text}, auth=auth)
                except Exception:
                    pass
            return media_id
        else:
            print(f"  -> WP Upload failed. Status: {response.status_code}")
    return None


def fetch_all_recent_posts(limit=100):
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    all_posts = []
    page = 1
    
    while len(all_posts) < limit:
        per_page = min(50, limit - len(all_posts))
        posts_url = f"{WP_URL}/wp-json/wp/v2/posts?per_page={per_page}&page={page}&_embed=1"
        try:
            res = requests.get(posts_url, auth=auth, timeout=15)
            if res.status_code == 200:
                batch = res.json()
                if not batch:
                    break
                all_posts.extend(batch)
                page += 1
            else:
                break
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    return all_posts


def enhance_and_fix_posts():
    print("==================================================================")
    print("[*] HinduDevGyan High-End Image Refresh & Missing Image Fix Engine")
    print("==================================================================")
    
    global WP_URL, WP_USERNAME, WP_APP_PASSWORD
    WP_URL = os.getenv("WP_URL") or "https://hindudevgyan.in"
    WP_USERNAME = os.getenv("WP_USERNAME") or os.getenv("WORDPRESS_USERNAME") or os.getenv("WP_USER")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD") or os.getenv("WORDPRESS_APP_PASSWORD") or os.getenv("WP_PASSWORD")

    if not WP_USERNAME or not WP_APP_PASSWORD:
        print(f"ERROR: Missing WordPress credentials. WP_URL: '{WP_URL}', WP_USERNAME: '{WP_USERNAME}', WP_APP_PASSWORD Present: {bool(WP_APP_PASSWORD)}")
        return

    print("Step 1: Scanning latest 100 published articles from WordPress...")
    posts = fetch_all_recent_posts(limit=100)
    print(f"Retrieved {len(posts)} articles.")

    # Process latest posts strictly from top-to-bottom (newest post #1 downwards)
    work_queue = []
    seen_ids = set()
    for p in posts[:40]:
        if p['id'] not in seen_ids:
            work_queue.append(p)
            seen_ids.add(p['id'])

    print(f"Total posts queued for processing (starting from newest Post #1): {len(work_queue)}\n")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    success_count = 0

    for idx, post in enumerate(work_queue, 1):
        post_id = post['id']
        headline = post['title']['rendered']
        slug = post.get('slug', f'post-{post_id}')
        
        category_name = "SPIRITUAL WISDOM"
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            if terms and len(terms) > 0 and len(terms[0]) > 0:
                category_name = terms[0][0].get('name', 'SPIRITUAL WISDOM')

        # 1. Generate Context-Aware Visual Prompt from Title + Article Body + Category
        post_content = post.get('content', {}).get('rendered', '')
        hq_prompt = generate_high_quality_image_prompt(headline, article_text=post_content, category_name=category_name)
        
        # 2. Smart Hybrid Visual Engine: Real photo if landmark, else 8K FLUX + Snug Watermark
        final_webp = f"{slug}-hq.webp"
        from image_engine import generate_hd_featured_image
        branded_image = generate_hd_featured_image(
            prompt_text=f"{headline}. {hq_prompt}",
            category=category_name,
            output_filename=final_webp
        )
        if not branded_image or not os.path.exists(branded_image):
            print("  -> Skipped (Failed to generate image).")
            continue

        # 4. Upload to WordPress Media Library
        media_id = upload_image_to_wp(branded_image, alt_text=headline)
        if not media_id:
            print("  -> Skipped (Upload failed).")
            continue

        # 5. Attach new Featured Media to Post
        update_url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
        res = requests.post(update_url, json={"featured_media": media_id}, auth=auth)
        if res.status_code == 200:
            print(f"  -> SUCCESS: Attached Branded 8K WebP (Media #{media_id}) to Post #{post_id}!")
            success_count += 1
        else:
            print(f"  -> Failed to update post. Status: {res.status_code}")

        # Cleanup local file
        if os.path.exists(final_webp):
            try:
                os.remove(final_webp)
            except Exception:
                pass

        time.sleep(3)

    print(f"\n[+] ALL DONE! Successfully updated {success_count} posts with High-End Branded 8K Images.")


if __name__ == "__main__":
    enhance_and_fix_posts()
