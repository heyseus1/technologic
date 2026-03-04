import os
import sys
import json
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def main() -> None:
    bridge_ip = os.getenv("HUE_BRIDGE_IP")
    app_key = os.getenv("HUE_USERNAME")  # username == hue-application-key for v2

    if not bridge_ip or not app_key:
        print("❌ Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    url = f"https://{bridge_ip}/clip/v2/resource/device"
    headers = {
        "hue-application-key": app_key,
        "Accept": "application/json",
    }

    r = requests.get(url, headers=headers, verify=False, timeout=10)

    # If Hue returns HTML, show it clearly (helps debugging)
    ct = r.headers.get("Content-Type", "")
    if "application/json" not in ct:
        print(f"❌ Expected JSON, got Content-Type: {ct}")
        print(r.text[:1000])
        sys.exit(1)

    data = r.json()
    devices = data.get("data", [])
    print(f"✅ Devices: {len(devices)}\n")
    for d in devices:
        name = (d.get("metadata") or {}).get("name", "Unknown")
        rid = d.get("id", "")
        print(f"- {name}  id={rid}")

if __name__ == "__main__":
    main()
