"""
Smart Electricity Monitoring System - Main Application
বাংলাদেশের জন্য তৈরি - Tuya Smart Breaker + Telegram + Web Dashboard
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from threading import Lock
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from config import (
    TUYA_ACCESS_ID, TUYA_ACCESS_SECRET, TUYA_DEVICE_ID,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, COST_PER_UNIT,
    BILL_ALERT_THRESHOLD, BANGLA_MONTHS
)
from tuya_client import TuyaClient
from data_store import DataStore
from telegram_handler import TelegramNotifier

# ===================== Flask App Setup =====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-meter-secret-key-2024-bangladesh'
# SocketIO কনফিগারেশন আপডেট করা হয়েছে
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ===================== Global Components =====================
tuya = TuyaClient()
store = DataStore()
telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# Real-time state
meter_state = {
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0,
    "status": "offline",
    "last_update": None,
    "device_online": False
}
state_lock = Lock()

# Background thread control
poll_thread = None
scheduler = None
running = True

# ===================== Helper Functions =====================
def get_formatted_time(dt=None):
    """বাংলাদেশি ফরম্যাটে সময়"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def emit_update():
    """সকল ক্লায়েন্টকে আপডেট পাঠানো"""
    with state_lock:
        state = meter_state.copy()
    stats = store.get_stats()
    payload = {**state, **stats}
    socketio.emit('meter_update', payload)

# ===================== Background Polling =====================
def device_polling_loop():
    """প্রতি ৫ সেকেন্ডে Tuya ডিভাইস থেকে ডাটা আনা"""
    global meter_state

    last_energy_time = time.time()
    consecutive_errors = 0

    print("[Poller] Device polling started...")

    while running:
        try:
            # Tuya API থেকে স্ট্যাটাস আনা
            status_resp = tuya.get_device_status()

            if status_resp and status_resp.get("success"):
                # API সফল - ডিভাইস অনলাইন
                parsed = tuya.parse_power_data(status_resp)

                if parsed:
                    now = time.time()
                    dt_seconds = now - last_energy_time

                    # পাওয়ার থেকে এনার্জি ক্যালকুলেট (Wh)
                    if parsed["power"] > 0 and dt_seconds > 0:
                        wh_increment = parsed["power"] * (dt_seconds / 3600.0)
                        store.add_energy(wh_increment)

                    # পাওয়ার রিডিং সেভ (চার্টের জন্য)
                    store.add_power_reading(
                        parsed["power"],
                        parsed["voltage"],
                        parsed["current"]
                    )

                    # আউটেজ রিকভারি চেক
                    data = store.load()
                    if not data["last_power_state"]:
                        outage_record = store.end_outage()
                        if outage_record:
                            start_dt = datetime.fromisoformat(outage_record["start"])
                            end_dt = datetime.fromisoformat(outage_record["end"])
                            telegram.send_restore_alert(
                                start_dt.strftime("%d %b %Y, %I:%M %p"),
                                end_dt.strftime("%d %b %Y, %I:%M %p"),
                                outage_record["duration_minutes"]
                            )
                            socketio.emit('power_restored', outage_record)

                    # স্টেট আপডেট
                    with state_lock:
                        meter_state = {
                            "voltage": parsed["voltage"],
                            "current": parsed["current"],
                            "power": parsed["power"],
                            "status": "online",
                            "last_update": get_formatted_time(),
                            "device_online": True
                        }

                    # বিল অ্যালার্ট চেক
                    stats = store.get_stats()
                    if stats["monthly_cost"] >= BILL_ALERT_THRESHOLD and not stats["alert_sent"]:
                        telegram.send_bill_alert(stats["monthly_cost"], stats["monthly_units"])
                        store.set_alert_sent()
                        socketio.emit('bill_alert', {
                            'cost': stats["monthly_cost"],
                            'threshold': BILL_ALERT_THRESHOLD
                        })

                    consecutive_errors = 0
                    last_energy_time = now
                else:
                    with state_lock:
                        meter_state["status"] = "online"
                        meter_state["device_online"] = True

            else:
                # API ফেইল - সম্ভাব্য আউটেজ বা কানেকশন সমস্যা
                consecutive_errors += 1

                if consecutive_errors >= 3:  # ৩ বার এরর হলে আউটেজ ধরা
                    data = store.load()
                    if data["last_power_state"]:
                        started, start_dt = store.start_outage()
                        if started:
                            time_str = start_dt.strftime("%d %b %Y, %I:%M %p")
                            telegram.send_outage_alert(time_str)
                            socketio.emit('power_outage', {
                                'time': time_str,
                                'message': 'বিদ্যুৎ সংযোগ বিচ্ছিন্ন!'
                            })

                    with state_lock:
                        meter_state["status"] = "offline"
                        meter_state["device_online"] = False

            # সকল ক্লায়েন্টকে আপডেট পাঠানো
            emit_update()

        except Exception as e:
            print(f"[Poller] Error: {e}")
            consecutive_errors += 1

        # Flask-SocketIO এর নিজস্ব sleep মেথড ব্যবহার করা হলো
        socketio.sleep(5)

