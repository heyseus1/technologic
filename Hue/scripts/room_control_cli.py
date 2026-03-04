# scripts/room_control_cli.py
from hue_async.core.config import get_settings
from hue_async.clients.hue_client import HueClient
from hue_async.services.room_service import RoomService


def prompt_choice(prompt: str, choices: list[str], allow_skip: bool = False):
    print(prompt)
    for i, c in enumerate(choices, start=1):
        print(f"  {i}) {c}")
    if allow_skip:
        print("  0) Skip")
    while True:
        raw = input("> ").strip()
        if allow_skip and raw == "0":
            return None
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(choices):
                return n - 1
        print("Enter a valid number.")


def prompt_brightness(current):
    raw = input(f"Brightness (0-100) [current {current}] (Enter to skip): ").strip()
    if raw == "":
        return None
    try:
        val = float(raw)
    except ValueError:
        print("Invalid number.")
        return None
    if 0 <= val <= 100:
        return val
    print("Brightness must be 0-100.")
    return None


def main():
    settings = get_settings()
    if not settings.HUE_USERNAME:
        raise SystemExit("HUE_USERNAME is missing in .env (this is the Hue app key).")

    client = HueClient(settings.HUE_BRIDGE_IP, settings.HUE_USERNAME)
    service = RoomService(client)

    rooms = service.list_rooms()
    if not rooms:
        raise SystemExit("No controllable rooms found.")

    idx = prompt_choice("\nSelect a room to control:", [r.name for r in rooms])
    room = rooms[idx]

    on, bri = service.get_grouped_light_state(room.grouped_light_id)
    print(f"\n✅ Room: {room.name}\n  on:        {on}\n  brightness:{bri}\n")

    toggle = prompt_choice("Toggle power?", ["Turn ON", "Turn OFF", "Leave as-is"])
    if toggle == 0:
        service.set_room_power(room.grouped_light_id, True)
        print("✅ Turned ON\n")
    elif toggle == 1:
        service.set_room_power(room.grouped_light_id, False)
        print("✅ Turned OFF. Done.")
        return

    # Scene first
    scenes = service.list_scenes_for_room(room.room_id)
    scene_id = None
    if scenes:
        sidx = prompt_choice(f"Select a scene for {room.name}:", [s.name for s in scenes], allow_skip=True)
        if sidx is not None:
            scene_id = scenes[sidx].scene_id

    if scene_id:
        service.activate_scene(scene_id)
        print("✅ Scene activated\n")
        on, bri = service.get_grouped_light_state(room.grouped_light_id)

    # Brightness trim
    new_bri = prompt_brightness(bri)
    if new_bri is not None:
        service.set_room_brightness(room.grouped_light_id, new_bri)
        print("✅ Brightness updated")

    print("Done.")


if __name__ == "__main__":
    main()
