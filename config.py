"""
Smart Electricity Monitor - Configuration
বাংলাদেশের জন্য কনফিগারেশন
"""

# ===================== Tuya Cloud API =====================
# আপনার Tuya Smart Circuit Breaker-এর API ক্রেডেনশিয়াল
# এগুলো আপনি দিয়েছেন:
TUYA_ACCESS_ID = "q5avqmrnwupjwhwvm5q3"           # Access ID (আপনি দিয়েছেন)
TUYA_ACCESS_SECRET = "0087dd259b1f4fa7801573a1401254f0"  # Access Secret (আপনি দিয়েছেন)
TUYA_DEVICE_ID = "bf253686d86878a2eduejn"         # Virtual ID (আপনি দিয়েছেন)

# Tuya API Endpoint - India region (Bangladesh-এর কাছাকাছি)
# যদি কানেক্ট না হয়, অন্য রিজিয়ন ট্রাই করুন:
TUYA_ENDPOINT = "https://openapi.tuyaeu.com"
#   China:    https://openapi.tuyacn.com
#   US:       https://openapi.tuyaus.com
#   EU:       https://openapi.tuyaeu.com  <-- বর্তমান
#   India:    https://openapi.tuyain.com

# Device info (আপনি দিয়েছেন)
DEVICE_IP = "114.130.168.226"
DEVICE_MAC = "00:33:7a:68:9b:e9"

# ===================== Telegram Bot =====================
TELEGRAM_BOT_TOKEN = "8824872160:AAFulh2sM7CSJa8B4_qDdrWPsCPAOXk5khw"
TELEGRAM_CHAT_ID = "6345338101"   # setup_telegram.py রান করে পাবেন

# ===================== Billing Settings =====================
COST_PER_UNIT = 9              # প্রতি ইউনিট = ৯ টাকা
BILL_ALERT_THRESHOLD = 500     # ৫০০ টাকা হলে অ্যালার্ট
DEVICE_RATING_AMPS = 60        # ৬০ অ্যাম্পিয়ার মেইন বোর্ড
DEVICE_PHASE = "Single Phase"  # সিঙ্গেল ফেজ

# ===================== Physical Meter Reading =====================
# আপনার মেইন মিটারের বর্তমান রিডিং (kWh) এখানে বসান।
# সিস্টেম ব্যবহৃত ইউনিটের সাথে যোগ করে আনুমানিক রিডিং বের করবে।
# টেলিগ্রামে /setmeter 1234.5 দিয়েও সেট করা যাবে।
METER_BASE_READING = 0.0   # যেমন: 1234.5

MSG_METER_READING = """🔢 <b>নতুন মাস - মিটার রিডিং!</b>

📅 মাস: {month_name} {year}
⚡ গত মাসে খরচ: {units} kWh
💰 গত মাসের বিল: ৳{cost:.2f}
🔢 আনুমানিক মিটার রিডিং: <b>{reading:.2f} kWh</b>

নতুন মাস শুরু হয়েছে। পাওয়ার ব্যবহার চালু!"""

# ===================== Notification Messages (Bangla) =====================
MSG_OUTAGE = """⚠️ <b>বিদ্যুৎ সংযোগ বিচ্ছিন্ন!</b>

🕐 সময়: {time}
📍 ডিভাইস: মেইন বোর্ড ({phase}, {amps}A)
🔌 স্ট্যাটাস: <b>অফলাইন</b>

বিদ্যুৎ চলে গেছে। সিস্টেম অফলাইন।"""

MSG_RESTORE = """✅ <b>বিদ্যুৎ সংযোগ পুনঃস্থাপিত!</b>

🕐 চলে গিয়েছিল: {start_time}
🕐 ফিরে এসেছে: {end_time}
⏱️ সময়কাল: {duration:.1f} মিনিট
📍 ডিভাইস: মেইন বোর্ড ({phase}, {amps}A)

বিদ্যুৎ আবার চলে এসেছে।"""

MSG_BILL_ALERT = """💰 <b>বিদ্যুৎ বিল অ্যালার্ট!</b>

আপনার বর্তমান মাসিক বিল <b>৳{cost:.2f}</b> হয়ে গেছে!
⚠️ সেট করা থ্রেশহোল্ড: ৳{threshold}
⚡ মাসিক ইউনিট: {units} kWh

এখন থেকে বিদ্যুৎ ব্যবহারে সচেতন হন।"""

MSG_MONTHLY_REPORT = """📊 <b>মাসিক বিদ্যুৎ রিপোর্ট</b>

📅 মাস: {month_name} {year}
⚡ মোট ইউনিট খরচ: {units} kWh
💰 মোট বিল: ৳{cost:.2f}
💵 প্রতি ইউনিট মূল্য: ৳{rate}
🔌 মোট বিচ্ছিন্নকরণ: {outage_count} বার
⏱️ মোট বিচ্ছিন্ন সময়: {total_outage_min:.1f} মিনিট

ধন্যবাদ! পরবর্তী মাসে দেখা হবে।"""

# Month names in Bangla
BANGLA_MONTHS = {
    1: "জানুয়ারি", 2: "ফেব্রুয়ারি", 3: "মার্চ", 4: "এপ্রিল",
    5: "মে", 6: "জুন", 7: "জুলাই", 8: "আগস্ট",
    9: "সেপ্টেম্বর", 10: "অক্টোবর", 11: "নভেম্বর", 12: "ডিসেম্বর"
}
