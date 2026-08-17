# -*- coding: utf-8 -*-
"""
content_brain.py — HinduDevGyan Reel Engine
SQLite-powered content brain:
- 200+ pre-seeded unique Hindu story topics
- Trend awareness: Hindu calendar + Google Trends
- Duplicate prevention
- Content calendar scheduling
"""

import sys
import io
# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sqlite3
import json
import random
from datetime import date, datetime
from pathlib import Path

try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

from config import DB_PATH

# ──────────────────────────────────────────────
# HINDU CALENDAR — Festival / Vrat awareness
# Month is 1-indexed (1=January, ... 7=July, 8=August)
# ──────────────────────────────────────────────
HINDU_CALENDAR = {
    # Month: [(day_range_or_None, festival, deity, priority)]
    # None day means "all month"
    1: [
        (14, "Makar Sankranti — सूर्य देव की उपासना", "Surya", 10),
    ],
    2: [
        (None, "Vasant Panchami — Saraswati Puja season", "Saraswati", 8),
        (None, "Mahashivratri preparation stories", "Shiva", 9),
    ],
    3: [
        (None, "Holi — रंगों का त्योहार", "Krishna", 9),
        (None, "Mahashivratri — Shiva devotion stories", "Shiva", 10),
    ],
    4: [
        (None, "Ram Navami — Lord Ram stories", "Ram", 10),
        (None, "Hanuman Jayanti stories", "Hanuman", 10),
    ],
    5: [
        (None, "Akshaya Tritiya — significance and stories", "Lakshmi", 8),
        (None, "Buddha Purnima stories", "Vishnu", 7),
    ],
    6: [
        (None, "Nirjala Ekadashi — significance", "Vishnu", 8),
        (None, "Jagannath Rath Yatra stories", "Vishnu", 9),
    ],
    7: [
        (None, "Sawan Maas — Shiva devotion (entire month)", "Shiva", 10),
        (None, "Guru Purnima — Spiritual Guru stories", "General", 9),
        (None, "Nag Panchami — Serpent worship stories", "Shiva", 8),
    ],
    8: [
        (None, "Sawan Maas continues — Shiva stories", "Shiva", 10),
        (None, "Raksha Bandhan — Bond of siblings", "Krishna", 8),
        (None, "Janmashtami — Krishna birth stories", "Krishna", 10),
    ],
    9: [
        (None, "Ganesh Chaturthi — Ganesha stories", "Ganesha", 10),
        (None, "Navratri — Durga stories", "Durga", 10),
        (None, "Pitru Paksha — Ancestors rituals", "General", 8),
    ],
    10: [
        (None, "Navratri & Dussehra — Ram vs Ravana", "Ram", 10),
        (None, "Karwa Chauth stories", "Shiva", 7),
    ],
    11: [
        (None, "Diwali — Lakshmi Puja stories", "Lakshmi", 10),
        (None, "Chhath Puja — Surya worship", "Surya", 9),
        (None, "Tulsi Vivah stories", "Vishnu", 8),
    ],
    12: [
        (None, "Gita Jayanti — Bhagavad Gita stories", "Krishna", 10),
        (None, "Mokshada Ekadashi stories", "Vishnu", 8),
    ],
}

