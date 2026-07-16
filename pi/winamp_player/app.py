"""Application entry point: main loop, action routing, motor sync.

Responsibilities:
  * poll the playback backend and physical controls
  * route semantic actions (from the UI or the microcontroller) to the backend
  * drive the motorized faders back toward the current state (the magic bit:
    the seek fader physically follows the song, volume follows volume, EQ
    faders snap to the active preset) — unless the user is touching them.
"""

from __future__ import annotations

import sys

import pygame

from .config import Config
from .controls import (
    ButtonId,
    ControlEvent,
    ControlEventType,
    FaderId,
    FADER_MAX,
    cmd_fader_target,
    make_controls,
)
from .images import ImageCache
from .library import BrowseState, make_library
from .models import EQ_BANDS, PlaybackStatus, Track
from .power import make_battery
from .spotify import make_backend
from .spotify_web import make_web
from .ui.screen import ScreenUI


class App:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        pygame.init()
        pygame.display.set_caption("WinAmp · Physical Edition")
        flags = pygame.FULLSCREEN if cfg.fullscreen else 0
        self.surface = pygame.display.set_mode(cfg.window_size, flags)
        self.clock = pygame.time.Clock()

        # One shared Web API client feeds both playback (webapi backend) and browsing.
        self.web = make_web(cfg)
        self.backend = make_backend(cfg, self.web)
        self.controls = make_controls(cfg)

        # Browsing (real Spotify playlists) + async album art.
        self.images = ImageCache()
        self.screen = ScreenUI(self.surface, self.on_action, self.images)
        self.browse = BrowseState()
        self.browse.can_play_followed = getattr(self.backend, "real_playback", False)
        self.library, msg = make_library(self.web)
        if self.library is not None:
            self.browse.has_library = True
            self.browse.view = "library"
            self.browse.loading = True
            self.library.start()
        else:
            print(f"[library] {msg} — using demo playlist")

        self.battery = make_battery(cfg)
        self._battery_accum = 99.0           # read on first frame

        self._grabbed: set[int] = set()      # fader ids the user is touching
        self._last_sent: dict[int, int] = {}  # last target per fader (avoid spam)
        self.running = True

    # ------------------------------------------------------------------ #
    # action routing (shared by mouse UI and physical controls)
    # ------------------------------------------------------------------ #
    def on_action(self, action: str, **kw) -> None:
        b, st = self.backend, self.backend.state
        if action == "play":
            if st.status is not PlaybackStatus.PLAYING:
                b.play_pause()
        elif action == "play_pause":
            b.play_pause()
        elif action == "stop":
            b.stop()
        elif action == "next":
            b.next()
        elif action == "prev":
            b.prev()
        elif action == "set_view":
            self.screen.set_view(kw["name"])
        elif action == "show_library":       # legacy alias -> Playlists view
            self.screen.set_view("playlists")
        elif action == "open_playlist":
            self._open_playlist(kw["index"])
            self.screen.set_view("now_playing")
        elif action == "seek":
            b.seek(kw["position_ms"])
        elif action == "set_volume":
            b.set_volume(kw["volume"])
        elif action == "set_eq_band":
            b.set_eq_band(kw["band"], kw["gain_db"])
        elif action == "set_preamp":
            st.eq_preamp = max(-12.0, min(12.0, kw["gain_db"]))
        elif action == "select_track":
            b.select_track(kw["index"])
        elif action == "toggle_shuffle":
            b.toggle_shuffle()
        elif action == "cycle_repeat":
            b.cycle_repeat()

    # ------------------------------------------------------------------ #
    # library browsing
    # ------------------------------------------------------------------ #
    def _open_playlist(self, index: int) -> None:
        if not self.library or not (0 <= index < len(self.browse.playlists)):
            return
        pl = self.browse.playlists[index]
        self.browse.current_playlist = pl.name
        self.browse.note = ""
        if pl.owned:
            # We can read the tracklist (Dev Mode allows owned/collaborative).
            self.library.open_playlist(pl)          # async -> 'tracks' event
        elif getattr(self.backend, "real_playback", False):
            # Can't read the tracklist, but we *can* play it by context URI.
            self.browse.view = "playlist"
            self.backend.state.playlist = []
            if not self.backend.play_context(pl.uri):
                self.browse.note = self._device_hint()
        else:
            self.browse.view = "playlist"
            self.backend.state.playlist = []
            self.backend.state.track = Track()
            self.browse.note = ("Followed playlists need real playback — set "
                                "backend = \"webapi\" in config.toml and open Spotify.")

    def _device_hint(self) -> str:
        err = getattr(self.backend, "last_error", "")
        if "404" in err or "NO_ACTIVE_DEVICE" in err.upper():
            return "No active Spotify device — open the Spotify app (or start go-librespot) and try again."
        return f"Couldn't start playback: {err}" if err else "Couldn't start playback."

    def _pump_library(self) -> None:
        if not self.library:
            return
        for kind, payload in self.library.poll():
            if kind == "playlists":
                self.browse.playlists = payload
                self.browse.loading = False
                # prefetch playlist thumbnails so the list looks alive fast
                for pl in payload:
                    if pl.image_url:
                        self.images.get(pl.image_url, (40, 40))
            elif kind == "tracks":
                playlist, tracks = payload
                self.browse.current_playlist = playlist.name
                self.browse.view = "playlist"
                if tracks:
                    self.browse.note = ""
                    self.backend.load_tracks(tracks, context_uri=playlist.uri)
                else:
                    # We only fetch tracks for owned playlists, so empty = empty.
                    self.browse.note = "This playlist has no tracks."
                    self.backend.stop()
                    self.backend.state.playlist = []
                    self.backend.state.track = Track()
            elif kind == "error":
                self.browse.error = str(payload)
                self.browse.loading = False
                print(f"[library] {payload}")

    # ------------------------------------------------------------------ #
    # battery
    # ------------------------------------------------------------------ #
    def _read_battery(self, dt: float) -> None:
        if not self.battery:
            return
        self._battery_accum += dt
        if self._battery_accum < 2.0:
            return
        self._battery_accum = 0.0
        bs = self.battery.read()
        st = self.backend.state
        if bs is None:
            st.battery_percent = None
            return
        st.battery_percent = bs.percent
        st.battery_charging = bs.charging
        # Clean shutdown on critical battery — real hardware only, opt-in only,
        # so a laptop in "mock" mode can never trigger it.
        if (self.cfg.battery_low_shutdown and self.cfg.battery == "x728"
                and not bs.charging and bs.percent <= 5.0):
            print("[power] battery critically low — shutting down")
            import os
            os.system("sudo shutdown -h now")

    # ------------------------------------------------------------------ #
    # physical controls -> actions
    # ------------------------------------------------------------------ #
    def _handle_control_event(self, ev: ControlEvent) -> None:
        if ev.type is ControlEventType.BUTTON and ev.value == 1:
            mapping = {
                ButtonId.PREV.value: ("prev", {}),
                ButtonId.PLAY.value: ("play", {}),
                ButtonId.PAUSE.value: ("play_pause", {}),
                ButtonId.STOP.value: ("stop", {}),
                ButtonId.NEXT.value: ("next", {}),
                ButtonId.SHUFFLE.value: ("toggle_shuffle", {}),
                ButtonId.REPEAT.value: ("cycle_repeat", {}),
            }
            if ev.id in mapping:
                a, kw = mapping[ev.id]
                self.on_action(a, **kw)
        elif ev.type is ControlEventType.TOUCH:
            (self._grabbed.add if ev.value else self._grabbed.discard)(ev.id)
        elif ev.type is ControlEventType.FADER:
            frac = ev.value / FADER_MAX
            self._fader_moved(ev.id, frac)

    def _fader_moved(self, fader_id: int, frac: float) -> None:
        st = self.backend.state
        if fader_id == FaderId.VOLUME.value:
            self.on_action("set_volume", volume=frac)
        elif fader_id == FaderId.SEEK.value:
            self.on_action("seek", position_ms=int(frac * st.track.duration_ms))
        elif fader_id == FaderId.PREAMP.value:
            self.on_action("set_preamp", gain_db=(frac - 0.5) * 24)
        elif 0 <= fader_id < EQ_BANDS:
            self.on_action("set_eq_band", band=fader_id, gain_db=(frac - 0.5) * 24)

    # ------------------------------------------------------------------ #
    # motor sync: push targets to the motorized faders
    # ------------------------------------------------------------------ #
    def _sync_motors(self) -> None:
        st = self.backend.state
        targets: dict[int, float] = {
            FaderId.VOLUME.value: st.volume,
            FaderId.SEEK.value: st.progress,
            FaderId.PREAMP.value: st.eq_preamp / 24 + 0.5,
        }
        for i in range(EQ_BANDS):
            targets[i] = st.eq_bands[i] / 24 + 0.5
        for fid, frac in targets.items():
            if fid in self._grabbed:   # don't fight the user's hand
                continue
            pos = max(0, min(FADER_MAX, int(frac * FADER_MAX)))
            if self._last_sent.get(fid) != pos:
                self.controls.send(cmd_fader_target(FaderId(fid), pos))
                self._last_sent[fid] = pos

    # ------------------------------------------------------------------ #
    # main loop
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.cfg.fps) / 1000.0
            self._pump_events()
            for ev in self.controls.read_events():
                self._handle_control_event(ev)
            self._pump_library()
            self.images.pump()
            self._read_battery(dt)
            self.backend.poll()
            self._sync_motors()
            self.screen.update(self.backend.state, dt)
            self.screen.draw(self.backend.state, self.browse)
            pygame.display.flip()
        self._shutdown()

    def _pump_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)
            else:
                self.screen.handle_event(event, self.backend.state, self.browse)

    def _on_key(self, key: int) -> None:
        st = self.backend.state
        if key in (pygame.K_ESCAPE, pygame.K_q):
            self.running = False
        elif key == pygame.K_SPACE:
            self.on_action("play_pause")
        elif key == pygame.K_RIGHT:
            self.on_action("next")
        elif key == pygame.K_LEFT:
            self.on_action("prev")
        elif key == pygame.K_UP:
            self.on_action("set_volume", volume=st.volume + 0.05)
        elif key == pygame.K_DOWN:
            self.on_action("set_volume", volume=st.volume - 0.05)
        elif key == pygame.K_s:
            self.on_action("stop")
        # View switching (physical buttons send these on the device; keys in dev).
        elif key == pygame.K_1:
            self.screen.set_view("now_playing")
        elif key == pygame.K_2:
            self.screen.set_view("playlists")
        elif key == pygame.K_3:
            self.screen.set_view("queue")
        elif key == pygame.K_TAB:
            self.screen.cycle_view(1)

    def _shutdown(self) -> None:
        self.backend.close()
        self.controls.close()
        pygame.quit()


def main(argv: list[str] | None = None) -> int:
    argv = argv or []
    if argv and argv[0] in ("authorize", "auth", "--authorize"):
        from .authorize import main as authorize_main
        return authorize_main()

    cfg = Config.load()
    App(cfg).run()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
