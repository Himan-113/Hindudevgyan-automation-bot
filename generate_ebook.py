import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_chapter(chapter_title, context):
    print(f"Authoring {chapter_title}...")
    prompt = f"""
    You are an enlightened Master of Vastu Shastra.
    Write a highly detailed, professional, and practical 1500-word chapter for a premium E-Book titled "Vastu Shastra for Wealth & Harmony".
    
    Chapter Title: {chapter_title}
    Context for this chapter: {context}
    
    CRITICAL INSTRUCTIONS:
    - Write the chapter strictly in beautiful HTML format.
    - Use <h2> for the Chapter Title, <h3> for subheadings, <p> for paragraphs, and <ul>/<li> for bullet points.
    - Make the tone authoritative, spiritual, yet highly practical for modern homes.
    - DO NOT include markdown backticks (```html) in your response. Just return the raw HTML.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        text = response.text
        if text.startswith("```html"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return text
    except Exception as e:
        print(f"Failed to generate chapter: {e}")
        return ""

def generate_full_ebook():
    print("Starting Automated E-Book Generation Process...")
    
    chapters = [
        ("Chapter 1: The Cosmic Architecture", "Introduction to Vastu Shastra, the 5 elements (Pancha Bhootas), and how energy (Prana) flows through a home."),
        ("Chapter 2: The Main Entrance (The Gateway of Wealth)", "Detailed rules for the main door, auspicious directions, what to avoid, and how to attract Goddess Lakshmi."),
        ("Chapter 3: The Wealth Corner (Kubera Sthana)", "The importance of the North and North-East directions. How to activate the wealth corner using water elements and colors."),
        ("Chapter 4: The Kitchen & Bedroom Vastu", "Where to cook for health (Agni Kund) and where to sleep for peace and marital harmony (South-West)."),
        ("Chapter 5: Vastu Dosha Remedies Without Demolition", "Practical remedies using mirrors, pyramids, sea salt, and yantras to fix existing Vastu flaws without breaking walls.")
    ]
    
    full_html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Vastu Shastra for Wealth & Harmony</title>
        <style>
            body { font-family: 'Georgia', serif; line-height: 1.8; color: #333; max-width: 800px; margin: 0 auto; padding: 40px; }
            h1 { color: #E65100; font-size: 36px; text-align: center; margin-bottom: 10px; }
            h2 { color: #b45309; font-size: 28px; margin-top: 50px; border-bottom: 2px solid #fef3c7; padding-bottom: 10px; }
            h3 { color: #d97706; font-size: 22px; margin-top: 30px; }
            p { font-size: 16px; margin-bottom: 20px; }
            .cover { text-align: center; margin-bottom: 80px; padding: 50px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; }
            .subtitle { font-size: 20px; color: #78350f; font-style: italic; }
            .author { font-size: 16px; color: #92400e; margin-top: 20px; font-weight: bold; }
            .page-break { page-break-before: always; }
        </style>
    </head>
    <body>
        <div class="cover">
            <h1>Vastu Shastra for Wealth & Harmony</h1>
            <div class="subtitle">The Ancient Science of Cosmic Architecture</div>
            <div class="author">By HinduDevGyan</div>
        </div>
    """
    
    for title, context in chapters:
        chapter_html = generate_chapter(title, context)
        full_html += f"<div class='page-break'></div>\n{chapter_html}\n"
        
    full_html += "\n</body>\n</html>"
    
    with open("Vastu_Shastra_Ebook.html", "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print("\nSUCCESS! Vastu_Shastra_Ebook.html has been generated.")
    print("To convert to PDF: Open this HTML file in Google Chrome, press Ctrl+P (Print), and select 'Save as PDF'.")

if __name__ == "__main__":
    generate_full_ebook()