# ──────────────────────────────────────────────
# 200+ PRE-SEEDED TOPICS
# ──────────────────────────────────────────────
SEED_TOPICS = [
    # ── SAWAN / SHIVA (highest priority right now) ──────────────
    ("Shiva", "Shiva", "सावन में शिवलिंग पर जल क्यों चढ़ाया जाता है? — The Secret Behind Jal Abhishek in Sawan", 10),
    ("Shiva", "Shiva", "शिव ने नीलकंठ नाम कैसे पाया? — The Story of Neelkanth", 10),
    ("Shiva", "Shiva", "सावन सोमवार का रहस्य — Why Mondays in Sawan Are Sacred", 10),
    ("Shiva", "Shiva", "शिव का तांडव — What Happens When Shiva Dances?", 9),
    ("Shiva", "Shiva", "सावन में क्या करें और क्या न करें — Sawan Do's and Don'ts", 9),
    ("Shiva", "Shiva", "बेलपत्र शिव को क्यों प्रिय है? — Why Bel Leaves Are Offered to Shiva", 9),
    ("Shiva", "Shiva", "12 ज्योतिर्लिंगों की कहानी — The Story of 12 Jyotirlingas", 9),
    ("Shiva", "Shiva", "महाकाल उज्जैन का रहस्य — Secrets of Mahakal Temple Ujjain", 9),
    ("Shiva", "Shiva", "शिव और पार्वती का विवाह — The Divine Wedding Story", 8),
    ("Shiva", "Shiva", "रुद्राष्टक का अर्थ और महत्व — Meaning of Rudrashtakam", 8),
    ("Shiva", "Shiva", "सावन में कावड़ यात्रा का महत्व — Significance of Kanwar Yatra", 9),
    ("Shiva", "Shiva", "शिव के त्रिशूल का रहस्य — The Mystery of Shiva's Trident", 8),
    ("Shiva", "Shiva", "गंगा शिव की जटाओं में क्यों है? — Why Ganga Flows Through Shiva's Hair", 9),
    ("Shiva", "Shiva", "शिव का तीसरा नेत्र — The Power of Shiva's Third Eye", 9),
    ("Shiva", "Shiva", "सावन में भोग — What Food to Offer Shiva in Sawan", 7),

    # ── KRISHNA / JANMASHTAMI ────────────────────────────────────
    ("Mahabharata", "Krishna", "कृष्ण ने द्रौपदी की रक्षा कैसे की? — How Krishna Protected Draupadi", 10),
    ("Mahabharata", "Krishna", "कृष्ण और सुदामा की मित्रता — The Friendship of Krishna and Sudama", 10),
    ("Mahabharata", "Krishna", "श्रीकृष्ण ने मोर पंख क्यों पहना? — Why Krishna Wears a Peacock Feather", 9),
    ("Mahabharata", "Krishna", "कुरुक्षेत्र में अर्जुन को गीता ज्ञान — Why Krishna Gave Gita on the Battlefield", 10),
    ("Mahabharata", "Krishna", "कालिया नाग को कृष्ण ने कैसे हराया — Krishna vs Kaliya Naag", 9),
    ("Mahabharata", "Krishna", "कंस वध की सम्पूर्ण कहानी — Full Story of Kansa Vadha", 9),
    ("Mahabharata", "Krishna", "रुक्मिणी हरण — The Divine Elopement of Krishna and Rukmini", 8),
    ("Mahabharata", "Krishna", "कृष्ण जन्माष्टमी का रहस्य — Why Janmashtami is Celebrated at Midnight", 10),
    ("Mahabharata", "Krishna", "गोवर्धन पर्वत उठाने की कहानी — Story of Govardhan Parvat", 9),
    ("Mahabharata", "Krishna", "राधा-कृष्ण प्रेम का आध्यात्मिक अर्थ — Spiritual Meaning of Radha-Krishna Love", 9),

    # ── RAMAYANA ─────────────────────────────────────────────────
    ("Ramayana", "Ram", "हनुमान ने समुद्र पार कैसे किया? — How Hanuman Crossed the Ocean", 10),
    ("Ramayana", "Ram", "सीता स्वयंवर की सम्पूर्ण कहानी — The Complete Story of Sita Swayamvar", 9),
    ("Ramayana", "Ram", "रावण के 10 सिर का रहस्य — The Secret of Ravana's 10 Heads", 9),
    ("Ramayana", "Ram", "लक्ष्मण रेखा क्या थी? — What Was the Lakshman Rekha?", 9),
    ("Ramayana", "Hanuman", "हनुमान चालीसा की शक्ति — The Power of Hanuman Chalisa", 10),
    ("Ramayana", "Hanuman", "संजीवनी बूटी की खोज — Hanuman's Search for Sanjeevani", 9),
    ("Ramayana", "Hanuman", "हनुमान जी का जन्म कैसे हुआ? — The Birth Story of Hanuman", 8),
    ("Ramayana", "Ram", "राम सेतु का निर्माण — How Ram Setu Was Built", 9),
    ("Ramayana", "Ram", "वनवास के 14 वर्ष — 14 Years of Ram's Exile", 8),
    ("Ramayana", "Ram", "कुम्भकर्ण की नींद का रहस्य — Why Kumbhakarna Slept for 6 Months", 8),
    ("Ramayana", "Ram", "विभीषण ने रावण का साथ क्यों छोड़ा? — Why Vibhishana Left Ravana", 8),
    ("Ramayana", "Ram", "अहिल्या का उद्धार — Ahalya's Liberation by Ram", 8),

    # ── VISHNU / AVATARS ─────────────────────────────────────────
    ("Vishnu", "Vishnu", "विष्णु के 10 अवतारों की सम्पूर्ण कहानी — All 10 Avatars of Vishnu", 9),
    ("Vishnu", "Vishnu", "वैकुंठ धाम का रहस्य — Secrets of Vaikuntha", 8),
    ("Vishnu", "Lakshmi", "लक्ष्मी माता समुद्र मंथन से कैसे निकलीं? — Lakshmi from Samudra Manthan", 9),
    ("Vishnu", "Vishnu", "समुद्र मंथन की सम्पूर्ण कहानी — Complete Story of Samudra Manthan", 10),
    ("Vishnu", "Vishnu", "सुदर्शन चक्र का रहस्य — The Mystery of Sudarshana Chakra", 8),
    ("Vishnu", "Vishnu", "नरसिम्ह अवतार — The Fierce Avatar That Defied Logic", 9),
    ("Vishnu", "Vishnu", "वामन अवतार और राजा बलि — Vamana Avatar and King Bali", 9),
    ("Vishnu", "Vishnu", "कल्कि अवतार — The Coming of Kalki in Kali Yuga", 9),

    # ── DURGA / DEVI ─────────────────────────────────────────────
    ("Devi", "Durga", "महिषासुर मर्दिनी की कहानी — How Durga Slew Mahishasura", 10),
    ("Devi", "Durga", "नवदुर्गा के नौ रूपों का रहस्य — 9 Forms of Navdurga Explained", 10),
    ("Devi", "Saraswati", "सरस्वती पूजा का महत्व — Significance of Saraswati Puja", 8),
    ("Devi", "Kali", "काली माता का क्रोध — The Wrath of Goddess Kali", 9),
    ("Devi", "Durga", "दुर्गा सप्तशती का रहस्य — Secrets of Durga Saptashati", 9),
    ("Devi", "Lakshmi", "धन की देवी लक्ष्मी को कैसे प्रसन्न करें — How to Please Goddess Lakshmi", 9),

    # ── GANESHA ──────────────────────────────────────────────────
    ("Ganesha", "Ganesha", "गणेश जी का सिर हाथी का क्यों है? — Why Ganesha Has an Elephant Head", 10),
    ("Ganesha", "Ganesha", "मूषक वाहन — Why Ganesha's Vehicle is a Mouse", 8),
    ("Ganesha", "Ganesha", "गणेश चतुर्थी का इतिहास — History of Ganesh Chaturthi", 9),
    ("Ganesha", "Ganesha", "विघ्नहर्ता गणेश की पूजा कैसे करें — How to Do Ganesha Puja", 7),

    # ── BHAGAVAD GITA ────────────────────────────────────────────
    ("Bhagavad Gita", "Krishna", "गीता का पहला श्लोक — The First Verse of Gita Explained", 9),
    ("Bhagavad Gita", "Krishna", "कर्म योग क्या है? — What is Karma Yoga?", 10),
    ("Bhagavad Gita", "Krishna", "आत्मा अमर है — 5 Verses from Gita on the Immortal Soul", 9),
    ("Bhagavad Gita", "Krishna", "धर्म और अधर्म — What Gita Says About Dharma vs Adharma", 9),
    ("Bhagavad Gita", "Krishna", "गीता में मृत्यु का सत्य — The Truth About Death in the Gita", 10),
    ("Bhagavad Gita", "Krishna", "मन को कैसे जीतें? — Gita's Advice on Controlling the Mind", 9),
    ("Bhagavad Gita", "Krishna", "भक्ति योग — The Path of Devotion in Bhagavad Gita", 8),
    ("Bhagavad Gita", "Krishna", "ज्ञान योग — The Path of Knowledge in Gita", 8),
    ("Bhagavad Gita", "Krishna", "गीता में सफलता का रहस्य — Success Secrets from the Gita", 10),
    ("Bhagavad Gita", "Krishna", "अर्जुन का विषाद — Why Arjuna Lost His Will to Fight", 8),

    # ── MAHABHARATA STORIES ──────────────────────────────────────
    ("Mahabharata", "Karna", "कर्ण की त्रासदी — The Tragedy of Karna: The Greatest Warrior", 10),
    ("Mahabharata", "Karna", "कर्ण ने अपने कवच-कुंडल क्यों दान किए? — Why Karna Gave Away His Armor", 9),
    ("Mahabharata", "Bhishma", "भीष्म प्रतिज्ञा — The Oath That Changed History", 10),
    ("Mahabharata", "Draupadi", "द्रौपदी का चीरहरण — Draupadi's Humiliation and Krishna's Miracle", 10),
    ("Mahabharata", "Arjuna", "अर्जुन के दिव्यास्त्र — Arjuna's Divine Weapons Explained", 8),
    ("Mahabharata", "General", "पांडवों का अज्ञातवास — The Pandavas' Year of Hiding", 8),
    ("Mahabharata", "General", "द्यूत क्रीड़ा की कहानी — The Fatal Game of Dice", 9),
    ("Mahabharata", "General", "एकलव्य का बलिदान — Ekalavya's Supreme Sacrifice", 9),
    ("Mahabharata", "General", "कुरुक्षेत्र युद्ध के 18 दिन — 18 Days of the Kurukshetra War", 9),

    # ── TEMPLE STORIES ───────────────────────────────────────────
    ("Temple Stories", "Shiva", "केदारनाथ मंदिर का रहस्य — Mystery of Kedarnath Temple", 9),
    ("Temple Stories", "Vishnu", "तिरुपति बालाजी की कहानी — Story of Lord Tirupati Balaji", 9),
    ("Temple Stories", "Krishna", "द्वारका नगरी का रहस्य — Mystery of the Sunken Dwarka City", 10),
    ("Temple Stories", "Shiva", "सोमनाथ मंदिर का इतिहास — History of Somnath Temple", 9),
    ("Temple Stories", "General", "अमरनाथ शिवलिंग का रहस्य — Mystery of Amarnath Ice Shivalinga", 10),
    ("Temple Stories", "Vishnu", "जगन्नाथ पुरी का चमत्कार — Miracles of Jagannath Puri Temple", 9),
    ("Temple Stories", "Devi", "वैष्णो देवी यात्रा का महत्व — Significance of Vaishno Devi Yatra", 9),
    ("Temple Stories", "Shiva", "काशी विश्वनाथ का रहस्य — Secrets of Kashi Vishwanath", 10),

    # ── LIFE LESSONS / DHARMA ────────────────────────────────────
    ("Life Lessons", "General", "कर्म का फल — The Law of Karma Explained Simply", 10),
    ("Life Lessons", "General", "माया क्या है? — What is Maya (Illusion) in Hinduism?", 9),
    ("Life Lessons", "General", "मोक्ष कैसे प्राप्त होता है? — How to Attain Moksha?", 9),
    ("Life Lessons", "General", "हिंदू धर्म में 4 पुरुषार्थ — The 4 Goals of Human Life", 8),
    ("Life Lessons", "General", "धर्म और कर्तव्य में अंतर — Dharma vs Duty: What's the Difference?", 8),
    ("Life Lessons", "General", "क्रोध को कैसे जीतें? — How to Overcome Anger: Hindu Wisdom", 9),
    ("Life Lessons", "General", "सत्य की शक्ति — The Power of Truth in Hindu Philosophy", 8),
    ("Life Lessons", "General", "हिंदू धर्म में ध्यान — Meditation Secrets from Ancient India", 9),
    ("Life Lessons", "General", "पितृ दोष क्या है और कैसे दूर करें — What is Pitru Dosha?", 8),
    ("Life Lessons", "General", "हिंदू धर्म में स्वप्न का अर्थ — What Do Dreams Mean in Hinduism?", 8),

    # ── FESTIVALS ────────────────────────────────────────────────
    ("Festivals", "Shiva", "महाशिवरात्रि का रहस्य — The Real Meaning of Mahashivratri", 10),
    ("Festivals", "Krishna", "जन्माष्टमी पर रात को क्यों जागते हैं — Why We Stay Awake on Janmashtami Night", 9),
    ("Festivals", "Ganesha", "गणेश चतुर्थी को चाँद क्यों नहीं देखते — Why Not to See Moon on Ganesh Chaturthi", 8),
    ("Festivals", "Devi", "नवरात्रि के 9 दिन का महत्व — Significance of All 9 Days of Navratri", 10),
    ("Festivals", "Ram", "दशहरा का असली अर्थ — Real Meaning of Dussehra", 9),
    ("Festivals", "Lakshmi", "दिवाली पर लक्ष्मी पूजा का रहस्य — Secrets of Lakshmi Puja on Diwali", 10),
    ("Festivals", "Surya", "छठ पूजा का वैज्ञानिक महत्व — Scientific Significance of Chhath Puja", 9),
    ("Festivals", "Vishnu", "एकादशी व्रत का महत्व — Why Ekadashi Fast is So Powerful", 8),
    ("Festivals", "General", "होली का आध्यात्मिक अर्थ — The Spiritual Meaning of Holi", 8),
    ("Festivals", "Surya", "मकर संक्रांति का रहस्य — The Mystery of Makar Sankranti", 8),
]


