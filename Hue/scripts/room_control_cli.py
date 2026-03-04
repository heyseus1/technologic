# scripts/room_control_cli.py
from __future__ import annotations

from typing import Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from hue_async.core.config import get_settings
from hue_async.clients.hue_client import HueClient
from hue_async.services.room_service import RoomService

console = Console()


def vu_meter(brightness: Optional[float]) -> str:
    """
    Render a simple "VU meter" based on brightness (0-100).
    Returns a Rich-markup string.
    """
    if brightness is None:
        return "[dim]VU: unknown[/dim]"

    b = max(0.0, min(100.0, float(brightness)))
    blocks = 16
    filled = int(round((b / 100.0) * blocks))

    # Pick a char that gets "denser" with higher brightness
    if b < 25:
        fill_char = "▁"
        color = "green"
    elif b < 50:
        fill_char = "▃"
        color = "green"
    elif b < 75:
        fill_char = "▆"
        color = "yellow"
    else:
        fill_char = "█"
        color = "red"

    bar = fill_char * filled + "·" * (blocks - filled)
    return f"[bold]{color}[/bold]VU [{color}]{bar}[/{color}] [dim]{int(round(b))}%[/dim]"


def dj_banner(room_name: str, brightness: Optional[float]) -> Text:
    """
    Returns a Rich Text banner with a VU meter line.
    """
    meter = vu_meter(brightness)

    banner = f"""
╔══════════════════════════════════════════════════════╗
║            🎛️  DJ TABLE LIGHTS CONTROLLER            ║
║  Room: {room_name:<44}║
║  {meter:<52}║
║                                                      ║
║   [■]  [■]  [■]     ◉      ◉      ◉                  ║
║   ║║  ║║  ║║     ─┼─    ─┼─    ─┼─                   ║
║   ║║  ║║  ║║      │      │      │                    ║
║   └┘  └┘  └┘    (___)  (___)  (___)                  ║
║             🔊  Bass | Mid | High                    ║
╚══════════════════════════════════════════════════════╝
""".strip(
        "\n"
    )

    # Text.from_markup lets us include Rich markup (the VU meter string)
    return Text.from_markup(banner, justify="center")


def brightness_bar(value: Optional[float]) -> str:
    if value is None:
        return "[dim]unknown[/dim]"
    v = max(0, min(100, int(round(value))))
    blocks = 20
    filled = int(round((v / 100) * blocks))
    return f"[{'█' * filled}{'░' * (blocks - filled)}] {v}%"


def choose_from_list(title: str, items: list[str], allow_skip: bool = False) -> Optional[int]:
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=4, justify="right")
    table.add_column("Option", style="white")

    for i, name in enumerate(items, start=1):
        table.add_row(str(i), name)

    if allow_skip:
        table.add_row("0", "[dim]Skip[/dim]")

    console.print(table)

    while True:
        choice = IntPrompt.ask("Select", default=0 if allow_skip else 1)
        if allow_skip and choice == 0:
            return None
        if 1 <= choice <= len(items):
            return choice - 1
        console.print("[red]Invalid choice.[/red]")


def prompt_brightness(current: Optional[float]) -> Optional[float]:
    cur_txt = "unknown" if current is None else f"{current:.1f}"
    raw = Prompt.ask(f"Brightness 0-100 (current {cur_txt}) [enter to skip]", default="")
    raw = raw.strip()
    if raw == "":
        return None
    try:
        val = float(raw)
    except ValueError:
        console.print("[red]Invalid number.[/red]")
        return None
    if not (0 <= val <= 100):
        console.print("[red]Brightness must be 0–100.[/red]")
        return None
    return val


def main() -> None:
    settings = get_settings()
    if not settings.HUE_USERNAME:
        raise SystemExit("HUE_USERNAME is missing in .env (Hue app key).")

    client = HueClient(settings.HUE_BRIDGE_IP, settings.HUE_USERNAME)
    service = RoomService(client)

    # Small neutral splash first (we don't know room/brightness yet)
    console.print(
        Panel.fit(
            Text("Hue Room Controller", style="bold bright_cyan"),
            subtitle="Local-only • Rooms • Scenes • Brightness",
            border_style="bright_cyan",
        )
    )

    rooms = service.list_rooms()
    if not rooms:
        console.print("[red]No controllable rooms found.[/red]")
        return

    ridx = choose_from_list("Rooms", [r.name for r in rooms], allow_skip=False)
    room = rooms[ridx]

    is_on, bri = service.get_grouped_light_state(room.grouped_light_id)

    # Now print the DJ banner with a VU meter based on brightness
    console.print(
        Panel(
            Align.center(dj_banner(room.name, bri)),
            subtitle="Local-only • Rooms • Scenes • Brightness",
            border_style="bright_cyan",
        )
    )

    console.print(
        Panel(
            f"[bold]{room.name}[/bold]\n"
            f"Power: {'[green]ON[/green]' if is_on else '[red]OFF[/red]'}\n"
            f"Brightness: {brightness_bar(bri)}",
            title="Current Status",
            border_style="magenta",
        )
    )

    # Power menu
    toggle_idx = choose_from_list(
        "Power",
        ["Turn ON", "Turn OFF", "Leave as-is"],
        allow_skip=False,
    )

    if toggle_idx == 0:
        service.set_room_power(room.grouped_light_id, True)
        console.print("[green]✅ Turned ON[/green]\n")
    elif toggle_idx == 1:
        service.set_room_power(room.grouped_light_id, False)
        console.print("[yellow]✅ Turned OFF. Done.[/yellow]")
        return

    # Scene first
    scenes = service.list_scenes_for_room(room.room_id)
    scene_id = None
    if scenes:
        sidx = choose_from_list(
            f"Scenes for {room.name}",
            [s.name for s in scenes],
            allow_skip=True,
        )
        if sidx is not None:
            scene_id = scenes[sidx].scene_id

    if scene_id:
        service.activate_scene(scene_id)
        console.print("[green]🎬 Scene activated[/green]\n")
        # Refresh state after scene
        is_on, bri = service.get_grouped_light_state(room.grouped_light_id)

        # Optional: show updated VU after scene
        console.print(
            Panel(
                Align.center(dj_banner(room.name, bri)),
                subtitle="VU updated after scene",
                border_style="bright_cyan",
            )
        )

    # Brightness trim
    new_bri = prompt_brightness(bri)
    if new_bri is not None:
        service.set_room_brightness(room.grouped_light_id, new_bri)
        console.print(f"[green]🌗 Brightness set to {new_bri:.0f}%[/green]")

    console.print("\n[bold bright_cyan]Done.[/bold bright_cyan]")


if __name__ == "__main__":
    main()