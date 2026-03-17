from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional

from hue_async.clients.hue_client import HueClient


@dataclass(frozen=True)
class DJModeConfig:
    bpm: float = 124.0

    # Musical structure
    beats_per_bar: int = 4          # house 4/4
    bars_per_color_change: int = 8  # phrase change

    # Brightness pump (kick)
    base_brightness: float = 35.0   # resting brightness
    peak_brightness: float = 85.0   # hit on each beat
    pulse_hold_s: float = 0.08      # how long to hold the peak (seconds)

    # Color behavior
    use_random_color: bool = True
    transition_ms: int = 0          # 0 = snap (recommended for DJ)

    start_delay_s: float = 1.0      # gives you time after hitting enter


class DJModeEngine:
    def __init__(self, client: HueClient) -> None:
        self.client = client

    @staticmethod
    def seconds_per_beat(bpm: float) -> float:
        return 60.0 / float(bpm)

    @staticmethod
    def _random_xy() -> tuple[float, float]:
        # “safe-ish” xy range for a fun neon vibe
        x = random.uniform(0.15, 0.7)
        y = random.uniform(0.1, 0.8)
        return x, y

    def _put_light(self, light_id: str, body: dict) -> None:
        # Keep payload minimal for snappiness
        self.client.put(f"/clip/v2/resource/light/{light_id}", body)

    def _set_color(self, light_id: str, x: float, y: float, transition_ms: int) -> None:
        body = {
            "on": {"on": True},
            "color": {"xy": {"x": float(x), "y": float(y)}},
        }
        if transition_ms and transition_ms > 0:
            body["dynamics"] = {"duration": int(transition_ms)}
        self._put_light(light_id, body)

    def _set_brightness(self, light_id: str, brightness: float) -> None:
        body = {
            "on": {"on": True},
            "dimming": {"brightness": float(brightness)},
        }
        self._put_light(light_id, body)

    def run_beat_pulse_with_phrase_color(
        self,
        light_id: str,
        cfg: DJModeConfig,
        *,
        on_beat=None,
        on_color_change=None,
    ) -> None:
        """
        Beat-synced pump + slower color changes:
        - Every beat: brightness -> peak, brief hold, then back to base
        - Every N bars: change color (snap by default)

        This gives a “kick pump” feel without hammering the bridge with high-rate color updates.
        """
        spb = self.seconds_per_beat(cfg.bpm)
        beats_per_color_change = cfg.beats_per_bar * cfg.bars_per_color_change

        # Start with base brightness
        self._set_brightness(light_id, cfg.base_brightness)

        # Drift-correct beat scheduling
        start = time.monotonic() + float(cfg.start_delay_s)
        beat_index = 0

        # Pick initial color (optional but feels nice)
        if cfg.use_random_color:
            x, y = self._random_xy()
            self._set_color(light_id, x, y, cfg.transition_ms)
            if on_color_change:
                on_color_change(0, f"init xy=({x:.3f},{y:.3f})")

        while True:
            target_time = start + (beat_index * spb)
            now = time.monotonic()

            # Sleep until the next beat
            if now < target_time:
                time.sleep(min(0.05, target_time - now))
                continue

            # Phrase color change on boundaries (every N bars)
            if beat_index > 0 and (beat_index % beats_per_color_change) == 0:
                if cfg.use_random_color:
                    x, y = self._random_xy()
                    self._set_color(light_id, x, y, cfg.transition_ms)
                    if on_color_change:
                        on_color_change(beat_index, f"xy=({x:.3f},{y:.3f})")

            # Beat pulse: peak then back to base
            self._set_brightness(light_id, cfg.peak_brightness)
            if on_beat:
                on_beat(beat_index)

            # Hold peak briefly, then return to base (still within the same beat window)
            time.sleep(max(0.0, float(cfg.pulse_hold_s)))
            self._set_brightness(light_id, cfg.base_brightness)

            beat_index += 1