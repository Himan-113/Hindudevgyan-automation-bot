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
                if any(k in err_msg for k in ['429', '503', 'RESOURCE_EXHAUSTED', 'UNAVAILABLE', 'quota']):
                    time.sleep(2 * (attempt + 1))
                else:
                    break
    return None


def generate_high_quality_image_prompt(headline):
    prompt = f"""
    You are a Master AI Art Director specializing in hyper-realistic, 8k National Geographic style photography and cinematic Vedic art.
    Article Headline: "{headline}"

    Task: Write a photorealistic, cinematic visual scene description in English for an AI image generator (FLUX).
    Rules:
    - Describe concrete physical subjects, authentic Indian architecture, temple stone carving, marble altars, brass lamps, or celestial cosmos.
    - Mention exact camera angle, natural golden hour lighting, depth of field, rich vibrant colors, 8k masterpiece.
    - NEVER use anime, cartoon, 3D render, CGI, fantasy illustration, or abstract jargon.
    - NEVER include text, watermark, or words.
    - Keep it under 35 words.

    Return ONLY the prompt string, nothing else.
    """
    res = safe_generate_content(prompt)
    if res:
        clean = res.strip().replace('"', '').replace('\n', ' ')
        return clean
    return f"Photorealistic 8k cinematic photography of {headline[:60]}, divine golden lighting, 35mm lens, National Geographic"


def generate_ai_image(prompt, filename="temp_hq_image.jpg"):
    print(f"  -> Generating FLUX 8K Studio Artwork for: {prompt[:60]}...")
    full_prompt = f"8k, ultra-detailed photorealistic award-winning photography, {prompt}, masterpiece, cinematic warm golden lighting, Hasselblad medium format camera, natural textures, sharp focus, 35mm photograph"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(2):
        seed = int(time.time()) + (attempt * 100)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1200&height=630&nologo=true&enhance=true&seed={seed}"
        try:
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            if response.status_code == 200 and len(response.content) > 10000:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return filename
            else:
                time.sleep(2)
        except Exception as e:
            print(f"  -> Attempt {attempt+1} notice ({e})")
            time.sleep(2)

    return None


def get_cross_platform_fonts(size_title=34, size_badge=18):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf"
    ]
    font_title, font_badge = None, None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_title = ImageFont.truetype(path, size_title)
                font_badge = ImageFont.truetype(path, size_badge)
                break
            except Exception:
                pass
    if not font_title:
        try:
            font_title = ImageFont.load_default(size=size_title)
            font_badge = ImageFont.load_default(size=size_badge)
        except Exception:
            font_title = ImageFont.load_default()
            font_badge = ImageFont.load_default()

    return font_title, font_badge


def process_and_brand_image(temp_filepath, output_filename="branded_featured.webp", headline_text="", category_text="SPIRITUAL WISDOM"):
    """
    Overlays high-CTR news thumbnail banner, logo watermark, applies UnsharpMask sharpening, and compresses to WebP.
    """
    try:
        raw_img = Image.open(temp_filepath)
        img = raw_img.convert("RGBA")
        width, height = img.size

        # 1. Subtle Dark Gradient at bottom (180px)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        banner_top = height - 180
        for y in range(banner_top, height):
            alpha = int(((y - banner_top) / (height - banner_top)) * 180)
            draw_ov.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img, overlay)

        draw = ImageDraw.Draw(img)
        font_title, font_badge = get_cross_platform_fonts(size_title=32, size_badge=16)

        # 2. Category Pill Badge
        badge_text = category_text.upper()[:22]
        try:
            badge_bbox = font_badge.getbbox(badge_text)
            badge_w = (badge_bbox[2] - badge_bbox[0]) + 20
            badge_h = (badge_bbox[3] - badge_bbox[1]) + 12
        except Exception:
            badge_w, badge_h = 140, 28

        badge_x1 = 35
        badge_y1 = height - 135
        badge_x2 = badge_x1 + badge_w
        badge_y2 = badge_y1 + badge_h

        draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=5, fill=(232, 84, 10, 245))
        draw.text((badge_x1 + 10, badge_y1 + 4), badge_text, font=font_badge, fill=(255, 255, 255))

        # 3. Clean Headline Banner Text
        clean_title = headline_text.upper()[:48]
        draw.text((35, height - 75), clean_title, font=font_title, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))

        # 4. Inset Top-Right HinduDevGyan Logo Badge
        logo_candidates = [
            os.path.join(os.path.dirname(__file__), "logo.png"),
            os.path.join(os.path.dirname(__file__), "cropped-hindu-dev-logo-without-background-1-1-300x70.png"),
            "logo.png"
        ]
        logo_path = next((p for p in logo_candidates if os.path.exists(p)), None)

        if logo_path:
            logo = Image.open(logo_path).convert("RGBA")
            bbox = logo.getbbox()
            if bbox:
                logo = logo.crop(bbox)

            target_w = 110
            w_percent = (target_w / float(logo.size[0]))
            target_h = int((float(logo.size[1]) * float(w_percent)))
            logo = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

            margin_right = 30
            margin_top = 20
            padding = 6
            card_w = target_w + (padding * 2)
            card_h = target_h + (padding * 2)

            card_x1 = width - margin_right - card_w
            card_y1 = margin_top
            card_x2 = width - margin_right
            card_y2 = margin_top + card_h

            card_ov = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            card_draw = ImageDraw.Draw(card_ov)
            card_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=6, fill=(255, 255, 255, 240), outline=(232, 84, 10, 240), width=1)
            img = Image.alpha_composite(img, card_ov)
            img.paste(logo, (card_x1 + padding, card_y1 + padding), logo)

        # 5. Apply UnsharpMask & Save WebP
        combined = img.convert("RGB")
        sharpened = combined.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=2))
        sharpened.save(output_filename, "WEBP", quality=88)
        return output_filename
    except Exception as e:
        print(f"  -> Error in branding image: {e}")
        return temp_filepath


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
    """Fetches up to limit recent posts across paginated WP API."""
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

    # Combine uniquely (do missing first, then upgrade remaining of top 30)
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
        
        # Extract Category
        category_name = "SPIRITUAL WISDOM"
        if '_embedded' in post and 'wp:term' in post['_embedded']:
            terms = post['_embedded']['wp:term']
            if terms and len(terms) > 0 and len(terms[0]) > 0:
                category_name = terms[0][0].get('name', 'SPIRITUAL WISDOM')

        print(f"[{idx}/{len(work_queue)}] [{task_type}] Processing #{post_id}: {headline}")

        # 1. Generate High Quality FLUX Prompt
        hq_prompt = generate_high_quality_image_prompt(headline)
        
        # 2. Generate FLUX 8K Artwork
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

        time.sleep(3)  # Gentle spacing

    print(f"\n[+] ALL DONE! Successfully updated {success_count} posts with High-End Branded 8K Images.")


if __name__ == "__main__":
    enhance_and_fix_posts()