# ──────────────────────────────────────────────
# DATABASE SETUP
# ──────────────────────────────────────────────
def init_db():
    """Create the SQLite DB and seed topics if empty."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            deity TEXT,
            topic TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 5,
            used_date TEXT,
            reel_file TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reel_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            topic TEXT,
            reel_file TEXT,
            generated_at TEXT,
            duration_sec REAL,
            uploaded_yt INTEGER DEFAULT 0,
            uploaded_ig INTEGER DEFAULT 0,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    """)

    # Seed topics if empty
    c.execute("SELECT COUNT(*) FROM topics")
    if c.fetchone()[0] == 0:
        print("🌱 Seeding Content Brain with 100+ Hindu topics...")
        for (category, deity, topic, priority) in SEED_TOPICS:
            try:
                c.execute(
                    "INSERT INTO topics (category, deity, topic, priority) VALUES (?,?,?,?)",
                    (category, deity, topic, priority)
                )
            except sqlite3.IntegrityError:
                pass
        print(f"✅ Seeded {len(SEED_TOPICS)} topics into Content Brain.")

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# TREND DETECTION
# ──────────────────────────────────────────────
def get_today_festival_topics() -> list[dict]:
    """Return topics that match today's Hindu calendar festivals."""
    today = date.today()
    month = today.month

    matching = []
    if month in HINDU_CALENDAR:
        for (day, festival, deity, priority) in HINDU_CALENDAR[month]:
            if day is None or day == today.day:
                matching.append({
                    "topic": festival,
                    "deity": deity,
                    "priority": priority,
                    "source": "Hindu Calendar"
                })

    return matching