# ===================== Scheduled Jobs =====================
def daily_report_job():
    """প্রতিদিন রাত ১২:০৫-এ আগের (সম্পূর্ণ) দিনের রিপোর্ট টেলিগ্রামে"""
    print("[Scheduler] Daily report triggered!")
    report = store.get_last_daily_report()
    if not report:
        print("[Scheduler] No daily data yet (system recently started).")
        return

    reading_info = store.get_meter_reading()
    day_dt = datetime.strptime(report["date"], "%Y-%m-%d")
    date_str = day_dt.strftime("%d %b %Y")

    # ওই দিনের আউটেজ সংখ্যা
    raw = store.load()
    outage_count = len([o for o in raw["outages"]
                        if datetime.fromisoformat(o["start"]).strftime("%Y-%m-%d") == report["date"]])

    telegram.send_daily_report(
        date_str=date_str,
        units=report["units"],
        cost=report["cost"],
        reading=reading_info["estimated_reading"],
        outage_count=outage_count
    )
    socketio.emit('daily_report', report)
    print(f"[Scheduler] Daily report sent for {report['date']}")

def monthly_report_job():
    """প্রতি মাসের ১ তারিখে সকাল ৯টায় রিপোর্ট"""
    print("[Scheduler] Monthly report triggered!")
    report = store.reset_monthly()

    month_name = BANGLA_MONTHS.get(report["month"], str(report["month"]))
    telegram.send_monthly_report(
        units=report["units"],
        cost=report["cost"],
        month=report["month"],
        year=report["year"],
        outage_count=report["outage_count"],
        total_outage_min=report["total_outage_min"]
    )

    # মিটার রিডিংসহ মাসের শুরুর অ্যালার্ট
    reading_info = store.get_meter_reading()
    telegram.send_meter_reading_alert(
        month_name=month_name,
        year=report["year"],
        units=report["units"],
        cost=report["cost"],
        reading=reading_info["estimated_reading"]
    )

    socketio.emit('monthly_report', report)
    print(f"[Scheduler] Report sent for {month_name} {report['year']}")

def month_end_report_job():
    """মাসের শেষ দিন রাত ১১:৫৫-এ চলতি মাসের সারসংক্ষেপ"""
    print("[Scheduler] Month-end report triggered!")
    report = store.get_monthly_report_data()
    reading_info = store.get_meter_reading()
    month_name = BANGLA_MONTHS.get(report["month"], str(report["month"]))

    telegram.send_month_end_report(
        month_name=month_name,
        year=report["year"],
        units=report["units"],
        cost=report["cost"],
        reading=reading_info["estimated_reading"],
        outage_count=report["outage_count"],
        total_outage_min=report["total_outage_min"]
    )
    socketio.emit('month_end_report', report)
    print(f"[Scheduler] Month-end report sent for {month_name} {report['year']}")

