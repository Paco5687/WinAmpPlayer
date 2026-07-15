"""Playback backends.

``PlayerBackend`` is the interface the app drives. Implementations:

* ``MockPlayer`` — a self-contained simulation. No network, no credentials,
  no Premium. Advances a fake playlist so the UI has something to render.
* ``WebApiPlayer`` — controls a real Spotify device via the Web API (the desktop
  app during dev, go-librespot on the Pi). Plays *any* playlist, including ones
  you only follow. Network I/O is off the main thread.
* ``LibrespotPlayer`` — talks to a running `go-librespot` daemon over its own
  HTTP API. Requires Spotify Premium.

Each keeps a ``PlayerState`` up to date; the app calls ``poll()`` each frame.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Protocol

from .models import (
    PlaybackStatus,
    PlayerState,
    RepeatMode,
    Track,
)


class PlayerBackend(Protocol):
    state: PlayerState
    real_playback: bool   # True if this backend drives a real Spotify device

    def poll(self) -> None: ...
    def play_context(self, uri: str) -> bool: ...
    def play_pause(self) -> None: ...
    def stop(self) -> None: ...
    def next(self) -> None: ...
    def prev(self) -> None: ...
    def seek(self, position_ms: int) -> None: ...
    def set_volume(self, volume: float) -> None: ...
    def load_tracks(self, tracks: list[Track], context_uri: str | None = None) -> None: ...
    def select_track(self, index: int) -> None: ...
    def toggle_shuffle(self) -> None: ...
    def cycle_repeat(self) -> None: ...
    def set_eq_band(self, band: int, gain_db: float) -> None: ...
    def close(self) -> None: ...


# --------------------------------------------------------------------------- #
# Mock
# --------------------------------------------------------------------------- #

_DEMO_PLAYLIST = [
    Track("Midnight City", "M83", "Hurry Up, We're Dreaming", 241_000),
    Track("Digital Love", "Daft Punk", "Discovery", 301_000),
    Track("Teardrop", "Massive Attack", "Mezzanine", 330_000),
    Track("Windowlicker", "Aphex Twin", "Windowlicker", 366_000),
    Track("Roygbiv", "Boards of Canada", "Music Has the Right...", 152_000),
    Track("Strobe", "deadmau5", "For Lack of a Better Name", 634_000),
    Track("Porcelain", "Moby", "Play", 240_000),
]


class MockPlayer:
    """A believable fake player so we can build the whole UI without hardware."""

    real_playback = False   # simulated only — can't play followed playlists

    def __init__(self) -> None:
        self.state = PlayerState(playlist=list(_DEMO_PLAYLIST))
        self.state.track = self.state.playlist[0]
        self._last_tick = time.monotonic()

    def play_context(self, uri: str) -> bool:
        return False        # mock can't drive a real device

    # -- lifecycle --------------------------------------------------------- #
    def poll(self) -> None:
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        if self.state.is_playing:
            self.state.position_ms += int(dt * 1000)
            if self.state.position_ms >= self.state.track.duration_ms:
                self._advance(auto=True)

    def close(self) -> None:  # nothing to clean up
        pass

    # -- transport --------------------------------------------------------- #
    def play_pause(self) -> None:
        if self.state.status is PlaybackStatus.PLAYING:
            self.state.status = PlaybackStatus.PAUSED
        else:
            self.state.status = PlaybackStatus.PLAYING

    def stop(self) -> None:
        self.state.status = PlaybackStatus.STOPPED
        self.state.position_ms = 0

    def next(self) -> None:
        self._advance(auto=False)

    def prev(self) -> None:
        # WinAmp behavior: restart track if >3s in, else go to previous.
        if self.state.position_ms > 3000:
            self.state.position_ms = 0
            return
        idx = (self.state.playlist_index - 1) % len(self.state.playlist)
        self.select_track(idx)

    def seek(self, position_ms: int) -> None:
        self.state.position_ms = max(0, min(position_ms, self.state.track.duration_ms))

    def load_tracks(self, tracks: list[Track], context_uri: str | None = None) -> None:
        if not tracks:
            return
        self.state.playlist = list(tracks)
        self.state.playlist_index = 0
        self.state.track = tracks[0]
        self.state.position_ms = 0
        self.state.status = PlaybackStatus.PLAYING

    def select_track(self, index: int) -> None:
        if not self.state.playlist:
            return
        index %= len(self.state.playlist)
        self.state.playlist_index = index
        self.state.track = self.state.playlist[index]
        self.state.position_ms = 0
        self.state.status = PlaybackStatus.PLAYING

    def set_volume(self, volume: float) -> None:
        self.state.volume = max(0.0, min(1.0, volume))

    def toggle_shuffle(self) -> None:
        self.state.shuffle = not self.state.shuffle

    def cycle_repeat(self) -> None:
        order = [RepeatMode.OFF, RepeatMode.CONTEXT, RepeatMode.TRACK]
        i = order.index(self.state.repeat)
        self.state.repeat = order[(i + 1) % len(order)]

    def set_eq_band(self, band: int, gain_db: float) -> None:
        self.state.eq_bands[band] = max(-12.0, min(12.0, gain_db))

    # -- internal ---------------------------------------------------------- #
    def _advance(self, *, auto: bool) -> None:
        if auto and self.state.repeat is RepeatMode.TRACK:
            self.state.position_ms = 0
            return
        idx = self.state.playlist_index + 1
        if idx >= len(self.state.playlist):
            if auto and self.state.repeat is RepeatMode.OFF:
                self.stop()
                return
            idx = 0
        self.select_track(idx)


# --------------------------------------------------------------------------- #
# go-librespot (real hardware)
# --------------------------------------------------------------------------- #


class LibrespotPlayer:
    """Thin wrapper over the go-librespot HTTP API.

    go-librespot exposes ``GET /status`` plus ``POST /player/<command>`` and a
    websocket event stream. We poll ``/status`` here for simplicity; swap to the
    websocket later to cut latency. See docs/architecture.md.

    Requires: a running go-librespot daemon and Spotify Premium.
    """

    def __init__(self, base_url: str) -> None:
        import requests  # imported lazily so mock mode needs no extra deps

        self._requests = requests
        self._base = base_url.rstrip("/")
        self.state = PlayerState()

    def _post(self, path: str, json: dict | None = None) -> None:
        try:
            self._requests.post(f"{self._base}{path}", json=json, timeout=1.0)
        except Exception:  # noqa: BLE001 — never let a control glitch crash the UI
            pass

    def poll(self) -> None:
        try:
            r = self._requests.get(f"{self._base}/status", timeout=1.0)
            self._apply_status(r.json())
        except Exception:  # noqa: BLE001
            pass

    def _apply_status(self, s: dict) -> None:
        track = s.get("track") or {}
        self.state.track = Track(
            title=track.get("name", "—"),
            artist=", ".join(track.get("artist_names", [])) or track.get("artist", ""),
            album=track.get("album_name", ""),
            duration_ms=int(track.get("duration", 0)),
            uri=track.get("uri"),
            art_url=track.get("album_cover_url"),
        )
        self.state.position_ms = int(s.get("position", 0))
        self.state.volume = float(s.get("volume", 65535)) / 65535.0
        paused = s.get("paused", True)
        stopped = s.get("stopped", False)
        self.state.status = (
            PlaybackStatus.STOPPED if stopped
            else PlaybackStatus.PAUSED if paused
            else PlaybackStatus.PLAYING
        )

    # Transport maps onto go-librespot's /player/* endpoints.
    def play_pause(self) -> None: self._post("/player/playpause")
    def stop(self) -> None: self._post("/player/pause")
    def next(self) -> None: self._post("/player/next")
    def prev(self) -> None: self._post("/player/prev")
    def seek(self, position_ms: int) -> None: self._post("/player/seek", {"position": position_ms})
    def set_volume(self, volume: float) -> None:
        self._post("/player/volume", {"volume": int(volume * 65535)})
    def load_tracks(self, tracks, context_uri: str | None = None) -> None:
        # Metadata for the UI; actual playback of the context is started via the
        # Web API against this librespot device (wired in the app). TODO: device id.
        self.state.playlist = list(tracks)
        if tracks:
            self.state.track = tracks[0]
    def select_track(self, index: int) -> None: pass  # driven by Web API playlist ctx
    def toggle_shuffle(self) -> None: self._post("/player/shuffle_context", {"shuffle": True})
    def cycle_repeat(self) -> None: self._post("/player/repeat_context", {"repeat": True})
    def set_eq_band(self, band: int, gain_db: float) -> None:
        # EQ lives in the Pi's ALSA pipeline, not go-librespot. See audio_eq.py (TODO).
        self.state.eq_bands[band] = gain_db
    real_playback = True
    def play_context(self, uri: str) -> bool:
        self._post("/player/play", {"uri": uri}); return True
    def close(self) -> None: pass


# --------------------------------------------------------------------------- #
# Web API player — controls a real Spotify Connect device (the desktop app now,
# go-librespot on the Pi later) and mirrors its now-playing state. This is the
# only backend that can play playlists you merely *follow*.
# --------------------------------------------------------------------------- #


class WebApiPlayer:
    """Drive playback through the Spotify Web API against an active device.

    ALL network I/O runs on a background thread: transport commands are queued,
    volume/seek are coalesced (latest value wins), and now-playing is polled once
    a second. The main loop's ``poll()`` only applies the latest snapshot and
    advances the position locally, so the UI never blocks on the network.
    """

    real_playback = True

    def __init__(self, web) -> None:
        self.web = web
        self.state = PlayerState()
        self._device_id: str | None = None
        self._context_uri: str | None = None
        self.last_error: str = ""

        self._cmds: queue.Queue = queue.Queue()      # transport callables
        self._pending_vol: int | None = None         # coalesced volume (percent)
        self._pending_seek: int | None = None        # coalesced seek (ms)
        self._latest: tuple | None = None            # (status_dict_or_None,)
        self._last_tick = time.monotonic()
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    # -- background worker: all periodic + coalesced network I/O ---------- #
    def _loop(self) -> None:
        last_net = 0.0
        last_queue = 0.0
        while self._running:
            try:
                while True:
                    self._cmds.get_nowait()()
            except queue.Empty:
                pass
            except Exception as e:  # noqa: BLE001
                self.last_error = str(e)
            if self._pending_vol is not None:
                v, self._pending_vol = self._pending_vol, None
                self._safe(lambda: self.web.set_volume(v))
            if self._pending_seek is not None:
                s, self._pending_seek = self._pending_seek, None
                self._safe(lambda: self.web.seek(s))
            now = time.monotonic()
            if now - last_net >= 1.0:
                last_net = now
                try:
                    self._latest = (self.web.current_playback(),)
                except Exception as e:  # noqa: BLE001
                    self.last_error = str(e)
            if now - last_queue >= 4.0:      # "up next" changes slowly
                last_queue = now
                try:
                    self.state.queue = self.web.queue()   # atomic ref assign
                except Exception as e:  # noqa: BLE001
                    self.last_error = f"queue: {e}"
            time.sleep(0.1)

    def _safe(self, fn) -> None:
        try:
            fn()
            self.last_error = ""
        except Exception as e:  # noqa: BLE001
            self.last_error = str(e)

    def _ensure_device(self) -> str | None:
        if self._device_id:
            return self._device_id
        try:
            devs = self.web.devices()
        except Exception:  # noqa: BLE001
            return None
        if not devs:
            return None
        chosen = next((d for d in devs if d.get("is_active")), devs[0])
        self._device_id = chosen.get("id")
        return self._device_id

    # -- main-thread poll: apply latest snapshot, smooth the position ----- #
    def poll(self) -> None:
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        if self._latest is not None:
            data, self._latest = self._latest[0], None
            self._apply(data)
        elif self.state.status is PlaybackStatus.PLAYING:
            self.state.position_ms += int(dt * 1000)

    def _apply(self, data) -> None:
        if not data:
            self.state.status = PlaybackStatus.STOPPED
            self.state.queue = []
            return
        item = data.get("item") or {}
        album = item.get("album", {})
        images = album.get("images") or []
        self.state.track = Track(
            title=item.get("name", "—"),
            artist=", ".join(a["name"] for a in item.get("artists", [])),
            album=album.get("name", ""),
            duration_ms=int(item.get("duration_ms", 0)),
            uri=item.get("uri"),
            art_url=images[0]["url"] if images else None,
        )
        self.state.position_ms = int(data.get("progress_ms") or 0)
        self.state.status = (PlaybackStatus.PLAYING if data.get("is_playing")
                             else PlaybackStatus.PAUSED)
        dev = data.get("device") or {}
        if dev.get("id"):
            self._device_id = dev["id"]
        if dev.get("volume_percent") is not None:
            self.state.volume = dev["volume_percent"] / 100.0

    # -- transport: enqueue, update state optimistically for snappy UI ---- #
    def play_pause(self) -> None:
        if self.state.status is PlaybackStatus.PLAYING:
            self.state.status = PlaybackStatus.PAUSED
            self._cmds.put(self.web.pause)
        else:
            self.state.status = PlaybackStatus.PLAYING
            self._cmds.put(lambda: self.web.resume(self._ensure_device()))

    def stop(self) -> None:
        self.state.status = PlaybackStatus.PAUSED
        self._cmds.put(self.web.pause)

    def next(self) -> None: self._cmds.put(self.web.next_track)
    def prev(self) -> None: self._cmds.put(self.web.previous_track)

    def seek(self, position_ms: int) -> None:
        self.state.position_ms = max(0, position_ms)
        self._pending_seek = max(0, int(position_ms))

    def set_volume(self, volume: float) -> None:
        self.state.volume = max(0.0, min(1.0, volume))
        self._pending_vol = int(self.state.volume * 100)

    def load_tracks(self, tracks, context_uri: str | None = None) -> None:
        self.state.playlist = list(tracks)
        self._context_uri = context_uri
        if context_uri:
            self.play_context(context_uri)

    def play_context(self, uri: str) -> bool:
        """Synchronous (one deliberate action) so the caller learns success."""
        self._context_uri = uri
        dev = self._ensure_device()
        try:
            self.web.play_context(uri, device_id=dev)
            self.state.status = PlaybackStatus.PLAYING
            self.last_error = ""
            return True
        except Exception as e:  # noqa: BLE001
            self.last_error = str(e)
            return False

    def select_track(self, index: int) -> None:
        if self._context_uri and 0 <= index < len(self.state.playlist):
            uri = self._context_uri
            self.state.status = PlaybackStatus.PLAYING
            self._cmds.put(lambda: self.web.play_context(
                uri, device_id=self._ensure_device(), offset_position=index))

    def toggle_shuffle(self) -> None: pass
    def cycle_repeat(self) -> None: pass
    def set_eq_band(self, band: int, gain_db: float) -> None:
        self.state.eq_bands[band] = gain_db
    def close(self) -> None:
        self._running = False


def make_backend(cfg, web=None) -> PlayerBackend:
    if cfg.backend == "webapi" and web is not None:
        return WebApiPlayer(web)
    if cfg.backend == "librespot":
        return LibrespotPlayer(cfg.librespot_url)
    return MockPlayer()
