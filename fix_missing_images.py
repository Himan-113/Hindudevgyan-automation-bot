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
FAL_KEY = os.getenv("FAL_KEY", "092232b9-8c57-4cd8-b6c0-5834c6125d89:4abc7379b3003f26666d9ae2ea156e5c")
WP_URL = os.getenv("WP_URL", "https://hindudevgyan.in")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

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


def generate_high_quality_image_prompt(headline, article_text=""):
    # Strip HTML and truncate to first 600 chars of context
    clean_context = ""
    if article_text:
        import re
        clean_context = re.sub(r'<[^>]+>', ' ', article_text)[:600].strip()

    prompt = f"""
    You are a Master AI Art Director specializing in hyper-realistic, 8k National Geographic style photography and cinematic Vedic art.
    Article Headline: "{headline}"
    Article Context & Ritual Details:
    "{clean_context}"

    Task: Read the headline AND article context to understand the exact deity, temple, and ritual described. Then write a photorealistic, cinematic visual scene description in English for an AI image generator (FLUX).
    Rules:
    - Focus on a HEROIC CENTERED PORTRAIT or TEMPLE SANCTUM SANCTORUM of the exact primary deity or sacred ritual altar described (e.g. Lord Shiva in meditation, Shiva Lingam abhishekam, Goddess Lakshmi, Lord Ganesha, etc.).
    - Incorporate specific elements from the article (e.g., holy ash, brass trishul, clay diyas, marigold garlands, sacred incense smoke).
    - Authentic Indian stone temple architecture, dramatic golden hour lighting, depth of field, 8k masterpiece.
    - NEVER describe distant crowds, background people, or miniature figurines.
    - NEVER include text, watermark, or words.
    - Keep it under 35 words.

    Return ONLY the prompt string, nothing else.
    """
    res = safe_generate_content(prompt)
    if res:
        clean = res.strip().replace('"', '').replace('\n', ' ')
        return clean
    return f"Heroic centered portrait of sacred deity in ancient stone temple sanctum, glowing brass diyas, golden lighting"


def generate_ai_image(prompt, filename="temp_hq_image.jpg"):
    """
    Calls centralized image_engine with Cloudflare FLUX.1 [schnell] & tight watermark badge.
    """
    from image_engine import generate_hd_featured_image
    return generate_hd_featured_image(prompt, category="Spiritual Wisdom", output_filename=filename)


def process_and_brand_image(temp_filepath, output_filename="branded_featured.webp", headline_text="", category_text="SPIRITUAL WISDOM"):
    """
    Applies tight logo watermark if not already applied.
    """
    from image_engine import apply_smart_logo_watermark
    return apply_smart_logo_watermark(temp_filepath, output_filename)


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
    
    if not all([WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing WordPress credentials in .env file.")
        return

    print("Step 1: Scanning latest 100 published articles from WordPress...")
    posts = fetch_all_recent_posts(limit=100)
    print(f"Retrieved {len(posts)} articles.")

    # Phase 1: Identify all posts missing featured images (0 or None)
    missing_image_posts = [p for p in posts if not p.get('featured_media') or p.get('featured_media') == 0]
    print(f"\n[!] Found {len(missing_image_posts)} posts with MISSING featured images.")

    # Phase 2: Top 30 posts to upgrade to High-End FLUX + Brand Logo Watermarks
    top_upgrade_posts = posts[:30]
    print(f"[*] Selecting top {len(top_upgrade_posts)} recent posts for High-End FLUX Art & Logo Upgrade.\n")

    seen_ids = set()
    work_queue = []

    for p in missing_image_posts:
        if p['id'] not in seen_ids:
            work_queue.append((p, "MISSING_FIX"))
            seen_ids.add(p['id'])

    for p in top_upgrade_posts:
        if p['id'] not in seen_ids:
            work_queue.append((p, "QUALITY_UPGRADE"))
            seen_ids.add(p['id'])

    print(f"Total posts queued for processing: {len(work_queue)}\n")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    success_count = 0

    for idx, (post, task_type) in enumerate(work_queue, 1):
        post_id = post['id']
        headline = post['title']['rendered']
        slug = post.get('slug', f'post-{post_id}')
        
        category_name = "SPIRITUAL WISDOM"
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            if terms and len(terms) > 0 and len(terms[0]) > 0:
                category_name = terms[0][0].get('name', 'SPIRITUAL WISDOM')

        # 1. Generate High Quality Context-Aware FLUX Prompt from Title + Article Body
        post_content = post.get('content', {}).get('rendered', '')
        hq_prompt = generate_high_quality_image_prompt(headline, article_text=post_content)
        
        # 2. Generate 8K Artwork (Fal.ai FLUX -> Pollinations Fallback)
        temp_file = f"temp_{slug}.jpg"
        raw_image = generate_ai_image(hq_prompt, filename=temp_file)
        if not raw_image:
            print("  -> Skipped (Failed to generate image).")
            continue

        # 3. Apply Brand Logo + Category Badge + UnsharpMask + Convert to WebP
        final_webp = f"{slug}-hq.webp"
        branded_image = process_and_brand_image(
            temp_filepath=raw_image,
            output_filename=final_webp,
            headline_text=headline,
            category_text=category_name
        )

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

        # Cleanup local files
        for f in [temp_file, final_webp]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        time.sleep(3)

    print(f"\n[+] ALL DONE! Successfully updated {success_count} posts with High-End Branded 8K Images.")


if __name__ == "__main__":
    enhance_and_fix_posts()
