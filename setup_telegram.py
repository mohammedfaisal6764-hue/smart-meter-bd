#!/usr/bin/env python3
"""
Telegram Chat ID Setup Helper
এই স্ক্রিপ্ট রান করলে আপনার Telegram Chat ID পাওয়া যাবে
"""
import time
import requests

BOT_TOKEN = "8824872160:AAFulh2sM7CSJa8B4_qDdrWPsCPAOXk5khw"
CHAT_ID = "6345338101"  # Already configured

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"limit": 10}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=15)
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return {"ok": False, "result": []}

def main():
    print("=" * 60)
    print("🔍 Telegram Chat ID Finder")
    print("=" * 60)
    print("\n📋 স্টেপস:")
    print("   ১. টেলিগ্রামে আপনার বটে যান")
    print("   ২. /start লিখে পাঠান")
    print("   ৩. নিচে আপনার Chat ID দেখা যাবে\n")
    print("⏳ অপেক্ষা করছি... (৩০ সেকেন্ড)\n")

    offset = None
    found = False

    for i in range(30):
        updates = get_updates(offset)
        if updates.get("ok"):
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    username = update["message"]["chat"].get("username", "N/A")
                    first_name = update["message"]["chat"].get("first_name", "N/A")

                    print("✅ Chat ID পাওয়া গেছে!")
                    print("-" * 60)
                    print(f"🆔 Chat ID: {chat_id}")
                    print(f"👤 Name: {first_name}")
                    print(f"🔤 Username: @{username}")
                    print("-" * 60)
                    print(f"\n👉 config.py ফাইলে নিচের লাইনটি আপডেট করুন:")
                    print(f'   TELEGRAM_CHAT_ID = "{chat_id}"')
                    print("\n✅ Setup complete!")
                    found = True
                    return

        if not found:
            print(f"⏳ অপেক্ষা করছি... ({i+1}/30) - বটে /start পাঠান")
            time.sleep(1)

    if not found:
        print("\n❌ Chat ID পাওয়া যায়নি।")
        print("   নিশ্চিত করুন:")
        print("   • বট টোকেন সঠিক")
        print("   • আপনি বটে /start পাঠিয়েছেন")
        print("   • ইন্টারনেট কানেকশন আছে")

if __name__ == "__main__":
    main()