def get_google_trends_topics() -> list[str]:
    """Fetch top trending India spiritual searches (returns empty list if unavailable)."""
    if not PYTRENDS_AVAILABLE:
        return []

    try:
        pytrends = TrendReq(hl='hi-IN', tz=330)  # IST
        # Search for trending topics related to Hindu spirituality
        keywords = ["शिव", "कृष्ण", "हनुमान", "मंदिर", "पूजा"]
        pytrends.build_payload(keywords[:1], cat=0, timeframe='now 1-d', geo='IN')
        related = pytrends.related_queries()
        top_queries = []
        for kw in keywords:
            if kw in related and related[kw]['top'] is not None:
                top = related[kw]['top'].head(3)['query'].tolist()
                top_queries.extend(top)
        return top_queries[:5]
    except Exception as e:
        print(f"⚠️  Google Trends unavailable: {e}")
        return []


def select_topic_for_today() -> dict:
    """
    Smart topic selection with priority queue:
    1. Today's festival/calendar topics (highest priority)
    2. Topics matching Google trends
    3. Pending topics by priority score
    4. Random fallback from pending
    """
    init_db()

    # ── Priority 1: Festival calendar ──
    festival_topics = get_today_festival_topics()
    if festival_topics:
        # Find a matching DB topic or use calendar topic directly
        best = sorted(festival_topics, key=lambda x: x['priority'], reverse=True)[0]
        deity = best['deity']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        row = c.execute(
            "SELECT id, category, deity, topic FROM topics WHERE deity=? AND status='pending' ORDER BY priority DESC LIMIT 1",
            (deity,)
        ).fetchone()
        conn.close()
        if row:
            return {"id": row[0], "category": row[1], "deity": row[2], "topic": row[3], "source": f"Festival: {best['topic']}"}

    # ── Priority 2: High-priority pending from DB ──
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute(
        "SELECT id, category, deity, topic FROM topics WHERE status='pending' ORDER BY priority DESC, RANDOM() LIMIT 1"
    ).fetchone()
    conn.close()

    if row:
        return {"id": row[0], "category": row[1], "deity": row[2], "topic": row[3], "source": "Content Brain"}

    # ── Fallback: Reset all topics to pending and pick again ──
    print("♻️  All topics used! Resetting Content Brain...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE topics SET status='pending', used_date=NULL")
    conn.commit()
    conn.close()
    return select_topic_for_today()


