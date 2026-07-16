"""Configuration loading.

Zero-config by default: everything runs mocked so you can develop the UI on a
laptop. Drop a ``config.toml`` next to ``config.example.toml`` to point at a
real go-librespot instance and the serial port for the microcontroller.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # "mock" (simulated player) or "librespot" (real go-librespot HTTP API).
    backend: str = "mock"
    librespot_url: str = "http://localhost:3678"

    # "mock" (no hardware) or "serial" (microcontroller over USB).
    controls: str = "mock"
    serial_port: str = "COM3"      # e.g. "/dev/ttyACM0" on the Pi
    serial_baud: int = 115200

    # Battery. "none" | "mock" (simulated, for UI dev) | "x728" (Geekworm UPS).
    battery: str = "none"
    battery_i2c_bus: int = 1
    battery_low_shutdown: bool = False   # only ever acts on real hardware

    # UI.
    fullscreen: bool = False       # True on the device's LCD
    window_size: tuple[int, int] = (720, 720)  # square — HyperPixel 4.0 Square
    fps: int = 30
    show_hardware_legend: bool = True  # shade physical vs touchscreen regions

    # Spotify Web API (for playlists / album art). Optional in mock mode.
    # PKCE flow — only the client id is needed; no secret lives on the device.
    spotify_client_id: str = ""
    spotify_redirect_port: int = 8888   # loopback callback port
    # Where the refresh/access token is cached. Empty -> next to config.toml.
    spotify_token_path: str = ""

    @property
    def spotify_redirect_uri(self) -> str:
        # Must match the dashboard exactly. Loopback + explicit 127.0.0.1
        # (Spotify banned "localhost"); plain HTTP is allowed for loopback.
        return f"http://127.0.0.1:{self.spotify_redirect_port}/callback"

    def token_path(self) -> Path:
        if self.spotify_token_path:
            return Path(self.spotify_token_path)
        return Path(__file__).resolve().parent.parent / "spotify_token.json"

    @staticmethod
    def load(path: str | Path | None = None) -> "Config":
        cfg = Config()
        if path is None:
            path = Path(__file__).resolve().parent.parent / "config.toml"
        path = Path(path)
        if not path.exists():
            return cfg
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for section in data.values() if _is_sectioned(data) else [data]:
            for key, value in section.items():
                if hasattr(cfg, key):
                    if key == "window_size":
                        value = tuple(value)
                    setattr(cfg, key, value)
        return cfg


def _is_sectioned(data: dict) -> bool:
    return all(isinstance(v, dict) for v in data.values()) and bool(data)
