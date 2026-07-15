"""Core data models shared across backends, controls, and the UI.

These are plain dataclasses with no dependency on Spotify, pygame, or serial —
so they're easy to construct in tests and in the mock backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Number of graphic-EQ bands. The physical unit can't fit 10 motorized 60 mm
# faders across a 5" (127 mm) body, so we standardize on 7 bands + a preamp.
# See docs/architecture.md and hardware/BOM.md for the reasoning.
EQ_BANDS = 7

# ISO-ish center frequencies for a 7-band graphic EQ, in Hz.
EQ_FREQS = [60, 150, 400, 1000, 2400, 6000, 15000]


class PlaybackStatus(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class RepeatMode(Enum):
    OFF = "off"
    CONTEXT = "context"  # repeat the playlist
    TRACK = "track"      # repeat the current track


@dataclass
class Track:
    title: str = "—"
    artist: str = ""
    album: str = ""
    duration_ms: int = 0
    uri: str | None = None
    art_url: str | None = None

    @property
    def display(self) -> str:
        if self.artist:
            return f"{self.artist} - {self.title}"
        return self.title


@dataclass
class PlayerState:
    """The single source of truth the UI renders each frame."""

    status: PlaybackStatus = PlaybackStatus.STOPPED
    track: Track = field(default_factory=Track)
    position_ms: int = 0

    volume: float = 0.70          # 0.0 .. 1.0
    balance: float = 0.0          # -1.0 (L) .. +1.0 (R)

    shuffle: bool = False
    repeat: RepeatMode = RepeatMode.OFF

    playlist: list[Track] = field(default_factory=list)
    playlist_index: int = 0

    # Graphic EQ. Each band is a gain in dB, roughly -12 .. +12.
    eq_enabled: bool = True
    eq_preamp: float = 0.0
    eq_bands: list[float] = field(default_factory=lambda: [0.0] * EQ_BANDS)

    # Stream info shown on the little LCD readout.
    bitrate_kbps: int = 320
    sample_rate_hz: int = 44100
    stereo: bool = True

    # Live spectrum magnitudes (0.0 .. 1.0), one per visualizer bar.
    # Populated by the audio tap on real hardware; simulated in mock mode.
    spectrum: list[float] = field(default_factory=list)

    # "Up next" from the Spotify playback queue. Works for any playing context
    # (incl. followed/editorial playlists we can't read the tracklist of).
    queue: list[Track] = field(default_factory=list)

    @property
    def is_playing(self) -> bool:
        return self.status is PlaybackStatus.PLAYING

    @property
    def duration_ms(self) -> int:
        return self.track.duration_ms

    @property
    def progress(self) -> float:
        if self.track.duration_ms <= 0:
            return 0.0
        return min(1.0, self.position_ms / self.track.duration_ms)
