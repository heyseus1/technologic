import os
import sys
import requests
import urllib3
from dotenv import load_dotenv

# Suppress the insecure HTTPS warning (equivalent to curl -k)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


def main():
    bridge_ip = os.getenv("HUE_BRIDGE_IP")

    if not bridge_ip:
        print("❌ HUE_BRIDGE_IP not set in .env")
        sys.exit(1)

    url = f"https://{bridge_ip}/api"

    payload = {
        "devicetype": "hue-async-poc#macbook",
        "generateclientkey": True,
    }

    print(f"\n🔐 Registering Hue app with bridge at {bridge_ip}")
    print("👉 Press the physical button on the bridge now...\n")

    try:
        response = requests.post(
            url,
            json=payload,
            verify=False,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)

    data = response.json()

    if not isinstance(data, list) or not data:
        print("❌ Unexpected response from bridge.")
        sys.exit(1)

    result = data[0]

    if "error" in result:
        error = result["error"]
        if error.get("type") == 101:
            print("❌ Link button not pressed.")
            print("Press the button and run the script again within 30 seconds.")
        else:
            print(f"❌ Hue error: {error.get('description')}")
        sys.exit(1)

    success = result.get("success", {})
    username = success.get("username")
    clientkey = success.get("clientkey")

    if not username:
        print("❌ Registration failed: no username returned.")
        sys.exit(1)

    print("✅ Registration successful!\n")
    print("Add these values to your .env file:\n")
    print(f"HUE_USERNAME={username}")
    print(f"HUE_CLIENTKEY={clientkey}")
    print("\nDone.")


if __name__ == "__main__":
    main()