# ⚡ Smart Electricity Monitoring System

**বাংলাদেশের জন্য তৈরি - Tuya Smart Circuit Breaker + Telegram + Live Web Dashboard**

---

## 📋 কী কী ফিচার আছে?

| ফিচার | বিবরণ |
|--------|--------|
| ⚡ **লাইভ মনিটরিং** | ভোল্টেজ, কারেন্ট, পাওয়ার রিয়েল-টাইম দেখুন |
| 💰 **অটো বিল ক্যালকুলেশন** | প্রতি ইউনিট ৳৯ হিসেবে অটোমেটিক বিল হিসাব |
| 📱 **টেলিগ্রাম নোটিফিকেশন** | বিদ্যুৎ চলে গেলে, ফিরে এলে, ৫০০ টাকা বিল হলে অ্যালার্ট |
| 📊 **মাসিক রিপোর্ট** | প্রতি মাসের ১ তারিখে সকাল ৯টায় অটো রিপোর্ট |
| 🔌 **বিদ্যুৎ বিচ্ছিন্নকরণ ট্র্যাকিং** | কখন চলে গেছে, কখন এসেছে, কতক্ষণ ছিল - সব রেকর্ড |
| 🌐 **ওয়েব ড্যাশবোর্ড** | সুন্দর লাইভ ড্যাশবোর্ড মোবাইল/ডেস্কটপে |

---

## 🛠️ প্রয়োজনীয় জিনিস

### হার্ডওয়্যার
- ✅ Tuya Smart Circuit Breaker (আপনার কাছে আছে)
- ✅ WiFi Router (ইন্টারনেট সংযোগ)
- ✅ কম্পিউটার / Raspberry Pi / VPS (সার্ভার হিসেবে)

### সফটওয়্যার
- Python 3.8+
- pip (Python package manager)

---

## 🚀 ইনস্টলেশন গাইড

### স্টেপ ১: প্রজেক্ট ডাউনলোড করুন

```bash
# ফোল্ডার তৈরি
mkdir smart-meter
cd smart-meter

# সব ফাইল এই ফোল্ডারে রাখুন
```

### স্টেপ ২: ডিপেন্ডেন্সি ইনস্টল করুন

```bash
pip install -r requirements.txt
```

### স্টেপ ৩: টেলিগ্রাম Chat ID সেটআপ

```bash
python setup_telegram.py
```

**নির্দেশনা:**
1. স্ক্রিপ্ট রান করুন
2. টেলিগ্রামে আপনার বটে যান: `@your_bot_name`
3. `/start` পাঠান
4. টার্মিনালে Chat ID দেখা যাবে
5. `config.py`-তে `TELEGRAM_CHAT_ID` আপডেট করুন

### স্টেপ ৪: Tuya API সেটআপ (যদি প্রয়োজন হয়)

আপনার Tuya Smart Breaker-এর জন্য Cloud API এক্সেস নিশ্চিত করুন:

1. [Tuya IoT Platform](https://iot.tuya.com/) এ লগইন করুন
2. Cloud Project তৈরি করুন
3. Authorization Key পান (Access ID + Access Secret)
4. Device ID যোগ করুন
5. API Service Enable করুন:
   - Device Status Notification
   - Device Information Query
   - Device Control

> **নোট:** আপনার প্রদান করা ক্রেডেনশিয়াল ইতিমধ্যে `config.py`-তে বসানো আছে।

### স্টেপ ৫: অ্যাপ্লিকেশন চালু করুন

```bash
python app.py
```

**আউটপুট দেখতে পাবেন:**
```
============================================================
⚡ Smart Electricity Monitoring System
============================================================
📍 Device: bf253686d86878a2eduejn
💵 Rate: ৳9/unit
⚠️ Alert: ৳500
📱 Telegram: Configured
============================================================

[Init] Testing Tuya connection...
[Init] ✅ Tuya API connected!
[Init] ✅ System initialized successfully!
[Init] Web dashboard: http://localhost:5000
```

### স্টেপ ৬: ড্যাশবোর্ড দেখুন

ব্রাউজারে যান:
```
http://localhost:5000
```

অথবা আপনার নেটওয়ার্কে অন্য ডিভাইস থেকে:
```
http://your-computer-ip:5000
```

---

## 📁 ফাইল স্ট্রাকচার

```
smart_electricity_monitor/
├── app.py                 # মূল অ্যাপ্লিকেশন
├── config.py              # কনফিগারেশন
├── tuya_client.py         # Tuya API ক্লায়েন্ট
├── data_store.py          # ডাটা স্টোরেজ
├── telegram_handler.py    # টেলিগ্রাম বট
├── setup_telegram.py      # Chat ID সেটআপ হেল্পার
├── requirements.txt       # পাইথন প্যাকেজ
├── .env.example           # এনভায়রনমেন্ট ভ্যারিয়েবল টেমপ্লেট
├── README.md              # এই ফাইল
└── templates/
    └── index.html         # ওয়েব ড্যাশবোর্ড
```

---

## 🔧 কনফিগারেশন

`config.py` ফাইলে নিচের সেটিংস পরিবর্তন করতে পারেন:

```python
# বিলিং
COST_PER_UNIT = 9              # প্রতি ইউনিট মূল্য (টাকা)
BILL_ALERT_THRESHOLD = 500     # কত টাকা হলে অ্যালার্ট (ডিফল্ট: ৫০০)

# নোটিফিকেশন সময়
# মাসিক রিপোর্ট: প্রতি মাসের ১ তারিখ সকাল ৯টা (অটো)
# দৈনিক সামারি: রাত ১১:৫৯ (কমেন্ট আউট করা আছে, চাইলে অন করুন)
```

---

## 📱 টেলিগ্রাম কম্যান্ড

বটে নিচের কম্যান্ডগুলো ব্যবহার করতে পারেন:

| কম্যান্ড | কাজ |
|-----------|-----|
| `/start` | বট শুরু এবং হেল্প মেনু |
| `/status` | বর্তমান ভোল্টেজ, কারেন্ট, পাওয়ার |
| `/bill` | বর্তমান বিল দেখুন |
| `/units` | ইউনিট খরচ দেখুন |
| `/outages` | বিচ্ছিন্নকরণের ইতিহাস |
| `/report` | মাসিক রিপোর্ট |
| `/help` | সাহায্য |

---

## 🔌 বিদ্যুৎ বিচ্ছিন্নকরণ কীভাবে ডিটেক্ট হয়?

আপনার Tuya Smart Breaker মেইন লাইন থেকে পাওয়ার পায়। তাই:

- **বিদ্যুৎ চলে গেলে** → Breaker অফলাইন → Tuya API এরর → সিস্টেম আউটেজ ডিটেক্ট করে → টেলিগ্রামে অ্যালার্ট
- **বিদ্যুৎ ফিরে এলে** → Breaker অনলাইন → API সফল → রিকভারি নোটিফিকেশন → সময়কাল হিসাব

---

## 🐛 সমস্যা সমাধান

### সমস্যা ১: Tuya API কানেক্ট হচ্ছে না
```
[Init] ⚠️ Tuya connection failed.
```
**সমাধান:**
- `TUYA_ENDPOINT` সঠিক কিনা চেক করুন (India: `https://openapi.tuyain.com`)
- Access ID ও Secret সঠিক কিনা চেক করুন
- Tuya IoT Platform-এ API Service Enable আছে কিনা চেক করুন

### সমস্যা ২: টেলিগ্রাম মেসেজ যাচ্ছে না
```
[Telegram] Chat ID not set!
```
**সমাধান:**
```bash
python setup_telegram.py
```
চালিয়ে Chat ID পান এবং `config.py`-তে বসান।

### সমস্যা ৩: ভোল্টেজ/কারেন্ট শো করছে না
**সমাধান:**
- Tuya app-এ চেক করুন ডাটা আসছে কিনা
- `tuya_client.py`-এ `parse_power_data()` ফাংশনে DP codes সঠিক কিনা চেক করুন
- বিভিন্ন ব্রেকারে ভিন্ন ভিন্ন DP code থাকতে পারে

---

## 🔒 সিকিউরিটি নোট

- `config.py`-তে আপনার API keys আছে - এই ফাইল কাউকে দেবেন না
- প্রোডাকশনে `.env` ফাইল ব্যবহার করুন
- টেলিগ্রাম বট টোকেন গোপন রাখুন

---

## 🔄 অটো স্টার্ট (Raspberry Pi/Linux)

সিস্টেম বুট হলে অটো স্টার্ট করতে:

```bash
# systemd service তৈরি
sudo nano /etc/systemd/system/smart-meter.service
```

```ini
[Unit]
Description=Smart Electricity Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-meter
ExecStart=/usr/bin/python3 /home/pi/smart-meter/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable smart-meter
sudo systemctl start smart-meter
sudo systemctl status smart-meter
```

---

## 📞 সাপোর্ট

সমস্যা হলে চেক করুন:
1. সব ক্রেডেনশিয়াল সঠিক কিনা
2. ইন্টারনেট কানেকশন আছে কিনা
3. Tuya app-এ ডিভাইস অনলাইন কিনা
4. `meter_data.json` ফাইল তৈরি হচ্ছে কিনা

---

**তৈরি করেছেন:** Smart Electricity Monitor System  
**ভার্সন:** 2.0  
**লাইসেন্স:** MIT