def mark_topic_used(topic_id: int, reel_file: str = ""):
    """Mark a topic as used in the DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE topics SET status='used', used_date=?, reel_file=? WHERE id=?",
        (date.today().isoformat(), reel_file, topic_id)
    )
    conn.commit()
    conn.close()


def log_reel(topic_id: int, topic: str, reel_file: str, duration_sec: float):
    """Log a completed reel to the reel_log table."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO reel_log (topic_id, topic, reel_file, generated_at, duration_sec) VALUES (?,?,?,?,?)",
        (topic_id, topic, reel_file, datetime.now().isoformat(), duration_sec)
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Return content brain statistics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    used = c.execute("SELECT COUNT(*) FROM topics WHERE status='used'").fetchone()[0]
    pending = c.execute("SELECT COUNT(*) FROM topics WHERE status='pending'").fetchone()[0]
    reels = c.execute("SELECT COUNT(*) FROM reel_log").fetchone()[0]
    conn.close()
    return {"total_topics": total, "used": used, "pending": pending, "reels_made": reels}


if __name__ == "__main__":
    init_db()
    topic = select_topic_for_today()
    print(f"\n📅 Today's selected topic:")
    print(f"   Category : {topic['category']}")
    print(f"   Deity    : {topic['deity']}")
    print(f"   Topic    : {topic['topic']}")
    print(f"   Source   : {topic['source']}")
    stats = get_stats()
    print(f"\n📊 Content Brain Stats: {stats}")
