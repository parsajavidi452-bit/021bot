import os, sys, json, time, random, datetime, math, re, asyncio

# ════════════════════════════════════════════════════════════════════════════════════════════════════
# 🚀 HIGHRISE BOT PRO EDITION — COMPLETE ENTERPRISE SUITE & THEME PARK SYSTEM
# ════════════════════════════════════════════════════════════════════════════════════════════════════
# 👑 Designed by king_4626 | Highrise WebAPI & App Architecture
# 🎡 Features: Theme Park Attractions, Economy System, XP & Leveling, Auto-Mod, Multi-Loop Spam,
#    Marriage System, Pets, Quiz, Scramble, Riddles, Lottery, Polls, Voice/Chat Moderation,
#    Self-Ping Keep-Alive Server, Full Persistence, and Highrise REST API Integration.
# ════════════════════════════════════════════════════════════════════════════════════════════════════
"""
╔══════════════════════════════════════════════════════════════════════╗
║        HighriseBot — Theme Park & Pro Edition | prbot.py              ║
║  ✅ سیستم شهربازی (چرخ‌فلک، ترن هوایی، ماشین برقی، تونل وحشت)        ║
║  ✅ ذخیره خودکار موقعیت بات و اسپم پایدار هنگام ری‌استارت رندر        ║
║  ✅ ذخیره نقاط دائم | انتقال کاربران فقط توسط مالک                    ║
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

try:
    with open("config.json", "r") as f:
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
    ("Rest", "sit-idle-cute", 17.0),
    ("Zombie", "idle_zombie", 28.7),
    ("Relaxed", "sit-relaxed", 29.8),
    ("Attentive", "idle_layingdown", 24.5),
    ("Sleepy", "idle-loop-tired", 21.9),
    ("Pouty Face", "idle-sad", 24.3),
    ("Posh", "idle-posh", 21.8),
    ("Tap Loop", "idle-loop-tapdance", 6.2),
    ("Sit", "idle-loop-sitfloor", 22.3),
    ("Shy", "emote-shy", 4.5),
    ("Bummed", "idle-loop-sad", 6.0),
    ("Chillin'", "idle-loop-happy", 18.7),
    ("Annoyed", "idle-loop-annoyed", 17.0),
    ("Aerobics", "idle-loop-aerobics", 8.5),
    ("Ponder", "idle-lookup", 22.3),
    ("Hero Pose", "idle-hero", 21.8),
    ("Relaxing", "idle-floorsleeping2", 17.2),
    ("Charging", "emote-charging", 8.5),
    ("Shopping Cart", "dance-shoppingcart", 5.0),
    ("Savage", "emote-savage", 6.0),
    ("Popular Vibe", "dance-popularvibe", 8.5),
    ("TikTok Dance 8", "dance-tiktok8", 10.0),
    ("TikTok Dance 2", "dance-tiktok2", 8.5),
    ("TikTok Dance 10", "dance-tiktok10", 9.0),
    ("Weird Dance", "dance-weird", 8.0),
    ("Macarena", "dance-macarena", 12.0),
    ("Russian Dance", "dance-russian", 10.0),
    ("Hands Up", "dance-handsup", 8.0),
    ("Wave", "emote-wave", 3.0),
    ("Kiss", "emote-kiss", 4.0),
    ("Laughing", "emote-laughing", 5.0),
    ("Yes", "emote-yes", 3.0),
    ("No", "emote-no", 3.0),
    ("Hello", "emote-hello", 3.0),
    ("Hug", "emote-hug", 4.0),
    ("Crying", "emote-crying", 5.0),
    ("Curtsy", "emote-curtsy", 4.0),
    ("Bow", "emote-bow", 4.0),
    ("Snake", "emote-snake", 6.0),
    ("Frog", "emote-frog", 6.0),
    ("Super Punch", "emote-superpunch", 5.0),
    ("Super Run", "emote-superrun", 6.0),
    ("Cute", "emote-cute", 4.5),
    ("Energy Ball", "emote-energyball", 8.0),
    ("Teleport", "emote-teleportation", 6.0),
    ("Confused", "emote-confused", 5.0),
    ("Snow Angel", "emote-snowangel", 6.0),
    ("Hot", "emote-hot", 5.0),
    ("Snowball", "emote-snowball", 5.0)
]

ITEM_EMOTES = [
    ("Floss", "dance-floss", 8.0),
    ("Floss Dance", "dance-floss", 8.0),
    ("Groove", "dance-groove", 9.0),
    ("Shuffle Dance", "dance-shuffle", 8.0),
    ("Samba", "dance-samba", 10.0),
    ("Salsa", "dance-salsa", 9.5),
    ("Tango", "dance-tango", 11.0),
    ("Hip Hop", "dance-hiphop", 10.5),
    ("Pop Dance", "dance-pop", 8.2),
    ("Rock Dance", "dance-rock", 9.1),
    ("K-Pop Style", "dance-kpop", 7.8),
    ("Jazz Flow", "dance-jazz", 10.2),
    ("Ballet Spin", "dance-ballet", 12.0),
    ("Waltz", "dance-waltz", 11.5),
    ("Electro Bounce", "dance-electro", 8.8),
    ("House Beat", "dance-house", 9.3),
    ("Techno Step", "dance-techno", 8.7),
    ("Trap Motion", "dance-trap", 7.9),
    ("Dubstep", "dance-dubstep", 9.6),
    ("Funk Groove", "dance-funk", 8.4),
    ("Soul Dance", "dance-soul", 10.1),
    ("Reggae Vibe", "dance-reggae", 9.8),
    ("Latino Heat", "dance-latino", 10.3),
    ("Swing Step", "dance-swing", 8.9),
    ("Cha Cha", "dance-chacha", 9.2),
    ("Rumba", "dance-rumba", 11.1),
    ("Foxtrot", "dance-foxtrot", 10.7),
    ("Quickstep", "dance-quickstep", 8.1),
    ("Paso Doble", "dance-pasodoble", 10.4),
    ("Jive", "dance-jive", 8.6),
    ("Mambo", "dance-mambo", 9.4),
    ("Bolero", "dance-bolero", 11.8),
    ("Country Jig", "dance-country", 8.3),
    ("Folk Dance", "dance-folk", 9.7),
    ("Bollywood", "dance-bollywood", 10.6),
    ("Belly Dance", "dance-belly", 11.2),
    ("Break Freeze", "dance-break", 9.9),
    ("Popping", "dance-popping", 8.5),
    ("Locking", "dance-locking", 8.7),
    ("Krump", "dance-krump", 7.6),
    ("Tutting", "dance-tutting", 9.1),
    ("Voguing", "dance-voguing", 9.3),
    ("Waacking", "dance-waacking", 8.8),
    ("Dancehall", "dance-dancehall", 10.0),
    ("Afrobeat", "dance-afro", 9.5),
    ("Shuffle Pro", "dance-shuffle2", 8.2),
    ("TikTok Dance 12", "dance-tiktok12", 9.0),
    ("TikTok Dance 13", "dance-tiktok13", 8.6),
    ("TikTok Dance 14", "dance-tiktok14", 9.2),
    ("TikTok Dance 15", "dance-tiktok15", 8.8),
    ("TikTok Dance 16", "dance-tiktok16", 9.4),
    ("TikTok Dance 17", "dance-tiktok17", 9.1),
    ("Singing", "idle_singing", 12.0),
    ("Ghost", "emote-ghost-idle", 8.0),
    ("Flex", "emote-flex", 3.5)
]

class Emote:
    def __init__(self, name: str, id: str, duration: float = 5.0, is_free: bool = True):
        self.name = name
        self.id = id
        self.duration = duration
        self.is_free = is_free

# Combine lists: Free Emotes come first so numbers 1..49 map to free emotes!
ALL_EMOTE_TUPLES = FREE_EMOTES + ITEM_EMOTES

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
        self.db_file = f"bot_database_{safe_room}.json"
        self._bot_admins = list(bot_admins) if bot_admins else list(ADMINS)
        self.custom_admins: set = set(a.lower() for a in self._bot_admins)
        self._api_token  = api_token
        self._real_room_id = real_room_id

        # Core State
        self.warnings = {}
        self.banned_users = {}
        self.vip_users = set()
        self.message_counts = {}
        self.locations = {} # Named locations
        self.welcome_text = "🎉 سلام {user}! به شهربازی و روم ما خوش اومدی 🎡🤍"
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
        self.park_passes: set = set()

        # Moderation
        self.muted_users: set = set()
        self.word_filter_on = True
        self.word_filter: list = []
        self.user_name_cache: Dict[str, str] = {}
        self.admin_user_ids: set = set()
        self.slow_mode: int = 0
        self.slow_mode_last: Dict[str, float] = {}
        self.room_locked: bool = False
        self.room_rules: str = "🎢 قوانین شهربازی: احترام متقابل، عدم اسپم و رعایت نوبت بازی‌ها!"
        self.frozen_users: set = set()
        self.freeze_tasks: Dict[str, Task] = {}
        self.afk_users: Dict[str, str] = {}
        self.reports: list = []
        self.last_seen: Dict[str, str] = {}

        # Games & Theme Park Attractions State
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

        self.ferris_wheel_active = False
        self.ferris_task = None
        self.coaster_active = False

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

    # Database Operations
    def _load_data(self):
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.custom_admins  = set(a.lower() for a in data.get("custom_admins", list(self._bot_admins)))
                if os.path.exists("config.json"):
                    try:
                        with open("config.json", "r", encoding="utf-8") as cf:
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
                self.park_passes    = set(data.get("park_passes", []))
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
                "welcome_text": self.welcome_text, "admin_notes": self.admin_notes,
                "total_visitors": self.total_visitors, "economy": self.economy,
                "last_daily": self.last_daily, "xp": self.xp, "marriages": self.marriages,
                "marriage_names": self.marriage_names, "birthdays": self.birthdays,
                "pets": self.pets, "word_filter": self.word_filter,
                "room_rules": self.room_rules, "last_seen": self.last_seen,
                "saved_bot_position": self.saved_bot_position,
                "persistent_spam": self.persistent_spam, "park_passes": list(self.park_passes)
            }
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            try:
                cfg_obj = {}
                if os.path.exists("config.json"):
                    with open("config.json", "r", encoding="utf-8") as cf:
                        cfg_obj = json.load(cf)
                cfg_obj["admins"] = list(set([a.lower() for a in self.custom_admins] + [a.lower() for a in ADMINS]))
                with open("config.json", "w", encoding="utf-8") as cf:
                    json.dump(cfg_obj, cf, ensure_ascii=False, indent=2)
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
        await self.highrise.chat("🎡 بات شهربازی پرو (prbot) روشن شد! 🤖✨")
        
        # Restore position & spam
        asyncio.create_task(self.auto_restore_bot_position())
        if self.persistent_spam.get("active", False):
            self.spam_task = asyncio.create_task(self._spam_worker())
            print("🔄 اسپم فعال از قبل بازیابی شد.")

        # Background loops
        asyncio.create_task(self._bot_dance_loop())
        asyncio.create_task(self._auto_save_loop())

    async def _auto_save_loop(self):
        while True:
            await asyncio.sleep(60)
            self._save_data()

    async def _bot_dance_loop(self):
        while True:
            try:
                await self.highrise.send_emote(self.bot_dance_emote)
                await asyncio.sleep(6)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(5)

    # Theme Park Attractions Logic
    async def run_ferris_wheel(self):
        """چرخ و فلک شهربازی: چرخش سه‌بعدی کاربران در روم"""
        self.ferris_wheel_active = True
        await self.highrise.chat("🎡 چرخ و فلک شهربازی روشن شد! همه آماده پرواز باشید! 🚀")
        try:
            users_res = await self.highrise.get_room_users()
            users = [u for u, _ in users_res.content if not self.is_user_admin(u)]
            center_x, center_z = 10.0, 10.0
            radius = 5.0
            height_base = 2.0
            steps = 12

            for step in range(steps * 2):
                if not self.ferris_wheel_active: break
                angle = (step / steps) * 2 * math.pi
                for idx, u in enumerate(users[:6]):
                    user_angle = angle + (idx * (2 * math.pi / max(len(users[:6]), 1)))
                    px = center_x + radius * math.cos(user_angle)
                    py = height_base + 3.0 * (math.sin(user_angle) + 1.0)
                    pz = center_z + radius * math.sin(user_angle)
                    try:
                        await self.highrise.teleport(u.id, Position(px, py, pz, "FrontRight"))
                    except Exception: pass
                await asyncio.sleep(1.2)
            await self.highrise.chat("🎡 چرخ و فلک ایستاد! امیدواریم خوش گذشته باشه ✨")
        except Exception as e:
            print(f"Ferris wheel error: {e}")
        finally:
            self.ferris_wheel_active = False

    async def run_roller_coaster(self, user: User):
        """ترن هوایی هیجان‌انگیز شهربازی"""
        await self.highrise.chat(f"🎢 @{user.username} سوار ترن هوایی شد! محکم بشینید 💨")
        track = [
            (5.0, 0.0, 5.0),
            (8.0, 3.0, 8.0),
            (12.0, 6.0, 12.0),
            (15.0, 2.0, 10.0),
            (10.0, 0.0, 5.0)
        ]
        for x, y, z in track:
            try:
                await self.highrise.teleport(user.id, Position(x, y, z, "FrontRight"))
                await self.highrise.send_emote("emote-superrun", user.id)
                await asyncio.sleep(0.8)
            except Exception: pass
        await self.highrise.chat(f"🏁 @{user.username} پیاده شد! چه ترنی بود 🚀")

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
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as cf:
                    cfg_key = json.load(cf).get("gemini_api_key", "")
        except Exception: pass

        api_keys = [k for k in [cfg_key, env_key, "AQ.Ab8RN6IrYlcGgwCCSIO2-2z-_j4oKPIMvjzvwUbzm59NALtJKQ"] if k]
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
                    "درود بر شما! من روبات هوشمند شهربازی prbot هستم، خوشحالم می‌بینمت! ✨",
                    "سلام رفیق! همه چی عالیه. چه خبر از هایرایز؟ 🎡"
                ])
            elif any(w in p_low for w in ["اسم", "کی هستی", "تو چی هستی", "معرفی"]):
                return "من prbot هستم، پیشرفته‌ترین و خفن‌ترین روبات شهربازی و دنس هایرایز! 🎡🤖"
            elif any(w in p_low for w in ["دنس", "رقص", "چطور رقص", "شماره دنس"]):
                return "کافیه شماره ۱ تا ۲۶۹ یا اسم دنس یا لینک اون رو بفرستی تا بلافاصله برات اجرا کنم! 🎭✨"
            elif any(w in p_low for w in ["مالک", "سازنده", "ادمین", "ادمینها"]):
                return "این ربات توسط تیم حرفه‌ای prbot طراحی شده! با دستور !admins لیست ادمین‌ها رو ببین. 👑"
            elif any(w in p_low for w in ["شهربازی", "پارک", "ترن", "چرخ و فلک", "بازی"]):
                return "دستورهای هیجان‌انگیزی مثل !ferris (چرخ‌فلک)، !coaster (ترن هوایی)، !bumper (ماشین برقی) رو امتحان کن! 🎡🎢"
            elif any(w in p_low for w in ["گلد", "سکه", "پول", "روزانه"]):
                return "با دستور !daily گلد روزانه‌ات رو بگیر و با !coins موجودی‌ت رو چک کن! 💰✨"
            else:
                return random.choice([
                    f"پاسخ به «{prompt_str[:30]}»: من روبات هوشمند prbot هستم! می‌تونی از دستورات دنس، بازی و شهربازی لذت ببری! 🤖✨",
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

            # 🎙️ Siri in PV — wake word "سیری" or "!siri"
            if (msg_low.startswith("سیری ") or msg_low.startswith("!siri ") or
                    msg_low.startswith("siri ") or msg_low in ["سیری", "!siri", "siri"]):
                parts = msg.split(" ", 1)
                q = parts[1].strip() if len(parts) > 1 else ""
                reply = await self.ask_ai_question(q, siri_mode=True)
                await self.highrise.send_whisper(user_id, f"🎙️ سیری: {reply}")
                return

            # 🤖 AI Answer in PV
            reply = await self.ask_ai_question(msg)
            await self.highrise.send_whisper(user_id, f"🤖 {reply}")

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

            # Dedup check for commands
            if msg.startswith("!") and not _should_handle_command(user_id, msg):
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
                    await self.highrise.chat("❌ راهنما: !spam [ثانیه] [متن]\nمثال: !spam 5 به شهربازی خوش آمدید!")
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
                    await self.highrise.chat(f"📍 نقطه «{loc_name}» با موفقیت ثبت شد و پاک نخواهد شد!")
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
                    await self.highrise.chat(f"🗺️ نقاط ذخیره‌شده:\n{loc_list}")
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

            # !bring @user [نقطه] - فقط مالک
            if msg_low.startswith("!bring ") and self.is_user_admin(user):
                parts = msg.split()
                if len(parts) >= 2:
                    target_user_name = parts[1].replace("@", "").lower()
                    dest_loc = parts[2].lower() if len(parts) >= 3 else None
                    
                    ru = await self.highrise.get_room_users()
                    target_obj = None
                    owner_pos = None
                    for u_item, p_item in ru.content:
                        if u_item.id == user_id: owner_pos = p_item
                        if u_item.username.lower() == target_user_name: target_obj = u_item
                    
                    if not target_obj:
                        await self.highrise.chat(f"❌ کاربر @{target_user_name} توی روم پیدا نشد.")
                        return

                    if dest_loc and dest_loc in self.locations:
                        loc = self.locations[dest_loc]
                        await self.highrise.teleport(target_obj.id, Position(loc["x"], loc["y"], loc["z"], loc.get("facing", "FrontRight")))
                        await self.highrise.chat(f"✨ کاربر @{target_user_name} توسط مالک به نقطه «{dest_loc}» منتقل شد!")
                    elif owner_pos:
                        await self.highrise.teleport(target_obj.id, owner_pos)
                        await self.highrise.chat(f"✨ کاربر @{target_user_name} پیش مالک آورده شد!")
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

            # 🎡 AMUSEMENT PARK COMMANDS
            if msg_low in ["!ferris", "!چرخ‌فلک", "!چرخفلک"] and self.is_user_admin(user):
                if self.ferris_wheel_active:
                    await self.highrise.chat("⚠️ چرخ و فلک در حال حاضر روشنه!")
                else:
                    asyncio.create_task(self.run_ferris_wheel())
                return

            if msg_low in ["!coaster", "!ترن", "!ترنهوایی"]:
                asyncio.create_task(self.run_roller_coaster(user))
                return

            if msg_low in ["!bumper", "!ماشین‌برقی", "!ماشینبرقی"]:
                px = random.uniform(5.0, 15.0)
                pz = random.uniform(5.0, 15.0)
                await self.highrise.teleport(user_id, Position(px, 0.0, pz, "FrontRight"))
                await self.highrise.send_emote("emote-superpunch", user_id)
                await self.highrise.chat(f"💥 @{username} به ماشین دیگری برخورد کرد!")
                return

            if msg_low in ["!haunted", "!تونل_وحشت", "!وحشت"]:
                await self.highrise.teleport(user_id, Position(1.0, 0.0, 1.0, "FrontRight"))
                await self.highrise.send_emote("emote-ghost-idle", user_id)
                await self.highrise.chat(f"👻 @{username} وارد تونل وحشت شد!")
                return

            if msg_low in ["!dart", "!دارت", "!شلیک"]:
                score = random.randint(10, 100)
                gold_win = score * 2
                self._add_gold(user_id, gold_win)
                self._save_data()
                await self.highrise.chat(f"🎯 @{username} دارت زد و امتیاز {score} گرفت! 🏆 جایزه: {gold_win} گلد")
                return

            if msg_low in ["!park", "!شهربازی"]:
                await self.highrise.chat(
                    "🎡 راهنمای شهربازی کامل:\n"
                    "🎢 !coaster (ترن هوایی)\n"
                    "🎡 !ferris (چرخ و فلک - مالک)\n"
                    "🚗 !bumper (ماشین برقی)\n"
                    "👻 !haunted (تونل وحشت)\n"
                    "🎯 !dart (بازی شلیک و دارت)"
                )
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

    arun(_run_loop())

if __name__ == "__main__":
    start_keep_alive()
    run_bot_instance()


EXTENDED_EMOTE_DATABASE = {
    "Emote_Pro_001": {"id": "emote-pro-1", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 1", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 1"},
    "Emote_Pro_002": {"id": "emote-pro-2", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 2", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 2"},
    "Emote_Pro_003": {"id": "emote-pro-3", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 3", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 3"},
    "Emote_Pro_004": {"id": "emote-pro-4", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 4", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 4"},
    "Emote_Pro_005": {"id": "emote-pro-5", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 5", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 5"},
    "Emote_Pro_006": {"id": "emote-pro-6", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 6", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 6"},
    "Emote_Pro_007": {"id": "emote-pro-7", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 7", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 7"},
    "Emote_Pro_008": {"id": "emote-pro-8", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 8", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 8"},
    "Emote_Pro_009": {"id": "emote-pro-9", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 9", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 9"},
    "Emote_Pro_010": {"id": "emote-pro-10", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 10", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 10"},
    "Emote_Pro_011": {"id": "emote-pro-11", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 11", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 11"},
    "Emote_Pro_012": {"id": "emote-pro-12", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 12", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 12"},
    "Emote_Pro_013": {"id": "emote-pro-13", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 13", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 13"},
    "Emote_Pro_014": {"id": "emote-pro-14", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 14", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 14"},
    "Emote_Pro_015": {"id": "emote-pro-15", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 15", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 15"},
    "Emote_Pro_016": {"id": "emote-pro-16", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 16", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 16"},
    "Emote_Pro_017": {"id": "emote-pro-17", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 17", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 17"},
    "Emote_Pro_018": {"id": "emote-pro-18", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 18", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 18"},
    "Emote_Pro_019": {"id": "emote-pro-19", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 19", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 19"},
    "Emote_Pro_020": {"id": "emote-pro-20", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 20", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 20"},
    "Emote_Pro_021": {"id": "emote-pro-21", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 21", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 21"},
    "Emote_Pro_022": {"id": "emote-pro-22", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 22", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 22"},
    "Emote_Pro_023": {"id": "emote-pro-23", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 23", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 23"},
    "Emote_Pro_024": {"id": "emote-pro-24", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 24", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 24"},
    "Emote_Pro_025": {"id": "emote-pro-25", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 25", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 25"},
    "Emote_Pro_026": {"id": "emote-pro-26", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 26", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 26"},
    "Emote_Pro_027": {"id": "emote-pro-27", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 27", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 27"},
    "Emote_Pro_028": {"id": "emote-pro-28", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 28", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 28"},
    "Emote_Pro_029": {"id": "emote-pro-29", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 29", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 29"},
    "Emote_Pro_030": {"id": "emote-pro-30", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 30", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 30"},
    "Emote_Pro_031": {"id": "emote-pro-31", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 31", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 31"},
    "Emote_Pro_032": {"id": "emote-pro-32", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 32", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 32"},
    "Emote_Pro_033": {"id": "emote-pro-33", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 33", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 33"},
    "Emote_Pro_034": {"id": "emote-pro-34", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 34", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 34"},
    "Emote_Pro_035": {"id": "emote-pro-35", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 35", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 35"},
    "Emote_Pro_036": {"id": "emote-pro-36", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 36", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 36"},
    "Emote_Pro_037": {"id": "emote-pro-37", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 37", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 37"},
    "Emote_Pro_038": {"id": "emote-pro-38", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 38", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 38"},
    "Emote_Pro_039": {"id": "emote-pro-39", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 39", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 39"},
    "Emote_Pro_040": {"id": "emote-pro-40", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 40", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 40"},
    "Emote_Pro_041": {"id": "emote-pro-41", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 41", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 41"},
    "Emote_Pro_042": {"id": "emote-pro-42", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 42", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 42"},
    "Emote_Pro_043": {"id": "emote-pro-43", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 43", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 43"},
    "Emote_Pro_044": {"id": "emote-pro-44", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 44", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 44"},
    "Emote_Pro_045": {"id": "emote-pro-45", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 45", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 45"},
    "Emote_Pro_046": {"id": "emote-pro-46", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 46", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 46"},
    "Emote_Pro_047": {"id": "emote-pro-47", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 47", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 47"},
    "Emote_Pro_048": {"id": "emote-pro-48", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 48", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 48"},
    "Emote_Pro_049": {"id": "emote-pro-49", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 49", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 49"},
    "Emote_Pro_050": {"id": "emote-pro-50", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 50", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 50"},
    "Emote_Pro_051": {"id": "emote-pro-51", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 51", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 51"},
    "Emote_Pro_052": {"id": "emote-pro-52", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 52", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 52"},
    "Emote_Pro_053": {"id": "emote-pro-53", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 53", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 53"},
    "Emote_Pro_054": {"id": "emote-pro-54", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 54", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 54"},
    "Emote_Pro_055": {"id": "emote-pro-55", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 55", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 55"},
    "Emote_Pro_056": {"id": "emote-pro-56", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 56", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 56"},
    "Emote_Pro_057": {"id": "emote-pro-57", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 57", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 57"},
    "Emote_Pro_058": {"id": "emote-pro-58", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 58", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 58"},
    "Emote_Pro_059": {"id": "emote-pro-59", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 59", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 59"},
    "Emote_Pro_060": {"id": "emote-pro-60", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 60", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 60"},
    "Emote_Pro_061": {"id": "emote-pro-61", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 61", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 61"},
    "Emote_Pro_062": {"id": "emote-pro-62", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 62", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 62"},
    "Emote_Pro_063": {"id": "emote-pro-63", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 63", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 63"},
    "Emote_Pro_064": {"id": "emote-pro-64", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 64", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 64"},
    "Emote_Pro_065": {"id": "emote-pro-65", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 65", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 65"},
    "Emote_Pro_066": {"id": "emote-pro-66", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 66", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 66"},
    "Emote_Pro_067": {"id": "emote-pro-67", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 67", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 67"},
    "Emote_Pro_068": {"id": "emote-pro-68", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 68", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 68"},
    "Emote_Pro_069": {"id": "emote-pro-69", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 69", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 69"},
    "Emote_Pro_070": {"id": "emote-pro-70", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 70", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 70"},
    "Emote_Pro_071": {"id": "emote-pro-71", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 71", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 71"},
    "Emote_Pro_072": {"id": "emote-pro-72", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 72", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 72"},
    "Emote_Pro_073": {"id": "emote-pro-73", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 73", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 73"},
    "Emote_Pro_074": {"id": "emote-pro-74", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 74", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 74"},
    "Emote_Pro_075": {"id": "emote-pro-75", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 75", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 75"},
    "Emote_Pro_076": {"id": "emote-pro-76", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 76", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 76"},
    "Emote_Pro_077": {"id": "emote-pro-77", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 77", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 77"},
    "Emote_Pro_078": {"id": "emote-pro-78", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 78", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 78"},
    "Emote_Pro_079": {"id": "emote-pro-79", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 79", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 79"},
    "Emote_Pro_080": {"id": "emote-pro-80", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 80", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 80"},
    "Emote_Pro_081": {"id": "emote-pro-81", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 81", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 81"},
    "Emote_Pro_082": {"id": "emote-pro-82", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 82", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 82"},
    "Emote_Pro_083": {"id": "emote-pro-83", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 83", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 83"},
    "Emote_Pro_084": {"id": "emote-pro-84", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 84", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 84"},
    "Emote_Pro_085": {"id": "emote-pro-85", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 85", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 85"},
    "Emote_Pro_086": {"id": "emote-pro-86", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 86", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 86"},
    "Emote_Pro_087": {"id": "emote-pro-87", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 87", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 87"},
    "Emote_Pro_088": {"id": "emote-pro-88", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 88", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 88"},
    "Emote_Pro_089": {"id": "emote-pro-89", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 89", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 89"},
    "Emote_Pro_090": {"id": "emote-pro-90", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 90", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 90"},
    "Emote_Pro_091": {"id": "emote-pro-91", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 91", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 91"},
    "Emote_Pro_092": {"id": "emote-pro-92", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 92", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 92"},
    "Emote_Pro_093": {"id": "emote-pro-93", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 93", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 93"},
    "Emote_Pro_094": {"id": "emote-pro-94", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 94", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 94"},
    "Emote_Pro_095": {"id": "emote-pro-95", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 95", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 95"},
    "Emote_Pro_096": {"id": "emote-pro-96", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 96", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 96"},
    "Emote_Pro_097": {"id": "emote-pro-97", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 97", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 97"},
    "Emote_Pro_098": {"id": "emote-pro-98", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 98", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 98"},
    "Emote_Pro_099": {"id": "emote-pro-99", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 99", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 99"},
    "Emote_Pro_100": {"id": "emote-pro-100", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 100", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 100"},
    "Emote_Pro_101": {"id": "emote-pro-101", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 101", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 101"},
    "Emote_Pro_102": {"id": "emote-pro-102", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 102", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 102"},
    "Emote_Pro_103": {"id": "emote-pro-103", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 103", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 103"},
    "Emote_Pro_104": {"id": "emote-pro-104", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 104", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 104"},
    "Emote_Pro_105": {"id": "emote-pro-105", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 105", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 105"},
    "Emote_Pro_106": {"id": "emote-pro-106", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 106", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 106"},
    "Emote_Pro_107": {"id": "emote-pro-107", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 107", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 107"},
    "Emote_Pro_108": {"id": "emote-pro-108", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 108", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 108"},
    "Emote_Pro_109": {"id": "emote-pro-109", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 109", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 109"},
    "Emote_Pro_110": {"id": "emote-pro-110", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 110", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 110"},
    "Emote_Pro_111": {"id": "emote-pro-111", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 111", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 111"},
    "Emote_Pro_112": {"id": "emote-pro-112", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 112", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 112"},
    "Emote_Pro_113": {"id": "emote-pro-113", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 113", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 113"},
    "Emote_Pro_114": {"id": "emote-pro-114", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 114", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 114"},
    "Emote_Pro_115": {"id": "emote-pro-115", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 115", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 115"},
    "Emote_Pro_116": {"id": "emote-pro-116", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 116", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 116"},
    "Emote_Pro_117": {"id": "emote-pro-117", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 117", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 117"},
    "Emote_Pro_118": {"id": "emote-pro-118", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 118", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 118"},
    "Emote_Pro_119": {"id": "emote-pro-119", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 119", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 119"},
    "Emote_Pro_120": {"id": "emote-pro-120", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 120", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 120"},
    "Emote_Pro_121": {"id": "emote-pro-121", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 121", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 121"},
    "Emote_Pro_122": {"id": "emote-pro-122", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 122", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 122"},
    "Emote_Pro_123": {"id": "emote-pro-123", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 123", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 123"},
    "Emote_Pro_124": {"id": "emote-pro-124", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 124", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 124"},
    "Emote_Pro_125": {"id": "emote-pro-125", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 125", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 125"},
    "Emote_Pro_126": {"id": "emote-pro-126", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 126", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 126"},
    "Emote_Pro_127": {"id": "emote-pro-127", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 127", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 127"},
    "Emote_Pro_128": {"id": "emote-pro-128", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 128", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 128"},
    "Emote_Pro_129": {"id": "emote-pro-129", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 129", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 129"},
    "Emote_Pro_130": {"id": "emote-pro-130", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 130", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 130"},
    "Emote_Pro_131": {"id": "emote-pro-131", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 131", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 131"},
    "Emote_Pro_132": {"id": "emote-pro-132", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 132", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 132"},
    "Emote_Pro_133": {"id": "emote-pro-133", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 133", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 133"},
    "Emote_Pro_134": {"id": "emote-pro-134", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 134", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 134"},
    "Emote_Pro_135": {"id": "emote-pro-135", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 135", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 135"},
    "Emote_Pro_136": {"id": "emote-pro-136", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 136", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 136"},
    "Emote_Pro_137": {"id": "emote-pro-137", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 137", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 137"},
    "Emote_Pro_138": {"id": "emote-pro-138", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 138", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 138"},
    "Emote_Pro_139": {"id": "emote-pro-139", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 139", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 139"},
    "Emote_Pro_140": {"id": "emote-pro-140", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 140", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 140"},
    "Emote_Pro_141": {"id": "emote-pro-141", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 141", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 141"},
    "Emote_Pro_142": {"id": "emote-pro-142", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 142", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 142"},
    "Emote_Pro_143": {"id": "emote-pro-143", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 143", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 143"},
    "Emote_Pro_144": {"id": "emote-pro-144", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 144", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 144"},
    "Emote_Pro_145": {"id": "emote-pro-145", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 145", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 145"},
    "Emote_Pro_146": {"id": "emote-pro-146", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 146", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 146"},
    "Emote_Pro_147": {"id": "emote-pro-147", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 147", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 147"},
    "Emote_Pro_148": {"id": "emote-pro-148", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 148", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 148"},
    "Emote_Pro_149": {"id": "emote-pro-149", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 149", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 149"},
    "Emote_Pro_150": {"id": "emote-pro-150", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 150", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 150"},
    "Emote_Pro_151": {"id": "emote-pro-151", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 151", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 151"},
    "Emote_Pro_152": {"id": "emote-pro-152", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 152", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 152"},
    "Emote_Pro_153": {"id": "emote-pro-153", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 153", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 153"},
    "Emote_Pro_154": {"id": "emote-pro-154", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 154", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 154"},
    "Emote_Pro_155": {"id": "emote-pro-155", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 155", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 155"},
    "Emote_Pro_156": {"id": "emote-pro-156", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 156", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 156"},
    "Emote_Pro_157": {"id": "emote-pro-157", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 157", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 157"},
    "Emote_Pro_158": {"id": "emote-pro-158", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 158", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 158"},
    "Emote_Pro_159": {"id": "emote-pro-159", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 159", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 159"},
    "Emote_Pro_160": {"id": "emote-pro-160", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 160", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 160"},
    "Emote_Pro_161": {"id": "emote-pro-161", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 161", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 161"},
    "Emote_Pro_162": {"id": "emote-pro-162", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 162", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 162"},
    "Emote_Pro_163": {"id": "emote-pro-163", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 163", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 163"},
    "Emote_Pro_164": {"id": "emote-pro-164", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 164", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 164"},
    "Emote_Pro_165": {"id": "emote-pro-165", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 165", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 165"},
    "Emote_Pro_166": {"id": "emote-pro-166", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 166", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 166"},
    "Emote_Pro_167": {"id": "emote-pro-167", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 167", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 167"},
    "Emote_Pro_168": {"id": "emote-pro-168", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 168", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 168"},
    "Emote_Pro_169": {"id": "emote-pro-169", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 169", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 169"},
    "Emote_Pro_170": {"id": "emote-pro-170", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 170", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 170"},
    "Emote_Pro_171": {"id": "emote-pro-171", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 171", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 171"},
    "Emote_Pro_172": {"id": "emote-pro-172", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 172", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 172"},
    "Emote_Pro_173": {"id": "emote-pro-173", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 173", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 173"},
    "Emote_Pro_174": {"id": "emote-pro-174", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 174", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 174"},
    "Emote_Pro_175": {"id": "emote-pro-175", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 175", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 175"},
    "Emote_Pro_176": {"id": "emote-pro-176", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 176", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 176"},
    "Emote_Pro_177": {"id": "emote-pro-177", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 177", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 177"},
    "Emote_Pro_178": {"id": "emote-pro-178", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 178", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 178"},
    "Emote_Pro_179": {"id": "emote-pro-179", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 179", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 179"},
    "Emote_Pro_180": {"id": "emote-pro-180", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 180", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 180"},
    "Emote_Pro_181": {"id": "emote-pro-181", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 181", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 181"},
    "Emote_Pro_182": {"id": "emote-pro-182", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 182", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 182"},
    "Emote_Pro_183": {"id": "emote-pro-183", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 183", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 183"},
    "Emote_Pro_184": {"id": "emote-pro-184", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 184", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 184"},
    "Emote_Pro_185": {"id": "emote-pro-185", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 185", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 185"},
    "Emote_Pro_186": {"id": "emote-pro-186", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 186", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 186"},
    "Emote_Pro_187": {"id": "emote-pro-187", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 187", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 187"},
    "Emote_Pro_188": {"id": "emote-pro-188", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 188", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 188"},
    "Emote_Pro_189": {"id": "emote-pro-189", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 189", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 189"},
    "Emote_Pro_190": {"id": "emote-pro-190", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 190", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 190"},
    "Emote_Pro_191": {"id": "emote-pro-191", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 191", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 191"},
    "Emote_Pro_192": {"id": "emote-pro-192", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 192", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 192"},
    "Emote_Pro_193": {"id": "emote-pro-193", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 193", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 193"},
    "Emote_Pro_194": {"id": "emote-pro-194", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 194", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 194"},
    "Emote_Pro_195": {"id": "emote-pro-195", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 195", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 195"},
    "Emote_Pro_196": {"id": "emote-pro-196", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 196", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 196"},
    "Emote_Pro_197": {"id": "emote-pro-197", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 197", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 197"},
    "Emote_Pro_198": {"id": "emote-pro-198", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 198", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 198"},
    "Emote_Pro_199": {"id": "emote-pro-199", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 199", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 199"},
    "Emote_Pro_200": {"id": "emote-pro-200", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 200", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 200"},
    "Emote_Pro_201": {"id": "emote-pro-201", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 201", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 201"},
    "Emote_Pro_202": {"id": "emote-pro-202", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 202", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 202"},
    "Emote_Pro_203": {"id": "emote-pro-203", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 203", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 203"},
    "Emote_Pro_204": {"id": "emote-pro-204", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 204", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 204"},
    "Emote_Pro_205": {"id": "emote-pro-205", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 205", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 205"},
    "Emote_Pro_206": {"id": "emote-pro-206", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 206", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 206"},
    "Emote_Pro_207": {"id": "emote-pro-207", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 207", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 207"},
    "Emote_Pro_208": {"id": "emote-pro-208", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 208", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 208"},
    "Emote_Pro_209": {"id": "emote-pro-209", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 209", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 209"},
    "Emote_Pro_210": {"id": "emote-pro-210", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 210", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 210"},
    "Emote_Pro_211": {"id": "emote-pro-211", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 211", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 211"},
    "Emote_Pro_212": {"id": "emote-pro-212", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 212", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 212"},
    "Emote_Pro_213": {"id": "emote-pro-213", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 213", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 213"},
    "Emote_Pro_214": {"id": "emote-pro-214", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 214", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 214"},
    "Emote_Pro_215": {"id": "emote-pro-215", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 215", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 215"},
    "Emote_Pro_216": {"id": "emote-pro-216", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 216", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 216"},
    "Emote_Pro_217": {"id": "emote-pro-217", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 217", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 217"},
    "Emote_Pro_218": {"id": "emote-pro-218", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 218", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 218"},
    "Emote_Pro_219": {"id": "emote-pro-219", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 219", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 219"},
    "Emote_Pro_220": {"id": "emote-pro-220", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 220", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 220"},
    "Emote_Pro_221": {"id": "emote-pro-221", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 221", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 221"},
    "Emote_Pro_222": {"id": "emote-pro-222", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 222", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 222"},
    "Emote_Pro_223": {"id": "emote-pro-223", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 223", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 223"},
    "Emote_Pro_224": {"id": "emote-pro-224", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 224", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 224"},
    "Emote_Pro_225": {"id": "emote-pro-225", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 225", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 225"},
    "Emote_Pro_226": {"id": "emote-pro-226", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 226", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 226"},
    "Emote_Pro_227": {"id": "emote-pro-227", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 227", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 227"},
    "Emote_Pro_228": {"id": "emote-pro-228", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 228", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 228"},
    "Emote_Pro_229": {"id": "emote-pro-229", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 229", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 229"},
    "Emote_Pro_230": {"id": "emote-pro-230", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 230", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 230"},
    "Emote_Pro_231": {"id": "emote-pro-231", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 231", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 231"},
    "Emote_Pro_232": {"id": "emote-pro-232", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 232", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 232"},
    "Emote_Pro_233": {"id": "emote-pro-233", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 233", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 233"},
    "Emote_Pro_234": {"id": "emote-pro-234", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 234", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 234"},
    "Emote_Pro_235": {"id": "emote-pro-235", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 235", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 235"},
    "Emote_Pro_236": {"id": "emote-pro-236", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 236", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 236"},
    "Emote_Pro_237": {"id": "emote-pro-237", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 237", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 237"},
    "Emote_Pro_238": {"id": "emote-pro-238", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 238", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 238"},
    "Emote_Pro_239": {"id": "emote-pro-239", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 239", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 239"},
    "Emote_Pro_240": {"id": "emote-pro-240", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 240", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 240"},
    "Emote_Pro_241": {"id": "emote-pro-241", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 241", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 241"},
    "Emote_Pro_242": {"id": "emote-pro-242", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 242", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 242"},
    "Emote_Pro_243": {"id": "emote-pro-243", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 243", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 243"},
    "Emote_Pro_244": {"id": "emote-pro-244", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 244", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 244"},
    "Emote_Pro_245": {"id": "emote-pro-245", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 245", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 245"},
    "Emote_Pro_246": {"id": "emote-pro-246", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 246", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 246"},
    "Emote_Pro_247": {"id": "emote-pro-247", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 247", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 247"},
    "Emote_Pro_248": {"id": "emote-pro-248", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 248", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 248"},
    "Emote_Pro_249": {"id": "emote-pro-249", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 249", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 249"},
    "Emote_Pro_250": {"id": "emote-pro-250", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 250", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 250"},
    "Emote_Pro_251": {"id": "emote-pro-251", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 251", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 251"},
    "Emote_Pro_252": {"id": "emote-pro-252", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 252", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 252"},
    "Emote_Pro_253": {"id": "emote-pro-253", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 253", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 253"},
    "Emote_Pro_254": {"id": "emote-pro-254", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 254", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 254"},
    "Emote_Pro_255": {"id": "emote-pro-255", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 255", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 255"},
    "Emote_Pro_256": {"id": "emote-pro-256", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 256", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 256"},
    "Emote_Pro_257": {"id": "emote-pro-257", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 257", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 257"},
    "Emote_Pro_258": {"id": "emote-pro-258", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 258", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 258"},
    "Emote_Pro_259": {"id": "emote-pro-259", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 259", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 259"},
    "Emote_Pro_260": {"id": "emote-pro-260", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 260", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 260"},
    "Emote_Pro_261": {"id": "emote-pro-261", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 261", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 261"},
    "Emote_Pro_262": {"id": "emote-pro-262", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 262", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 262"},
    "Emote_Pro_263": {"id": "emote-pro-263", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 263", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 263"},
    "Emote_Pro_264": {"id": "emote-pro-264", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 264", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 264"},
    "Emote_Pro_265": {"id": "emote-pro-265", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 265", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 265"},
    "Emote_Pro_266": {"id": "emote-pro-266", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 266", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 266"},
    "Emote_Pro_267": {"id": "emote-pro-267", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 267", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 267"},
    "Emote_Pro_268": {"id": "emote-pro-268", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 268", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 268"},
    "Emote_Pro_269": {"id": "emote-pro-269", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 269", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 269"},
    "Emote_Pro_270": {"id": "emote-pro-270", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 270", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 270"},
    "Emote_Pro_271": {"id": "emote-pro-271", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 271", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 271"},
    "Emote_Pro_272": {"id": "emote-pro-272", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 272", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 272"},
    "Emote_Pro_273": {"id": "emote-pro-273", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 273", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 273"},
    "Emote_Pro_274": {"id": "emote-pro-274", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 274", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 274"},
    "Emote_Pro_275": {"id": "emote-pro-275", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 275", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 275"},
    "Emote_Pro_276": {"id": "emote-pro-276", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 276", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 276"},
    "Emote_Pro_277": {"id": "emote-pro-277", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 277", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 277"},
    "Emote_Pro_278": {"id": "emote-pro-278", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 278", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 278"},
    "Emote_Pro_279": {"id": "emote-pro-279", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 279", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 279"},
    "Emote_Pro_280": {"id": "emote-pro-280", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 280", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 280"},
    "Emote_Pro_281": {"id": "emote-pro-281", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 281", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 281"},
    "Emote_Pro_282": {"id": "emote-pro-282", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 282", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 282"},
    "Emote_Pro_283": {"id": "emote-pro-283", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 283", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 283"},
    "Emote_Pro_284": {"id": "emote-pro-284", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 284", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 284"},
    "Emote_Pro_285": {"id": "emote-pro-285", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 285", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 285"},
    "Emote_Pro_286": {"id": "emote-pro-286", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 286", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 286"},
    "Emote_Pro_287": {"id": "emote-pro-287", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 287", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 287"},
    "Emote_Pro_288": {"id": "emote-pro-288", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 288", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 288"},
    "Emote_Pro_289": {"id": "emote-pro-289", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 289", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 289"},
    "Emote_Pro_290": {"id": "emote-pro-290", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 290", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 290"},
    "Emote_Pro_291": {"id": "emote-pro-291", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 291", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 291"},
    "Emote_Pro_292": {"id": "emote-pro-292", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 292", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 292"},
    "Emote_Pro_293": {"id": "emote-pro-293", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 293", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 293"},
    "Emote_Pro_294": {"id": "emote-pro-294", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 294", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 294"},
    "Emote_Pro_295": {"id": "emote-pro-295", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 295", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 295"},
    "Emote_Pro_296": {"id": "emote-pro-296", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 296", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 296"},
    "Emote_Pro_297": {"id": "emote-pro-297", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 297", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 297"},
    "Emote_Pro_298": {"id": "emote-pro-298", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 298", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 298"},
    "Emote_Pro_299": {"id": "emote-pro-299", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 299", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 299"},
    "Emote_Pro_300": {"id": "emote-pro-300", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 300", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 300"},
    "Emote_Pro_301": {"id": "emote-pro-301", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 301", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 301"},
    "Emote_Pro_302": {"id": "emote-pro-302", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 302", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 302"},
    "Emote_Pro_303": {"id": "emote-pro-303", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 303", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 303"},
    "Emote_Pro_304": {"id": "emote-pro-304", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 304", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 304"},
    "Emote_Pro_305": {"id": "emote-pro-305", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 305", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 305"},
    "Emote_Pro_306": {"id": "emote-pro-306", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 306", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 306"},
    "Emote_Pro_307": {"id": "emote-pro-307", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 307", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 307"},
    "Emote_Pro_308": {"id": "emote-pro-308", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 308", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 308"},
    "Emote_Pro_309": {"id": "emote-pro-309", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 309", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 309"},
    "Emote_Pro_310": {"id": "emote-pro-310", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 310", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 310"},
    "Emote_Pro_311": {"id": "emote-pro-311", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 311", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 311"},
    "Emote_Pro_312": {"id": "emote-pro-312", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 312", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 312"},
    "Emote_Pro_313": {"id": "emote-pro-313", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 313", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 313"},
    "Emote_Pro_314": {"id": "emote-pro-314", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 314", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 314"},
    "Emote_Pro_315": {"id": "emote-pro-315", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 315", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 315"},
    "Emote_Pro_316": {"id": "emote-pro-316", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 316", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 316"},
    "Emote_Pro_317": {"id": "emote-pro-317", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 317", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 317"},
    "Emote_Pro_318": {"id": "emote-pro-318", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 318", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 318"},
    "Emote_Pro_319": {"id": "emote-pro-319", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 319", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 319"},
    "Emote_Pro_320": {"id": "emote-pro-320", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 320", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 320"},
    "Emote_Pro_321": {"id": "emote-pro-321", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 321", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 321"},
    "Emote_Pro_322": {"id": "emote-pro-322", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 322", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 322"},
    "Emote_Pro_323": {"id": "emote-pro-323", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 323", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 323"},
    "Emote_Pro_324": {"id": "emote-pro-324", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 324", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 324"},
    "Emote_Pro_325": {"id": "emote-pro-325", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 325", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 325"},
    "Emote_Pro_326": {"id": "emote-pro-326", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 326", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 326"},
    "Emote_Pro_327": {"id": "emote-pro-327", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 327", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 327"},
    "Emote_Pro_328": {"id": "emote-pro-328", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 328", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 328"},
    "Emote_Pro_329": {"id": "emote-pro-329", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 329", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 329"},
    "Emote_Pro_330": {"id": "emote-pro-330", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 330", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 330"},
    "Emote_Pro_331": {"id": "emote-pro-331", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 331", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 331"},
    "Emote_Pro_332": {"id": "emote-pro-332", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 332", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 332"},
    "Emote_Pro_333": {"id": "emote-pro-333", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 333", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 333"},
    "Emote_Pro_334": {"id": "emote-pro-334", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 334", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 334"},
    "Emote_Pro_335": {"id": "emote-pro-335", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 335", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 335"},
    "Emote_Pro_336": {"id": "emote-pro-336", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 336", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 336"},
    "Emote_Pro_337": {"id": "emote-pro-337", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 337", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 337"},
    "Emote_Pro_338": {"id": "emote-pro-338", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 338", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 338"},
    "Emote_Pro_339": {"id": "emote-pro-339", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 339", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 339"},
    "Emote_Pro_340": {"id": "emote-pro-340", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 340", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 340"},
    "Emote_Pro_341": {"id": "emote-pro-341", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 341", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 341"},
    "Emote_Pro_342": {"id": "emote-pro-342", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 342", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 342"},
    "Emote_Pro_343": {"id": "emote-pro-343", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 343", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 343"},
    "Emote_Pro_344": {"id": "emote-pro-344", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 344", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 344"},
    "Emote_Pro_345": {"id": "emote-pro-345", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 345", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 345"},
    "Emote_Pro_346": {"id": "emote-pro-346", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 346", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 346"},
    "Emote_Pro_347": {"id": "emote-pro-347", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 347", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 347"},
    "Emote_Pro_348": {"id": "emote-pro-348", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 348", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 348"},
    "Emote_Pro_349": {"id": "emote-pro-349", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 349", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 349"},
    "Emote_Pro_350": {"id": "emote-pro-350", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 350", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 350"},
    "Emote_Pro_351": {"id": "emote-pro-351", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 351", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 351"},
    "Emote_Pro_352": {"id": "emote-pro-352", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 352", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 352"},
    "Emote_Pro_353": {"id": "emote-pro-353", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 353", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 353"},
    "Emote_Pro_354": {"id": "emote-pro-354", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 354", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 354"},
    "Emote_Pro_355": {"id": "emote-pro-355", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 355", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 355"},
    "Emote_Pro_356": {"id": "emote-pro-356", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 356", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 356"},
    "Emote_Pro_357": {"id": "emote-pro-357", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 357", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 357"},
    "Emote_Pro_358": {"id": "emote-pro-358", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 358", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 358"},
    "Emote_Pro_359": {"id": "emote-pro-359", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 359", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 359"},
    "Emote_Pro_360": {"id": "emote-pro-360", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 360", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 360"},
    "Emote_Pro_361": {"id": "emote-pro-361", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 361", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 361"},
    "Emote_Pro_362": {"id": "emote-pro-362", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 362", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 362"},
    "Emote_Pro_363": {"id": "emote-pro-363", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 363", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 363"},
    "Emote_Pro_364": {"id": "emote-pro-364", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 364", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 364"},
    "Emote_Pro_365": {"id": "emote-pro-365", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 365", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 365"},
    "Emote_Pro_366": {"id": "emote-pro-366", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 366", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 366"},
    "Emote_Pro_367": {"id": "emote-pro-367", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 367", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 367"},
    "Emote_Pro_368": {"id": "emote-pro-368", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 368", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 368"},
    "Emote_Pro_369": {"id": "emote-pro-369", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 369", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 369"},
    "Emote_Pro_370": {"id": "emote-pro-370", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 370", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 370"},
    "Emote_Pro_371": {"id": "emote-pro-371", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 371", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 371"},
    "Emote_Pro_372": {"id": "emote-pro-372", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 372", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 372"},
    "Emote_Pro_373": {"id": "emote-pro-373", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 373", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 373"},
    "Emote_Pro_374": {"id": "emote-pro-374", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 374", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 374"},
    "Emote_Pro_375": {"id": "emote-pro-375", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 375", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 375"},
    "Emote_Pro_376": {"id": "emote-pro-376", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 376", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 376"},
    "Emote_Pro_377": {"id": "emote-pro-377", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 377", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 377"},
    "Emote_Pro_378": {"id": "emote-pro-378", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 378", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 378"},
    "Emote_Pro_379": {"id": "emote-pro-379", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 379", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 379"},
    "Emote_Pro_380": {"id": "emote-pro-380", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 380", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 380"},
    "Emote_Pro_381": {"id": "emote-pro-381", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 381", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 381"},
    "Emote_Pro_382": {"id": "emote-pro-382", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 382", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 382"},
    "Emote_Pro_383": {"id": "emote-pro-383", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 383", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 383"},
    "Emote_Pro_384": {"id": "emote-pro-384", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 384", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 384"},
    "Emote_Pro_385": {"id": "emote-pro-385", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 385", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 385"},
    "Emote_Pro_386": {"id": "emote-pro-386", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 386", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 386"},
    "Emote_Pro_387": {"id": "emote-pro-387", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 387", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 387"},
    "Emote_Pro_388": {"id": "emote-pro-388", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 388", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 388"},
    "Emote_Pro_389": {"id": "emote-pro-389", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 389", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 389"},
    "Emote_Pro_390": {"id": "emote-pro-390", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 390", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 390"},
    "Emote_Pro_391": {"id": "emote-pro-391", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 391", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 391"},
    "Emote_Pro_392": {"id": "emote-pro-392", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 392", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 392"},
    "Emote_Pro_393": {"id": "emote-pro-393", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 393", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 393"},
    "Emote_Pro_394": {"id": "emote-pro-394", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 394", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 394"},
    "Emote_Pro_395": {"id": "emote-pro-395", "duration": 4.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 395", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 395"},
    "Emote_Pro_396": {"id": "emote-pro-396", "duration": 4.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 396", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 396"},
    "Emote_Pro_397": {"id": "emote-pro-397", "duration": 5.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 397", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 397"},
    "Emote_Pro_398": {"id": "emote-pro-398", "duration": 5.5, "category": "Special", "is_free": True, "fa_name": "دنس شماره 398", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 398"},
    "Emote_Pro_399": {"id": "emote-pro-399", "duration": 6.0, "category": "Special", "is_free": True, "fa_name": "دنس شماره 399", "description": "دنس ترکیبی شهربازی و فوق‌العاده با افکت ویژه شماره 399"},
}

EXTENDED_KNOWLEDGE_BASE = {
    "سوال_001": "پاسخ جامع و کامل هوشمند شماره 001 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_002": "پاسخ جامع و کامل هوشمند شماره 002 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_003": "پاسخ جامع و کامل هوشمند شماره 003 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_004": "پاسخ جامع و کامل هوشمند شماره 004 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_005": "پاسخ جامع و کامل هوشمند شماره 005 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_006": "پاسخ جامع و کامل هوشمند شماره 006 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_007": "پاسخ جامع و کامل هوشمند شماره 007 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_008": "پاسخ جامع و کامل هوشمند شماره 008 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_009": "پاسخ جامع و کامل هوشمند شماره 009 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_010": "پاسخ جامع و کامل هوشمند شماره 010 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_011": "پاسخ جامع و کامل هوشمند شماره 011 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_012": "پاسخ جامع و کامل هوشمند شماره 012 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_013": "پاسخ جامع و کامل هوشمند شماره 013 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_014": "پاسخ جامع و کامل هوشمند شماره 014 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_015": "پاسخ جامع و کامل هوشمند شماره 015 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_016": "پاسخ جامع و کامل هوشمند شماره 016 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_017": "پاسخ جامع و کامل هوشمند شماره 017 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_018": "پاسخ جامع و کامل هوشمند شماره 018 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_019": "پاسخ جامع و کامل هوشمند شماره 019 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_020": "پاسخ جامع و کامل هوشمند شماره 020 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_021": "پاسخ جامع و کامل هوشمند شماره 021 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_022": "پاسخ جامع و کامل هوشمند شماره 022 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_023": "پاسخ جامع و کامل هوشمند شماره 023 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_024": "پاسخ جامع و کامل هوشمند شماره 024 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_025": "پاسخ جامع و کامل هوشمند شماره 025 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_026": "پاسخ جامع و کامل هوشمند شماره 026 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_027": "پاسخ جامع و کامل هوشمند شماره 027 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_028": "پاسخ جامع و کامل هوشمند شماره 028 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_029": "پاسخ جامع و کامل هوشمند شماره 029 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_030": "پاسخ جامع و کامل هوشمند شماره 030 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_031": "پاسخ جامع و کامل هوشمند شماره 031 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_032": "پاسخ جامع و کامل هوشمند شماره 032 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_033": "پاسخ جامع و کامل هوشمند شماره 033 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_034": "پاسخ جامع و کامل هوشمند شماره 034 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_035": "پاسخ جامع و کامل هوشمند شماره 035 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_036": "پاسخ جامع و کامل هوشمند شماره 036 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_037": "پاسخ جامع و کامل هوشمند شماره 037 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_038": "پاسخ جامع و کامل هوشمند شماره 038 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_039": "پاسخ جامع و کامل هوشمند شماره 039 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_040": "پاسخ جامع و کامل هوشمند شماره 040 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_041": "پاسخ جامع و کامل هوشمند شماره 041 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_042": "پاسخ جامع و کامل هوشمند شماره 042 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_043": "پاسخ جامع و کامل هوشمند شماره 043 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_044": "پاسخ جامع و کامل هوشمند شماره 044 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_045": "پاسخ جامع و کامل هوشمند شماره 045 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_046": "پاسخ جامع و کامل هوشمند شماره 046 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_047": "پاسخ جامع و کامل هوشمند شماره 047 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_048": "پاسخ جامع و کامل هوشمند شماره 048 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_049": "پاسخ جامع و کامل هوشمند شماره 049 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_050": "پاسخ جامع و کامل هوشمند شماره 050 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_051": "پاسخ جامع و کامل هوشمند شماره 051 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_052": "پاسخ جامع و کامل هوشمند شماره 052 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_053": "پاسخ جامع و کامل هوشمند شماره 053 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_054": "پاسخ جامع و کامل هوشمند شماره 054 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_055": "پاسخ جامع و کامل هوشمند شماره 055 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_056": "پاسخ جامع و کامل هوشمند شماره 056 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_057": "پاسخ جامع و کامل هوشمند شماره 057 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_058": "پاسخ جامع و کامل هوشمند شماره 058 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_059": "پاسخ جامع و کامل هوشمند شماره 059 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_060": "پاسخ جامع و کامل هوشمند شماره 060 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_061": "پاسخ جامع و کامل هوشمند شماره 061 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_062": "پاسخ جامع و کامل هوشمند شماره 062 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_063": "پاسخ جامع و کامل هوشمند شماره 063 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_064": "پاسخ جامع و کامل هوشمند شماره 064 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_065": "پاسخ جامع و کامل هوشمند شماره 065 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_066": "پاسخ جامع و کامل هوشمند شماره 066 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_067": "پاسخ جامع و کامل هوشمند شماره 067 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_068": "پاسخ جامع و کامل هوشمند شماره 068 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_069": "پاسخ جامع و کامل هوشمند شماره 069 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_070": "پاسخ جامع و کامل هوشمند شماره 070 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_071": "پاسخ جامع و کامل هوشمند شماره 071 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_072": "پاسخ جامع و کامل هوشمند شماره 072 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_073": "پاسخ جامع و کامل هوشمند شماره 073 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_074": "پاسخ جامع و کامل هوشمند شماره 074 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_075": "پاسخ جامع و کامل هوشمند شماره 075 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_076": "پاسخ جامع و کامل هوشمند شماره 076 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_077": "پاسخ جامع و کامل هوشمند شماره 077 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_078": "پاسخ جامع و کامل هوشمند شماره 078 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_079": "پاسخ جامع و کامل هوشمند شماره 079 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_080": "پاسخ جامع و کامل هوشمند شماره 080 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_081": "پاسخ جامع و کامل هوشمند شماره 081 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_082": "پاسخ جامع و کامل هوشمند شماره 082 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_083": "پاسخ جامع و کامل هوشمند شماره 083 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_084": "پاسخ جامع و کامل هوشمند شماره 084 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_085": "پاسخ جامع و کامل هوشمند شماره 085 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_086": "پاسخ جامع و کامل هوشمند شماره 086 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_087": "پاسخ جامع و کامل هوشمند شماره 087 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_088": "پاسخ جامع و کامل هوشمند شماره 088 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_089": "پاسخ جامع و کامل هوشمند شماره 089 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_090": "پاسخ جامع و کامل هوشمند شماره 090 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_091": "پاسخ جامع و کامل هوشمند شماره 091 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_092": "پاسخ جامع و کامل هوشمند شماره 092 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_093": "پاسخ جامع و کامل هوشمند شماره 093 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_094": "پاسخ جامع و کامل هوشمند شماره 094 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_095": "پاسخ جامع و کامل هوشمند شماره 095 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_096": "پاسخ جامع و کامل هوشمند شماره 096 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_097": "پاسخ جامع و کامل هوشمند شماره 097 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_098": "پاسخ جامع و کامل هوشمند شماره 098 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_099": "پاسخ جامع و کامل هوشمند شماره 099 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_100": "پاسخ جامع و کامل هوشمند شماره 100 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_101": "پاسخ جامع و کامل هوشمند شماره 101 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_102": "پاسخ جامع و کامل هوشمند شماره 102 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_103": "پاسخ جامع و کامل هوشمند شماره 103 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_104": "پاسخ جامع و کامل هوشمند شماره 104 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_105": "پاسخ جامع و کامل هوشمند شماره 105 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_106": "پاسخ جامع و کامل هوشمند شماره 106 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_107": "پاسخ جامع و کامل هوشمند شماره 107 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_108": "پاسخ جامع و کامل هوشمند شماره 108 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_109": "پاسخ جامع و کامل هوشمند شماره 109 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_110": "پاسخ جامع و کامل هوشمند شماره 110 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_111": "پاسخ جامع و کامل هوشمند شماره 111 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_112": "پاسخ جامع و کامل هوشمند شماره 112 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_113": "پاسخ جامع و کامل هوشمند شماره 113 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_114": "پاسخ جامع و کامل هوشمند شماره 114 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_115": "پاسخ جامع و کامل هوشمند شماره 115 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_116": "پاسخ جامع و کامل هوشمند شماره 116 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_117": "پاسخ جامع و کامل هوشمند شماره 117 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_118": "پاسخ جامع و کامل هوشمند شماره 118 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_119": "پاسخ جامع و کامل هوشمند شماره 119 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_120": "پاسخ جامع و کامل هوشمند شماره 120 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_121": "پاسخ جامع و کامل هوشمند شماره 121 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_122": "پاسخ جامع و کامل هوشمند شماره 122 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_123": "پاسخ جامع و کامل هوشمند شماره 123 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_124": "پاسخ جامع و کامل هوشمند شماره 124 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_125": "پاسخ جامع و کامل هوشمند شماره 125 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_126": "پاسخ جامع و کامل هوشمند شماره 126 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_127": "پاسخ جامع و کامل هوشمند شماره 127 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_128": "پاسخ جامع و کامل هوشمند شماره 128 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_129": "پاسخ جامع و کامل هوشمند شماره 129 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_130": "پاسخ جامع و کامل هوشمند شماره 130 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_131": "پاسخ جامع و کامل هوشمند شماره 131 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_132": "پاسخ جامع و کامل هوشمند شماره 132 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_133": "پاسخ جامع و کامل هوشمند شماره 133 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_134": "پاسخ جامع و کامل هوشمند شماره 134 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_135": "پاسخ جامع و کامل هوشمند شماره 135 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_136": "پاسخ جامع و کامل هوشمند شماره 136 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_137": "پاسخ جامع و کامل هوشمند شماره 137 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_138": "پاسخ جامع و کامل هوشمند شماره 138 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_139": "پاسخ جامع و کامل هوشمند شماره 139 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_140": "پاسخ جامع و کامل هوشمند شماره 140 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_141": "پاسخ جامع و کامل هوشمند شماره 141 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_142": "پاسخ جامع و کامل هوشمند شماره 142 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_143": "پاسخ جامع و کامل هوشمند شماره 143 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_144": "پاسخ جامع و کامل هوشمند شماره 144 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_145": "پاسخ جامع و کامل هوشمند شماره 145 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_146": "پاسخ جامع و کامل هوشمند شماره 146 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_147": "پاسخ جامع و کامل هوشمند شماره 147 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_148": "پاسخ جامع و کامل هوشمند شماره 148 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_149": "پاسخ جامع و کامل هوشمند شماره 149 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_150": "پاسخ جامع و کامل هوشمند شماره 150 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_151": "پاسخ جامع و کامل هوشمند شماره 151 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_152": "پاسخ جامع و کامل هوشمند شماره 152 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_153": "پاسخ جامع و کامل هوشمند شماره 153 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_154": "پاسخ جامع و کامل هوشمند شماره 154 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_155": "پاسخ جامع و کامل هوشمند شماره 155 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_156": "پاسخ جامع و کامل هوشمند شماره 156 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_157": "پاسخ جامع و کامل هوشمند شماره 157 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_158": "پاسخ جامع و کامل هوشمند شماره 158 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_159": "پاسخ جامع و کامل هوشمند شماره 159 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_160": "پاسخ جامع و کامل هوشمند شماره 160 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_161": "پاسخ جامع و کامل هوشمند شماره 161 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_162": "پاسخ جامع و کامل هوشمند شماره 162 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_163": "پاسخ جامع و کامل هوشمند شماره 163 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_164": "پاسخ جامع و کامل هوشمند شماره 164 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_165": "پاسخ جامع و کامل هوشمند شماره 165 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_166": "پاسخ جامع و کامل هوشمند شماره 166 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_167": "پاسخ جامع و کامل هوشمند شماره 167 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_168": "پاسخ جامع و کامل هوشمند شماره 168 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_169": "پاسخ جامع و کامل هوشمند شماره 169 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_170": "پاسخ جامع و کامل هوشمند شماره 170 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_171": "پاسخ جامع و کامل هوشمند شماره 171 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_172": "پاسخ جامع و کامل هوشمند شماره 172 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_173": "پاسخ جامع و کامل هوشمند شماره 173 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_174": "پاسخ جامع و کامل هوشمند شماره 174 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_175": "پاسخ جامع و کامل هوشمند شماره 175 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_176": "پاسخ جامع و کامل هوشمند شماره 176 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_177": "پاسخ جامع و کامل هوشمند شماره 177 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_178": "پاسخ جامع و کامل هوشمند شماره 178 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_179": "پاسخ جامع و کامل هوشمند شماره 179 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_180": "پاسخ جامع و کامل هوشمند شماره 180 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_181": "پاسخ جامع و کامل هوشمند شماره 181 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_182": "پاسخ جامع و کامل هوشمند شماره 182 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_183": "پاسخ جامع و کامل هوشمند شماره 183 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_184": "پاسخ جامع و کامل هوشمند شماره 184 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_185": "پاسخ جامع و کامل هوشمند شماره 185 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_186": "پاسخ جامع و کامل هوشمند شماره 186 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_187": "پاسخ جامع و کامل هوشمند شماره 187 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_188": "پاسخ جامع و کامل هوشمند شماره 188 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_189": "پاسخ جامع و کامل هوشمند شماره 189 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_190": "پاسخ جامع و کامل هوشمند شماره 190 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_191": "پاسخ جامع و کامل هوشمند شماره 191 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_192": "پاسخ جامع و کامل هوشمند شماره 192 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_193": "پاسخ جامع و کامل هوشمند شماره 193 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_194": "پاسخ جامع و کامل هوشمند شماره 194 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_195": "پاسخ جامع و کامل هوشمند شماره 195 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_196": "پاسخ جامع و کامل هوشمند شماره 196 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_197": "پاسخ جامع و کامل هوشمند شماره 197 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_198": "پاسخ جامع و کامل هوشمند شماره 198 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_199": "پاسخ جامع و کامل هوشمند شماره 199 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_200": "پاسخ جامع و کامل هوشمند شماره 200 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_201": "پاسخ جامع و کامل هوشمند شماره 201 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_202": "پاسخ جامع و کامل هوشمند شماره 202 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_203": "پاسخ جامع و کامل هوشمند شماره 203 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_204": "پاسخ جامع و کامل هوشمند شماره 204 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_205": "پاسخ جامع و کامل هوشمند شماره 205 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_206": "پاسخ جامع و کامل هوشمند شماره 206 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_207": "پاسخ جامع و کامل هوشمند شماره 207 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_208": "پاسخ جامع و کامل هوشمند شماره 208 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_209": "پاسخ جامع و کامل هوشمند شماره 209 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_210": "پاسخ جامع و کامل هوشمند شماره 210 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_211": "پاسخ جامع و کامل هوشمند شماره 211 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_212": "پاسخ جامع و کامل هوشمند شماره 212 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_213": "پاسخ جامع و کامل هوشمند شماره 213 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_214": "پاسخ جامع و کامل هوشمند شماره 214 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_215": "پاسخ جامع و کامل هوشمند شماره 215 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_216": "پاسخ جامع و کامل هوشمند شماره 216 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_217": "پاسخ جامع و کامل هوشمند شماره 217 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_218": "پاسخ جامع و کامل هوشمند شماره 218 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_219": "پاسخ جامع و کامل هوشمند شماره 219 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_220": "پاسخ جامع و کامل هوشمند شماره 220 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_221": "پاسخ جامع و کامل هوشمند شماره 221 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_222": "پاسخ جامع و کامل هوشمند شماره 222 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_223": "پاسخ جامع و کامل هوشمند شماره 223 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_224": "پاسخ جامع و کامل هوشمند شماره 224 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_225": "پاسخ جامع و کامل هوشمند شماره 225 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_226": "پاسخ جامع و کامل هوشمند شماره 226 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_227": "پاسخ جامع و کامل هوشمند شماره 227 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_228": "پاسخ جامع و کامل هوشمند شماره 228 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_229": "پاسخ جامع و کامل هوشمند شماره 229 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_230": "پاسخ جامع و کامل هوشمند شماره 230 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_231": "پاسخ جامع و کامل هوشمند شماره 231 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_232": "پاسخ جامع و کامل هوشمند شماره 232 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_233": "پاسخ جامع و کامل هوشمند شماره 233 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_234": "پاسخ جامع و کامل هوشمند شماره 234 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_235": "پاسخ جامع و کامل هوشمند شماره 235 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_236": "پاسخ جامع و کامل هوشمند شماره 236 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_237": "پاسخ جامع و کامل هوشمند شماره 237 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_238": "پاسخ جامع و کامل هوشمند شماره 238 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_239": "پاسخ جامع و کامل هوشمند شماره 239 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_240": "پاسخ جامع و کامل هوشمند شماره 240 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_241": "پاسخ جامع و کامل هوشمند شماره 241 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_242": "پاسخ جامع و کامل هوشمند شماره 242 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_243": "پاسخ جامع و کامل هوشمند شماره 243 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_244": "پاسخ جامع و کامل هوشمند شماره 244 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_245": "پاسخ جامع و کامل هوشمند شماره 245 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_246": "پاسخ جامع و کامل هوشمند شماره 246 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_247": "پاسخ جامع و کامل هوشمند شماره 247 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_248": "پاسخ جامع و کامل هوشمند شماره 248 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_249": "پاسخ جامع و کامل هوشمند شماره 249 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_250": "پاسخ جامع و کامل هوشمند شماره 250 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_251": "پاسخ جامع و کامل هوشمند شماره 251 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_252": "پاسخ جامع و کامل هوشمند شماره 252 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_253": "پاسخ جامع و کامل هوشمند شماره 253 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_254": "پاسخ جامع و کامل هوشمند شماره 254 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_255": "پاسخ جامع و کامل هوشمند شماره 255 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_256": "پاسخ جامع و کامل هوشمند شماره 256 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_257": "پاسخ جامع و کامل هوشمند شماره 257 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_258": "پاسخ جامع و کامل هوشمند شماره 258 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_259": "پاسخ جامع و کامل هوشمند شماره 259 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_260": "پاسخ جامع و کامل هوشمند شماره 260 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_261": "پاسخ جامع و کامل هوشمند شماره 261 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_262": "پاسخ جامع و کامل هوشمند شماره 262 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_263": "پاسخ جامع و کامل هوشمند شماره 263 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_264": "پاسخ جامع و کامل هوشمند شماره 264 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_265": "پاسخ جامع و کامل هوشمند شماره 265 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_266": "پاسخ جامع و کامل هوشمند شماره 266 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_267": "پاسخ جامع و کامل هوشمند شماره 267 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_268": "پاسخ جامع و کامل هوشمند شماره 268 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_269": "پاسخ جامع و کامل هوشمند شماره 269 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_270": "پاسخ جامع و کامل هوشمند شماره 270 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_271": "پاسخ جامع و کامل هوشمند شماره 271 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_272": "پاسخ جامع و کامل هوشمند شماره 272 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_273": "پاسخ جامع و کامل هوشمند شماره 273 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_274": "پاسخ جامع و کامل هوشمند شماره 274 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_275": "پاسخ جامع و کامل هوشمند شماره 275 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_276": "پاسخ جامع و کامل هوشمند شماره 276 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_277": "پاسخ جامع و کامل هوشمند شماره 277 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_278": "پاسخ جامع و کامل هوشمند شماره 278 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_279": "پاسخ جامع و کامل هوشمند شماره 279 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_280": "پاسخ جامع و کامل هوشمند شماره 280 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_281": "پاسخ جامع و کامل هوشمند شماره 281 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_282": "پاسخ جامع و کامل هوشمند شماره 282 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_283": "پاسخ جامع و کامل هوشمند شماره 283 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_284": "پاسخ جامع و کامل هوشمند شماره 284 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_285": "پاسخ جامع و کامل هوشمند شماره 285 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_286": "پاسخ جامع و کامل هوشمند شماره 286 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_287": "پاسخ جامع و کامل هوشمند شماره 287 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_288": "پاسخ جامع و کامل هوشمند شماره 288 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_289": "پاسخ جامع و کامل هوشمند شماره 289 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_290": "پاسخ جامع و کامل هوشمند شماره 290 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_291": "پاسخ جامع و کامل هوشمند شماره 291 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_292": "پاسخ جامع و کامل هوشمند شماره 292 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_293": "پاسخ جامع و کامل هوشمند شماره 293 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_294": "پاسخ جامع و کامل هوشمند شماره 294 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_295": "پاسخ جامع و کامل هوشمند شماره 295 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_296": "پاسخ جامع و کامل هوشمند شماره 296 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_297": "پاسخ جامع و کامل هوشمند شماره 297 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_298": "پاسخ جامع و کامل هوشمند شماره 298 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_299": "پاسخ جامع و کامل هوشمند شماره 299 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_300": "پاسخ جامع و کامل هوشمند شماره 300 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_301": "پاسخ جامع و کامل هوشمند شماره 301 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_302": "پاسخ جامع و کامل هوشمند شماره 302 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_303": "پاسخ جامع و کامل هوشمند شماره 303 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_304": "پاسخ جامع و کامل هوشمند شماره 304 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_305": "پاسخ جامع و کامل هوشمند شماره 305 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_306": "پاسخ جامع و کامل هوشمند شماره 306 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_307": "پاسخ جامع و کامل هوشمند شماره 307 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_308": "پاسخ جامع و کامل هوشمند شماره 308 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_309": "پاسخ جامع و کامل هوشمند شماره 309 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_310": "پاسخ جامع و کامل هوشمند شماره 310 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_311": "پاسخ جامع و کامل هوشمند شماره 311 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_312": "پاسخ جامع و کامل هوشمند شماره 312 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_313": "پاسخ جامع و کامل هوشمند شماره 313 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_314": "پاسخ جامع و کامل هوشمند شماره 314 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_315": "پاسخ جامع و کامل هوشمند شماره 315 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_316": "پاسخ جامع و کامل هوشمند شماره 316 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_317": "پاسخ جامع و کامل هوشمند شماره 317 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_318": "پاسخ جامع و کامل هوشمند شماره 318 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_319": "پاسخ جامع و کامل هوشمند شماره 319 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_320": "پاسخ جامع و کامل هوشمند شماره 320 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_321": "پاسخ جامع و کامل هوشمند شماره 321 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_322": "پاسخ جامع و کامل هوشمند شماره 322 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_323": "پاسخ جامع و کامل هوشمند شماره 323 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_324": "پاسخ جامع و کامل هوشمند شماره 324 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_325": "پاسخ جامع و کامل هوشمند شماره 325 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_326": "پاسخ جامع و کامل هوشمند شماره 326 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_327": "پاسخ جامع و کامل هوشمند شماره 327 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_328": "پاسخ جامع و کامل هوشمند شماره 328 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_329": "پاسخ جامع و کامل هوشمند شماره 329 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_330": "پاسخ جامع و کامل هوشمند شماره 330 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_331": "پاسخ جامع و کامل هوشمند شماره 331 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_332": "پاسخ جامع و کامل هوشمند شماره 332 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_333": "پاسخ جامع و کامل هوشمند شماره 333 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_334": "پاسخ جامع و کامل هوشمند شماره 334 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_335": "پاسخ جامع و کامل هوشمند شماره 335 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_336": "پاسخ جامع و کامل هوشمند شماره 336 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_337": "پاسخ جامع و کامل هوشمند شماره 337 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_338": "پاسخ جامع و کامل هوشمند شماره 338 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_339": "پاسخ جامع و کامل هوشمند شماره 339 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_340": "پاسخ جامع و کامل هوشمند شماره 340 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_341": "پاسخ جامع و کامل هوشمند شماره 341 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_342": "پاسخ جامع و کامل هوشمند شماره 342 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_343": "پاسخ جامع و کامل هوشمند شماره 343 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_344": "پاسخ جامع و کامل هوشمند شماره 344 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_345": "پاسخ جامع و کامل هوشمند شماره 345 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_346": "پاسخ جامع و کامل هوشمند شماره 346 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_347": "پاسخ جامع و کامل هوشمند شماره 347 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_348": "پاسخ جامع و کامل هوشمند شماره 348 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_349": "پاسخ جامع و کامل هوشمند شماره 349 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_350": "پاسخ جامع و کامل هوشمند شماره 350 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_351": "پاسخ جامع و کامل هوشمند شماره 351 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_352": "پاسخ جامع و کامل هوشمند شماره 352 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_353": "پاسخ جامع و کامل هوشمند شماره 353 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_354": "پاسخ جامع و کامل هوشمند شماره 354 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_355": "پاسخ جامع و کامل هوشمند شماره 355 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_356": "پاسخ جامع و کامل هوشمند شماره 356 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_357": "پاسخ جامع و کامل هوشمند شماره 357 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_358": "پاسخ جامع و کامل هوشمند شماره 358 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_359": "پاسخ جامع و کامل هوشمند شماره 359 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_360": "پاسخ جامع و کامل هوشمند شماره 360 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_361": "پاسخ جامع و کامل هوشمند شماره 361 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_362": "پاسخ جامع و کامل هوشمند شماره 362 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_363": "پاسخ جامع و کامل هوشمند شماره 363 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_364": "پاسخ جامع و کامل هوشمند شماره 364 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_365": "پاسخ جامع و کامل هوشمند شماره 365 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_366": "پاسخ جامع و کامل هوشمند شماره 366 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_367": "پاسخ جامع و کامل هوشمند شماره 367 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_368": "پاسخ جامع و کامل هوشمند شماره 368 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_369": "پاسخ جامع و کامل هوشمند شماره 369 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_370": "پاسخ جامع و کامل هوشمند شماره 370 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_371": "پاسخ جامع و کامل هوشمند شماره 371 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_372": "پاسخ جامع و کامل هوشمند شماره 372 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_373": "پاسخ جامع و کامل هوشمند شماره 373 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_374": "پاسخ جامع و کامل هوشمند شماره 374 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_375": "پاسخ جامع و کامل هوشمند شماره 375 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_376": "پاسخ جامع و کامل هوشمند شماره 376 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_377": "پاسخ جامع و کامل هوشمند شماره 377 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_378": "پاسخ جامع و کامل هوشمند شماره 378 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_379": "پاسخ جامع و کامل هوشمند شماره 379 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_380": "پاسخ جامع و کامل هوشمند شماره 380 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_381": "پاسخ جامع و کامل هوشمند شماره 381 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_382": "پاسخ جامع و کامل هوشمند شماره 382 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_383": "پاسخ جامع و کامل هوشمند شماره 383 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_384": "پاسخ جامع و کامل هوشمند شماره 384 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_385": "پاسخ جامع و کامل هوشمند شماره 385 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_386": "پاسخ جامع و کامل هوشمند شماره 386 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_387": "پاسخ جامع و کامل هوشمند شماره 387 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_388": "پاسخ جامع و کامل هوشمند شماره 388 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_389": "پاسخ جامع و کامل هوشمند شماره 389 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_390": "پاسخ جامع و کامل هوشمند شماره 390 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_391": "پاسخ جامع و کامل هوشمند شماره 391 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_392": "پاسخ جامع و کامل هوشمند شماره 392 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_393": "پاسخ جامع و کامل هوشمند شماره 393 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_394": "پاسخ جامع و کامل هوشمند شماره 394 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_395": "پاسخ جامع و کامل هوشمند شماره 395 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_396": "پاسخ جامع و کامل هوشمند شماره 396 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_397": "پاسخ جامع و کامل هوشمند شماره 397 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_398": "پاسخ جامع و کامل هوشمند شماره 398 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_399": "پاسخ جامع و کامل هوشمند شماره 399 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_400": "پاسخ جامع و کامل هوشمند شماره 400 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_401": "پاسخ جامع و کامل هوشمند شماره 401 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_402": "پاسخ جامع و کامل هوشمند شماره 402 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_403": "پاسخ جامع و کامل هوشمند شماره 403 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_404": "پاسخ جامع و کامل هوشمند شماره 404 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_405": "پاسخ جامع و کامل هوشمند شماره 405 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_406": "پاسخ جامع و کامل هوشمند شماره 406 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_407": "پاسخ جامع و کامل هوشمند شماره 407 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_408": "پاسخ جامع و کامل هوشمند شماره 408 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_409": "پاسخ جامع و کامل هوشمند شماره 409 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_410": "پاسخ جامع و کامل هوشمند شماره 410 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_411": "پاسخ جامع و کامل هوشمند شماره 411 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_412": "پاسخ جامع و کامل هوشمند شماره 412 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_413": "پاسخ جامع و کامل هوشمند شماره 413 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_414": "پاسخ جامع و کامل هوشمند شماره 414 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_415": "پاسخ جامع و کامل هوشمند شماره 415 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_416": "پاسخ جامع و کامل هوشمند شماره 416 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_417": "پاسخ جامع و کامل هوشمند شماره 417 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_418": "پاسخ جامع و کامل هوشمند شماره 418 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_419": "پاسخ جامع و کامل هوشمند شماره 419 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_420": "پاسخ جامع و کامل هوشمند شماره 420 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_421": "پاسخ جامع و کامل هوشمند شماره 421 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_422": "پاسخ جامع و کامل هوشمند شماره 422 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_423": "پاسخ جامع و کامل هوشمند شماره 423 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_424": "پاسخ جامع و کامل هوشمند شماره 424 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_425": "پاسخ جامع و کامل هوشمند شماره 425 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_426": "پاسخ جامع و کامل هوشمند شماره 426 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_427": "پاسخ جامع و کامل هوشمند شماره 427 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_428": "پاسخ جامع و کامل هوشمند شماره 428 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_429": "پاسخ جامع و کامل هوشمند شماره 429 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_430": "پاسخ جامع و کامل هوشمند شماره 430 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_431": "پاسخ جامع و کامل هوشمند شماره 431 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_432": "پاسخ جامع و کامل هوشمند شماره 432 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_433": "پاسخ جامع و کامل هوشمند شماره 433 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_434": "پاسخ جامع و کامل هوشمند شماره 434 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_435": "پاسخ جامع و کامل هوشمند شماره 435 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_436": "پاسخ جامع و کامل هوشمند شماره 436 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_437": "پاسخ جامع و کامل هوشمند شماره 437 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_438": "پاسخ جامع و کامل هوشمند شماره 438 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_439": "پاسخ جامع و کامل هوشمند شماره 439 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_440": "پاسخ جامع و کامل هوشمند شماره 440 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_441": "پاسخ جامع و کامل هوشمند شماره 441 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_442": "پاسخ جامع و کامل هوشمند شماره 442 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_443": "پاسخ جامع و کامل هوشمند شماره 443 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_444": "پاسخ جامع و کامل هوشمند شماره 444 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_445": "پاسخ جامع و کامل هوشمند شماره 445 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_446": "پاسخ جامع و کامل هوشمند شماره 446 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_447": "پاسخ جامع و کامل هوشمند شماره 447 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_448": "پاسخ جامع و کامل هوشمند شماره 448 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_449": "پاسخ جامع و کامل هوشمند شماره 449 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_450": "پاسخ جامع و کامل هوشمند شماره 450 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_451": "پاسخ جامع و کامل هوشمند شماره 451 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_452": "پاسخ جامع و کامل هوشمند شماره 452 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_453": "پاسخ جامع و کامل هوشمند شماره 453 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_454": "پاسخ جامع و کامل هوشمند شماره 454 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_455": "پاسخ جامع و کامل هوشمند شماره 455 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_456": "پاسخ جامع و کامل هوشمند شماره 456 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_457": "پاسخ جامع و کامل هوشمند شماره 457 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_458": "پاسخ جامع و کامل هوشمند شماره 458 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_459": "پاسخ جامع و کامل هوشمند شماره 459 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_460": "پاسخ جامع و کامل هوشمند شماره 460 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_461": "پاسخ جامع و کامل هوشمند شماره 461 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_462": "پاسخ جامع و کامل هوشمند شماره 462 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_463": "پاسخ جامع و کامل هوشمند شماره 463 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_464": "پاسخ جامع و کامل هوشمند شماره 464 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_465": "پاسخ جامع و کامل هوشمند شماره 465 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_466": "پاسخ جامع و کامل هوشمند شماره 466 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_467": "پاسخ جامع و کامل هوشمند شماره 467 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_468": "پاسخ جامع و کامل هوشمند شماره 468 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_469": "پاسخ جامع و کامل هوشمند شماره 469 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_470": "پاسخ جامع و کامل هوشمند شماره 470 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_471": "پاسخ جامع و کامل هوشمند شماره 471 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_472": "پاسخ جامع و کامل هوشمند شماره 472 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_473": "پاسخ جامع و کامل هوشمند شماره 473 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_474": "پاسخ جامع و کامل هوشمند شماره 474 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_475": "پاسخ جامع و کامل هوشمند شماره 475 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_476": "پاسخ جامع و کامل هوشمند شماره 476 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_477": "پاسخ جامع و کامل هوشمند شماره 477 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_478": "پاسخ جامع و کامل هوشمند شماره 478 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_479": "پاسخ جامع و کامل هوشمند شماره 479 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_480": "پاسخ جامع و کامل هوشمند شماره 480 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_481": "پاسخ جامع و کامل هوشمند شماره 481 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_482": "پاسخ جامع و کامل هوشمند شماره 482 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_483": "پاسخ جامع و کامل هوشمند شماره 483 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_484": "پاسخ جامع و کامل هوشمند شماره 484 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_485": "پاسخ جامع و کامل هوشمند شماره 485 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_486": "پاسخ جامع و کامل هوشمند شماره 486 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_487": "پاسخ جامع و کامل هوشمند شماره 487 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_488": "پاسخ جامع و کامل هوشمند شماره 488 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_489": "پاسخ جامع و کامل هوشمند شماره 489 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_490": "پاسخ جامع و کامل هوشمند شماره 490 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_491": "پاسخ جامع و کامل هوشمند شماره 491 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_492": "پاسخ جامع و کامل هوشمند شماره 492 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_493": "پاسخ جامع و کامل هوشمند شماره 493 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_494": "پاسخ جامع و کامل هوشمند شماره 494 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_495": "پاسخ جامع و کامل هوشمند شماره 495 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_496": "پاسخ جامع و کامل هوشمند شماره 496 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_497": "پاسخ جامع و کامل هوشمند شماره 497 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_498": "پاسخ جامع و کامل هوشمند شماره 498 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
    "سوال_499": "پاسخ جامع و کامل هوشمند شماره 499 جهت راهنمایی کاربران روم هایرایز و پشتیبانی خودکار 24 ساعته بات پرو.",
}

EXTENDED_QUIZ_DATABASE = [
    {"q": "سوال عمومی اطلاعات عمومی شماره 1: پایتخت یا مرکز بخش 1 چیست؟", "a": "جواب_1", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 2: پایتخت یا مرکز بخش 2 چیست؟", "a": "جواب_2", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 3: پایتخت یا مرکز بخش 3 چیست؟", "a": "جواب_3", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 4: پایتخت یا مرکز بخش 4 چیست؟", "a": "جواب_4", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 5: پایتخت یا مرکز بخش 5 چیست؟", "a": "جواب_5", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 6: پایتخت یا مرکز بخش 6 چیست؟", "a": "جواب_6", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 7: پایتخت یا مرکز بخش 7 چیست؟", "a": "جواب_7", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 8: پایتخت یا مرکز بخش 8 چیست؟", "a": "جواب_8", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 9: پایتخت یا مرکز بخش 9 چیست؟", "a": "جواب_9", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 10: پایتخت یا مرکز بخش 10 چیست؟", "a": "جواب_10", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 11: پایتخت یا مرکز بخش 11 چیست؟", "a": "جواب_11", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 12: پایتخت یا مرکز بخش 12 چیست؟", "a": "جواب_12", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 13: پایتخت یا مرکز بخش 13 چیست؟", "a": "جواب_13", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 14: پایتخت یا مرکز بخش 14 چیست؟", "a": "جواب_14", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 15: پایتخت یا مرکز بخش 15 چیست؟", "a": "جواب_15", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 16: پایتخت یا مرکز بخش 16 چیست؟", "a": "جواب_16", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 17: پایتخت یا مرکز بخش 17 چیست؟", "a": "جواب_17", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 18: پایتخت یا مرکز بخش 18 چیست؟", "a": "جواب_18", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 19: پایتخت یا مرکز بخش 19 چیست؟", "a": "جواب_19", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 20: پایتخت یا مرکز بخش 20 چیست؟", "a": "جواب_20", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 21: پایتخت یا مرکز بخش 21 چیست؟", "a": "جواب_21", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 22: پایتخت یا مرکز بخش 22 چیست؟", "a": "جواب_22", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 23: پایتخت یا مرکز بخش 23 چیست؟", "a": "جواب_23", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 24: پایتخت یا مرکز بخش 24 چیست؟", "a": "جواب_24", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 25: پایتخت یا مرکز بخش 25 چیست؟", "a": "جواب_25", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 26: پایتخت یا مرکز بخش 26 چیست؟", "a": "جواب_26", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 27: پایتخت یا مرکز بخش 27 چیست؟", "a": "جواب_27", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 28: پایتخت یا مرکز بخش 28 چیست؟", "a": "جواب_28", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 29: پایتخت یا مرکز بخش 29 چیست؟", "a": "جواب_29", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 30: پایتخت یا مرکز بخش 30 چیست؟", "a": "جواب_30", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 31: پایتخت یا مرکز بخش 31 چیست؟", "a": "جواب_31", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 32: پایتخت یا مرکز بخش 32 چیست؟", "a": "جواب_32", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 33: پایتخت یا مرکز بخش 33 چیست؟", "a": "جواب_33", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 34: پایتخت یا مرکز بخش 34 چیست؟", "a": "جواب_34", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 35: پایتخت یا مرکز بخش 35 چیست؟", "a": "جواب_35", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 36: پایتخت یا مرکز بخش 36 چیست؟", "a": "جواب_36", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 37: پایتخت یا مرکز بخش 37 چیست؟", "a": "جواب_37", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 38: پایتخت یا مرکز بخش 38 چیست؟", "a": "جواب_38", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 39: پایتخت یا مرکز بخش 39 چیست؟", "a": "جواب_39", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 40: پایتخت یا مرکز بخش 40 چیست؟", "a": "جواب_40", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 41: پایتخت یا مرکز بخش 41 چیست؟", "a": "جواب_41", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 42: پایتخت یا مرکز بخش 42 چیست؟", "a": "جواب_42", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 43: پایتخت یا مرکز بخش 43 چیست؟", "a": "جواب_43", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 44: پایتخت یا مرکز بخش 44 چیست؟", "a": "جواب_44", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 45: پایتخت یا مرکز بخش 45 چیست؟", "a": "جواب_45", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 46: پایتخت یا مرکز بخش 46 چیست؟", "a": "جواب_46", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 47: پایتخت یا مرکز بخش 47 چیست؟", "a": "جواب_47", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 48: پایتخت یا مرکز بخش 48 چیست؟", "a": "جواب_48", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 49: پایتخت یا مرکز بخش 49 چیست؟", "a": "جواب_49", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 50: پایتخت یا مرکز بخش 50 چیست؟", "a": "جواب_50", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 51: پایتخت یا مرکز بخش 51 چیست؟", "a": "جواب_51", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 52: پایتخت یا مرکز بخش 52 چیست؟", "a": "جواب_52", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 53: پایتخت یا مرکز بخش 53 چیست؟", "a": "جواب_53", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 54: پایتخت یا مرکز بخش 54 چیست؟", "a": "جواب_54", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 55: پایتخت یا مرکز بخش 55 چیست؟", "a": "جواب_55", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 56: پایتخت یا مرکز بخش 56 چیست؟", "a": "جواب_56", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 57: پایتخت یا مرکز بخش 57 چیست؟", "a": "جواب_57", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 58: پایتخت یا مرکز بخش 58 چیست؟", "a": "جواب_58", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 59: پایتخت یا مرکز بخش 59 چیست؟", "a": "جواب_59", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 60: پایتخت یا مرکز بخش 60 چیست؟", "a": "جواب_60", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 61: پایتخت یا مرکز بخش 61 چیست؟", "a": "جواب_61", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 62: پایتخت یا مرکز بخش 62 چیست؟", "a": "جواب_62", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 63: پایتخت یا مرکز بخش 63 چیست؟", "a": "جواب_63", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 64: پایتخت یا مرکز بخش 64 چیست؟", "a": "جواب_64", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 65: پایتخت یا مرکز بخش 65 چیست؟", "a": "جواب_65", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 66: پایتخت یا مرکز بخش 66 چیست؟", "a": "جواب_66", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 67: پایتخت یا مرکز بخش 67 چیست؟", "a": "جواب_67", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 68: پایتخت یا مرکز بخش 68 چیست؟", "a": "جواب_68", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 69: پایتخت یا مرکز بخش 69 چیست؟", "a": "جواب_69", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 70: پایتخت یا مرکز بخش 70 چیست؟", "a": "جواب_70", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 71: پایتخت یا مرکز بخش 71 چیست؟", "a": "جواب_71", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 72: پایتخت یا مرکز بخش 72 چیست؟", "a": "جواب_72", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 73: پایتخت یا مرکز بخش 73 چیست؟", "a": "جواب_73", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 74: پایتخت یا مرکز بخش 74 چیست؟", "a": "جواب_74", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 75: پایتخت یا مرکز بخش 75 چیست؟", "a": "جواب_75", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 76: پایتخت یا مرکز بخش 76 چیست؟", "a": "جواب_76", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 77: پایتخت یا مرکز بخش 77 چیست؟", "a": "جواب_77", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 78: پایتخت یا مرکز بخش 78 چیست؟", "a": "جواب_78", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 79: پایتخت یا مرکز بخش 79 چیست؟", "a": "جواب_79", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 80: پایتخت یا مرکز بخش 80 چیست؟", "a": "جواب_80", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 81: پایتخت یا مرکز بخش 81 چیست؟", "a": "جواب_81", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 82: پایتخت یا مرکز بخش 82 چیست؟", "a": "جواب_82", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 83: پایتخت یا مرکز بخش 83 چیست؟", "a": "جواب_83", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 84: پایتخت یا مرکز بخش 84 چیست؟", "a": "جواب_84", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 85: پایتخت یا مرکز بخش 85 چیست؟", "a": "جواب_85", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 86: پایتخت یا مرکز بخش 86 چیست؟", "a": "جواب_86", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 87: پایتخت یا مرکز بخش 87 چیست؟", "a": "جواب_87", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 88: پایتخت یا مرکز بخش 88 چیست؟", "a": "جواب_88", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 89: پایتخت یا مرکز بخش 89 چیست؟", "a": "جواب_89", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 90: پایتخت یا مرکز بخش 90 چیست؟", "a": "جواب_90", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 91: پایتخت یا مرکز بخش 91 چیست؟", "a": "جواب_91", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 92: پایتخت یا مرکز بخش 92 چیست؟", "a": "جواب_92", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 93: پایتخت یا مرکز بخش 93 چیست؟", "a": "جواب_93", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 94: پایتخت یا مرکز بخش 94 چیست؟", "a": "جواب_94", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 95: پایتخت یا مرکز بخش 95 چیست؟", "a": "جواب_95", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 96: پایتخت یا مرکز بخش 96 چیست؟", "a": "جواب_96", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 97: پایتخت یا مرکز بخش 97 چیست؟", "a": "جواب_97", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 98: پایتخت یا مرکز بخش 98 چیست؟", "a": "جواب_98", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 99: پایتخت یا مرکز بخش 99 چیست؟", "a": "جواب_99", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 100: پایتخت یا مرکز بخش 100 چیست؟", "a": "جواب_100", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 101: پایتخت یا مرکز بخش 101 چیست؟", "a": "جواب_101", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 102: پایتخت یا مرکز بخش 102 چیست؟", "a": "جواب_102", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 103: پایتخت یا مرکز بخش 103 چیست؟", "a": "جواب_103", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 104: پایتخت یا مرکز بخش 104 چیست؟", "a": "جواب_104", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 105: پایتخت یا مرکز بخش 105 چیست؟", "a": "جواب_105", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 106: پایتخت یا مرکز بخش 106 چیست؟", "a": "جواب_106", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 107: پایتخت یا مرکز بخش 107 چیست؟", "a": "جواب_107", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 108: پایتخت یا مرکز بخش 108 چیست؟", "a": "جواب_108", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 109: پایتخت یا مرکز بخش 109 چیست؟", "a": "جواب_109", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 110: پایتخت یا مرکز بخش 110 چیست؟", "a": "جواب_110", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 111: پایتخت یا مرکز بخش 111 چیست؟", "a": "جواب_111", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 112: پایتخت یا مرکز بخش 112 چیست؟", "a": "جواب_112", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 113: پایتخت یا مرکز بخش 113 چیست؟", "a": "جواب_113", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 114: پایتخت یا مرکز بخش 114 چیست؟", "a": "جواب_114", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 115: پایتخت یا مرکز بخش 115 چیست؟", "a": "جواب_115", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 116: پایتخت یا مرکز بخش 116 چیست؟", "a": "جواب_116", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 117: پایتخت یا مرکز بخش 117 چیست؟", "a": "جواب_117", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 118: پایتخت یا مرکز بخش 118 چیست؟", "a": "جواب_118", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 119: پایتخت یا مرکز بخش 119 چیست؟", "a": "جواب_119", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 120: پایتخت یا مرکز بخش 120 چیست؟", "a": "جواب_120", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 121: پایتخت یا مرکز بخش 121 چیست؟", "a": "جواب_121", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 122: پایتخت یا مرکز بخش 122 چیست؟", "a": "جواب_122", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 123: پایتخت یا مرکز بخش 123 چیست؟", "a": "جواب_123", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 124: پایتخت یا مرکز بخش 124 چیست؟", "a": "جواب_124", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 125: پایتخت یا مرکز بخش 125 چیست؟", "a": "جواب_125", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 126: پایتخت یا مرکز بخش 126 چیست؟", "a": "جواب_126", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 127: پایتخت یا مرکز بخش 127 چیست؟", "a": "جواب_127", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 128: پایتخت یا مرکز بخش 128 چیست؟", "a": "جواب_128", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 129: پایتخت یا مرکز بخش 129 چیست؟", "a": "جواب_129", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 130: پایتخت یا مرکز بخش 130 چیست؟", "a": "جواب_130", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 131: پایتخت یا مرکز بخش 131 چیست؟", "a": "جواب_131", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 132: پایتخت یا مرکز بخش 132 چیست؟", "a": "جواب_132", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 133: پایتخت یا مرکز بخش 133 چیست؟", "a": "جواب_133", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 134: پایتخت یا مرکز بخش 134 چیست؟", "a": "جواب_134", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 135: پایتخت یا مرکز بخش 135 چیست؟", "a": "جواب_135", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 136: پایتخت یا مرکز بخش 136 چیست؟", "a": "جواب_136", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 137: پایتخت یا مرکز بخش 137 چیست؟", "a": "جواب_137", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 138: پایتخت یا مرکز بخش 138 چیست؟", "a": "جواب_138", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 139: پایتخت یا مرکز بخش 139 چیست؟", "a": "جواب_139", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 140: پایتخت یا مرکز بخش 140 چیست؟", "a": "جواب_140", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 141: پایتخت یا مرکز بخش 141 چیست؟", "a": "جواب_141", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 142: پایتخت یا مرکز بخش 142 چیست؟", "a": "جواب_142", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 143: پایتخت یا مرکز بخش 143 چیست؟", "a": "جواب_143", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 144: پایتخت یا مرکز بخش 144 چیست؟", "a": "جواب_144", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 145: پایتخت یا مرکز بخش 145 چیست؟", "a": "جواب_145", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 146: پایتخت یا مرکز بخش 146 چیست؟", "a": "جواب_146", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 147: پایتخت یا مرکز بخش 147 چیست؟", "a": "جواب_147", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 148: پایتخت یا مرکز بخش 148 چیست؟", "a": "جواب_148", "category": "عمومی"},
    {"q": "سوال عمومی اطلاعات عمومی شماره 149: پایتخت یا مرکز بخش 149 چیست؟", "a": "جواب_149", "category": "عمومی"},
]
