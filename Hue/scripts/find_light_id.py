import os
import sys
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

TARGET_DEVICE_NAME = "Hue lightstrip dj table"

def main():
    ip = os.getenv("HUE_BRIDGE_IP")
    key = os.getenv("HUE_USERNAME")
    if not ip or not key:
        print("Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    r = requests.get(
        f"https://{ip}/clip/v2/resource/device",
        headers={"hue-application-key": key, "Accept": "application/json"},
        verify=False,
        timeout=10,
    )
    r.raise_for_status()
    devices = r.json().get("data", [])

    for d in devices:
        name = (d.get("metadata") or {}).get("name")
        if name == TARGET_DEVICE_NAME:
            services = d.get("services") or []
            lights = [s.get("rid") for s in services if s.get("rtype") == "light" and s.get("rid")]
            print(f"Device: {name}")
            for lid in lights:
                print(f"light_id={lid}")
            return

    print(f"Device not found: {TARGET_DEVICE_NAME}")

if __name__ == "__main__":
    main()
