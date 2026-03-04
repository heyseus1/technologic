import os
import sys
import json
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BEDROOM_ROOM_ID = "ddb5b645-7b81-4c7e-a9e2-a8afd324dc0a"

def main() -> None:
    bridge_ip = os.getenv("HUE_BRIDGE_IP")
    app_key = os.getenv("HUE_USERNAME")  # username == hue-application-key

    if not bridge_ip or not app_key:
        print("❌ Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    url = f"https://{bridge_ip}/clip/v2/resource/room/{BEDROOM_ROOM_ID}"
    headers = {"hue-application-key": app_key, "Accept": "application/json"}

    r = requests.get(url, headers=headers, verify=False, timeout=10)
    r.raise_for_status()

    payload = r.json()
    data = payload.get("data", [])
    if not data:
        print("❌ No room data returned")
        sys.exit(1)

    room = data[0]
    name = (room.get("metadata") or {}).get("name", "Unknown")
    print(f"\n✅ Room: {name}")
    print(f"room_id={room.get('id')}")

    # Print the important linkage fields for next steps
    print("\nServices (things you can control at room-level):")
    for s in (room.get("services") or []):
        print(f"- rtype={s.get('rtype')}  rid={s.get('rid')}")

    print("\nChildren (things contained in the room):")
    for c in (room.get("children") or []):
        print(f"- rtype={c.get('rtype')}  rid={c.get('rid')}")

    # Optional: full JSON for debugging
    # print("\n--- Full room JSON ---")
    # print(json.dumps(room, indent=2))

if __name__ == "__main__":
    main()
