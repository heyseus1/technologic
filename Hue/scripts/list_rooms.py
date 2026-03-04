import os
import sys
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

def main() -> None:
    bridge_ip = os.getenv("HUE_BRIDGE_IP")
    app_key = os.getenv("HUE_USERNAME")  # username == hue-application-key

    if not bridge_ip or not app_key:
        print("❌ Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    url = f"https://{bridge_ip}/clip/v2/resource/room"
    headers = {"hue-application-key": app_key, "Accept": "application/json"}

    r = requests.get(url, headers=headers, verify=False, timeout=10)
    r.raise_for_status()
    data = r.json().get("data", [])

    print(f"✅ Rooms: {len(data)}\n")
    for room in data:
        name = (room.get("metadata") or {}).get("name", "Unknown")
        rid = room.get("id", "")
        print(f"- {name}  room_id={rid}")

if __name__ == "__main__":
    main()
