import os
import json
import time
import requests
import urllib.parse
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)


def safe_generate_content(prompt):
    """
    Robustly calls Gemini API using a fallback chain of models:
    gemini-2.5-flash -> gemini-2.5-flash-lite -> gemini-3.6-flash -> gemini-flash-latest.
    Automatically retries on 429 (quota/rate limit) and 503 (high demand) errors.
    """
    if not client:
        print("Error: Gemini client not initialized.")
        return None

    models_to_try = [
        'gemini-3.6-flash',
        'gemini-2.5-flash-lite',
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
                    time.sleep(3 * (attempt + 1))
                else:
                    break

    print(f"Error: All Gemini model attempts failed. Last error: {last_error}")
    return None


def generate_image_prompt(headline):
    prompt = f"""
    You are an expert AI Image Designer. 
    I have an article with this headline: "{headline}"
    
    Write a highly descriptive, cinematic English prompt for an AI Image Generator to create a featured image for this article (e.g. "Cinematic realistic image of Lord Shiva meditating in the Himalayas, golden hour lighting"). 
    Do NOT include any text in the image prompt.
    Return ONLY the prompt string, nothing else.
    """
    res = safe_generate_content(prompt)
    return res.strip() if res else None

def generate_ai_image(prompt, filename="temp_fix_image.jpg"):
    print(f"  -> Generating image for prompt: {prompt[:50]}...")
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=630&nologo=true"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return filename
        else:
            print("  -> Pollinations API failed.")
            return None
    except Exception as e:
        print(f"  -> Exception generating image: {e}")
        return None

def upload_image_to_wp(image_path):
    print("  -> Uploading to WordPress Media Library...")
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

def fix_missing_images():
    print("Starting WordPress Missing Image Cleanup...")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    
    # Fetch last 30 posts
    posts_url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=30"
    response = requests.get(posts_url, auth=auth)
    
    if response.status_code != 200:
        print(f"Failed to fetch posts from WordPress. Status: {response.status_code} Response: {response.text}")
        return
        
    posts = response.json()
    broken_posts = [p for p in posts if p.get('featured_media') == 0]
    
    print(f"Found {len(broken_posts)} posts missing featured images.")
    
    for post in broken_posts:
        time.sleep(10) # FORCE a 10-second delay before every single post, no matter what!
        post_id = post['id']
        headline = post['title']['rendered']
        print(f"\nFixing Post #{post_id}: {headline}")
        
        # 1. Generate prompt
        prompt = generate_image_prompt(headline)
        if not prompt: continue
        
        # 2. Download Image
        image_path = generate_ai_image(prompt)
        if not image_path: continue
        
        # 3. Upload to WP
        media_id = upload_image_to_wp(image_path)
        if not media_id:
            print("  -> Failed to upload media.")
            continue
            
        # 4. Attach to post
        print(f"  -> Attaching Media ID {media_id} to Post #{post_id}...")
        update_url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
        update_response = requests.post(update_url, json={"featured_media": media_id}, auth=auth)
        
        if update_response.status_code == 200:
            print("  -> SUCCESS!")
        else:
            print(f"  -> Failed to attach. Status: {update_response.status_code}")
            
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)
            
        print(f"  -> Finished processing Post #{post_id}.")
        
    print("\nCleanup Complete! All missing images have been fixed.")

if __name__ == "__main__":
    fix_missing_images()
