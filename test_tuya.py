#!/usr/bin/env python3
"""
Tuya API Connection Test
আপনার দেওয়া ক্রেডেনশিয়াল দিয়ে টেস্ট করুন
"""
import requests
import hmac
import hashlib
import base64
import time
import json

# আপনার এক্স্যাক্ট ক্রেডেনশিয়াল
ACCESS_ID = "q5avqmrnwupjwhwvm5q3"
ACCESS_SECRET = "0087dd259b1f4fa7801573a1401254f0"
DEVICE_ID = "bf253686d86878a2eduejn"
ENDPOINT = "https://openapi.tuyaeu.com"

def generate_sign(client_id, secret, method, url_path, body="", access_token=""):
    timestamp = str(int(time.time() * 1000))

    if body and body != "":
        if isinstance(body, dict):
            body_str = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
        else:
            body_str = str(body)
        content_hash = hashlib.md5(body_str.encode('utf-8')).hexdigest()
    else:
        content_hash = "d41d8cd98f00b204e9800998ecf8427e"

    if not url_path.startswith("/"):
        url_path = "/" + url_path

    string_to_sign = client_id + access_token + timestamp + method.upper() + "\n" + content_hash + "\n" + "\n" + url_path

    sign = base64.b64encode(
        hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

    return sign, timestamp

def get_token():
    url_path = "/v1.0/token?grant_type=1"
    url = f"{ENDPOINT}{url_path}"
    sign, timestamp = generate_sign(ACCESS_ID, ACCESS_SECRET, "GET", url_path)

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
        "Content-Type": "application/json"
    }

    resp = requests.get(url, headers=headers, timeout=15)
    return resp.json()

def get_device_status(token):
    url_path = f"/v1.0/devices/{DEVICE_ID}/status"
    url = f"{ENDPOINT}{url_path}"
    sign, timestamp = generate_sign(ACCESS_ID, ACCESS_SECRET, "GET", url_path, access_token=token)

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
        "access_token": token,
        "Content-Type": "application/json"
    }

    resp = requests.get(url, headers=headers, timeout=15)
    return resp.json()

def get_device_info(token):
    url_path = f"/v1.0/devices/{DEVICE_ID}"
    url = f"{ENDPOINT}{url_path}"
    sign, timestamp = generate_sign(ACCESS_ID, ACCESS_SECRET, "GET", url_path, access_token=token)

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
        "access_token": token,
        "Content-Type": "application/json"
    }

    resp = requests.get(url, headers=headers, timeout=15)
    return resp.json()

def parse_status(result_list):
    data = {"voltage": 0, "current": 0, "power": 0, "switch_on": True, "online": True}
    for item in result_list:
        code = item.get("code", "")
        value = item.get("value", 0)
        if code in ["cur_current", "current"]:
            data["current"] = value / 1000.0 if value > 1000 else float(value)
        elif code in ["cur_voltage", "voltage"]:
            data["voltage"] = value / 10.0 if value > 1000 else float(value)
        elif code in ["cur_power", "power", "active_power"]:
            data["power"] = value / 10.0 if value > 10000 else float(value)
        elif code in ["switch_1", "switch"]:
            data["switch_on"] = bool(value)
    return data

def main():
    print("=" * 60)
    print("🔌 Tuya API Connection Test - Your Credentials")
    print("=" * 60)
    print(f"Access ID: {ACCESS_ID}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Endpoint: {ENDPOINT}")
    print()

    # Step 1: Get token
    print("[1/3] Getting access token...")
    token_resp = get_token()
    print(f"Response: {json.dumps(token_resp, indent=2)}")

    if not token_resp.get("success"):
        print("\n❌ TOKEN FAILED!")
        print("Possible reasons:")
        print("  - Wrong Access ID or Secret")
        print("  - Wrong endpoint (try https://openapi.tuyacn.com for China)")
        print("  - IP not whitelisted in Tuya IoT Platform")
        return

    token = token_resp["result"]["access_token"]
    print(f"\n✅ Token: {token[:20]}...")

    # Step 2: Device info
    print("\n[2/3] Getting device info...")
    info = get_device_info(token)
    print(f"Response: {json.dumps(info, indent=2)}")

    # Step 3: Device status
    print("\n[3/3] Getting device status...")
    status = get_device_status(token)
    print(f"Response: {json.dumps(status, indent=2)}")

    if status.get("success"):
        parsed = parse_status(status.get("result", []))
        print(f"\n📊 Parsed Data:")
        print(f"   Voltage: {parsed['voltage']} V")
        print(f"   Current: {parsed['current']} A")
        print(f"   Power: {parsed['power']} W")
        print(f"   Switch: {'ON' if parsed['switch_on'] else 'OFF'}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
