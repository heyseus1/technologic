import os
import sys
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

GROUPED_LIGHT_ID = "79869001-4976-4f15-bd0b-f2cc66a12acb"

def main() -> None:
    bridge_ip = os.getenv("HUE_BRIDGE_IP")
    app_key = os.getenv("HUE_USERNAME")  # username == hue-application-key

    if not bridge_ip or not app_key:
        print("❌ Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    url = f"https://{bridge_ip}/clip/v2/resource/grouped_light/{GROUPED_LIGHT_ID}"
    headers = {"hue-application-key": app_key, "Accept": "application/json"}

    r = requests.get(url, headers=headers, verify=False, timeout=10)
    r.raise_for_status()

    payload = r.json()
    data = payload.get("data", [])
    if not data:
        print("❌ No grouped_light data returned")
        sys.exit(1)

    gl = data[0]

    is_on = ((gl.get("on") or {}).get("on") is True)
    bri = (gl.get("dimming") or {}).get("brightness")

    print("\n✅ Bedroom grouped_light state")
    print(f"grouped_light_id={gl.get('id')}")
    print(f"on={is_on}")
    print(f"brightness={bri}")

    # Useful extra fields (present depending on devices)
    ct = (gl.get("color_temperature") or {}).get("mirek")
    if ct is not None:
        print(f"color_temperature_mirek={ct}")

    alert = (gl.get("alert") or {}).get("action")
    if alert:
        print(f"alert_action={alert}")

if __name__ == "__main__":
    main()
