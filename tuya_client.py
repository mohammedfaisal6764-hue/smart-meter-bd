"""
Tuya Cloud API Client - FIXED VERSION
Tuya Smart Device থেকে রিয়েল-টাইম ডাটা আনে
"""
import requests
import hmac
import hashlib
import base64
import time
import json
from urllib.parse import urlencode
from config import TUYA_ACCESS_ID, TUYA_ACCESS_SECRET, TUYA_DEVICE_ID, TUYA_ENDPOINT

class TuyaClient:
    def __init__(self):
        self.client_id = TUYA_ACCESS_ID
        self.client_secret = TUYA_ACCESS_SECRET
        self.device_id = TUYA_DEVICE_ID
        self.endpoint = TUYA_ENDPOINT.rstrip("/")
        self.access_token = None
        self.token_expire_time = 0
        self._session = requests.Session()

    def _generate_sign(self, method, url_path, body="", access_token=""):
        """Tuya API signature generate করা (HMAC-SHA256, SHA-256 content hash, hex uppercase)"""
        timestamp = str(int(time.time() * 1000))

        # Content-SHA256
        if body and body != "":
            if isinstance(body, dict):
                body_str = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
            else:
                body_str = str(body)
        else:
            body_str = ""
        content_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest()

        # Ensure url_path starts with /
        if not url_path.startswith("/"):
            url_path = "/" + url_path

        sign_str = method.upper() + "\n" + content_hash + "\n\n" + url_path

        sign = hmac.new(
            self.client_secret.encode('utf-8'),
            (self.client_id + access_token + timestamp + sign_str).encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()

        return sign, timestamp

    def _get_headers(self, method, url_path, body="", access_token=""):
        sign, timestamp = self._generate_sign(method, url_path, body, access_token)
        headers = {
            "client_id": self.client_id,
            "sign": sign,
            "t": timestamp,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json"
        }
        if access_token:
            headers["access_token"] = access_token
        return headers

    def get_token(self):
        """Tuya API access token নেওয়া"""
        url_path = "/v1.0/token?grant_type=1"
        url = f"{self.endpoint}{url_path}"
        headers = self._get_headers("GET", url_path)

        try:
            resp = self._session.get(url, headers=headers, timeout=15)
            data = resp.json()

            if data.get("success"):
                result = data["result"]
                self.access_token = result["access_token"]
                
                # --- Token Expiration Fix ---
                expire_in = result.get("expire_time", 7200)
                buffer_time = 300 if expire_in > 600 else 10  # সময় কম থাকলে বাফার ১০ সেকেন্ড
                self.token_expire_time = time.time() + expire_in - buffer_time
                
                print(f"[Tuya] ✅ Token acquired. Expires in {expire_in}s")
                return self.access_token
            else:
                print(f"[Tuya] ❌ Token error: {data}")
                return None
        except Exception as e:
            print(f"[Tuya] ❌ Token request failed: {e}")
            return None

    def ensure_token(self):
        """টোকেন ভ্যালিড কিনা চেক করে, প্রয়োজনে নতুন নেয়"""
        if not self.access_token or time.time() > self.token_expire_time:
            return self.get_token()
        return self.access_token

    def get_device_status(self):
        """ডিভাইসের বর্তমান স্ট্যাটাস আনা (voltage, current, power, etc.)"""
        token = self.ensure_token()
        if not token:
            return None

        url_path = f"/v1.0/devices/{self.device_id}/status"
        url = f"{self.endpoint}{url_path}"
        headers = self._get_headers("GET", url_path, access_token=token)

        try:
            resp = self._session.get(url, headers=headers, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[Tuya] ❌ Status request failed: {e}")
            return None

    def get_device_info(self):
        """ডিভাইসের বেসিক ইনফো আনা"""
        token = self.ensure_token()
        if not token:
            return None

        url_path = f"/v1.0/devices/{self.device_id}"
        url = f"{self.endpoint}{url_path}"
        headers = self._get_headers("GET", url_path, access_token=token)

        try:
            resp = self._session.get(url, headers=headers, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[Tuya] ❌ Info request failed: {e}")
            return None

    def get_device_logs(self, start_time=None, end_time=None, codes=None, size=100):
        """ডিভাইসের ইভেন্ট লগ আনা (আউটেজ ট্র্যাকিং-এর জন্য)"""
        token = self.ensure_token()
        if not token:
            return None

        # Convert to timestamps if not provided
        if not end_time:
            end_time = int(time.time() * 1000)
        if not start_time:
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # Last 7 days

        url_path = f"/v1.0/devices/{self.device_id}/logs"
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "size": size
        }
        if codes:
            params["codes"] = ",".join(codes)

        query = urlencode(params)
        full_path = f"{url_path}?{query}"
        url = f"{self.endpoint}{full_path}"
        headers = self._get_headers("GET", full_path, access_token=token)

        try:
            resp = self._session.get(url, headers=headers, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[Tuya] ❌ Logs request failed: {e}")
            return None

    def parse_power_data(self, status_response):
        """Tuya API response থেকে power, voltage, current বের করা"""
        if not status_response or not status_response.get("success"):
            return None

        result = status_response.get("result", [])
        data = {
            "voltage": 0.0,
            "current": 0.0,
            "power": 0.0,
            "energy_wh": 0.0,
            "switch_on": True,
            "online": True
        }

        for item in result:
            code = item.get("code", "")
            value = item.get("value", 0)

            # Tuya smart breaker common DPs (Data Points)
            if code in ["cur_current", "current", "phase_a_current", "total_current"]:
                if value > 1000:
                    data["current"] = value / 1000.0
                else:
                    data["current"] = float(value)
            elif code in ["cur_voltage", "voltage", "phase_a_voltage", "total_voltage"]:
                if value > 1000:
                    data["voltage"] = value / 10.0
                else:
                    data["voltage"] = float(value)
            elif code in ["cur_power", "active_power", "phase_a_power", "total_power", "power"]:
                # Tuya smart meters send power scaled by 10 (e.g., 3616 -> 361.6W)
                data["power"] = round(float(value) / 10.0, 2)
            elif code in ["total_energy", "forward_energy", "energy", "total_forward_energy"]:
                data["energy_wh"] = float(value)
            elif code in ["switch_1", "switch", "switch_led", "switch_boiler"]:
                data["switch_on"] = bool(value)
            elif code == "online":
                data["online"] = bool(value)

        # If power is 0 but current and voltage are present, calculate apparent power
        if data["power"] == 0 and data["voltage"] > 0 and data["current"] > 0:
            data["power"] = data["voltage"] * data["current"]

        return data

    def test_connection(self):
        """সম্পূর্ণ কানেকশন টেস্ট"""
        print("\n" + "=" * 60)
        print("🔌 Tuya Connection Test")
        print("=" * 60)
        print(f"Endpoint: {self.endpoint}")
        print(f"Device ID: {self.device_id}")
        print(f"Access ID: {self.client_id[:10]}...")

        print("\n[1/3] Getting access token...")
        token = self.get_token()
        if not token:
            print("❌ FAILED: Could not get token")
            return False
        print("✅ Token acquired successfully")

        print("\n[2/3] Getting device info...")
        info = self.get_device_info()
        if info and info.get("success"):
            dev = info["result"]
            print(f"✅ Device found!")
            print(f"   Name: {dev.get('name', 'N/A')}")
            print(f"   Model: {dev.get('model', 'N/A')}")
            print(f"   Online: {dev.get('online', False)}")
        else:
            print(f"⚠️ Device info: {info}")

        print("\n[3/3] Getting device status...")
        status = self.get_device_status()
        if status and status.get("success"):
            parsed = self.parse_power_data(status)
            if parsed:
                print(f"✅ Status received!")
                print(f"   Voltage: {parsed['voltage']} V")
                print(f"   Current: {parsed['current']} A")
                print(f"   Power: {parsed['power']} W")
            else:
                print("⚠️ Status received but could not parse power data")
        else:
            print(f"❌ Status failed: {status}")

        print("\n" + "=" * 60)
        return True

if __name__ == "__main__":
    client = TuyaClient()
    client.test_connection()