# ===================== Telegram Command Handler =====================
def handle_telegram_command(command, chat_id):
    """টেলিগ্রাম কম্যান্ড হ্যান্ডলার"""
    if command == "/start":
        msg = """🚀 <b>Smart Electricity Monitor</b>

আপনার বাড়ির বিদ্যুৎ মনিটরিং বটে স্বাগতম!

কম্যান্ড লিস্ট:
/status - বর্তমান স্ট্যাটাস
/bill - বর্তমান বিল
/units - ইউনিট খরচ
/outages - বিচ্ছিন্নকরণের ইতিহাস
/report - মাসিক রিপোর্ট
/meter - আনুমানিক মিটার রিডিং
/setmeter 1234.5 - মিটার রিডিং সেট
/help - সাহায্য"""
        telegram.send_message(msg)

    elif command == "/status":
        with state_lock:
            state = meter_state.copy()
        stats = store.get_stats()
        status_emoji = "🟢" if state["device_online"] else "🔴"
        msg = f"""{status_emoji} <b>বর্তমান স্ট্যাটাস</b>

⚡ পাওয়ার: {state['power']:.1f} W
🔌 ভোল্টেজ: {state['voltage']:.1f} V
🔋 কারেন্ট: {state['current']:.3f} A
📶 স্ট্যাটাস: {'অনলাইন' if state['device_online'] else 'অফলাইন'}
🕐 আপডেট: {state['last_update'] or 'N/A'}"""
        telegram.send_message(msg)

    elif command == "/bill":
        stats = store.get_stats()
        msg = f"""💰 <b>বিদ্যুৎ বিল</b>

📅 মাসিক বিল: ৳{stats['monthly_cost']}
💵 সর্বমোট বিল: ৳{stats['total_cost']}
⚡ মাসিক ইউনিট: {stats['monthly_units']} kWh
⚠️ অ্যালার্ট থ্রেশহোল্ড: ৳{BILL_ALERT_THRESHOLD}"""
        telegram.send_message(msg)

    elif command == "/units":
        stats = store.get_stats()
        msg = f"""⚡ <b>ইউনিট খরচ</b>

📊 মাসিক ইউনিট: {stats['monthly_units']} kWh
📈 সর্বমোট ইউনিট: {stats['total_units']} kWh
💵 প্রতি ইউনিট: ৳{COST_PER_UNIT}"""
        telegram.send_message(msg)

    elif command == "/outages":
        stats = store.get_stats()
        outages = stats["outages"]
        if not outages:
            msg = "✅ কোনো বিচ্ছিন্নকরণের রেকর্ড নেই।"
        else:
            msg_lines = ["🔌 <b>বিচ্ছিন্নকরণের ইতিহাস (শেষ ১০টি)</b>\n"]
            for i, o in enumerate(reversed(outages[-10:]), 1):
                start = datetime.fromisoformat(o["start"]).strftime("%d %b, %I:%M %p")
                end = datetime.fromisoformat(o["end"]).strftime("%d %b, %I:%M %p") if o["end"] else "চলমান"
                msg_lines.append(f"{i}. {start} → {end} ({o['duration_minutes']:.1f} মিনিট)")
            msg = "\n".join(msg_lines)
        telegram.send_message(msg)

    elif command == "/report":
        report = store.get_monthly_report_data()
        month_name = BANGLA_MONTHS.get(report["month"], str(report["month"]))
        msg = f"""📊 <b>মাসিক রিপোর্ট ({month_name} {report['year']})</b>

⚡ মোট ইউনিট: {report['units']} kWh
💰 মোট বিল: ৳{report['cost']}
🔌 বিচ্ছিন্ন হয়েছে: {report['outage_count']} বার
⏱️ মোট বিচ্ছিন্ন সময়: {report['total_outage_min']:.1f} মিনিট"""
        telegram.send_message(msg)

    elif command == "/meter":
        info = store.get_meter_reading()
        telegram.send_meter_info(
            info["base_reading"],
            info["used_units"],
            info["estimated_reading"]
        )

    elif command.startswith("/setmeter"):
        parts = command.split()
        if len(parts) == 2:
            try:
                val = float(parts[1])
                if val < 0:
                    raise ValueError
                info = store.set_base_reading(val)
                telegram.send_message(
                    f"✅ <b>মিটার রিডিং সেট হয়েছে!</b>\n\n"
                    f"🏁 নতুন শুরুর রিডিং: <b>{val:.2f} kWh</b>\n"
                    f"🔢 আনুমানিক বর্তমান রিডিং: <b>{info['estimated_reading']:.2f} kWh</b>"
                )
            except ValueError:
                telegram.send_message("❌ ভুল রিডিং! সঠিক ফরম্যাট: /setmeter 1234.5")
        else:
            telegram.send_message("❌ ব্যবহার: /setmeter 1234.5")

    elif command == "/help":
        msg = """ℹ️ <b>সাহায্য</b>

/start - বট শুরু
/status - লাইভ স্ট্যাটাস
/bill - বর্তমান বিল দেখুন
/units - ইউনিট খরচ দেখুন
/outages - বিচ্ছিন্নকরণের ইতিহাস
/report - মাসিক রিপোর্ট
/meter - আনুমানিক মিটার রিডিং
/setmeter 1234.5 - মিটার রিডিং সেট

ওয়েব ড্যাশবোর্ড: http://your-server-ip:5000"""
        telegram.send_message(msg)

# ===================== Flask Routes =====================
@app.route('/')
def index():
    """মূল ওয়েব ড্যাশবোর্ড"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API: বর্তমান স্ট্যাটাস JSON"""
    with state_lock:
        state = meter_state.copy()
    stats = store.get_stats()
    return jsonify({**state, **stats})

@app.route('/api/outages')
def api_outages():
    """API: বিচ্ছিন্নকরণের ইতিহাস"""
    stats = store.get_stats()
    return jsonify(stats["outages"])

