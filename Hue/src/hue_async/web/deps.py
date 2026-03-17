from __future__ import annotations

from hue_async.clients.hue_client import HueClient
from hue_async.core.config import get_settings
from hue_async.services.room_service import RoomService


def get_room_service() -> RoomService:
    settings = get_settings()

    if not settings.HUE_USERNAME:
        raise RuntimeError("HUE_USERNAME is missing in .env")

    client = HueClient(settings.HUE_BRIDGE_IP, settings.HUE_USERNAME)
    return RoomService(client)