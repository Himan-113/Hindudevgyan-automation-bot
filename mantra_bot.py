import os
import requests
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

client = genai.Client(api_key=GEMINI_API_KEY)

DAY_NAMES = {
    1: "Monday (ruling deity: Lord Shiva)",
    2: "Tuesday (ruling deity: Lord Hanuman / Mangal)",
    3: "Wednesday (ruling deity: Lord Ganesha / Budh)",
    4: "Thursday (ruling deity: Guru Brihaspati / Lord Vishnu)",
    5: "Friday (ruling deity: Goddess Lakshmi / Devi / Shukra)",
    6: "Saturday (ruling deity: Lord Shani)",
    7: "Sunday (ruling deity: Surya, the Sun God)",
}


def get_current_pool():
    print("Fetching current mantra pool from WordPress...")
    try:
        res = requests.get(f"{WP_URL}/wp-json/hdg/v1/mantras")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Failed to fetch pool: {e}")
    return []


def find_neediest_day(pool):
    counts = {d: 0 for d in range(1, 8)}
    for m in pool:
        day = m.get('day')
        if day in counts:
            counts[day] += 1

    neediest_day = min(counts, key=counts.get)
    print(f"Current counts per day: {counts}")
    print(f"Neediest day: {neediest_day} - {DAY_NAMES[neediest_day]}")
    return neediest_day


def generate_new_mantra(target_day, existing_sanskrit_openers):
    day_description = DAY_NAMES[target_day]

    avoid_text = ""
    if existing_sanskrit_openers:
        avoid_text = (
            "\n\nDo NOT repeat any of these mantras already in our pool (matching by opening words):\n"
            + "\n".join(f"- {s}" for s in existing_sanskrit_openers)
        )

    prompt = f"""
    You are an enlightened Vedic Scholar and SEO Expert. Provide one short, well-known,
    authentic Sanskrit mantra or shloka appropriate for {day_description}.
    {avoid_text}

    Requirements:
    1. Must be a genuine, traditional Sanskrit mantra (not invented) - one that is
       widely recognized and commonly recited, appropriate for {day_description}.
    2. Keep it short - 1 to 2 lines of Sanskrit, suitable for a small card display.
    3. Provide an accurate Hindi meaning (2-3 sentences).
    4. Provide an accurate English translation (2-3 sentences).
    5. Provide a short title in English and in Hindi.
    6. Write a slightly longer (100-150 word) English explanation of the mantra's
       significance and when/how it is traditionally recited - this will be published
       as its own short article, so it needs enough substance to be a real page.
    7. SEO META: "meta_title" (under 60 characters, e.g. "Shani Mantra - Meaning & Benefits"),
       "meta_description" (under 155 characters), "focus_keyword" (2-4 words,
       e.g. "Shani mantra meaning").
    8. URL Slug: a 3-5 word English slug for this mantra, hyphenated (e.g. "shani-mantra-meaning-benefits").

    Format EXACTLY as valid JSON, no markdown, no extra text:
    {{
        "title_en": "Short English Title",
        "title_hi": "संक्षिप्त हिंदी शीर्षक",
        "sanskrit": "The Sanskrit mantra text",
        "hindi": "Hindi meaning",
        "english": "English translation",
        "explanation": "100-150 word explanation of significance and how it's used",
        "meta_title": "SEO title under 60 chars",
        "meta_description": "SEO description under 155 chars",
        "focus_keyword": "2-4 word focus phrase",
        "slug": "3-5-word-url-slug"
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
        print(f"Failed to generate mantra: {e}")
        return None


def get_or_create_category(category_name="Mantras & Chants"):
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


def publish_mantra_post(mantra_data, category_id):
    """Publishes the mantra as its own real WordPress post, so it gets a
    genuine, unique, indexable URL - not just an anchor on a shared page."""
    print(f"Publishing '{mantra_data['title_en']}' as its own post...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = (WP_USERNAME, WP_APP_PASSWORD)

    content = f"""
    <div style="background:#fffcf0; border-left:5px solid #FF9800; padding:25px; margin-bottom:30px;">
        <h3 style="color:#E65100; margin-top:0;">{mantra_data['sanskrit']}</h3>
        <p><em>"{mantra_data['english']}"</em></p>
    </div>
    <h2>हिंदी अर्थ (Hindi Meaning)</h2>
    <p>{mantra_data['hindi']}</p>
    <h2>Significance</h2>
    <p>{mantra_data['explanation']}</p>
    """

    payload = {
        "title": mantra_data['title_en'],
        "content": content,
        "status": "publish",
        "slug": mantra_data.get('slug', ''),
        "categories": [category_id] if category_id else [],
        "meta": {
            "rank_math_title": mantra_data.get('meta_title', mantra_data['title_en'])[:60],
            "rank_math_description": mantra_data.get('meta_description', '')[:160],
            "rank_math_focus_keyword": mantra_data.get('focus_keyword', '')
        }
    }

    response = requests.post(post_url, json=payload, auth=auth)
    if response.status_code == 201:
        post_data = response.json()
        permalink = post_data.get('link', '')
        print(f"Post published: {permalink}")
        return permalink
    else:
        print(f"Failed to publish post. Status: {response.status_code}")
        print(response.text)
        return None


def add_mantra_to_pool(mantra_data, day, post_url):
    print("Adding mantra to the sidebar widget pool...")
    auth = (WP_USERNAME, WP_APP_PASSWORD)
    payload = {
        "day": day,
        "title_en": mantra_data['title_en'],
        "title_hi": mantra_data['title_hi'],
        "sanskrit": mantra_data['sanskrit'],
        "hindi": mantra_data['hindi'],
        "english": mantra_data['english'],
        "url": post_url or ""
    }
    res = requests.post(f"{WP_URL}/wp-json/hdg/v1/mantras", json=payload, auth=auth)
    if res.status_code == 201:
        print(f"Success! Pool now has {res.json().get('total_pool_size')} mantras total.")
    else:
        print(f"Failed to add mantra to pool. Status: {res.status_code}")
        print(res.text)


def main():
    print("Starting Mantra Pool Growth Bot...")

    if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print("ERROR: Missing environment variables.")
        return

    pool = get_current_pool()
    target_day = find_neediest_day(pool)
    existing_openers = [m['sanskrit'][:25] for m in pool if 'sanskrit' in m]

    new_mantra = None
    for attempt in range(3):
        candidate = generate_new_mantra(target_day, existing_openers)
        if not candidate:
            continue
        if any(candidate['sanskrit'][:25] == opener for opener in existing_openers):
            print(f"Attempt {attempt + 1}: duplicate detected, retrying...")
            continue
        new_mantra = candidate
        break

    if not new_mantra:
        print("Could not generate a fresh, non-duplicate mantra after several attempts. Skipping this run.")
        return

    category_id = get_or_create_category()
    post_url = publish_mantra_post(new_mantra, category_id)

    add_mantra_to_pool(new_mantra, target_day, post_url)


if __name__ == "__main__":
    main()
