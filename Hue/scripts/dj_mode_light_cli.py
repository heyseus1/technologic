# scripts/dj_mode_light_cli.py
from __future__ import annotations

import os
import sys

from hue_async.core.config import get_settings
from hue_async.clients.hue_client import HueClient
from hue_async.services.dj_mode import DJModeEngine, DJModeConfig


def prompt_float(prompt: str, default: float) -> float:
    raw = input(f"{prompt} [{default}]: ").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        print("Invalid number, using default.")
        return default


def prompt_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print("Invalid integer, using default.")
        return default


def prompt_bool(prompt: str, default: bool) -> bool:
    default_str = "Y/n" if default else "y/N"
    raw = input(f"{prompt} [{default_str}]: ").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes", "true", "1")


def main() -> None:
    # Settings come from .env via pydantic-settings (see src/hue_async/core/config.py)
    settings = get_settings()

    if not settings.HUE_USERNAME:
        raise SystemExit("HUE_USERNAME is missing in .env (Hue app key).")

    # DJ light ID is stored as a plain env var for now (prototype-friendly).
    # Add this to your .env:
    #   DJ_LIGHT_ID=<light resource id>
    dj_light_id = os.getenv("DJ_LIGHT_ID")
    if not dj_light_id:
        raise SystemExit(
            "DJ_LIGHT_ID missing in your environment.\n"
            "Add it to .env (or export it) after you discover it.\n"
            "Tip: run your device/light mapping script to find the light_id for the DJ lightstrip."
        )

    client = HueClient(settings.HUE_BRIDGE_IP, settings.HUE_USERNAME)
    engine = DJModeEngine(client)

    print("\n🎛️  DJ MODE (single light) — beat pulse + phrase color")
    print("This will pulse brightness on every beat and change color every N bars.")
    print("Press Ctrl+C to stop.\n")

    bpm = prompt_float("BPM", 124.0)
    bars_per_color_change = prompt_int("Color change every N bars", 8)
    beats_per_bar = prompt_int("Beats per bar (house is 4)", 4)

    base_brightness = prompt_float("Base brightness (resting) 0-100", 35.0)
    peak_brightness = prompt_float("Peak brightness (beat hit) 0-100", 85.0)
    pulse_hold_ms = prompt_int("Peak hold time (ms)", 80)

    snap = prompt_bool("Snap color changes (no fade)?", True)
    transition_ms = 0 if snap else prompt_int("Color transition (ms)", 200)

    use_random_color = prompt_bool("Use random colors?", True)

    cfg = DJModeConfig(
        bpm=bpm,
        beats_per_bar=beats_per_bar,
        bars_per_color_change=bars_per_color_change,
        base_brightness=base_brightness,
        peak_brightness=peak_brightness,
        pulse_hold_s=pulse_hold_ms / 1000.0,
        use_random_color=use_random_color,
        transition_ms=transition_ms,
        start_delay_s=1.0,
    )

    seconds_per_beat = engine.seconds_per_beat(cfg.bpm)
    phrase_beats = cfg.beats_per_bar * cfg.bars_per_color_change
    phrase_seconds = phrase_beats * seconds_per_beat

    print("\n✅ Running configuration")
    print(f"  Light: {dj_light_id}")
    print(f"  BPM: {cfg.bpm}  (beat ≈ {seconds_per_beat:.3f}s)")
    print(f"  Pulse: base {cfg.base_brightness:.0f}% → peak {cfg.peak_brightness:.0f}% (hold {pulse_hold_ms}ms)")
    print(f"  Color change: every {cfg.bars_per_color_change} bars ({phrase_beats} beats ≈ {phrase_seconds:.2f}s)")
    print(f"  Color mode: {'random' if cfg.use_random_color else 'palette (not wired here)'}")
    print(f"  Color transition: {'snap' if cfg.transition_ms == 0 else str(cfg.transition_ms) + 'ms'}")
    print("\nPress Ctrl+C to stop.\n")

    def on_beat(i: int) -> None:
        # Print occasionally to avoid spamming terminal (every 8 beats)
        if (i + 1) % 8 == 0:
            print(f"🥁 beat {i + 1}")

    def on_color_change(beat_index: int, label: str) -> None:
        print(f"🎨 color change @ beat {beat_index}: {label}")

    try:
        engine.run_beat_pulse_with_phrase_color(
            dj_light_id,
            cfg,
            on_beat=on_beat,
            on_color_change=on_color_change,
        )
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()