"""
script_generator.py — HinduDevGyan Reel Engine
Uses Gemini to generate a complete reel script from a topic:
- Viral Hindi hook
- Scene-by-scene narration (6-8 scenes)
- Image prompts per scene
- YouTube/Instagram metadata
- Trending hashtags
"""

import json
import re
from google import genai
import time
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



SCRIPT_PROMPT_TEMPLATE = """
You are the Creative Director of HinduDevGyan — India's most viral Hindu devotional Instagram and YouTube channel.

Your task: Write a COMPLETE reel script for this topic:
"{topic}"

Category: {category}
Deity/Theme: {deity}

CRITICAL RULES:
1. Language: Narration MUST be in simple, conversational HINDI (not Sanskrit-heavy). Like a storyteller speaking to common people.
2. Hook: The first 3 seconds must STOP people from scrolling. Start with a shocking fact, mystery, or question.
3. Scenes: Generate exactly 7 scenes. Each scene = 5 seconds of screen time.
4. Each scene needs:
   - Hindi narration text (what the voice says — max 25 words per scene)
   - English image prompt for Imagen 3 (cinematic, photorealistic, divine art style, 9:16 vertical)
   - Subtitle text (same as narration, for on-screen text)
5. Style: Cinematic divine art. Consistent warm saffron/gold color palette. No modern elements.
6. Total narration should be 60-75 seconds when read at normal pace.
7. End with a call to action: "Follow HinduDevGyan for more such stories"

IMAGE PROMPT RULES (very important):
- Always specify: "cinematic vertical 9:16, divine warm golden light, Indian devotional art style, ultra detailed"
- No text in images
- Be very specific about the scene (characters, setting, action, emotion, lighting)
- Example good prompt: "Lord Shiva meditating on Mount Kailash, snow peaks background, crescent moon in dark sky, divine blue glow, Ganga flowing from matted hair, sacred serpent coiled around neck, cinematic vertical 9:16, ultra detailed 8k"

Return ONLY valid JSON in this exact format:
{{
    "title": "Short viral Hindi title (max 8 words)",
    "hook": "The shocking/mystery opening line in Hindi (max 15 words)",
    "total_duration_sec": 40,
    "scenes": [
        {{
            "id": 1,
            "narration": "Hindi narration text for this scene (max 25 words)",
            "subtitle": "Same text for subtitle overlay",
            "image_prompt": "Detailed English image prompt for Imagen 3, cinematic vertical 9:16...",
            "duration_sec": 5,
            "effect": "zoom_in"
        }}
    ],
    "outro_text": "Follow HinduDevGyan for more divine stories | Link in bio",
    "youtube_title": "Engaging YouTube Shorts title in Hindi with emoji",
    "youtube_description": "3-4 line YouTube description in Hindi + English, with website link: hindudevgyan.in",
    "instagram_caption": "Instagram caption in Hindi with emojis (3-4 lines) + 15 relevant hashtags",
    "hashtags": "#hindudevgyan #sanatan #hindumythology #viral"
}}

Effects options for each scene: zoom_in, zoom_out, pan_left, pan_right, ken_burns
"""


def generate_script(topic: str, category: str, deity: str) -> dict | None:
    """
    Generate a complete reel script using Gemini.
    Returns parsed JSON dict or None on failure.
    """
    print(f"🎬 Generating reel script for: {topic[:60]}...")

    prompt = SCRIPT_PROMPT_TEMPLATE.format(
        topic=topic,
        category=category,
        deity=deity
    )

    raw_text = safe_generate_content(prompt)
    if not raw_text:
        print("Failed to generate script: Could not get response from Gemini API.")
        return None
    raw = raw_text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"Failed to parse script JSON: {e}")
        return None

    # Validate required fields
    required = ["title", "hook", "scenes", "youtube_title", "instagram_caption", "hashtags"]
    for field in required:
        if field not in data:
            print(f"⚠️  Missing field in script: {field}")
            return None

    if not data.get("scenes") or len(data["scenes"]) < 4:
        print("⚠️  Too few scenes generated. Retrying is recommended.")
        return None

    # Ensure each scene has required sub-fields
    valid_effects = {"zoom_in", "zoom_out", "pan_left", "pan_right", "ken_burns"}
    for i, scene in enumerate(data["scenes"]):
        scene.setdefault("id", i + 1)
        scene.setdefault("duration_sec", SCENE_DURATION_SEC)
        scene.setdefault("subtitle", scene.get("narration", ""))
        effect = scene.get("effect", "zoom_in")
        if effect not in valid_effects:
            scene["effect"] = "zoom_in"

    print(f"✅ Script generated: {len(data['scenes'])} scenes, title: {data['title']}")
    return data


def print_script_summary(script: dict):
    """Pretty-print a script summary to console."""
    print("\n" + "═" * 60)
    print(f"🎬 REEL SCRIPT")
    print("═" * 60)
    print(f"📌 Title    : {script.get('title')}")
    print(f"⚡ Hook     : {script.get('hook')}")
    print(f"🎞️  Scenes   : {len(script.get('scenes', []))}")
    print(f"📺 YT Title : {script.get('youtube_title')}")
    print("─" * 60)
    for scene in script.get("scenes", []):
        print(f"  Scene {scene['id']} [{scene.get('effect','zoom_in')}] ({scene.get('duration_sec',5)}s)")
        print(f"    🗣️  {scene.get('narration', '')[:80]}")
        print(f"    🖼️  {scene.get('image_prompt', '')[:80]}...")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    # Quick test
    test_topic = "सावन में शिवलिंग पर जल क्यों चढ़ाया जाता है? — The Secret Behind Jal Abhishek in Sawan"
    script = generate_script(test_topic, "Shiva", "Shiva")
    if script:
        print_script_summary(script)
