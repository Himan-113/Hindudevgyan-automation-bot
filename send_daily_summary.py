import os
import requests
import smtplib
from datetime import datetime
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL", "https://hindudevgyan.in")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def get_todays_published_posts():
    """Fetches all posts published on WordPress today (IST timezone)."""
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    start_of_today = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    iso_start = start_of_today.strftime('%Y-%m-%dT00:00:00')

    url = f"{WP_URL}/wp-json/wp/v2/posts"
    params = {
        "after": iso_start,
        "per_page": 50,
        "_embed": "1"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            raw_posts = response.json()
            formatted_posts = []
            for p in raw_posts:
                title = p.get('title', {}).get('rendered', 'Untitled')
                link = p.get('link', WP_URL)
                date_str = p.get('date', '')

                # Extract Category Name if embedded
                cats = []
                if '_embedded' in p and 'wp:term' in p['_embedded']:
                    terms = p['_embedded']['wp:term']
                    if terms and len(terms) > 0:
                        cats = [t['name'] for t in terms[0]]
                category_name = ", ".join(cats) if cats else "Spiritual"

                formatted_posts.append({
                    "id": p.get('id'),
                    "title": title,
                    "link": link,
                    "category": category_name,
                    "date": date_str
                })
            return formatted_posts
        else:
            print(f"Failed to fetch posts from WordPress API. Status: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching today's posts from WordPress: {e}")
        return []


def send_collective_daily_report():
    print("Generating Collective Daily Publication Report...")

    posts = get_todays_published_posts()
    ist_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y')

    if not posts:
        print(f"Notice: No posts were published on {ist_date} yet.")
        summary_title = f"📰 [HinduDevGyan Daily Summary] 0 Articles Published on {ist_date}"
        items_html = "<tr><td colspan='3' style='padding: 20px; text-align: center; color: #6b7280;'>No new articles were published today.</td></tr>"
        items_text = f"No new articles were published on {ist_date}."
    else:
        summary_title = f"🎉 [HinduDevGyan Daily Summary] {len(posts)} Article(s) Published on {ist_date}"
        items_html = ""
        items_text = ""
        for idx, post in enumerate(posts, 1):
            items_html += f"""
            <tr style="border-bottom: 1px solid #f3f4f6;">
                <td style="padding: 12px 8px; font-weight: bold; color: #111827; width: 30px;">{idx}.</td>
                <td style="padding: 12px 8px;">
                    <a href="{post['link']}" target="_blank" style="color: #111827; font-weight: bold; text-decoration: none; font-size: 15px;">
                        {post['title']}
                    </a><br>
                    <span style="color: #6b7280; font-size: 12px;">📂 {post['category']}</span>
                </td>
                <td style="padding: 12px 8px; text-align: right; width: 120px;">
                    <a href="{post['link']}" target="_blank" style="background: #e8540a; color: #ffffff; padding: 6px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; display: inline-block;">
                        View Post &rarr;
                    </a>
                </td>
            </tr>
            """
            items_text += f"{idx}. {post['title']}\n   Category: {post['category']}\n   Link: {post['link']}\n\n"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; padding: 24px; border: 1px solid #e5e7eb; border-radius: 10px; background-color: #ffffff;">
        <div style="text-align: center; padding-bottom: 16px; border-bottom: 2px solid #e8540a; margin-bottom: 20px;">
            <h2 style="color: #e8540a; margin: 0; font-size: 22px;">🕉️ HinduDevGyan Daily Publication Summary</h2>
            <p style="color: #6b7280; font-size: 14px; margin: 6px 0 0 0;">Collective Daily Report &bull; {ist_date}</p>
        </div>

        <div style="background-color: #fcf8f5; border: 1px solid #fed7aa; padding: 16px; border-radius: 8px; margin-bottom: 24px; text-align: center;">
            <span style="font-size: 28px; font-weight: bold; color: #e8540a;">{len(posts)}</span>
            <span style="font-size: 16px; color: #7c2d12; display: block; margin-top: 4px;">Total Articles Published Today</span>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
            <tbody>
                {items_html}
            </tbody>
        </table>

        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0 16px 0;">
        <p style="font-size: 12px; color: #9ca3af; text-align: center; margin: 0;">
            Sent automatically by HinduDevGyan Automation Bot &bull; <a href="https://hindudevgyan.in" style="color: #e8540a; text-decoration: none;">hindudevgyan.in</a>
        </p>
    </div>
    """

    # 1. Try Resend API (1-click email API)
    if RESEND_API_KEY and NOTIFY_EMAIL:
        try:
            res = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": "HinduDevGyan Bot <onboarding@resend.dev>",
                    "to": [NOTIFY_EMAIL],
                    "subject": summary_title,
                    "html": html_body
                },
                timeout=10
            )
            if res.status_code in [200, 201]:
                print(f"📧 Collective daily summary email sent to {NOTIFY_EMAIL} via Resend API!")
                return
            else:
                print(f"Resend notice: {res.status_code} {res.text}")
        except Exception as e:
            print(f"Failed to send email via Resend API: {e}")

    # 2. Try Standard SMTP / Gmail
    if SMTP_USER and SMTP_PASS and NOTIFY_EMAIL:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = summary_title
            msg["From"] = f"HinduDevGyan Bot <{SMTP_USER}>"
            msg["To"] = NOTIFY_EMAIL
            msg.attach(MIMEText(items_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())
            print(f"📧 Collective daily summary email sent to {NOTIFY_EMAIL} via SMTP!")
            return
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")

    # 3. Try Telegram Bot if configured
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            tg_text = f"<b>📰 {summary_title}</b>\n\n" + items_text
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_text, "parse_mode": "HTML"},
                timeout=10
            )
            print("📱 Sent daily summary to Telegram!")
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")

    # 4. Try Discord Webhook if configured
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": f"**{summary_title}**\n\n{items_text}"}, timeout=10)
            print("💬 Sent daily summary to Discord!")
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")

    if not any([RESEND_API_KEY, (SMTP_USER and SMTP_PASS), TELEGRAM_BOT_TOKEN, DISCORD_WEBHOOK_URL]):
        print(f"Summary ready: {len(posts)} article(s) published today! Add NOTIFY_EMAIL & SMTP_PASS (or RESEND_API_KEY) in GitHub Secrets to receive email reports.")


if __name__ == "__main__":
    send_collective_daily_report()
