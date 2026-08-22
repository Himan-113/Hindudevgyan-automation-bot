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

gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_SA_KEY")

if gcp_project and gcp_credentials:
    # Routes Text Generation through Vertex AI to burn your ₹28,000 Credit Balance with 0 Quota limits
    client = genai.Client(vertexai=True, project=gcp_project, location=os.getenv("GCP_LOCATION", "us-central1"))
elif GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None


def safe_generate_content(prompt):
    """
    Robustly calls Gemini API using a fallback chain of models:
    gemini-2.5-flash-lite -> gemini-3.6-flash -> gemini-flash-latest.
    Automatically retries on 429 and 503 errors.
    """
    if not client:
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
    return None


def generate_high_quality_image_prompt(headline, article_text="", category_name=""):
    clean_context = ""
    if article_text:
        import re
        clean_context = re.sub(r'<[^>]+>', ' ', article_text)[:600].strip()

    prompt = f"""
    You are the Senior Visual Director for HinduDevGyan, designing 2026 Ultra-HD Divine Spiritual Art.
    Headline: "{headline}"
    Category: "{category_name}"
    Context: "{clean_context}"

    Task: Create a magnificent, high-CTR visual scene description for Google Imagen 3.
    CORE VISUAL RULES:
    1. CENTRAL DIVINE SUBJECT: The image MUST always feature a glorious, radiant Hindu Deity or Grand Sacred Temple. NEVER generate only an inanimate diya, empty altar, or stone wall.
    2. DEITY PORTRAYAL (Shiva, Krishna, Vishnu, Lakshmi, Ganesha, Rama, Hanuman, Durga):
       - Depict the deity in a majestic, serene, divine posture with a glowing golden ethereal aura, ornate Vedic crown/jewelry, and sacred attributes (Trishul, Flute, Sudarshana Chakra, Lotus).
    3. FOR FESTIVALS & VRATS (Ekadashi, Sawan, Raksha Bandhan, Janmashtami, Diwali, Navratri):
       - Depict the presiding Supreme Deity (e.g. Lord Vishnu & Lakshmi for Ekadashi; Lord Shiva for Sawan Somwar; Lord Krishna for Janmashtami) giving divine blessings with glowing celestial golden light and floating lotus flowers.
    4. FOR GITA WISDOM & VEDIC PHILOSOPHY:
       - Depict Lord Krishna in majestic cosmic golden form imparting sacred divine wisdom, with cosmic starlight and radiant glowing aura.
    5. FOR TEMPLES & PILGRIMAGE:
       - Depict the grand illuminated temple architecture (e.g. Kedarnath, Kashi, Ayodhya, Somnath) bathed in divine golden sunrise light with snow peaks or sacred river ghats.
    6. FOR PANCHANG & ASTROLOGY:
       - Depict Lord Ganesha or Sun God Surya seated gracefully in glowing golden cosmos surrounded by radiant celestial constellations.
    7. STYLE: Ultra-detailed, 8K resolution, radiant saffron gold, warm amber light, cosmic indigo. Strictly NO text, NO letters, NO modern gadgets.

    Keep prompt under 35 words. Return ONLY the final visual prompt string.
    """
    res = safe_generate_content(prompt)
    if res:
        clean = res.strip().replace('"', '').replace('\n', ' ')
        return clean
    return f"A divine cosmic portrait of Hindu deity in glowing golden ethereal temple setting"


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

    # Skip the first 31 manually updated posts and process strictly from Post #32 to Post #100
    start_index = int(os.getenv("FIX_START_INDEX", "31"))
    work_queue = []
    seen_ids = set()
    for p in posts[start_index:100]:
        if p['id'] not in seen_ids:
            work_queue.append(p)
            seen_ids.add(p['id'])

    print(f"Total posts queued for processing (Starting from Post #{start_index+1} onwards): {len(work_queue)}\n")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    success_count = 0

    for idx, post in enumerate(work_queue, 1):
        post_id = post['id']
        headline = post['title']['rendered']
        slug = post.get('slug', f'post-{post_id}')

        print(f"\n[{idx}/{len(work_queue)}] Processing Post #{post_id}: '{headline[:60]}'", flush=True)

        category_name = "SPIRITUAL WISDOM"
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            if terms and len(terms) > 0 and len(terms[0]) > 0:
                category_name = terms[0][0].get('name', 'SPIRITUAL WISDOM')

        # 1. Generate Context-Aware Visual Prompt from Title + Article Body + Category
        post_content = post.get('content', {}).get('rendered', '')
        hq_prompt = generate_high_quality_image_prompt(headline, article_text=post_content, category_name=category_name)

        # 2. Smart 2026 Visual Engine: 8K FLUX / Imagen + Snug Watermark
        final_webp = f"{slug}-hq.webp"
        from image_engine import generate_hd_featured_image
        branded_image = generate_hd_featured_image(
            prompt_text=hq_prompt,
            category=category_name,
            output_filename=final_webp
        )
        if not branded_image or not os.path.exists(branded_image):
            print("  -> Skipped (Failed to generate image).", flush=True)
            continue

        # 4. Upload to WordPress Media Library
        media_id = upload_image_to_wp(branded_image, alt_text=headline)
        if not media_id:
            print("  -> Skipped (Upload failed).", flush=True)
            continue

        # 5. Attach new Featured Media to Post
        update_url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
        res = requests.post(update_url, json={"featured_media": media_id}, auth=auth)
        if res.status_code == 200:
            print(f"  -> SUCCESS: Attached Branded 8K WebP (Media #{media_id}) to Post #{post_id}!", flush=True)
            success_count += 1
        else:
            print(f"  -> Failed to update post. Status: {res.status_code}", flush=True)

        # Cleanup local file
        if os.path.exists(final_webp):
            try:
                os.remove(final_webp)
            except Exception:
                pass

        time.sleep(2)

    print(f"\n[+] ALL DONE! Successfully updated {success_count} posts with High-End Branded 8K Images.", flush=True)


if __name__ == "__main__":
    enhance_and_fix_posts()
