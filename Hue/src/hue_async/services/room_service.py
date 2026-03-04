from __future__ import annotations

"""
RoomService: business logic for controlling Hue rooms.

Hue v2 recap:
- "room" is a resource: /clip/v2/resource/room
- Each room has services. For room-wide control we use the room's
  "grouped_light" service (rtype=grouped_light) which provides a rid.
- "scene" is a resource: /clip/v2/resource/scene
  Scenes are linked to a room by: scene.group.rtype == "room" and scene.group.rid == room.id

This module stays *agnostic*:
- No hardcoded room names or IDs.
- It only provides helpers to list rooms, read state, and apply changes.
"""

from dataclasses import dataclass
from typing import Optional

from hue_async.clients.hue_client import HueClient


@dataclass(frozen=True)
class Room:
    """
    A simplified, CLI-friendly representation of a Hue room.
    We store the grouped_light_id because that's what we control for room-wide power/brightness.
    """
    name: str
    room_id: str
    grouped_light_id: str


@dataclass(frozen=True)
class Scene:
    """A simplified representation of a Hue scene."""
    name: str
    scene_id: str


class RoomService:
    """
    Service layer for room operations.

    This class depends on HueClient:
    - HueClient handles HTTP transport and headers.
    - RoomService focuses on Hue resource relationships and "what to do".
    """

    def __init__(self, client: HueClient) -> None:
        self.client = client

    def list_rooms(self) -> list[Room]:
        """
        Return a list of controllable rooms (rooms that have a grouped_light service).
        """
        payload = self.client.get("/clip/v2/resource/room")
        rooms = payload.get("data", []) or []

        out: list[Room] = []
        for r in rooms:
            name = (r.get("metadata") or {}).get("name", "Unknown")
            room_id = r.get("id")
            grouped_light_id = self._grouped_light_id(r)

            # Only include rooms that can be controlled as a room (grouped_light exists).
            if room_id and grouped_light_id:
                out.append(Room(name=name, room_id=room_id, grouped_light_id=grouped_light_id))

        return out

    def _grouped_light_id(self, room_obj: dict) -> Optional[str]:
        """
        Hue rooms have a "services" list. We want the service entry where:
          rtype == "grouped_light"
        and then use its rid as grouped_light_id.
        """
        for s in (room_obj.get("services") or []):
            if s.get("rtype") == "grouped_light" and s.get("rid"):
                return s["rid"]
        return None

    def get_grouped_light_state(self, grouped_light_id: str) -> tuple[bool, Optional[float]]:
        """
        Read a grouped_light resource (room-wide control) and return:
          (is_on, brightness)
        brightness is 0-100, may be None depending on device/bridge response.
        """
        payload = self.client.get(f"/clip/v2/resource/grouped_light/{grouped_light_id}")
        data = payload.get("data", []) or []
        if not data:
            raise RuntimeError(f"Grouped light not found: {grouped_light_id}")

        gl = data[0]
        is_on = (gl.get("on") or {}).get("on", False)
        bri = (gl.get("dimming") or {}).get("brightness")
        return is_on, bri

    def set_room_power(self, grouped_light_id: str, on: bool) -> None:
        """
        Turn a room on or off via its grouped_light resource.
        We use PUT because your bridge returned 405 for PATCH.
        """
        self.client.put(f"/clip/v2/resource/grouped_light/{grouped_light_id}", {"on": {"on": on}})

    def set_room_brightness(self, grouped_light_id: str, brightness: float) -> None:
        """
        Set room brightness (0-100) via grouped_light.
        """
        self.client.put(
            f"/clip/v2/resource/grouped_light/{grouped_light_id}",
            {"dimming": {"brightness": float(brightness)}},
        )

    def list_scenes_for_room(self, room_id: str) -> list[Scene]:
        """
        Return scenes that belong to a specific room (by room_id).
        """
        payload = self.client.get("/clip/v2/resource/scene")
        scenes = payload.get("data", []) or []

        out: list[Scene] = []
        for s in scenes:
            group = s.get("group") or {}
            if group.get("rtype") == "room" and group.get("rid") == room_id:
                name = (s.get("metadata") or {}).get("name", "Unnamed scene")
                scene_id = s.get("id")
                if scene_id:
                    out.append(Scene(name=name, scene_id=scene_id))

        return out

    def activate_scene(self, scene_id: str) -> None:
        """
        Activate a scene by setting recall.action=active.
        """
        self.client.put(f"/clip/v2/resource/scene/{scene_id}", {"recall": {"action": "active"}})
