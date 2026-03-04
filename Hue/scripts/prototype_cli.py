import os
import sys
import urllib3
import requests
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BRIDGE_ROOM_ID = "ddb5b645-7b81-4c7e-a9e2-a8afd324dc0a"
GROUPED_LIGHT_ID = "79869001-4976-4f15-bd0b-f2cc66a12acb"


def get_env():
    bridge_ip = os.getenv("HUE_BRIDGE_IP")
    app_key = os.getenv("HUE_USERNAME")

    if not bridge_ip or not app_key:
        print("❌ Missing HUE_BRIDGE_IP or HUE_USERNAME in .env")
        sys.exit(1)

    return bridge_ip, app_key


def get_json(url, headers):
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    r.raise_for_status()
    return r.json()


def put_json(url, headers, body):
    r = requests.put(url, headers=headers, json=body, verify=False, timeout=10)
    r.raise_for_status()
    if r.content:
        return r.json()
    return {}


def prompt_choice(prompt, choices, allow_skip=True):
    print(prompt)

    for i, c in enumerate(choices, start=1):
        print(f"  {i}) {c}")

    if allow_skip:
        print("  0) Skip")

    while True:
        choice = input("> ").strip()

        if allow_skip and choice == "0":
            return None

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(choices):
                return idx - 1

        print("Enter a valid number.")


def prompt_brightness(current):
    raw = input(f"Brightness (0-100) [current {current}] (Enter to skip): ").strip()

    if raw == "":
        return None

    try:
        val = float(raw)
    except ValueError:
        print("Invalid number. Skipping brightness change.")
        return None

    if not (0 <= val <= 100):
        print("Brightness must be between 0-100.")
        return None

    return val


def read_grouped_light_state(bridge_ip, headers):
    gl_url = f"https://{bridge_ip}/clip/v2/resource/grouped_light/{GROUPED_LIGHT_ID}"
    state = get_json(gl_url, headers)["data"][0]
    is_on = state["on"]["on"]
    brightness = state["dimming"]["brightness"]
    return gl_url, is_on, brightness


def main():
    bridge_ip, app_key = get_env()

    headers = {
        "hue-application-key": app_key,
        "Accept": "application/json",
    }

    put_headers = {
        "hue-application-key": app_key,
        "Content-Type": "application/json",
    }

    gl_url, is_on, brightness = read_grouped_light_state(bridge_ip, headers)

    print("\n✅ Bedroom status")
    print(f"  on:        {is_on}")
    print(f"  brightness:{brightness}\n")

    toggle = prompt_choice("Toggle power?", ["Turn ON", "Turn OFF"], True)

    # TURN OFF → APPLY AND EXIT
    if toggle == 1:
        put_json(gl_url, put_headers, {"on": {"on": False}})
        print("✅ Bedroom turned OFF. Done.")
        return

    # TURN ON → APPLY AND CONTINUE
    if toggle == 0:
        put_json(gl_url, put_headers, {"on": {"on": True}})
        print("✅ Bedroom turned ON\n")

    # ---- SCENE FIRST ----
    scenes_url = f"https://{bridge_ip}/clip/v2/resource/scene"
    scenes_data = get_json(scenes_url, headers)["data"]

    bedroom_scenes = []
    for scene in scenes_data:
        group = scene.get("group", {})
        if group.get("rid") == BRIDGE_ROOM_ID:
            name = scene["metadata"]["name"]
            bedroom_scenes.append((name, scene["id"]))

    scene_id = None
    if bedroom_scenes:
        idx = prompt_choice(
            "Select a Bedroom scene to activate:",
            [x[0] for x in bedroom_scenes],
        )
        if idx is not None:
            scene_id = bedroom_scenes[idx][1]

    if scene_id:
        scene_url = f"https://{bridge_ip}/clip/v2/resource/scene/{scene_id}"
        put_json(scene_url, put_headers, {"recall": {"action": "active"}})
        print("✅ Scene activated\n")

        # Re-read state after scene so the brightness prompt shows accurate current value
        _, _, brightness = read_grouped_light_state(bridge_ip, headers)

    # ---- THEN BRIGHTNESS TRIM ----
    new_brightness = prompt_brightness(brightness)

    if new_brightness is not None:
        put_json(gl_url, put_headers, {"dimming": {"brightness": new_brightness}})
        print("✅ Brightness updated")

    if scene_id is None and new_brightness is None and toggle is None:
        print("No changes requested.")


if __name__ == "__main__":
    main()