@app.route('/api/history')
def api_history():
    """API: পাওয়ার রিডিং হিস্টরি"""
    stats = store.get_stats()
    return jsonify(stats["power_readings"])

@app.route('/api/reset_alert', methods=['POST'])
def api_reset_alert():
    """API: বিল অ্যালার্ট রিসেট"""
    store.reset_alert()
    return jsonify({"success": True, "message": "Alert reset successfully"})

@app.route('/api/set_meter', methods=['POST'])
def api_set_meter():
    """API: মিটার রিডিং সেট করা (web dashboard থেকে)"""
    try:
        if request.is_json:
            reading = request.json.get('reading')
        else:
            reading = request.form.get('reading')
        reading = float(reading)
        if reading < 0:
            raise ValueError
        info = store.set_base_reading(reading)
        return jsonify({"success": True, **info})
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid reading"}), 400

@app.route('/api/meter')
def api_meter():
    """API: বর্তমান আনুমানিক মিটার রিডিং"""
    return jsonify(store.get_meter_reading())

@app.route('/api/config')
def api_config():
    """API: কনফিগারেশন (সেনসিটিভ ডাটা বাদে)"""
    return jsonify({
        "cost_per_unit": COST_PER_UNIT,
        "alert_threshold": BILL_ALERT_THRESHOLD,
        "device_phase": "Single Phase",
        "device_amps": 60
    })

# ===================== Socket.IO Events =====================
@socketio.on('connect')
def handle_connect():
    """ক্লায়েন্ট কানেক্ট হলে বর্তমান ডাটা পাঠানো"""
    with state_lock:
        state = meter_state.copy()
    stats = store.get_stats()
    emit('meter_update', {**state, **stats})

@socketio.on('request_update')
def handle_request_update():
    """ক্লায়েন্ট রিকোয়েস্ট করলে আপডেট পাঠানো"""
    emit_update()

# ===================== Application Startup =====================
def init_app():
    """অ্যাপ্লিকেশন ইনিশিয়ালাইজেশন"""
    global poll_thread, scheduler

    print("\n" + "=" * 60)
    print("⚡ Smart Electricity Monitoring System")
    print("=" * 60)
    print(f"📍 Device ID: {TUYA_DEVICE_ID}")
    print(f"💵 Rate: ৳{COST_PER_UNIT}/unit")
    print(f"⚠️ Alert: ৳{BILL_ALERT_THRESHOLD}")
    print(f"📱 Telegram: {'Configured' if TELEGRAM_CHAT_ID else 'NOT CONFIGURED'}")
    print("=" * 60 + "\n")

    # Tuya connection test
    print("[Init] Testing Tuya connection...")
    try:
        token = tuya.get_token()
        if token:
            print("[Init] ✅ Tuya API connected!")
            info = tuya.get_device_info()
            if info and info.get("success"):
                dev = info["result"]
                dev_name = dev.get("name", "Unknown")
                dev_online = dev.get("online", False)
                print(f"[Init] Device: {dev_name} | Online: {dev_online}")
            else:
                print(f"[Init] ⚠️ Device info: {info}")
        else:
            print("[Init] ⚠️ Tuya token failed. Will retry in background...")
    except Exception as e:
        print(f"[Init] ⚠️ Tuya test error: {e}")
        print("[Init] Will retry in background polling...")

    # Threading এর পরিবর্তে socketio.start_background_task ব্যবহার করা হলো
    poll_thread = socketio.start_background_task(device_polling_loop)

    # Start Telegram command polling
    if TELEGRAM_BOT_TOKEN:
        telegram.start_polling(handle_telegram_command)

    # Start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_report_job, 'cron', hour=0, minute=5, id='daily_report')
    scheduler.add_job(monthly_report_job, 'cron', day=1, hour=9, minute=0, id='monthly_report')
    scheduler.add_job(month_end_report_job, 'cron', day='last', hour=23, minute=55, id='month_end_report')
    scheduler.start()

    # Startup notification
    if TELEGRAM_CHAT_ID:
        telegram.send_startup_notification()

    print("[Init] ✅ System initialized successfully!")
    print("[Init] Web dashboard: http://localhost:5000")
    print("[Init] Press Ctrl+C to stop\n")

# ===================== Main Entry Point =====================
if __name__ == '__main__':
    init_app()
    try:
        # allow_unsafe_werkzeug যুক্ত করা হয়েছে যেন লোকাল নেটওয়ার্কে ব্লক না হয়
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping system...")
        running = False
        if scheduler:
            scheduler.shutdown()
        print("[Shutdown] Goodbye!")