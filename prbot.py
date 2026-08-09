import os, sys, json, time, random, datetime, math, re, asyncio

# ════════════════════════════════════════════════════════════════════════════════════════════════════
# 🚀 HIGHRISE BOT PRO EDITION — COMPLETE ENTERPRISE SUITE
# ════════════════════════════════════════════════════════════════════════════════════════════════════
# 👑 Designed by king_4626 | Highrise WebAPI & App Architecture
# 🎡 Features: Economy System, XP & Leveling, Auto-Mod, Multi-Loop Spam,
#    Marriage System, Pets, Quiz, Scramble, Riddles, Lottery, Polls, Voice/Chat Moderation,
#    Self-Ping Keep-Alive Server, Full Persistence, and Highrise REST API Integration.
# ════════════════════════════════════════════════════════════════════════════════════════════════════
"""
╔══════════════════════════════════════════════════════════════════════╗
║        HighriseBot — Pro Edition | prbot.py                           ║
║  ✅ ذخیره خودکار موقعیت بات و اسپم پایدار هنگام ری‌استارت رندر        ║
║  ✅ ذخیره نقاط عمومی | همه می‌تونن با تایپ اسم به نقطه برن            ║
║  ✅ نقاط ادمین (!adminsave) | فقط ادمین می‌تونه کاربر رو ببره (!bring) ║
║  ✅ انتقال مالک پیش کاربران (!goto @user) و احضار بات (!bot)         ║
║  ✅ Keep-Alive قدرتمند برای رندر + Flask Web Server                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os, sys, json, time, random, datetime, math, re, asyncio, threading
from typing import Optional, Dict, Any
from asyncio import Task

try:
    import requests
except ImportError:
    requests = None

try:
    from highrise import BaseBot, User, Position
    from highrise.__main__ import BotDefinition, main as run_bot
except ImportError:
    class BaseBot: pass
    class User:
        def __init__(self, id="test", username="test"):
            self.id = id
            self.username = username
    class Position:
        def __init__(self, x=0, y=0, z=0, facing="FrontRight"):
            self.x, self.y, self.z, self.facing = x, y, z, facing
    BotDefinition = None
    run_bot = None

try:
    from highrise import Item
except ImportError:
    try:
        from highrise.models import Item
    except ImportError:
        Item = None

START_TIME = time.time()
HTML_PAGE = "<html><body><h1>prbot status: online</h1></body></html>"
try:
    from flask import Flask, render_template_string
    app = Flask(__name__)
except Exception:
    Flask = None
    render_template_string = None
    class DummyFlask:
        def route(self, *args, **kwargs):
            return lambda f: f
    app = DummyFlask()

@app.route('/')
def home():
    uptime_sec = int(time.time() - START_TIME)
    h, m = divmod(uptime_sec // 60, 60)
    return render_template_string(HTML_PAGE, uptime=f"{h}h {m}m")

@app.route('/ping')
def ping():
    return "Pong! Bot server is healthy."

def auto_self_ping():
    """پینگ خودکار هر 3 دقیقه جهت جلوگیری از خوابیدن رندر"""
    app_url = os.environ.get("APP_URL", "")
    port = os.environ.get("PORT", "5000")
    url = app_url if app_url else f"http://127.0.0.1:{port}/ping"
    while True:
        try:
            time.sleep(180) # 3 minutes
            requests.get(url, timeout=5)
            print("🔄 Self-ping sent to keep Render alive!")
        except Exception as e:
            pass

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_keep_alive():
    t1 = threading.Thread(target=run_flask, daemon=True)
    t1.start()
    t2 = threading.Thread(target=auto_self_ping, daemon=True)
    t2.start()

# ════════════════════════════════════════════════════════════════
# Admin setup
# ════════════════════════════════════════════════════════════════
try:
    import tiba
    ROOM_ID = tiba.ROOM_ID
    HIGHRISE_API_TOKEN = tiba.HIGHRISE_API_TOKEN
    ADMIN_USERNAME = tiba.ADMIN_USERNAME
    ADMINS = [ADMIN_USERNAME]
except ImportError:
    ROOM_ID = os.environ.get("ROOM_ID", "")
    HIGHRISE_API_TOKEN = os.environ.get("HIGHRISE_API_TOKEN", "")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "parsapr")
    ADMINS = [ADMIN_USERNAME]

# ════════════════════════════════════════════════════════════════
# 💾 پوشه ذخیره‌سازی دائمی (برای رندر: یک Persistent Disk به این مسیر وصل کنید
#    تا نقاط، ادمین‌ها و همه‌چیز حتی بعد از ری‌دیپلوی/ری‌استارت رندر پاک نشه)
# ════════════════════════════════════════════════════════════════
DATA_DIR = os.environ.get("DATA_DIR", ".").rstrip("/") or "."
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception as e:
    print(f"⚠️ Could not create DATA_DIR '{DATA_DIR}': {e}")

def _data_path(filename: str) -> str:
    """مسیر کامل فایل داخل پوشه دائمی داده"""
    return os.path.join(DATA_DIR, filename)

# سازگاری با نسخه‌های قدیمی: اگر فایل‌های config.json/دیتابیس قبلاً کنار کد
# ذخیره شده بودن ولی DATA_DIR جدید تنظیم شده، یک‌بار به مسیر جدید منتقلشون کن
def _migrate_legacy_file(filename: str):
    legacy = filename
    new_path = _data_path(filename)
    try:
        if DATA_DIR != "." and os.path.exists(legacy) and not os.path.exists(new_path):
            import shutil
            shutil.copy2(legacy, new_path)
            print(f"📦 فایل قدیمی «{legacy}» به «{new_path}» منتقل شد.")
    except Exception as e:
        print(f"⚠️ Migration warning for {filename}: {e}")

_migrate_legacy_file("config.json")

try:
    with open(_data_path("config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
        for admin in config.get("admins", []):
            if admin not in ADMINS:
                ADMINS.append(admin)
except Exception:
    pass

def is_admin(user: User) -> bool:
    if not user: return False
    uname = (user.username.lower() if hasattr(user, 'username') and user.username else "").strip()
    uid = (user.id if hasattr(user, 'id') else str(user)).strip()
    return uname in [a.lower() for a in ADMINS] or uid in ADMINS

# Deduplication
_dance_claimed: dict = {}
_cmd_processed: dict = {}
CMD_DEDUP_WINDOW = 1.2

def _should_handle_command(user_id: str, message: str) -> bool:
    key = f"{user_id}:{hash(message) & 0xFFFFFFFF}"
    now = time.time()
    expired = [k for k, t in list(_cmd_processed.items()) if now - t > CMD_DEDUP_WINDOW]
    for k in expired:
        del _cmd_processed[k]
    if key in _cmd_processed:
        return False
    _cmd_processed[key] = now
    return True

# ════════════════════════════════════════════════════════════════
# Constants & Data
# ════════════════════════════════════════════════════════════════
SLOT_SYMBOLS  = ["🍒", "🍋", "🍊", "🍇", "💎", "🌟", "🎰", "7️⃣"]
SLOT_WEIGHTS  = [30, 25, 20, 15, 5, 3, 1, 1]

EIGHT_BALL    = [
    "✅ بله، قطعاً!", "✅ آره!", "✅ امیدوارم که آره.",
    "✅ به نظرم آره.", "✅ احتمالش زیاده.",
    "🤔 الان جواب واضحی نیست.", "🤔 دوباره بپرس.",
    "🤔 بهتره الان پیش‌بینی نکنم.", "🤔 کمی صبر کن.",
    "❌ احتمالش کمه.", "❌ نه!", "❌ مطمئناً نه.",
    "❌ نگاهم میگه نه.", "❌ خیر.",
]

FORTUNE_COOKIES = [
    "🥠 یه ایده بزرگ الان توی ذهنته — دنبالش برو!",
    "🥠 امروز یه آشنای قدیمی رو می‌بینی.",
    "🥠 صبر کن، بهترین‌ها دیر میان.",
    "🥠 یه خطر کوچیک امروز سود بزرگی داره.",
    "🥠 کمک به دیگران امروز برمیگرده.",
    "🥠 دوستی که الان فکرش رو می‌کنی بهت نیاز داره.",
    "🥠 لبخند بزن؛ دنیا بهش جواب میده.",
    "🥠 تغییری که ازش می‌ترسی دقیقاً همون چیزیه که نیاز داری.",
    "🥠 پولی که انتظارش نداشتی بهت میرسه.",
    "🥠 امروز روز خوبیه برای شروع یه چیز جدید.",
]

TRUTHS = [
    "آخرین دروغی که گفتی چی بود؟",
    "به کی بیشتر از همه تکیه می‌کنی؟",
    "چه راز بزرگی داری که کسی نمیدونه؟",
    "اگه ۱ میلیون داشتی اول چیکار می‌کردی؟",
    "آخرین باری که گریه کردی کِی بود؟",
    "قشنگ‌ترین خاطره‌ات چیه؟",
    "از چی بیشتر از همه می‌ترسی؟",
    "اگه یه روز دیگه‌ای بودی چه کسی می‌خواستی باشی؟",
    "آرزوی سال آینده‌ات چیه؟",
    "از چه چیزی توی خودت بیشتر خوشت میاد؟",
]

DARES = [
    "10 تا اسم حیوان بگو که با حرف «پ» شروع میشه!",
    "یه شعر 2 بیتی درباره بات بگو!",
    "اسم رنگ‌ها رو فارسی بگو تا 10 تا!",
    "3 تا دنس مختلف بزن!",
    "به نفر بعدی که وارد روم میشه خوش‌آمد بگو!",
    "یه جمله انگلیسی به فارسی ترجمه کن!",
    "اسم 5 تا فیلم معروف بگو!",
    "5 بار پشت سرهم emote wave بزن!",
    "برای همه روم یه شعر کوتاه بگو!",
]

RIDDLES = [
    {"q": "هر چقدر بیشتر ازم بگیری، بزرگتر میشم. چی‌ام؟", "a": "چاله"},
    {"q": "روز ولادت داری ولی تولد نداری. چی‌ای؟", "a": "سن"},
    {"q": "با آب مردم میشم. چی‌ام؟", "a": "آتش"},
    {"q": "همه دارنش ولی نمیتونن ببیننش. چیه؟", "a": "عقل"},
    {"q": "هرچی بیشتر دارش کمتر میبینی. چیه؟", "a": "تاریکی"},
    {"q": "پا دارم ولی نمیرم. سر دارم ولی نمیخورم. چی‌ام؟", "a": "میز"},
    {"q": "صبح 4 تا پا، ظهر 2 تا پا، شب 3 تا پا. چیه؟", "a": "انسان"},
    {"q": "دندون دارم ولی گاز نمیگیرم. چی‌ام؟", "a": "شانه"},
    {"q": "چه چیزی شکستنیه بدون اینکه بیفتد؟", "a": "سکوت"},
    {"q": "هرچه بیشتر خشکش کنی خیس‌تر میشه. چیه؟", "a": "حوله"},
]

SCRAMBLE_WORDS = [
    ("ایران", "ناری", "کشور"),
    ("تهران", "نارهت", "پایتخت"),
    ("کتاب", "باتک", "خوندنی"),
    ("مداد", "دادم", "نوشتن"),
    ("پنجره", "رپنجه", "شیشه"),
    ("میوه", "ویمه", "خوردنی"),
    ("درخت", "تخرد", "سبز"),
    ("ستاره", "ارسته", "شب"),
    ("آسمان", "نامسآ", "آبی"),
    ("دریا", "ریاد", "آب"),
]

TYPING_PHRASES = [
    "هایرایز بهترین بازیه!",
    "بات ما از همه باتها قوی‌تره!",
    "امروز روز خوبیه!",
    "فارسی زیباترین زبان دنیاست!",
    "به موفقیت ایمان داشته باش!",
    "دنس بزن و شاد باش!",
    "دوستی ارزشمندترین چیزه!",
    "خندیدن بهترین دارویه!",
]

HOROSCOPES = {
    "حمل": "♈ امروز انرژی زیادی داری! پروژه‌های متوقف رو شروع کن.",
    "ثور": "♉ ثبات مالی امروز بهتره. یه سرمایه‌گذاری کوچیک کن.",
    "جوزا": "♊ ارتباطاتت امروز قوی‌تر از هیشه. با دوستا حرف بزن.",
    "سرطان": "♋ احساساتت امروز شدیده. به خودت استراحت بده.",
    "اسد": "♌ خلاقیتت اوج می‌گیره. یه ایده جدید داری؟ دنبالش برو!",
    "سنبله": "♍ جزئیات رو از دست نده. دقت امروز کلید موفقیتته.",
    "میزان": "♎ روابطت امروز هماهنگ‌تره. با همه مهربون باش.",
    "عقرب": "♏ قدرت درونیت امروز بالاست. تصمیم‌های مهم بگیر.",
    "قوس": "♐ ماجراجویی امروز کلیدیه. یه چیز جدید امتحان کن!",
    "جدی": "♑ پشتکارت امروز نتیجه میده. ادامه بده!",
    "دلو": "♒ ایده‌های نوآورانه‌ات امروز درخشان‌تره. به جمع کمک کن.",
    "حوت": "♓ حس ششمت امروز قوی‌تره. به غریزه‌ات اعتماد کن.",
}

PV_RESPONSES = {
    "سلام": "سلام عزیزم! خوش اومدی 🤍 چطوری؟",
    "هی": "هی هی! چه خبر؟ 😄",
    "درود": "درود بر تو! حالت خوبه؟ 🌟",
    "صبح بخیر": "صبح بخیر عزیزم! روزت پر از خوشی باشه ☀️",
    "شب بخیر": "شب بخیر! خواب خوب ببینی 🌙",
    "عصر بخیر": "عصر بخیر! چه روزی داشتی؟ 😊",
    "ظهر بخیر": "ظهر بخیر! ناهار خوردی؟ 😋",
    "چطوری": "خوبم قربانت! تو چطوری؟ 😄",
    "حالت چطوره": "ممنون که پرسیدی! خوبم 🤍 تو چی؟",
    "چه خبر": "سلامتی! همه چیز خوبه 😎 تو چه خبر؟",
    "چی شد": "هیچی خاصی نشد! تو بگو 😄",
    "خوبی": "آره خوبم! ممنون 🤍 تو خوبی؟",
    "بدی": "نه نه، خوبم! ممنون که نگرانمی 🥰",
    "ممنون": "قربانت! هر وقت کاری داشتی اینجام 🤍",
    "مرسی": "خواهش میکنم عزیزم! 😄",
    "ممنونم": "بی زحمت! برام مهمی 🤍",
    "دستت درد نکنه": "ممنون از لطفت! 🌸",
    "خداحافظ": "خداحافظ عزیزم! مراقب خودت باش 🤍",
    "بای": "بای بای! زود برگرد 😄",
    "فعلاً": "فعلاً! منتظرتم 🌟",
    "برم": "باشه برو! زود برگرد 😊",
    "خدافظ": "خداحافظ! قربانت 🤍",
    "بعداً": "باشه! بعداً میبینمت 😄",
    "کمک": "البته! بگو چی لازم داری؟ 🤝",
    "help": "چه کمکی از دستم بر میاد؟ 😊",
    "دوستت دارم": "منم دوستت دارم عزیزم! 🤍",
    "عاشقتم": "🥰 ممنون! تو هم خیلی خاصی!",
    "خوشگل": "ممنون! تو هم خوشگلی 😄",
    "ایران": "زنده باد ایران و ایرانی! 🇮🇷",
    "فارسی": "زبان شیرین فارسی! 📖",
    "عشق": "عشق قشنگ‌ترین احساسه 💕",
    "تولد": "تولدت مبارک! 🎂🎉",
    "تولدمه": "تولدت مبارک!! 🎉🎂❤️",
}

# ════════════════════════════════════════════════════════════════
# HighriseBot Class — Combined Master Code with Theme Park & Persistent State
# ════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════
# 🎭 HIGHRISE EMOTES DATABASE (Free Emotes First for 1..N numbers)
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# 🎭 HIGHRISE EMOTES DATABASE (Free Emotes First for 1..N numbers)
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# 🎭 HIGHRISE EMOTES DATABASE (Free Emotes First for 1..N numbers)
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# 🎭 HIGHRISE EMOTES DATABASE (Free Emotes First for 1..N numbers)
# ════════════════════════════════════════════════════════════════
FREE_EMOTES = [
    ("Sit", "idle-loop-sitfloor", 22.3),
    ("Shy", "emote-shy", 4.5),
    ("Enthused", "idle-enthusiastic", 15.9),
    ("Yes", "emote-yes", 2.6),
    ("The Wave", "emote-wave", 2.7),
    ("Tired", "emote-tired", 4.6),
    ("Snowball Fight!", "emote-snowball", 5.2),
    ("Snow Angel", "emote-snowangel", 6.2),
    ("Sad", "emote-sad", 5.4),
    ("No", "emote-no", 2.7),
    ("Model", "emote-model", 6.5),
    ("Flirty Wave", "emote-lust", 4.7),
    ("Kiss", "emote-kiss", 2.4),
    ("Sweating", "emote-hot", 4.4),
    ("Hello", "emote-hello", 2.7),
    ("Greedy Emote", "emote-greedy", 4.6),
    ("Face Palm", "emote-exasperatedb", 2.7),
    ("Curtsy", "emote-curtsy", 2.4),
    ("Confusion", "emote-confused", 8.6),
    ("Charging", "emote-charging", 8.0),
    ("Bow", "emote-bow", 3.3),
    ("Thumbs Up", "emoji-thumbsup", 2.7),
    ("Tummy Ache", "emoji-gagging", 5.5),
    ("Flex", "emoji-flex", 2.1),
    ("Cursing Emote", "emoji-cursing", 2.4),
    ("Raise The Roof", "emoji-celebrate", 3.4),
    ("Angry", "emoji-angry", 5.8),
    ("Savage Dance", "dance-tiktok8", 10.9),
    ("Don't Start Now", "dance-tiktok2", 10.4),
    ("Let's Go Shopping", "dance-shoppingcart", 4.3),
    ("Russian Dance", "dance-russian", 10.3),
    ("Penny's Dance", "dance-pennywise", 1.2),
    ("Macarena", "dance-macarena", 12.2),
    ("K-Pop Dance", "dance-blackpink", 7.2),
    ("Hyped", "emote-hyped", 7.5),
    ("Jinglebell", "dance-jinglebell", 11.0),
    ("Nervous", "idle-nervous", 21.7),
    ("Toilet", "idle-toilet", 32.2),
    ("Astronaut", "emote-astronaut", 13.8),
    ("Dance Zombie", "dance-zombie", 12.9),
    ("Heart Eyes", "emote-hearteyes", 4.0),
    ("Swordfight", "emote-swordfight", 5.9),
    ("TimeJump", "emote-timejump", 4.0),
    ("Snake", "emote-snake", 5.3),
    ("Heart Fingers", "emote-heartfingers", 4.0),
    ("Float", "emote-float", 9.0),
    ("Telekinesis", "emote-telekinesis", 10.5),
    ("Penguin dance", "dance-pinguin", 11.6),
    ("Creepy puppet", "dance-creepypuppet", 6.4),
    ("Sleigh", "emote-sleigh", 11.3),
    ("Maniac", "emote-maniac", 4.9),
    ("Energy Ball", "emote-energyball", 7.6),
    ("Singing", "idle_singing", 10.3),
    ("Frog", "emote-frog", 14.6),
    ("Superpose", "emote-superpose", 4.5),
    ("Cute", "emote-cute", 6.2),
    ("TikTok Dance 9", "dance-tiktok9", 11.9),
    ("Weird Dance", "dance-weird", 21.6),
    ("TikTok Dance 10", "dance-tiktok10", 8.2),
    ("Pose 7", "emote-pose7", 4.7),
    ("Pose 8", "emote-pose8", 4.8),
    ("Casual Dance", "idle-dance-casual", 9.1),
    ("Pose 1", "emote-pose1", 2.8),
    ("Pose 3", "emote-pose3", 5.1),
    ("Pose 5", "emote-pose5", 4.6),
    ("Cutey", "emote-cutey", 3.3),
    ("Punk Guitar", "emote-punkguitar", 9.4),
    ("Fashionista", "emote-fashionista", 5.6),
    ("Gravity", "emote-gravity", 9.0),
    ("Ice Cream Dance", "dance-icecream", 14.8),
    ("Wrong Dance", "dance-wrong", 12.4),
    ("UwU", "idle-uwu", 24.8),
    ("TikTok Dance 4", "idle-dance-tiktok4", 15.5),
    ("Advanced Shy", "emote-shy2", 5.0),
    ("Anime Dance", "dance-anime", 8.5),
    ("Kawaii", "dance-kawai", 10.3),
    ("Scritchy", "idle-wild", 26.4),
    ("Ice Skating", "emote-iceskating", 7.3),
    ("SurpriseBig", "emote-pose6", 5.4),
    ("Celebration Step", "emote-celebrationstep", 3.4),
    ("Creepycute", "emote-creepycute", 7.9),
    ("Pose 10", "emote-pose10", 4.0),
    ("Boxer", "emote-boxer", 5.6),
    ("Head Blowup", "emote-headblowup", 11.7),
    ("Ditzy Pose", "emote-pose9", 4.6),
    ("Teleporting", "emote-teleporting", 11.8),
    ("Touch", "dance-touch", 11.7),
    ("Air Guitar", "idle-guitar", 13.2),
    ("This Is For You", "emote-gift", 5.8),
    ("Push it", "dance-employee", 8.0),
    ("Wop Dance", "dance-tiktok11", 11.0),
    ("Cute Salute", "emote-cutesalute", 3.0),
    ("At Attention", "emote-salute", 3.0),
]

ITEM_EMOTES = [
    ("Rest", "sit-idle-cute", 17.1),
    ("Zombie", "idle_zombie", 28.8),
    ("Relaxed", "sit-relaxed", 29.9),
    ("Attentive", "idle_layingdown", 24.6),
    ("Sleepy", "idle-loop-tired", 22.0),
    ("Pouty Face", "idle-sad", 24.4),
    ("Posh", "idle-posh", 21.9),
    ("Tap Loop", "idle-loop-tapdance", 6.3),
    ("Bummed", "idle-loop-sad", 6.1),
    ("Chillin'", "idle-loop-happy", 18.8),
    ("Annoyed", "idle-loop-annoyed", 17.1),
    ("Aerobics", "idle-loop-aerobics", 8.5),
    ("Ponder", "idle-lookup", 22.3),
    ("Hero Pose", "idle-hero", 21.9),
    ("Relaxing", "idle-floorsleeping2", 17.3),
    ("Cozy Nap", "idle-floorsleeping", 13.9),
    ("Boogie Swing", "idle-dance-swinging", 13.2),
    ("Feel The Beat", "idle-dance-headbobbing", 25.4),
    ("Irritated", "idle-angry", 25.4),
    ("I Believe I Can Fly", "emote-wings", 13.1),
    ("Think", "emote-think", 3.7),
    ("Theatrical", "emote-theatrical", 8.6),
    ("Tap Dance", "emote-tapdance", 11.1),
    ("Super Run", "emote-superrun", 6.3),
    ("Super Punch", "emote-superpunch", 3.8),
    ("Sumo Fight", "emote-sumo", 10.9),
    ("Thumb Suck", "emote-suckthumb", 4.2),
    ("Splits Drop", "emote-splitsdrop", 4.5),
    ("Secret Handshake", "emote-secrethandshake", 3.9),
    ("Rope Pull", "emote-ropepull", 8.8),
    ("Roll", "emote-roll", 3.6),
    ("ROFL!", "emote-rofl", 6.3),
    ("Robot", "emote-robot", 7.6),
    ("Rainbow", "emote-rainbow", 2.8),
    ("Proposing", "emote-proposing", 4.3),
    ("Peekaboo!", "emote-peekaboo", 3.6),
    ("Peace", "emote-peace", 5.8),
    ("Panic", "emote-panic", 2.9),
    ("Ninja Run", "emote-ninjarun", 4.8),
    ("Night Fever", "emote-nightfever", 5.5),
    ("Monster Fail", "emote-monster_fail", 4.6),
    ("Level Up!", "emote-levelup", 6.1),
    ("Amused", "emote-laughing2", 5.1),
    ("Laugh", "emote-lagughing", 1.1),
    ("Super Kick", "emote-kicking", 4.9),
    ("Jump", "emote-jumpb", 3.6),
    ("Judo Chop", "emote-judochop", 2.4),
    ("Imaginary Jetpack", "emote-jetpack", 16.8),
    ("Hug Yourself", "emote-hugyourself", 5.0),
    ("Hero Entrance", "emote-hero", 5.0),
    ("Headball", "emote-headball", 10.1),
    ("Harlem Shake", "emote-harlemshake", 13.6),
    ("Happy", "emote-happy", 3.5),
    ("Handstand", "emote-handstand", 4.0),
    ("Graceful", "emote-graceful", 3.7),
    ("Moonwalk", "emote-gordonshuffle", 8.1),
    ("Ghost Float", "emote-ghost-idle", 19.6),
    ("Gangnam Style", "emote-gangnam", 7.3),
    ("Frolic ", "emote-frollicking", 3.7),
    ("Faint", "emote-fainting", 18.4),
    ("Clumsy", "emote-fail2", 6.5),
    ("Fall", "emote-fail1", 5.6),
    ("Exasperated", "emote-exasperated", 2.4),
    ("Elbow Bump", "emote-elbowbump", 3.8),
    ("Disco", "emote-disco", 5.4),
    ("Blast Off", "emote-disappear", 6.2),
    ("Faint Drop", "emote-deathdrop", 3.8),
    ("Collapse", "emote-death2", 4.9),
    ("Revival", "emote-death", 6.6),
    ("Dab", "emote-dab", 2.7),
    ("Cold", "emote-cold", 3.7),
    ("Bunny Hop", "emote-bunnyhop", 12.4),
    ("Boo", "emote-boo", 4.5),
    ("Home Run!", "emote-baseball", 7.3),
    ("Falling Apart", "emote-apart", 4.8),
    ("Point", "emoji-there", 2.1),
    ("Sneeze", "emoji-sneeze", 3.0),
    ("Smirk", "emoji-smirking", 4.8),
    ("Sick", "emoji-sick", 5.1),
    ("Gasp", "emoji-scared", 3.0),
    ("Punch", "emoji-punch", 1.8),
    ("Pray", "emoji-pray", 4.5),
    ("Stinky", "emoji-poop", 4.8),
    ("Naughty", "emoji-naughty", 4.3),
    ("Mind Blown", "emoji-mind-blown", 2.4),
    ("Lying", "emoji-lying", 6.3),
    ("Levitate", "emoji-halo", 5.8),
    ("Fireball Lunge", "emoji-hadoken", 2.7),
    ("Give Up", "emoji-give-up", 5.4),
    ("Stunned", "emoji-dizzy", 4.1),
    ("Sob", "emoji-crying", 3.7),
    ("Clap", "emoji-clapping", 2.2),
    ("Arrogance", "emoji-arrogance", 6.9),
    ("Vogue Hands", "dance-voguehands", 9.2),
    ("Yoga Flow", "dance-spiritual", 15.8),
    ("Smoothwalk", "dance-smoothwalk", 6.7),
    ("Ring on It", "dance-singleladies", 21.2),
    ("Robotic", "dance-robotic", 17.8),
    ("Orange Juice Dance", "dance-orangejustice", 6.5),
    ("Rock Out", "dance-metal", 15.1),
    ("Karate", "dance-martial-artist", 13.3),
    ("Hands in the Air", "dance-handsup", 22.3),
    ("Floss", "dance-floss", 21.3),
    ("Duck Walk", "dance-duckwalk", 11.7),
    ("Breakdance", "dance-breakdance", 17.6),
    ("Push Ups", "dance-aerobics", 8.8),
    ("Attention", "emote-attention", 4.4),
    ("Ghost", "emoji-ghost", 3.5),
    ("Heart Shape", "emote-heartshape", 6.2),
    ("Hug", "emote-hug", 3.5),
    ("Eyeroll", "emoji-eyeroll", 3.0),
    ("Embarrassed", "emote-embarrassed", 7.4),
    ("Sexy dance", "dance-sexy", 12.3),
    ("Puppet", "emote-puppet", 16.3),
    ("Fighter idle", "idle-fighter", 17.2),
    ("Zombie Run", "emote-zombierun", 9.2),
    ("Frustrated", "emote-frustrated", 5.6),
    ("Laid Back", "sit-open", 26.0),
    ("Star gazing", "emote-stargaze", 1.1),
    ("Slap", "emote-slap", 2.7),
    ("KawaiiGoGo", "emote-kawaiigogo", 10.0),
    ("Repose", "emote-repose", 1.1),
    ("Tiktok7", "idle-dance-tiktok7", 13.0),
    ("Shrink", "emote-shrink", 8.7),
    ("Sweet Smooch", "emote-kissing", 5.0),
]

EXTRA_EMOTES = []  # رزرو برای دنس‌های آینده (در صورت تایید Highrise)


class Emote:
    def __init__(self, name: str, id: str, duration: float = 5.0, is_free: bool = True):
        self.name = name
        self.id = id
        self.duration = duration
        self.is_free = is_free

# Combine lists: Free Emotes first, then Item Emotes (all ۲۱۸ دنس/ایموت واقعی و تأییدشده)
ALL_EMOTE_TUPLES = FREE_EMOTES + ITEM_EMOTES + EXTRA_EMOTES

emotes = [
    Emote(name=item[0], id=item[1], duration=item[2], is_free=(item in FREE_EMOTES))
    for item in ALL_EMOTE_TUPLES
]

emote_dict = {
    item[0]: [item[1], item[2], (item in FREE_EMOTES)]
    for item in ALL_EMOTE_TUPLES
}


class HighriseBot(BaseBot):

    def __init__(self, room_id: str = "", bot_admins: list = None, api_token: str = "", real_room_id: str = ""):
        super().__init__()
        safe_room = (room_id or "default").replace("/", "_")[:16]
        self.db_file = _data_path(f"bot_database_{safe_room}.json")
        _migrate_legacy_file(f"bot_database_{safe_room}.json")
        self._bot_admins = list(bot_admins) if bot_admins else list(ADMINS)
        self.custom_admins: set = set(a.lower() for a in self._bot_admins)
        self._api_token  = api_token
        self._real_room_id = real_room_id

        # Core State
        self.warnings = {}
        self.banned_users = {}
        self.vip_users = set()
        self.message_counts = {}
        self.locations = {} # Named locations (public — anyone can teleport by typing the name)
        self.admin_locations = {} # Named locations (admin-only — فقط ادمین می‌تونه کاربر رو ببره، جدا از self.locations)
        self._public_tp_cooldown: Dict[str, float] = {}  # جلوگیری از اسپم انتقال عمومی به نقاط
        self.copy_outfit_enabled = False  # وقتی روشنه، بات لباس‌های رایگان ادمین/مالک رو کپی می‌کنه
        self._last_seen_outfits: Dict[str, list] = {}  # فینگرپرینت آخرین لباس هر ادمین/مالک که چک شده
        self.welcome_text = "🎉 سلام {user}! به روم ما خوش اومدی 🤍"
        self.admin_notes = {}
        self.total_visitors = 0
        self.bot_id = None

        # Bot Position Persistence
        self.saved_bot_position = None # {"x": ..., "y": ..., "z": ..., "facing": ...}

        # Persistent Spam System
        self.persistent_spam = {"active": False, "message": "", "interval": 5.0}
        self.spam_task: Optional[Task] = None

        # Economy & XP
        self.economy: Dict[str, int] = {}
        self.last_daily: Dict[str, float] = {}
        self.xp: Dict[str, int] = {}
        self.level_thresholds = [0,100,250,500,900,1400,2000,2800,3800,5000,7000]

        # Marriage & Pass
        self.marriages: Dict[str, str] = {}
        self.marriage_names: Dict[str, str] = {}
        self.birthdays: Dict[str, str] = {}

        # Moderation
        self.muted_users: set = set()
        self.word_filter_on = True
        self.word_filter: list = []
        self.user_name_cache: Dict[str, str] = {}
        self.admin_user_ids: set = set()
        self.slow_mode: int = 0
        self.slow_mode_last: Dict[str, float] = {}
        self.room_locked: bool = False
        self.room_rules: str = "📜 قوانین روم: احترام متقابل و عدم اسپم!"
        self.frozen_users: set = set()
        self.freeze_tasks: Dict[str, Task] = {}
        self.afk_users: Dict[str, str] = {}
        self.reports: list = []
        self.last_seen: Dict[str, str] = {}

        # Games State
        self.lottery: Dict = {"active": False, "tickets": {}, "prize": 0, "task": None}
        self.poll: Dict = {"active": False, "question": "", "options": [], "votes": {}, "voted": set()}
        self.active_timers: Dict[str, Task] = {}
        self.typing_challenge: Dict = {"active": False, "phrase": "", "started": 0, "winner": None}
        self.active_scramble: Dict = {}
        self.active_riddle: Dict = {}
        self.pets: Dict[str, Dict] = {}
        self.auction = {'active': False, 'bids': {}, 'description': '', 'end_time': 0, 'task': None}
        self.active_games = {}
        self.active_quiz = {}

        # Dance
        self.dance_enabled = True
        self.auto_emotes = {}
        self.emotes = emotes
        self.emotes_dict = emote_dict
        self.bot_dance_emote: str = "dance-popularvibe"
        self.follow_target: Optional[str] = None
        self.follow_task: Optional[Task] = None
        self.whisper_history = {}

        self._load_data()

    # 👑 Check if user is Admin / Owner
    def is_user_admin(self, user) -> bool:
        if not user: return False
        uname = (user.username.lower() if hasattr(user, "username") and user.username else "").strip()
        uid   = (user.id if hasattr(user, "id") else str(user)).strip()

        for a in ADMINS:
            if a.lower() == uname or a == uid:
                return True
        for a in getattr(self, "custom_admins", []):
            if a.lower() == uname or a == uid:
                return True
        for a in getattr(self, "_bot_admins", []):
            if a.lower() == uname or a == uid:
                return True
        return False

    # 👑 فقط مالک اصلی (ADMIN_USERNAME) — نه ادمین‌های اضافه‌شده
    def is_owner(self, user) -> bool:
        if not user or not ADMIN_USERNAME:
            return False
        uname = (user.username.lower() if hasattr(user, "username") and user.username else "").strip()
        return uname == ADMIN_USERNAME.lower()

    # Database Operations
    def _load_data(self):
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.custom_admins  = set(a.lower() for a in data.get("custom_admins", list(self._bot_admins)))
                if os.path.exists(_data_path("config.json")):
                    try:
                        with open(_data_path("config.json"), "r", encoding="utf-8") as cf:
                            cfg_data = json.load(cf)
                            for ca in cfg_data.get("admins", []):
                                if ca: self.custom_admins.add(ca.lower())
                    except Exception: pass
                if ADMIN_USERNAME: self.custom_admins.add(ADMIN_USERNAME.lower())
                for ba in getattr(self, "_bot_admins", []):
                    if ba: self.custom_admins.add(ba.lower())
                for ca in self.custom_admins:
                    if ca.lower() not in [a.lower() for a in ADMINS]:
                        ADMINS.append(ca.lower())
                self.warnings       = data.get("warnings", {})
                self.banned_users   = data.get("banned_users", {})
                self.vip_users      = set(data.get("vip_users", []))
                self.locations      = data.get("locations", {})
                self.admin_locations = data.get("admin_locations", {})
                self.copy_outfit_enabled = data.get("copy_outfit_enabled", False)
                self.welcome_text   = data.get("welcome_text", self.welcome_text)
                self.admin_notes    = data.get("admin_notes", {})
                self.total_visitors = data.get("total_visitors", 0)
                self.economy        = data.get("economy", {})
                self.last_daily     = data.get("last_daily", {})
                self.xp             = data.get("xp", {})
                self.marriages      = data.get("marriages", {})
                self.marriage_names = data.get("marriage_names", {})
                self.birthdays      = data.get("birthdays", {})
                self.pets           = data.get("pets", {})
                self.word_filter    = data.get("word_filter", [])
                self.room_rules     = data.get("room_rules", self.room_rules)
                self.last_seen      = data.get("last_seen", {})
                self.saved_bot_position = data.get("saved_bot_position", None)
                self.persistent_spam = data.get("persistent_spam", {"active": False, "message": "", "interval": 5.0})
                print("✅ دیتابیس با موفقیت بارگذاری شد.")
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری دیتابیس: {e}")

    def _save_data(self):
        try:
            if ADMIN_USERNAME: self.custom_admins.add(ADMIN_USERNAME.lower())
            for ca in self.custom_admins:
                if ca.lower() not in [a.lower() for a in ADMINS]:
                    ADMINS.append(ca.lower())
            data = {
                "custom_admins": list(self.custom_admins), "warnings": self.warnings, "banned_users": self.banned_users,
                "vip_users": list(self.vip_users), "locations": self.locations,
                "admin_locations": self.admin_locations,
                "copy_outfit_enabled": self.copy_outfit_enabled,
                "welcome_text": self.welcome_text, "admin_notes": self.admin_notes,
                "total_visitors": self.total_visitors, "economy": self.economy,
                "last_daily": self.last_daily, "xp": self.xp, "marriages": self.marriages,
                "marriage_names": self.marriage_names, "birthdays": self.birthdays,
                "pets": self.pets, "word_filter": self.word_filter,
                "room_rules": self.room_rules, "last_seen": self.last_seen,
                "saved_bot_position": self.saved_bot_position,
                "persistent_spam": self.persistent_spam
            }
            with open(self.db_file + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(self.db_file + ".tmp", self.db_file)
            try:
                cfg_obj = {}
                if os.path.exists(_data_path("config.json")):
                    with open(_data_path("config.json"), "r", encoding="utf-8") as cf:
                        cfg_obj = json.load(cf)
                cfg_obj["admins"] = list(set([a.lower() for a in self.custom_admins] + [a.lower() for a in ADMINS]))
                with open(_data_path("config.json") + ".tmp", "w", encoding="utf-8") as cf:
                    json.dump(cfg_obj, cf, ensure_ascii=False, indent=2)
                os.replace(_data_path("config.json") + ".tmp", _data_path("config.json"))
            except Exception: pass
        except Exception as e:
            print(f"⚠️ خطا در ذخیره دیتابیس: {e}")

    # Economy Helpers
    def _get_gold(self, uid: str) -> int: return self.economy.get(uid, 0)
    def _add_gold(self, uid: str, amount: int): self.economy[uid] = max(0, self.economy.get(uid, 0) + amount)
    def _take_gold(self, uid: str, amount: int) -> bool:
        if amount <= 0: return False
        if self.economy.get(uid, 0) >= amount:
            self.economy[uid] -= amount
            return True
        return False

    # XP Helpers
    def _add_xp(self, uid: str, amount: int = 5) -> Optional[int]:
        old_lvl = self._get_level(uid)
        self.xp[uid] = self.xp.get(uid, 0) + amount
        new_lvl = self._get_level(uid)
        return new_lvl if new_lvl > old_lvl else None

    def _get_level(self, uid: str) -> int:
        xp_val = self.xp.get(uid, 0)
        lvl = 0
        for i, t in enumerate(self.level_thresholds):
            if xp_val >= t: lvl = i
        return lvl

    # Location & Position Management
    async def get_user_pos(self, uid: str) -> Optional[Position]:
        try:
            resp = await self.highrise.get_room_users()
            if resp and hasattr(resp, "content"):
                for u, pos in resp.content:
                    if u.id == uid:
                        return pos
        except Exception as e:
            print(f"Pos error: {e}")
        return None

    async def auto_restore_bot_position(self):
        """بازگرداندن خودکار جایگاه بات هنگام اتصال مجدد"""
        await asyncio.sleep(2)
        if self.saved_bot_position:
            try:
                p = self.saved_bot_position
                pos = Position(p["x"], p["y"], p["z"], p.get("facing", "FrontRight"))
                if self.bot_id:
                    await self.highrise.teleport(self.bot_id, pos)
                    print(f"📍 بات به موقعیت ذخیره‌شده بازگشت: ({p['x']}, {p['y']}, {p['z']})")
            except Exception as e:
                print(f"⚠️ Auto teleport bot error: {e}")

    # Spam Loop Logic (Persistent)
    def start_persistent_spam(self, message: str, interval: float):
        self.stop_persistent_spam()
        self.persistent_spam = {"active": True, "message": message, "interval": interval}
        self._save_data()
        self.spam_task = asyncio.create_task(self._spam_worker())

    def stop_persistent_spam(self):
        self.persistent_spam["active"] = False
        self._save_data()
        if self.spam_task and not self.spam_task.done():
            self.spam_task.cancel()

    async def _spam_worker(self):
        try:
            while self.persistent_spam.get("active", False):
                msg = self.persistent_spam.get("message", "")
                sec = self.persistent_spam.get("interval", 5.0)
                if msg:
                    await self.highrise.chat(msg)
                await asyncio.sleep(max(sec, 1.0))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Spam worker error: {e}")

    # Dance helpers
    def _claim_dance(self, uid: str) -> bool:
        cur = _dance_claimed.get(uid)
        if cur is None or cur == id(self):
            _dance_claimed[uid] = id(self)
            return True
        return False

    def _release_dance(self, uid: str):
        if _dance_claimed.get(uid) == id(self):
            _dance_claimed.pop(uid, None)

    async def start_user_dance(self, uid: str, emote_key: str):
        if uid in self.auto_emotes:
            self.auto_emotes[uid].cancel()
        self.auto_emotes[uid] = asyncio.create_task(self._repeat_emote(uid, emote_key))

    async def stop_user_dance(self, uid: str):
        if uid in self.auto_emotes:
            self.auto_emotes[uid].cancel()
            del self.auto_emotes[uid]
        # ارسال emote کوتاه برای قطع فوری انیمیشن جاری روی سرور هایرایز
        await asyncio.sleep(0)  # به asyncio اجازه می‌دهیم کنسل را پردازش کند
        try:
            await self.highrise.send_emote("emote-wave", uid)
        except Exception:
            pass

    def resolve_emote_data(self, emote_key: str):
        if not emote_key:
            return None
        
        # 1. Convert Persian/Arabic digits to ASCII digits
        key_raw = str(emote_key).strip()
        p_digits = '۰۱۲۳۴۵۶۷۸۹'
        a_digits = '٠١٢٣٤٥٦٧٨٩'
        for p, a, e in zip(p_digits, a_digits, '0123456789'):
            key_raw = key_raw.replace(p, e).replace(a, e)
        
        key_str = key_raw.lower()

        # 2. Strip common dance prefixes (with or without !)
        prefixes = [
            "!dance ", "!دنس ", "!رقص ", "!d ", "!emote ",
            "dance ", "دنس ", "رقص ", "pr ", "emote ", "d "
        ]
        for pref in prefixes:
            if key_str.startswith(pref):
                key_str = key_str[len(pref):].strip()
                break

        # Handle attached prefixes like "دنس1", "رقص5", "dance12"
        for pref_short in ["دنس", "رقص", "dance", "emote"]:
            if key_str.startswith(pref_short) and len(key_str) > len(pref_short) and key_str[len(pref_short):].isdigit():
                key_str = key_str[len(pref_short):].strip()
                break

        # 3. Persian Aliases Dictionary
        persian_aliases = {
            "فلوس": "dance-floss",
            "سویج": "emote-savage",
            "پوپولار": "dance-popularvibe",
            "شاپینگ": "dance-shoppingcart",
            "استراحت": "sit-idle-cute",
            "رست": "sit-idle-cute",
            "نشستن": "idle-loop-sitfloor",
            "خجالتی": "emote-shy",
            "تیکتاک": "dance-tiktok8",
            "تیک تاک": "dance-tiktok8",
            "سلام": "emote-wave",
            "ویو": "emote-wave",
            "بوس": "emote-kiss",
            "کیس": "emote-kiss",
            "خنده": "emote-laughing",
            "زامبی": "idle_zombie",
            "روح": "emote-ghost-idle",
            "آواز": "idle_singing",
            "سینگ": "idle_singing",
            "هیرو": "idle-hero",
            "شارژ": "emote-charging",
            "ماکارنا": "dance-macarena",
            "روسی": "dance-russian",
            "دست بالا": "dance-handsup",
            "بغل": "emote-hug",
            "گریه": "emote-crying",
            "کیوت": "emote-cute",
            "مار": "emote-snake",
            "قورباغه": "emote-frog",
            "داغ": "emote-hot",
            "برفی": "emote-snowball",
            "دنس": "dance-popularvibe",
            "رقص": "dance-popularvibe",
            "پارتی": "dance-popularvibe"
        }

        if key_str in persian_aliases:
            key_str = persian_aliases[key_str]

        # Explicit Floss matching
        if key_str in ["floss", "flos", "فلوس", "دنس فلوس", "رقص فلوس", "dance-floss", "floss dance"]:
            return {"id": "dance-floss", "name": "Floss", "duration": 8.0}

        # Numbers 1 to len(self.emotes)
        if key_str.isdigit():
            num = int(key_str)
            if 1 <= num <= len(self.emotes):
                e = self.emotes[num - 1]
                return {"id": e.id, "name": e.name, "duration": getattr(e, "duration", 5.0)}

        # URL or direct emote ID (e.g. dance-popularvibe, emote-shy, idle_singing)
        is_url_or_emote_id = (
            "high.rs" in key_str or "item?id=" in key_str or
            "highrise.game" in key_str or "highrise.com" in key_str or
            key_str.startswith("dance-") or key_str.startswith("emote-") or
            key_str.startswith("idle") or key_str.startswith("sit-") or key_str.startswith("walk-")
        )
        if is_url_or_emote_id:
            # First try to extract from URL ?id= param
            m_id = re.search(r"[?&]id=([a-zA-Z0-9_\-]+)", key_raw)
            if m_id:
                return {"id": m_id.group(1), "name": m_id.group(1), "duration": 5.0}
            # Then try to find any emote/dance/idle pattern in the string
            m_d = re.search(r"((?:dance|emote|idle|sit|walk)[-_][a-zA-Z0-9_\-]+|idle_[a-zA-Z0-9_]+)", key_raw, re.IGNORECASE)
            if m_d:
                return {"id": m_d.group(1), "name": m_d.group(1), "duration": 5.0}
            # If key_str itself is a bare emote ID return it directly
            if key_str.startswith("dance-") or key_str.startswith("emote-") or key_str.startswith("idle") or key_str.startswith("sit-") or key_str.startswith("walk-"):
                return {"id": key_str, "name": key_str, "duration": 5.0}

        # Exact match in emote_dict or self.emotes
        for k, val in self.emotes_dict.items():
            if k.lower() == key_str:
                eid = val[0] if isinstance(val, (list, tuple)) else val.get("id", k)
                dur = val[1] if isinstance(val, (list, tuple)) and len(val) > 1 else 5.0
                return {"id": eid, "name": k, "duration": dur}

        # Match in self.emotes
        for e in self.emotes:
            e_id = getattr(e, "id", "")
            e_name = getattr(e, "name", "")
            if e_id.lower() == key_str or e_name.lower() == key_str or key_str in e_id.lower() or key_str in e_name.lower():
                return {"id": e_id, "name": e_name, "duration": getattr(e, "duration", 5.0)}

        # Fallback raw key if present
        if len(key_raw) > 0:
            return {"id": key_raw, "name": key_raw, "duration": 5.0}

        return None

    async def _repeat_emote(self, uid: str, emote_key: str):
        # emote_key is already a resolved emote ID (e.g. "dance-floss")
        # resolve once more to get duration info if available
        emote_data = self.resolve_emote_data(emote_key)
        emote_id = emote_key  # always use the passed key as primary ID
        dur = 5.0
        if emote_data:
            emote_id = emote_data.get("id", emote_key)
            dur = float(emote_data.get("duration", 5.0))

        fallback_emotes = ["dance-popularvibe", "dance-shoppingcart", "idle-loop-happy", "emote-shy", "emote-wave"]
        current_emote_id = emote_id

        fail_count = 0
        while True:
            try:
                await self.highrise.send_emote(current_emote_id, uid)
                fail_count = 0
                await asyncio.sleep(max(dur - 0.3, 0.8))
            except asyncio.CancelledError:
                break
            except Exception as ex:
                fail_count += 1
                print(f"Emote repeat error for {uid} ({current_emote_id}): {ex}")

                if fail_count == 1 and current_emote_id != fallback_emotes[0]:
                    current_emote_id = fallback_emotes[0]
                    dur = 8.5
                    try:
                        await self.highrise.send_whisper(uid, f"⚠️ دنس اصلی نیازمند آیتم بود — دنس جایگزین اجرا شد! ✨")
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    continue

                if fail_count >= 3:
                    try:
                        await self.highrise.send_whisper(uid, f"⚠️ اجرای دنس با خطا مواجه شد. لطفاً دنس دیگری امتحان کنید.")
                    except Exception:
                        pass
                    break
                await asyncio.sleep(1)

    # On Start
    async def on_start(self, session_metadata) -> None:
        print("✅ Bot connected!")
        try:
            self.bot_id = session_metadata.user_id
        except Exception: pass
        await self.highrise.chat("🤖 بات prbot روشن شد! ✨")
        
        # Restore position & spam
        asyncio.create_task(self.auto_restore_bot_position())
        if self.persistent_spam.get("active", False):
            self.spam_task = asyncio.create_task(self._spam_worker())
            print("🔄 اسپم فعال از قبل بازیابی شد.")

        # Background loops
        asyncio.create_task(self._bot_dance_loop())
        asyncio.create_task(self._auto_save_loop())
        asyncio.create_task(self._outfit_watch_loop())

    async def _auto_save_loop(self):
        while True:
            await asyncio.sleep(60)
            self._save_data()

    async def _copy_free_outfit(self, source_user_id: str, source_username: str):
        """لباس یه ادمین/مالک رو می‌گیره و فقط آیتم‌هایی که بات می‌تونه بپوشه (رایگان/در اختیار بات) رو روی بات کپی می‌کنه.
        آیتم‌های پولی که بات مالکشون نیست به‌صورت خودکار رد می‌شن، پس فقط تیکه‌های رایگان اعمال می‌شن."""
        if Item is None:
            return
        try:
            res = await self.highrise.get_user_outfit(source_user_id)
            outfit_items = getattr(res, "outfit", None)
            if not outfit_items:
                return
        except Exception as e:
            print(f"⚠️ خطا در گرفتن لباس {source_username}: {e}")
            return

        working_outfit = []
        applied = 0
        for it in outfit_items:
            trial = working_outfit + [it]
            try:
                await self.highrise.set_outfit(outfit=trial)
                working_outfit = trial
                applied += 1
            except Exception:
                continue  # این آیتم رایگان نبود یا بات مالکش نیست
            await asyncio.sleep(0.15)

        if applied:
            print(f"👕 بات {applied} آیتم رایگان از لباس {source_username} رو کپی کرد.")

    async def _outfit_watch_loop(self):
        """هر ۵ ثانیه چک می‌کنه ادمین‌ها/مالک لباسشون رو عوض کردن یا نه، و در صورت روشن بودن قابلیت، کپی می‌کنه."""
        while True:
            await asyncio.sleep(5)
            if not self.copy_outfit_enabled or Item is None:
                continue
            try:
                users_res = await self.highrise.get_room_users()
            except Exception:
                continue
            for u, _p in users_res.content:
                if not self.is_user_admin(u):
                    continue
                try:
                    res = await self.highrise.get_user_outfit(u.id)
                    outfit_items = getattr(res, "outfit", None)
                    if not outfit_items:
                        continue
                    fingerprint = tuple(sorted(getattr(i, "id", str(i)) for i in outfit_items))
                except Exception:
                    continue
                if self._last_seen_outfits.get(u.id) == fingerprint:
                    continue
                self._last_seen_outfits[u.id] = fingerprint
                await self._copy_free_outfit(u.id, u.username)

    # 💖 قلب فرستادن با تأخیر بین هر نفر — برای جلوگیری از قطع شدن بات توی روم شلوغ (rate limit)
    async def _broadcast_hearts(self):
        try:
            ru = await self.highrise.get_room_users()
            sent = 0
            for u, _pos in ru.content:
                try:
                    await self.highrise.react(u.id, "heart")
                    sent += 1
                except Exception as e:
                    print(f"Heart react failed for {getattr(u, 'username', '?')}: {e}")
                await asyncio.sleep(0.35)
            await self.highrise.chat(f"💖 قلب برای {sent} نفر توی روم فرستاده شد!")
        except Exception as e:
            print(f"Heart broadcast error: {e}")
            try:
                await self.highrise.chat("❌ نتونستم قلب بفرستم، دوباره امتحان کن.")
            except Exception:
                pass

    async def _bot_dance_loop(self):
        while True:
            try:
                await self.highrise.send_emote(self.bot_dance_emote)
                await asyncio.sleep(6)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(5)

    # Theme Park Attractions Logic
    # On Chat — Full Command Handling
    
        # 🤖 AI Assistant Engine (Gemini + Persian Smart Conversational Fallback)
    async def ask_ai_question(self, prompt: str, siri_mode: bool = False) -> str:
        import urllib.request, json, asyncio, os, random
        prompt_str = prompt.strip()
        if not prompt_str:
            if siri_mode:
                return "بله؟ چطور می‌تونم کمکت کنم؟ 🎙️"
            return "سلام! چی می‌خوای ازم بپرسی؟ 😊"

        # Check API Keys
        env_key = os.environ.get("GEMINI_API_KEY", "")
        cfg_key = ""
        try:
            if os.path.exists(_data_path("config.json")):
                with open(_data_path("config.json"), "r", encoding="utf-8") as cf:
                    cfg_key = json.load(cf).get("gemini_api_key", "")
        except Exception: pass

        api_keys = [k for k in [cfg_key, env_key] if k]
        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]

        for key in api_keys:
            for model in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                if siri_mode:
                    prompt_text = (
                        f"تو دستیار هوشمند فارسی‌زبانی هستی به اسم سیری که توی بازی هایرایز کار می‌کنی. "
                        f"مثل سیری اپل خیلی هوشمند، صمیمی و مودب جواب می‌دی. جواب‌هات کوتاه، واضح و کاربردی باشه. "
                        f"اگه سوال علمی، خبری یا دانشی داری دقیق جواب بده. به فارسی روان جواب بده: {prompt_str}"
                    )
                else:
                    prompt_text = f"شما دستیار هوشمند، دانا و صمیمی بات هایرایز (prbot) هستید. به صورت بسیار جذاب، محترمانه و کوتاه به فارسی پاسخ دهید: {prompt_str}"
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt_text}]
                    }]
                }
                try:
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                    loop = asyncio.get_event_loop()
                    def _call():
                        with urllib.request.urlopen(req, timeout=6) as resp:
                            return json.loads(resp.read().decode('utf-8'))
                    res = await loop.run_in_executor(None, _call)
                    if 'candidates' in res and res['candidates']:
                        text = res['candidates'][0]['content']['parts'][0]['text'].strip()
                        if text:
                            return text[:350]
                except Exception:
                    continue

        # 🧠 Smart Persian Conversational AI Fallback (When API rate limits occur)
        p_low = prompt_str.lower()
        if siri_mode:
            if any(w in p_low for w in ["سلام", "درود", "چطوری", "خوبی", "سلامت"]):
                return random.choice([
                    "سلام! من سیری هستم، دستیار هوشمند بات prbot. چطور می‌تونم کمکت کنم؟ 🎙️",
                    "سلام! آماده‌ام. چه سوالی داری؟ 😊",
                    "درود! بپرس، اینجام ✨"
                ])
            elif any(w in p_low for w in ["کی هستی", "اسمت", "معرفی", "تو چی هستی"]):
                return "من سیری هستم — دستیار هوشمند فارسی‌زبان بات prbot در هایرایز! می‌تونی هر سوالی ازم بپرسی 🎙️"
            elif any(w in p_low for w in ["ساعت", "تاریخ", "امروز", "الان چنده"]):
                now = datetime.datetime.now()
                return f"الان ساعت {now.strftime('%H:%M')} و تاریخ {now.strftime('%Y/%m/%d')} هست 📅"
            elif any(w in p_low for w in ["دنس", "رقص", "شماره دنس"]):
                return "برای دنس کافیه شماره (مثلاً ۵) یا اسم دنس (مثلاً floss) یا لینک هایرایز رو بفرستی! 🎭"
            else:
                return random.choice([
                    f"درباره «{prompt_str[:40]}» متأسفانه الان اطلاعات کافی ندارم. سعی کن سوال رو واضح‌تر بپرسی 🎙️",
                    "سوال جالبیه! ولی الان به اینترنت دسترسی ندارم. بعداً دوباره بپرس 😊",
                    "نمی‌تونم مطمئن جواب بدم. یه سوال دیگه بپرس! 🎙️"
                ])
        else:
            if any(w in p_low for w in ["سلام", "درود", "چطوری", "خوبی", "چخبر", "سلامت"]):
                return random.choice([
                    "سلام دوست عزیز! عالی‌ام، امیدوارم حال تو هم فوق‌العاده باشه! 🌟 چطور می‌تونم کمکت کنم؟",
                    "درود بر شما! من روبات هوشمند prbot هستم، خوشحالم می‌بینمت! ✨",
                    "سلام رفیق! همه چی عالیه. چه خبر از هایرایز؟ 🎡"
                ])
            elif any(w in p_low for w in ["اسم", "کی هستی", "تو چی هستی", "معرفی"]):
                return "من prbot هستم، پیشرفته‌ترین و خفن‌ترین روبات دنس هایرایز! 🤖"
            elif any(w in p_low for w in ["دنس", "رقص", "چطور رقص", "شماره دنس"]):
                return "کافیه شماره ۱ تا ۲۶۹ یا اسم دنس یا لینک اون رو بفرستی تا بلافاصله برات اجرا کنم! 🎭✨"
            elif any(w in p_low for w in ["مالک", "سازنده", "ادمین", "ادمینها"]):
                return "این ربات توسط تیم حرفه‌ای prbot طراحی شده! با دستور !admins لیست ادمین‌ها رو ببین. 👑"
            elif any(w in p_low for w in ["بازی"]):
                return "دستورهای هیجان‌انگیزی مثل !quiz، !scramble و !riddle رو امتحان کن! 🎮"
            elif any(w in p_low for w in ["گلد", "سکه", "پول", "روزانه"]):
                return "با دستور !daily گلد روزانه‌ات رو بگیر و با !coins موجودی‌ت رو چک کن! 💰✨"
            else:
                return random.choice([
                    f"پاسخ به «{prompt_str[:30]}»: من روبات هوشمند prbot هستم! می‌تونی از دستورات دنس و بازی لذت ببری! 🤖✨",
                    "سوال خیلی جالبی بود! من همیشه اینجام تا توی هایرایز همراهت باشم و بهترین دنس‌ها رو برات اجرا کنم! 🌟",
                    "مرسی که با من چت می‌کنی! برای دیدن تمام دستورات عجیب و خفن من، راهنمای پنل رو نگاه کن! 🎡🚀"
                ])


    # 📩 Private Message Handler (PV / Whisper AI & Commands)
    async def on_whisper(self, user: User, message: str) -> None:
        try:
            username = user.username
            user_id  = user.id
            msg      = message.strip()
            msg_low  = msg.lower()

            # 🛑 Stop Dance Command
            if msg_low in ["stop", "!stop", "استپ", "ایست", "توقف", "قطع", "!توقف", "!قطع", "0", "!0"]:
                await self.stop_user_dance(user_id)
                await self.highrise.send_whisper(user_id, "⏹️ دنس شما متوقف شد.")
                return

            # 🏃 Follow Commands
            if msg_low.startswith("!follow") or msg_low.startswith("!فالو") or msg_low in ["follow", "فالو"]:
                target_u = user_id
                parts = msg.split(" ", 1)
                if len(parts) > 1:
                    target_u = parts[1].replace("@", "").strip()
                await self.start_follow(target_u)
                await self.highrise.send_whisper(user_id, f"🏃 بات شروع به فالو کردن {target_u} کرد!")
                return

            if msg_low in ["!unfollow", "!آنفالو", "!توقف_فالو", "!stopfollow", "unfollow"]:
                await self.stop_follow()
                await self.highrise.send_whisper(user_id, "⏹️ فالو متوقف شد.")
                return

            # 🎭 Universal Dance Handler in PV
            is_explicit_dance_pv = (
                msg_low in ["floss", "فلوس", "فلوس زدن", "دنس فلوس", "رقص فلوس", "سویج", "پوپولار", "استراحت", "شاپینگ", "تیکتاک", "کیوت", "زامبی", "ماکارنا"] or
                msg_low.startswith("!dance") or msg_low.startswith("!دنس") or msg_low.startswith("!رقص") or
                msg_low.startswith("dance") or msg_low.startswith("دنس") or msg_low.startswith("رقص") or
                msg_low.startswith("pr ") or msg_low.startswith("!emote") or msg_low.startswith("emote") or
                "high.rs" in msg_low or "item?id=" in msg_low or
                msg_low.startswith("dance-") or msg_low.startswith("emote-") or msg_low.startswith("idle")
            )

            converted_msg_pv = msg
            for p, a, e in zip('۰۱۲۳۴۵۶۷۸۹', '٠١٢٣٤٥٦٧٨٩', '0123456789'):
                converted_msg_pv = converted_msg_pv.replace(p, e).replace(a, e)

            is_digit_dance_pv = converted_msg_pv.strip().isdigit()

            if is_explicit_dance_pv or is_digit_dance_pv:
                e_data = self.resolve_emote_data(msg)
                if e_data and e_data.get("id"):
                    await self.start_user_dance(user_id, e_data["id"])
                    await self.highrise.send_whisper(user_id, f"🎭 دنس «{e_data.get('name', e_data['id'])}» برای شما اجرا شد! ✨")
                    return

            # 🫶🏻 راهنما / تبلیغ بات — جایگزین هوش مصنوعی برای هر پیام دیگه (حتی خالی)
            await self.highrise.send_whisper(
                user_id,
                "برای دریافت بات رایگان به سایت زیر برید 🫶🏻🤖\nhighrisepr.ir"
            )

        except Exception as e:
            print(f"Error on_whisper: {e}")

    async def on_chat(self, user: User, message: str) -> None:
        try:
            username = user.username
            user_id  = user.id
            msg      = message.strip()
            msg_low  = msg.lower()

            self.user_name_cache[user_id] = username
            if self.is_user_admin(user): self.admin_user_ids.add(user_id)
            if user_id in self.muted_users: return

            # 🛑 Stop Dance Command
            if msg_low in ["stop", "!stop", "استپ", "ایست", "توقف", "قطع", "!توقف", "!قطع", "0", "!0"]:
                await self.stop_user_dance(user_id)
                await self.highrise.chat(f"⏹️ دنس @{username} متوقف شد.")
                return

            # 🤖 Public AI Command
            if msg_low.startswith("!ai ") or msg_low.startswith("!هوش ") or msg_low.startswith("!gpt "):
                q = msg.split(" ", 1)[1].strip()
                reply = await self.ask_ai_question(q)
                await self.highrise.chat(f"🤖 @{username}: {reply}")
                return

            # 🎙️ Siri Command — !siri یا سیری (wake word)
            if (msg_low.startswith("!siri ") or msg_low.startswith("سیری ") or
                    msg_low.startswith("siri ") or msg_low == "!siri" or msg_low == "سیری"):
                parts = msg.split(" ", 1)
                q = parts[1].strip() if len(parts) > 1 else ""
                reply = await self.ask_ai_question(q, siri_mode=True)
                await self.highrise.chat(f"🎙️ سیری → @{username}: {reply}")
                return

            # Word filter
            if self.word_filter_on and not self.is_user_admin(user):
                for w in self.word_filter:
                    if w.lower() in msg_low:
                        await self.highrise.chat(f"⚠️ {username} کلمه ممنوع استفاده نکن!")
                        return

            # 🌍 PUBLIC LOCATION TELEPORT — همه کاربران با نوشتن نام نقطه ثبت‌شده به اونجا منتقل می‌شن
            # (نقاط رو فقط ادمین‌ها با !save <نام> ثبت می‌کنن — بعد از ثبت، هرکسی اسم نقطه رو بنویسه می‌بره اونجا)
            if self.locations:
                candidate = None
                if msg_low in self.locations:
                    candidate = msg_low
                elif msg_low.startswith("!") and msg_low[1:] in self.locations:
                    candidate = msg_low[1:]
                elif (msg_low.startswith("!go ") or msg_low.startswith("!goto ") or
                      msg_low.startswith("!برو ") or msg_low.startswith("!نقطه ")):
                    cand = msg.split(" ", 1)[1].strip().lower()
                    if cand in self.locations:
                        candidate = cand

                if candidate:
                    now_ts = time.time()
                    last_tp = self._public_tp_cooldown.get(user_id, 0)
                    # ادمین‌ها محدودیت زمانی ندارن، بقیه هر ۳ ثانیه یک‌بار
                    if self.is_user_admin(user) or (now_ts - last_tp >= 3.0):
                        loc = self.locations[candidate]
                        try:
                            await self.highrise.teleport(
                                user_id,
                                Position(loc["x"], loc["y"], loc["z"], loc.get("facing", "FrontRight"))
                            )
                            self._public_tp_cooldown[user_id] = now_ts
                            await self.highrise.chat(f"🌀 @{username} به نقطه «{candidate}» منتقل شد!")
                        except Exception as e:
                            print(f"⚠️ Public location teleport error: {e}")
                    return

            # Dedup check for commands
            if msg.startswith("!") and not _should_handle_command(user_id, msg):
                return

            # 💖 قلب فرستادن به همه‌ی کاربران روم — فقط مالک اصلی
            if msg_low in ["!heart", "!قلب", "!love", "!عشق"] and self.is_owner(user):
                asyncio.create_task(self._broadcast_hearts())
                return

            # 👑 OWNER/ADMIN COMMANDS
# 👑 ADMIN MANAGEMENT COMMANDS (!addadmin, !remadmin, !admins)
            if (msg_low.startswith("!addadmin ") or msg_low.startswith("!افزودن_ادمین ") or msg_low.startswith("!ادمین ")) and self.is_user_admin(user):
                target_str = msg.split(" ", 1)[1].strip().replace("@", "").lower()
                if target_str:
                    self.custom_admins.add(target_str)
                    if target_str not in ADMINS:
                        ADMINS.append(target_str)
                    self._save_data()
                    await self.highrise.chat(f"👑 کاربر @{target_str} با موفقیت به عنوان ادمین جدید اضافه شد! (دسترسی کامل دسترسی مالک) ✨")
                else:
                    await self.highrise.chat("❌ راهنما: !addadmin @username")
                return

            if (msg_low.startswith("!remadmin ") or msg_low.startswith("!عزل_ادمین ") or msg_low.startswith("!حذف_ادمین ")) and self.is_user_admin(user):
                target_str = msg.split(" ", 1)[1].strip().replace("@", "").lower()
                if ADMIN_USERNAME and target_str == ADMIN_USERNAME.lower():
                    await self.highrise.chat(f"❌ کاربر @{target_str} مالک اصلی ربات است و قابل عزل نمی‌باشد!")
                    return
                if target_str in self.custom_admins or target_str in [a.lower() for a in ADMINS]:
                    self.custom_admins.discard(target_str)
                    ADMINS[:] = [a for a in ADMINS if a.lower() != target_str]
                    self._save_data()
                    await self.highrise.chat(f"❌ کاربر @{target_str} از لیست ادمین‌های بات برکنار شد.")
                else:
                    await self.highrise.chat(f"❌ کاربر @{target_str} در لیست ادمین‌ها پیدا نشد.")
                return

            if msg_low in ["!admins", "!ادمین‌ها", "!ادمینها", "!لیست_ادمین"]:
                all_adm = sorted(list(self.custom_admins.union(set(a.lower() for a in ADMINS)).union(set(a.lower() for a in self._bot_admins))))
                if all_adm:
                    adm_str = ", ".join([f"👑 @{a}" for a in all_adm])
                    await self.highrise.chat(f"📜 لیست ادمین‌های بات: {adm_str}")
                else:
                    await self.highrise.chat("❌ هنوز هیچ ادمینی ثبت نشده است.")
                return

            # 👕 کپی خودکار لباس‌های رایگان ادمین/مالک روی بات
            if (msg_low.startswith("!copyoutfit") or msg_low.startswith("!کپی_لباس")) and self.is_user_admin(user):
                arg = msg_low.split(" ", 1)[1].strip() if " " in msg_low else ""
                if arg in ["on", "روشن", "فعال"]:
                    self.copy_outfit_enabled = True
                    self._last_seen_outfits.clear()
                    self._save_data()
                    await self.highrise.chat("👕 کپی خودکار لباس روشن شد! هر وقت ادمین یا مالک لباس عوض کنه، بات همون لباس‌های رایگانش رو می‌پوشه.")
                elif arg in ["off", "خاموش", "غیرفعال"]:
                    self.copy_outfit_enabled = False
                    self._save_data()
                    await self.highrise.chat("👕 کپی خودکار لباس خاموش شد.")
                else:
                    status = "روشن ✅" if self.copy_outfit_enabled else "خاموش ❌"
                    await self.highrise.chat(f"👕 وضعیت کپی لباس: {status}\nراهنما: !copyoutfit on یا !copyoutfit off")
                return

            # 📝 تغییر متن خوش‌آمدگویی
            if (msg_low.startswith("!setwelcome ") or msg_low.startswith("!خوشامد ") or msg_low.startswith("!تنظیم_خوشامد ")) and self.is_user_admin(user):
                new_text = msg.split(" ", 1)[1].strip()
                if new_text:
                    self.welcome_text = new_text
                    self._save_data()
                    preview = self.welcome_text.replace("{user}", username)
                    await self.highrise.chat(f"📝 متن خوش‌آمدگویی تغییر کرد!\nپیش‌نمایش: {preview}")
                else:
                    await self.highrise.chat("❌ راهنما: !setwelcome <متن>  (از {user} برای اسم کاربر استفاده کن)\nمثال: !setwelcome سلام {user} خوش اومدی!")
                return

            if msg_low in ["!welcome", "!خوشامدگویی"]:
                await self.highrise.chat(f"📝 متن فعلی خوش‌آمدگویی: {self.welcome_text}")
                return


            # 1. ذخیره موقعیت بات (Save bot default position)
            if msg_low in ["!savebotloc", "!savebot", "!ثبت_بات"] and self.is_user_admin(user):
                pos = await self.get_user_pos(user_id)
                if pos:
                    self.saved_bot_position = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
                    self._save_data()
                    await self.highrise.chat(f"✅ جایگاه بات به صورت دائمی ثبت شد: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
                return

            # 2. اسپم ساده با ثانیه سفارشی (Persistent Spam Command)
            if msg_low.startswith("!spam ") and self.is_user_admin(user):
                parts = msg.split(" ", 2)
                if len(parts) >= 3 and parts[1].replace('.','',1).isdigit():
                    sec = float(parts[1])
                    text = parts[2].strip()
                    self.start_persistent_spam(text, sec)
                    await self.highrise.chat(f"🚀 اسپم شروع شد (هر {sec} ثانیه) - هنگام خاموش شدن ماندگار است.")
                else:
                    await self.highrise.chat("❌ راهنما: !spam [ثانیه] [متن]\nمثال: !spam 5 به روم ما خوش آمدید!")
                return

            if msg_low in ["!stopspam", "!توقف_اسپم"] and self.is_user_admin(user):
                self.stop_persistent_spam()
                await self.highrise.chat("🛑 اسپم متوقف و پاکسازی شد.")
                return

            if msg_low in ["!spamstatus", "!وضعیت_اسپم"] and self.is_user_admin(user):
                st = self.persistent_spam
                if st.get("active"):
                    await self.highrise.chat(f"🔄 اسپم فعال: هر {st['interval']}s ← {st['message']}")
                else:
                    await self.highrise.chat("❌ اسپمی فعال نیست.")
                return

            # 3. ذخیره نقاط دائمی (Save Permanent Named Location)
            if (msg_low.startswith("!save ") or msg_low.startswith("!saveloc ")) and self.is_user_admin(user):
                loc_name = msg.split(" ", 1)[1].strip().lower()
                pos = await self.get_user_pos(user_id)
                if pos:
                    self.locations[loc_name] = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
                    self._save_data()
                    await self.highrise.chat(f"📍 نقطه «{loc_name}» ثبت شد و پاک نخواهد شد! از الان هرکسی «{loc_name}» رو تایپ کنه به اینجا منتقل می‌شه ✨")
                else:
                    await self.highrise.chat("❌ نتوانستم موقعیت شما را دریافت کنم.")
                return

            if (msg_low.startswith("!delloc ") or msg_low.startswith("!removeloc ")) and self.is_user_admin(user):
                loc_name = msg.split(" ", 1)[1].strip().lower()
                if loc_name in self.locations:
                    del self.locations[loc_name]
                    self._save_data()
                    await self.highrise.chat(f"🗑️ نقطه «{loc_name}» حذف شد.")
                else:
                    await self.highrise.chat(f"❌ نقطه «{loc_name}» پیدا نشد.")
                return

            if msg_low in ["!locs", "!locations", "!نقاط"]:
                if self.locations:
                    loc_list = ", ".join([f"📍 {k}" for k in self.locations.keys()])
                    await self.highrise.chat(f"🗺️ نقاط ذخیره‌شده (کافیه اسمش رو تایپ کنید تا منتقل بشید):\n{loc_list}")
                else:
                    await self.highrise.chat("❌ هنوز هیچ نقطه‌ای ذخیره نشده است.")
                return

            # 4. رفتن به نقطه یا انتقال کاربر (Teleport & Bring)
            if (msg_low.startswith("!tp ") or msg_low.startswith("!go ")) and self.is_user_admin(user):
                target_str = msg.split(" ", 1)[1].strip()
                if target_str.startswith("@") or (" " not in target_str and target_str not in self.locations):
                    clean_name = target_str.replace("@", "").lower()
                    target_pos = None
                    ru = await self.highrise.get_room_users()
                    for u_item, p_item in ru.content:
                        if u_item.username.lower() == clean_name:
                            target_pos = p_item
                            break
                    if target_pos:
                        await self.highrise.teleport(user_id, target_pos)
                        await self.highrise.chat(f"✨ مالک به موقعیت @{clean_name} منتقل شد!")
                    else:
                        await self.highrise.chat(f"❌ کاربر @{clean_name} یا نقطه پیدا نشد.")
                    return
                elif target_str.lower() in self.locations:
                    loc = self.locations[target_str.lower()]
                    await self.highrise.teleport(user_id, Position(loc["x"], loc["y"], loc["z"], loc.get("facing", "FrontRight")))
                    await self.highrise.chat(f"🌀 رفتید به نقطه «{target_str}»!")
                    return

            # 5. دستور !bot یا !come (بات بیاید پیش مالک)
            if msg_low in ["!bot", "!come", "!بیا", "!بات"] and self.is_user_admin(user):
                pos = await self.get_user_pos(user_id)
                if pos:
                    if self.bot_id:
                        await self.highrise.teleport(self.bot_id, pos)
                    else:
                        await self.highrise.walk_to(pos)
                    await self.highrise.chat(f"🤖 بات اومد پیش شما @{username}!")
                return

            # 6. دستور !goto @user (رفتن مالک پیش یکی)
            if msg_low.startswith("!goto ") and self.is_user_admin(user):
                target_name = msg.split(" ", 1)[1].strip().replace("@", "").lower()
                ru = await self.highrise.get_room_users()
                target_pos = None
                for u_item, p_item in ru.content:
                    if u_item.username.lower() == target_name:
                        target_pos = p_item
                        break
                if target_pos:
                    await self.highrise.teleport(user_id, target_pos)
                    await self.highrise.chat(f"🚶 مالک رفت پیش @{target_name}!")
                else:
                    await self.highrise.chat(f"❌ کاربر @{target_name} پیدا نشد.")
                return

            # 🔐 ADMIN-ONLY LOCATIONS — این نقاط با !save عمومی فرق دارن و کاملاً جداست
            # فقط ادمین می‌تونه نقطه ثبت کنه و فقط ادمین می‌تونه کاربر رو به این نقاط ببره
            # هیچ کاربر عادی‌ای با تایپ اسم نقطه منتقل نمی‌شه (برخلاف self.locations عمومی)
            if (msg_low.startswith("!adminsave ") or msg_low.startswith("!ثبت_نقطه_ادمین ")) and self.is_user_admin(user):
                loc_name = msg.split(" ", 1)[1].strip().lower()
                pos = await self.get_user_pos(user_id)
                if pos:
                    self.admin_locations[loc_name] = {"x": pos.x, "y": pos.y, "z": pos.z, "facing": pos.facing}
                    self._save_data()
                    await self.highrise.chat(f"🔒 نقطه ادمین «{loc_name}» ثبت شد. فقط ادمین‌ها می‌تونن کاربران رو به این نقطه ببرن (با !bring {loc_name} @user).")
                else:
                    await self.highrise.chat("❌ نتوانستم موقعیت شما را دریافت کنم.")
                return

            if (msg_low.startswith("!deladminloc ") or msg_low.startswith("!حذف_نقطه_ادمین ")) and self.is_user_admin(user):
                loc_name = msg.split(" ", 1)[1].strip().lower()
                if loc_name in self.admin_locations:
                    del self.admin_locations[loc_name]
                    self._save_data()
                    await self.highrise.chat(f"🗑️ نقطه ادمین «{loc_name}» حذف شد.")
                else:
                    await self.highrise.chat(f"❌ نقطه ادمین «{loc_name}» پیدا نشد.")
                return

            if msg_low in ["!adminlocs", "!نقاط_ادمین"] and self.is_user_admin(user):
                if self.admin_locations:
                    names = "، ".join(self.admin_locations.keys())
                    await self.highrise.chat(f"🔒 نقاط ادمین: {names}")
                else:
                    await self.highrise.chat("❌ هنوز هیچ نقطه ادمینی ثبت نشده.")
                return

            if (msg_low.startswith("!bring ") or msg_low.startswith("!ببر ")) and self.is_user_admin(user):
                parts = msg.split(" ", 2)
                if len(parts) < 3:
                    await self.highrise.chat("❌ راهنما: !bring <نام_نقطه> @username  (یا !bring <نام_نقطه> all برای بردن همه)")
                    return
                loc_name = parts[1].strip().lower()
                target_raw = parts[2].strip().replace("@", "")
                if loc_name not in self.admin_locations:
                    await self.highrise.chat(f"❌ نقطه ادمین «{loc_name}» پیدا نشد. اول با !adminsave {loc_name} ثبتش کن.")
                    return
                loc = self.admin_locations[loc_name]
                dest = Position(loc["x"], loc["y"], loc["z"], loc.get("facing", "FrontRight"))
                try:
                    if target_raw.lower() == "all":
                        users_res = await self.highrise.get_room_users()
                        for u, _ in users_res.content:
                            try: await self.highrise.teleport(u.id, dest)
                            except Exception: pass
                        await self.highrise.chat(f"🔒 همه کاربران توسط ادمین به نقطه «{loc_name}» منتقل شدند.")
                    else:
                        target_id = None
                        users_res = await self.highrise.get_room_users()
                        for u, _ in users_res.content:
                            if u.username.lower() == target_raw.lower() or u.id == target_raw:
                                target_id = u.id
                                break
                        if not target_id:
                            await self.highrise.chat(f"❌ کاربر @{target_raw} در روم پیدا نشد.")
                            return
                        await self.highrise.teleport(target_id, dest)
                        await self.highrise.chat(f"🔒 @{target_raw} توسط ادمین به نقطه «{loc_name}» منتقل شد.")
                except Exception as e:
                    print(f"⚠️ Admin bring error: {e}")
                return

            # 💰 Economy & Daily
            if msg_low in ["!daily", "!جایزه"]:
                now = time.time()
                last = self.last_daily.get(user_id, 0)
                if now - last < 86400:
                    await self.highrise.chat(f"⏰ @{username} جایزه روزانه رو قبلا گرفتی!")
                    return
                bonus = 200
                self._add_gold(user_id, bonus)
                self.last_daily[user_id] = now
                self._save_data()
                await self.highrise.chat(f"🎁 @{username} جایزه روزانه ۲۰۰ گلد دریافت کرد!")
                return

            if msg_low in ["!balance", "!موجودی"]:
                g = self._get_gold(user_id)
                await self.highrise.chat(f"💰 موجودی @{username}: {g:,} گلد")
                return

                        # 🏃 Follow Commands (!follow, !فالو, !unfollow)
            if msg_low.startswith("!follow") or msg_low.startswith("!فالو") or msg_low in ["!فالو", "!follow"]:
                target_u = user_id
                parts = msg.split(" ", 1)
                if len(parts) > 1:
                    target_u = parts[1].replace("@", "").strip()
                await self.start_follow(target_u)
                await self.highrise.chat(f"🏃 بات در حال فالو کردن @{target_u} می‌باشد! ✨")
                return

            if msg_low in ["!unfollow", "!آنفالو", "!توقف_فالو", "!stopfollow"]:
                await self.stop_follow()
                await self.highrise.chat("⏹️ فالو متوقف شد.")
                return

            # 🎵 Universal Dance Handler
            is_explicit_dance = (
                msg_low in ["floss", "فلوس", "فلوس زدن", "دنس فلوس", "رقص فلوس", "سویج", "پوپولار", "استراحت", "شاپینگ", "تیکتاک", "کیوت", "زامبی", "ماکارنا"] or
                msg_low.startswith("!dance") or msg_low.startswith("!دنس") or msg_low.startswith("!رقص") or
                msg_low.startswith("dance") or msg_low.startswith("دنس") or msg_low.startswith("رقص") or
                msg_low.startswith("pr ") or msg_low.startswith("!emote") or msg_low.startswith("emote") or
                "high.rs" in msg_low or "item?id=" in msg_low or
                msg_low.startswith("dance-") or msg_low.startswith("emote-") or msg_low.startswith("idle")
            )

            converted_msg = msg
            for p, a, e in zip('۰۱۲۳۴۵۶۷۸۹', '٠١٢٣٤٥٦٧٨٩', '0123456789'):
                converted_msg = converted_msg.replace(p, e).replace(a, e)

            is_digit_dance = converted_msg.strip().isdigit()

            if is_explicit_dance or is_digit_dance:
                e_data = self.resolve_emote_data(msg)
                if e_data and e_data.get("id"):
                    await self.start_user_dance(user_id, e_data["id"])
                    await self.highrise.chat(f"🎭 دنس «{e_data.get('name', e_data['id'])}» برای @{username} اجرا شد! ✨")
                    return

            # 🤖 Direct AI Question in Chat (!ai or !سوال or !چت or بات/bot prefix)
            if msg_low.startswith("!ai ") or msg_low.startswith("!سوال ") or msg_low.startswith("!چت ") or msg_low.startswith("bot ") or msg_low.startswith("بات "):
                parts = msg.split(" ", 1)
                if len(parts) > 1:
                    ai_reply = await self.ask_ai_question(parts[1])
                    await self.highrise.chat(f"🤖 @{username}: {ai_reply}")
                return

            # 🎙️ Siri second trigger (catch-all at bottom too)
            if msg_low.startswith("!siri ") or msg_low.startswith("سیری ") or msg_low.startswith("siri "):
                parts = msg.split(" ", 1)
                q = parts[1].strip() if len(parts) > 1 else ""
                siri_reply = await self.ask_ai_question(q, siri_mode=True)
                await self.highrise.chat(f"🎙️ سیری → @{username}: {siri_reply}")
                return

            # Dance numbers — convert Persian/Arabic digits then check again
            converted_final = msg.strip()
            for p, a, e in zip('۰۱۲۳۴۵۶۷۸۹', '٠١٢٣٤٥٦٧٨٩', '0123456789'):
                converted_final = converted_final.replace(p, e).replace(a, e)
            if converted_final.isdigit():
                num = int(converted_final)
                if 1 <= num <= len(self.emotes):
                    e_obj = self.emotes[num - 1]
                    await self.start_user_dance(user_id, e_obj.id)
                    await self.highrise.chat(f"🎭 دنس شماره {num} ({e_obj.name}) برای @{username} اجرا شد! ✨")
                else:
                    await self.highrise.chat(f"⚠️ شماره دنس باید بین ۱ تا {len(self.emotes)} باشد.")
                return

        except Exception as e:
            print(f"Error on_chat: {e}")

    # User Join & Leave Events
    async def on_user_join(self, user: User, position) -> None:
        try:
            self.total_visitors += 1
            username = user.username
            user_id  = user.id
            self.user_name_cache[user_id] = username

            if user_id in self.banned_users:
                try: await self.highrise.moderate_room(user_id, "kick")
                except Exception: pass
                return

            welcome = self.welcome_text.replace("{user}", username)
            await self.highrise.chat(welcome)
            try: await self.highrise.send_emote("emote-wave", user_id)
            except Exception: pass
            try: await self.highrise.react(user_id, "heart")
            except Exception: pass
        except Exception as e:
            print(f"Join error: {e}")

# Launcher
def run_bot_instance():
    bot_configs = []
    if os.path.exists("bots_config.json"):
        try:
            with open("bots_config.json","r",encoding="utf-8") as f:
                raw = json.load(f)
            entries = raw if isinstance(raw, list) else ([{"room_id": k, **v} for k, v in raw.items()] if isinstance(raw, dict) else [])
            for entry in entries:
                r, t, a = str(entry.get("room_id","")).strip(), str(entry.get("api_token","")).strip(), str(entry.get("admin_username","parsapr")).strip()
                if r and t and "YOUR_" not in r:
                    bot_configs.append({"room_id":r,"api_token":t,"admin_username":a})
        except Exception as e: print(f"bots_config error: {e}")

    if not bot_configs:
        try:
            import tiba
            bot_configs.append({"room_id": tiba.ROOM_ID, "api_token": tiba.HIGHRISE_API_TOKEN, "admin_username": tiba.ADMIN_USERNAME})
        except ImportError: pass

    if not bot_configs:
        r, t, a = os.environ.get("ROOM_ID",""), os.environ.get("HIGHRISE_API_TOKEN",""), os.environ.get("ADMIN_USERNAME","parsapr")
        if r and t: bot_configs.append({"room_id":r,"api_token":t,"admin_username":a})

    if not bot_configs:
        print("❌ هیچ توکنی یافت نشد!")
        return

    definitions = []
    for idx, cfg in enumerate(bot_configs):
        bot = HighriseBot(room_id=f"{cfg['room_id']}_{idx}", bot_admins=[cfg['admin_username']], api_token=cfg['api_token'], real_room_id=cfg['room_id'])
        definitions.append(BotDefinition(bot, cfg['room_id'], cfg['api_token']))

    async def _run_loop():
        while True:
            try: await run_bot(definitions)
            except Exception as e:
                print(f"⚠️ Reconnecting in 5s: {e}")
                await asyncio.sleep(5)

    asyncio.run(_run_loop())

if __name__ == "__main__":
    start_keep_alive()
    run_bot_instance()

