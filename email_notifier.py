import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


def send_publication_email(bot_name, published_posts):
    """
    Sends an email notification with the list of published posts (Title & Link).
    Supports:
    1. Resend API (RESEND_API_KEY, NOTIFY_EMAIL)
    2. Standard SMTP / Gmail (SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL)
    3. Telegram Bot (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    4. Discord Webhook (DISCORD_WEBHOOK_URL)
    """
    notify_email = os.getenv("NOTIFY_EMAIL")
    resend_key = os.getenv("RESEND_API_KEY")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not published_posts:
        return

    # Build HTML and Plain Text bodies
    items_html = ""
    items_text = ""
    for idx, post in enumerate(published_posts, 1):
        title = post.get("title", "Untitled Article")
        link = post.get("link", "https://hindudevgyan.in")
        category = post.get("category", "General")

        items_html += f"""
        <li style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #f3f4f6;">
            <strong style="color: #111827; font-size: 16px; display: block; margin-bottom: 4px;">{title}</strong>
            <span style="color: #6b7280; font-size: 13px; display: block; margin-bottom: 6px;">📂 Category: {category}</span>
            <a href="{link}" target="_blank" style="color: #e8540a; text-decoration: none; font-weight: bold; font-size: 14px;">🔗 View Published Article &rarr;</a>
        </li>
        """
        items_text += f"{idx}. {title}\n   Category: {category}\n   Link: {link}\n\n"

    subject = f"📰 [HinduDevGyan Bot] Published {len(published_posts)} New Article(s) ({bot_name})"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e5e7eb; border-radius: 10px; background-color: #ffffff;">
        <h2 style="color: #e8540a; margin-top: 0; font-size: 20px;">🕉️ HinduDevGyan Publication Report</h2>
        <p style="font-size: 14px; color: #374151; line-height: 1.5;">
            The <strong>{bot_name}</strong> has successfully generated and published <strong>{len(published_posts)}</strong> new article(s) to your website:
        </p>
        <ul style="padding-left: 0; list-style-type: none; margin-top: 20px;">
            {items_html}
        </ul>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0 16px 0;">
        <p style="font-size: 12px; color: #9ca3af; text-align: center; margin: 0;">
            Sent automatically by HinduDevGyan Automation Bot &bull; <a href="https://hindudevgyan.in" style="color: #e8540a; text-decoration: none;">hindudevgyan.in</a>
        </p>
    </div>
    """

    # 1. Try Resend API (1-click email API)
    if resend_key and notify_email:
        try:
            res = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                json={
                    "from": "HinduDevGyan Bot <onboarding@resend.dev>",
                    "to": [notify_email],
                    "subject": subject,
                    "html": html_body
                },
                timeout=10
            )
            if res.status_code in [200, 201]:
                print(f"📧 Notification email sent to {notify_email} via Resend API!")
                return
            else:
                print(f"Resend API notice: {res.status_code} {res.text}")
        except Exception as e:
            print(f"Failed to send email via Resend API: {e}")

    # 2. Try Standard SMTP / Gmail
    if smtp_user and smtp_pass and notify_email:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"HinduDevGyan Bot <{smtp_user}>"
            msg["To"] = notify_email
            msg.attach(MIMEText(items_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, notify_email, msg.as_string())
            print(f"📧 Notification email sent to {notify_email} via SMTP!")
            return
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")

    # 3. Try Telegram Bot if configured
    if telegram_token and telegram_chat_id:
        try:
            tg_text = f"<b>📰 {subject}</b>\n\n" + items_text
            requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                json={"chat_id": telegram_chat_id, "text": tg_text, "parse_mode": "HTML"},
                timeout=10
            )
            print("📱 Sent publication report to Telegram!")
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")

    # 4. Try Discord Webhook if configured
    if discord_webhook:
        try:
            requests.post(discord_webhook, json={"content": f"**{subject}**\n\n{items_text}"}, timeout=10)
            print("💬 Sent publication report to Discord!")
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")

    if not any([resend_key, (smtp_user and smtp_pass), telegram_token, discord_webhook]):
        print(f"Notice: {len(published_posts)} article(s) published! Add NOTIFY_EMAIL & SMTP_PASS (or RESEND_API_KEY) in GitHub Secrets to receive email reports.")
