"""
Telegram Bot Handler
নোটিফিকেশন পাঠানো এবং কম্যান্ড হ্যান্ডলিং
"""
import requests
import time
import threading
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, COST_PER_UNIT,
    BILL_ALERT_THRESHOLD, DEVICE_PHASE, DEVICE_RATING_AMPS,
    MSG_OUTAGE, MSG_RESTORE, MSG_BILL_ALERT, MSG_MONTHLY_REPORT,
    MSG_METER_READING, BANGLA_MONTHS
)

class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._session = requests.Session()

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id

    def send_message(self, text, parse_mode="HTML"):
        """টেলিগ্রামে মেসেজ পাঠানো"""
        if not self.chat_id:
            print("[Telegram] Chat ID not set! Run setup_telegram.py first.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            resp = self._session.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                return True
            else:
                print(f"[Telegram] Send failed: {result}")
                return False
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            return False

    def send_outage_alert(self, start_time):
        """বিদ্যুৎ চলে গেলে অ্যালার্ট"""
        msg = MSG_OUTAGE.format(
            time=start_time,
            phase=DEVICE_PHASE,
            amps=DEVICE_RATING_AMPS
        )
        return self.send_message(msg)

    def send_restore_alert(self, start_time, end_time, duration_minutes):
        """বিদ্যুৎ ফিরে এলে অ্যালার্ট"""
        msg = MSG_RESTORE.format(
            start_time=start_time,
            end_time=end_time,
            duration=duration_minutes,
            phase=DEVICE_PHASE,
            amps=DEVICE_RATING_AMPS
        )
        return self.send_message(msg)

    def send_bill_alert(self, current_cost, current_units):
        """৫০০ টাকা বিল হলে অ্যালার্ট"""
        msg = MSG_BILL_ALERT.format(
            cost=current_cost,
            threshold=BILL_ALERT_THRESHOLD,
            units=current_units
        )
        return self.send_message(msg)

    def send_monthly_report(self, units, cost, month, year, outage_count=0, total_outage_min=0):
        """প্রতি মাসের ১ তারিখে রিপোর্ট"""
        month_name = BANGLA_MONTHS.get(month, str(month))
        msg = MSG_MONTHLY_REPORT.format(
            month_name=month_name,
            year=year,
            units=units,
            cost=cost,
            rate=COST_PER_UNIT,
            outage_count=outage_count,
            total_outage_min=total_outage_min
        )
        return self.send_message(msg)

    def send_meter_reading_alert(self, month_name, year, units, cost, reading):
        """মাসের শুরুতে মিটার রিডিংসহ অ্যালার্ট"""
        msg = MSG_METER_READING.format(
            month_name=month_name,
            year=year,
            units=units,
            cost=cost,
            reading=reading
        )
        return self.send_message(msg)

    def send_month_end_report(self, month_name, year, units, cost, reading, outage_count=0, total_outage_min=0):
        """মাসের শেষ দিনে চলতি মাসের সারসংক্ষেপ"""
        msg = f"""🗓 <b>মাস শেষের হিসাব ({month_name} {year})</b>

⚡ এই মাসে মোট খরচ: {units} kWh
💰 এই মাসের বিল: ৳{cost:.2f}
🔢 আনুমানিক মিটার রিডিং: <b>{reading:.2f} kWh</b>
🔌 এই মাসে বিচ্ছিন্ন: {outage_count} বার
⏱️ মোট বিচ্ছিন্ন সময়: {total_outage_min:.1f} মিনিট

কাল থেকে নতুন মাস শুরু! 📅"""
        return self.send_message(msg)

    def send_daily_report(self, date_str, units, cost, reading, outage_count=0):
        """প্রতিদিন রাত ১২:০৫-এ গতকালের রিপোর্ট"""
        msg = f"""📅 <b>দৈনিক রিপোর্ট ({date_str})</b>

⚡ গতকালের খরচ: {units} kWh
💰 গতকালের বিল: ৳{cost:.2f}
🔢 আনুমানিক মিটার রিডিং: <b>{reading:.2f} kWh</b>
🔌 গতকাল বিচ্ছিন্ন: {outage_count} বার

আজকের জন্য হিসাব শুরু! ⚡"""
        return self.send_message(msg)

    def send_meter_info(self, base, used, reading):
        """বর্তমান আনুমানিক মিটার রিডিং দেখানো"""
        msg = f"""🔢 <b>মিটার রিডিং</b>

🏁 শুরুর রিডিং: {base:.2f} kWh
⚡ ব্যবহৃত ইউনিট: {used:.3f} kWh
🔢 আনুমানিক বর্তমান রিডিং: <b>{reading:.2f} kWh</b>

রিডিং সেট করতে: /setmeter 1234.5"""
        return self.send_message(msg)

    def send_startup_notification(self):
        """সিস্টেম চালু হলে নোটিফিকেশন"""
        msg = f"""🚀 <b>Smart Electricity Monitor চালু হয়েছে!</b>

📍 ডিভাইস: মেইন বোর্ড ({DEVICE_PHASE}, {DEVICE_RATING_AMPS}A)
💵 প্রতি ইউনিট: ৳{COST_PER_UNIT}
⚠️ বিল অ্যালার্ট: ৳{BILL_ALERT_THRESHOLD}

সিস্টেম সফলভাবে কানেক্টেড।"""
        return self.send_message(msg)

    def get_updates(self, offset=None):
        """টেলিগ্রাম থেকে নতুন মেসেজ আনা (polling এর জন্য)"""
        url = f"{self.base_url}/getUpdates"
        params = {"limit": 10}
        if offset:
            params["offset"] = offset
        try:
            resp = self._session.get(url, params=params, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[Telegram] Get updates error: {e}")
            return {"ok": False, "result": []}

    def start_polling(self, command_callback):
        """ব্যাকগ্রাউন্ডে টেলিগ্রাম কম্যান্ড লিসেন করা"""
        def poll_loop():
            offset = None
            print("[Telegram] Command polling started...")
            while True:
                try:
                    updates = self.get_updates(offset)
                    if updates.get("ok"):
                        for update in updates.get("result", []):
                            offset = update["update_id"] + 1
                            if "message" in update and "text" in update["message"]:
                                chat_id = update["message"]["chat"]["id"]
                                text = update["message"]["text"]

                                # Auto-set chat ID if not set
                                if not self.chat_id:
                                    self.set_chat_id(chat_id)
                                    self.send_message("✅ Chat ID সেট হয়ে গেছে! এখন থেকে নোটিফিকেশন পাবেন।")

                                # Process command
                                command_callback(text.lower(), chat_id)
                    time.sleep(2)
                except Exception as e:
                    print(f"[Telegram] Polling error: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        return thread


def setup_telegram_chat_id():
    """টেলিগ্রাম Chat ID খোঁজার হেল্পার ফাংশন"""
    print("=" * 50)
    print("🔍 Telegram Chat ID Setup")
    print("=" * 50)
    print("\n১. টেলিগ্রামে আপনার বটে যান: @your_bot_name")
    print("২. /start কম্যান্ড পাঠান")
    print("৩. এখানে 'y' চাপুন আপডেট চেক করতে...\n")

    notifier = TelegramNotifier()
    offset = None
    found = False

    for attempt in range(30):  # ৩০ সেকেন্ড ট্রাই
        updates = notifier.get_updates(offset)
        if updates.get("ok"):
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    username = update["message"]["chat"].get("username", "N/A")
                    print(f"✅ Chat ID পাওয়া গেছে: {chat_id}")
                    print(f"👤 Username: {username}")
                    print(f"\n👉 config.py-তে TELEGRAM_CHAT_ID = \"{chat_id}\" বসান")
                    found = True
                    return chat_id

        if not found:
            print(f"⏳ অপেক্ষা করছি... ({attempt + 1}/30)")
            time.sleep(1)

    if not found:
        print("❌ Chat ID পাওয়া যায়নি। নিশ্চিত করুন বটে /start পাঠিয়েছেন।")
        return None


if __name__ == "__main__":
    setup_telegram_chat_id()
