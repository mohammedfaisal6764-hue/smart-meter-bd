"""
Data Store - JSON File Based Database
সব ডাটা JSON ফাইলে সেভ হয়
"""
import json
import os
from datetime import datetime, timedelta
from threading import Lock
from config import COST_PER_UNIT, METER_BASE_READING

class DataStore:
    def __init__(self, filepath="meter_data.json"):
        self.filepath = filepath
        self.lock = Lock()
        self._ensure_file()

    def _ensure_file(self):
        """ফাইল না থাকলে ডিফল্ট স্ট্রাকচার তৈরি"""
        if not os.path.exists(self.filepath):
            now = datetime.now()
            self.save({
                "total_energy_wh": 0.0,           # সর্বমোট বিদ্যুৎ (Wh)
                "daily_energy_wh": 0.0,           # আজকের বিদ্যুৎ (Wh)
                "current_day": now.day,           # বর্তমান দিন
                "daily_reports": [],              # আগের দিনগুলোর রিপোর্ট (রাত ১২:০৫-এ টেলিগ্রামে যায়)
                "monthly_energy_wh": 0.0,         # এই মাসের বিদ্যুৎ (Wh)
                "current_month": now.month,       # বর্তমান মাস
                "current_year": now.year,         # বর্তমান বছর
                "outages": [],                    # বিচ্ছিন্নকরণের ইতিহাস
                "current_outage": None,           # চলমান বিচ্ছিন্নকরণ
                "last_power_state": True,         # শেষ পাওয়ার স্ট্যাটাস
                "alert_sent_500": False,          # ৫০০ টাকা অ্যালার্ট পাঠানো হয়েছে কিনা
                "power_readings": [],             # পাওয়ার রিডিং হিস্টরি (চার্টের জন্য)
                "max_readings_history": 288,      # ২৪ ঘণ্টা = ২৮৮ টি রিডিং (৫ মিনিটে ১টি)
                "last_update": now.isoformat(),
                "meter_base_reading": METER_BASE_READING,  # মেইন মিটারের শুরুর রিডিং (kWh)
                "device_ip": "114.130.168.226",
                "device_mac": "00:33:7a:68:9b:e9"
            })

    def load(self):
        with self.lock:
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self._ensure_file()
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)

    def save(self, data):
        with self.lock:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def add_energy(self, wh_increment):
        """নতুন বিদ্যুৎ যোগ করা (Wh এ)"""
        data = self.load()
        now = datetime.now()

        # দিন পরিবর্তন চেক — আগের দিনের রিপোর্ট আর্কাইভ
        if now.day != data.get("current_day"):
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            day_report = {
                "date": yesterday,
                "units": round(data.get("daily_energy_wh", 0.0) / 1000, 3),
                "cost": round(data.get("daily_energy_wh", 0.0) / 1000 * COST_PER_UNIT, 2)
            }
            data.setdefault("daily_reports", []).append(day_report)
            while len(data["daily_reports"]) > 62:
                data["daily_reports"].pop(0)
            data["daily_energy_wh"] = 0.0
            data["current_day"] = now.day

        # মাস পরিবর্তন চেক
        if now.month != data["current_month"] or now.year != data["current_year"]:
            # পুরানো মাসের রিপোর্ট সেভ করে নতুন মাস শুরু
            old_report = {
                "month": data["current_month"],
                "year": data["current_year"],
                "units": round(data["monthly_energy_wh"] / 1000, 3),
                "cost": round(data["monthly_energy_wh"] / 1000 * COST_PER_UNIT, 2)
            }
            if "monthly_reports" not in data:
                data["monthly_reports"] = []
            data["monthly_reports"].append(old_report)

            data["monthly_energy_wh"] = 0.0
            data["current_month"] = now.month
            data["current_year"] = now.year
            data["alert_sent_500"] = False

        data["total_energy_wh"] += wh_increment
        data["monthly_energy_wh"] += wh_increment
        data["daily_energy_wh"] = data.get("daily_energy_wh", 0.0) + wh_increment
        data["last_update"] = now.isoformat()
        self.save(data)
        return data

    def add_power_reading(self, power_w, voltage, current_a):
        """পাওয়ার রিডিং চার্টের জন্য সেভ করা"""
        data = self.load()
        now = datetime.now()

        reading = {
            "time": now.isoformat(),
            "power": round(power_w, 1),
            "voltage": round(voltage, 1),
            "current": round(current_a, 3)
        }

        data["power_readings"].append(reading)

        # পুরানো রিডিং মুছে ফেলা
        max_hist = data.get("max_readings_history", 288)
        while len(data["power_readings"]) > max_hist:
            data["power_readings"].pop(0)

        self.save(data)
        return reading

    def start_outage(self):
        """বিদ্যুৎ চলে গেলে রেকর্ড শুরু"""
        data = self.load()
        if data["current_outage"] is None and data["last_power_state"]:
            now = datetime.now()
            data["current_outage"] = {
                "start": now.isoformat(),
                "end": None,
                "duration_minutes": 0
            }
            data["last_power_state"] = False
            self.save(data)
            return True, now
        return False, None

    def end_outage(self):
        """বিদ্যুৎ ফিরে এলে রেকর্ড শেষ"""
        data = self.load()
        if data["current_outage"] is not None:
            now = datetime.now()
            start = datetime.fromisoformat(data["current_outage"]["start"])
            duration = (now - start).total_seconds() / 60.0

            outage_record = {
                "start": data["current_outage"]["start"],
                "end": now.isoformat(),
                "duration_minutes": round(duration, 2)
            }
            data["outages"].append(outage_record)
            data["current_outage"] = None
            data["last_power_state"] = True
            self.save(data)
            return outage_record
        return None

    def get_stats(self):
        """বর্তমান স্ট্যাটিস্টিক্স"""
        data = self.load()
        total_kwh = data["total_energy_wh"] / 1000.0
        monthly_kwh = data["monthly_energy_wh"] / 1000.0

        # চলমান বিচ্ছিন্নকরণের সময় হিসাব
        current_outage_duration = 0
        if data["current_outage"]:
            start = datetime.fromisoformat(data["current_outage"]["start"])
            current_outage_duration = (datetime.now() - start).total_seconds() / 60.0

        return {
            "total_units": round(total_kwh, 3),
            "monthly_units": round(monthly_kwh, 3),
            "daily_units": round(data.get("daily_energy_wh", 0.0) / 1000.0, 3),
            "total_cost": round(total_kwh * COST_PER_UNIT, 2),
            "monthly_cost": round(monthly_kwh * COST_PER_UNIT, 2),
            "outages": data["outages"][-50:],  # শেষ ৫০টি
            "current_outage": data["current_outage"],
            "current_outage_duration": round(current_outage_duration, 1),
            "alert_sent": data["alert_sent_500"],
            "meter_base_reading": round(data.get("meter_base_reading", METER_BASE_READING), 3),
            "estimated_reading": round(data.get("meter_base_reading", METER_BASE_READING) + total_kwh, 3),
            "power_readings": data["power_readings"],
            "last_update": data["last_update"],
            "device_online": data["last_power_state"]
        }

    def set_alert_sent(self):
        data = self.load()
        data["alert_sent_500"] = True
        self.save(data)

    def reset_alert(self):
        data = self.load()
        data["alert_sent_500"] = False
        self.save(data)

    def get_meter_reading(self):
        """মেইন মিটারের আনুমানিক বর্তমান রিডিং"""
        data = self.load()
        base = float(data.get("meter_base_reading", METER_BASE_READING))
        used_kwh = data["total_energy_wh"] / 1000.0
        return {
            "base_reading": round(base, 3),
            "used_units": round(used_kwh, 3),
            "estimated_reading": round(base + used_kwh, 3)
        }

    def set_base_reading(self, reading):
        """মেইন মিটারের শুরুর রিডিং সেট/আপডেট করা"""
        data = self.load()
        data["meter_base_reading"] = float(reading)
        self.save(data)
        return self.get_meter_reading()

    def get_last_daily_report(self):
        """সবশেষ আর্কাইভকৃত দিনের (গতকালের) রিপোর্ট"""
        data = self.load()
        reports = data.get("daily_reports", [])
        return reports[-1] if reports else None

    def get_today_report(self):
        """আজকের এ পর্যন্তের খরচ"""
        data = self.load()
        daily_kwh = data.get("daily_energy_wh", 0.0) / 1000.0
        return {"units": round(daily_kwh, 3), "cost": round(daily_kwh * COST_PER_UNIT, 2)}

    def reset_monthly(self):
        """মাস শেষে রিসেট এবং রিপোর্ট রিটার্ন"""
        data = self.load()
        now = datetime.now()

        report = {
            "units": round(data["monthly_energy_wh"] / 1000, 3),
            "cost": round(data["monthly_energy_wh"] / 1000 * COST_PER_UNIT, 2),
            "month": data["current_month"],
            "year": data["current_year"],
            "outage_count": len([o for o in data["outages"] 
                                 if datetime.fromisoformat(o["start"]).month == data["current_month"]
                                 and datetime.fromisoformat(o["start"]).year == data["current_year"]]),
            "total_outage_min": sum(o["duration_minutes"] for o in data["outages"]
                                    if datetime.fromisoformat(o["start"]).month == data["current_month"]
                                    and datetime.fromisoformat(o["start"]).year == data["current_year"]),
            "estimated_reading": round(data.get("meter_base_reading", METER_BASE_READING) + data["total_energy_wh"] / 1000.0, 2)
        }

        # মাসিক রিপোর্ট আর্কাইভ
        if "monthly_reports" not in data:
            data["monthly_reports"] = []
        data["monthly_reports"].append(report)

        # রিসেট
        data["monthly_energy_wh"] = 0.0
        data["current_month"] = now.month
        data["current_year"] = now.year
        data["alert_sent_500"] = False
        self.save(data)
        return report

    def get_monthly_report_data(self):
        """বর্তমান মাসের রিপোর্ট ডাটা (রিসেট না করে)"""
        data = self.load()
        monthly_kwh = data["monthly_energy_wh"] / 1000.0

        # এই মাসের আউটেজগুলো
        month_outages = [o for o in data["outages"]
                        if datetime.fromisoformat(o["start"]).month == data["current_month"]
                        and datetime.fromisoformat(o["start"]).year == data["current_year"]]

        return {
            "units": round(monthly_kwh, 3),
            "cost": round(monthly_kwh * COST_PER_UNIT, 2),
            "month": data["current_month"],
            "year": data["current_year"],
            "outage_count": len(month_outages),
            "total_outage_min": sum(o["duration_minutes"] for o in month_outages),
            "estimated_reading": round(data.get("meter_base_reading", METER_BASE_READING) + data["total_energy_wh"] / 1000.0, 2)
        }
