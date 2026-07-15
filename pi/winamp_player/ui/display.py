"""The renderer + input handling for the WinAmp-inspired UI.

``Display.draw(state)`` paints one frame. ``Display.handle_event(event, state)``
turns pygame mouse events into semantic actions via the ``on_action`` callback,
so the same UI works whether input comes from the mouse (dev) or from physical
controls echoing their state back (device).
"""

from __future__ import annotations

import math
import random
from typing import Callable

import pygame

from ..models import EQ_BANDS, PlaybackStatus, PlayerState
from . import skin
from .skin import Layout, Rect

Action = Callable[..., None]

_TRANSPORT = ["prev", "play", "pause", "stop", "next", "eject"]
_GLYPH = {
    "prev": "|◀", "play": "▶", "pause": "▮▮",
    "stop": "■", "next": "▶|", "eject": "⏏",
}
_NUM_EQ_COLS = EQ_BANDS + 1  # bands + preamp


class Display:
    def __init__(self, surface: pygame.Surface, layout: Layout, on_action: Action,
                 show_legend: bool = True) -> None:
        self.surface = surface
        self.L = layout
        self.on_action = on_action
        self.show_legend = show_legend

        self.f_title = pygame.font.SysFont("segoeui", 15, bold=True)
        self.f_small = pygame.font.SysFont("segoeui", 12)
        self.f_lcd = pygame.font.SysFont("consolas", 20, bold=True)
        self.f_lcd_big = pygame.font.SysFont("consolas", 30, bold=True)
        self.f_tiny = pygame.font.SysFont("consolas", 11, bold=True)

        self._scroll = 0.0
        self._spectrum = [0.0] * 24
        self._peaks = [0.0] * 24
        self._drag: str | None = None      # which fader is being dragged
        self._transport_rects: dict[str, Rect] = {}
        self._eq_rects: list[Rect] = []
        self._library_rects: list[Rect] = []   # playlist rows (library view)
        self._back_rect: Rect | None = None    # "‹ Library" button (track view)
        self._images = None                    # ImageCache, set per-frame in draw()

    # ------------------------------------------------------------------ #
    # input
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event, state: PlayerState,
                     browse=None) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_press(event.pos, state, browse)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_release()
        elif event.type == pygame.MOUSEMOTION and self._drag:
            self._on_drag(event.pos, state)

    def _on_press(self, pos: tuple[int, int], state: PlayerState, browse) -> None:
        x, y = pos
        # transport buttons
        for name, r in self._transport_rects.items():
            if r.contains(x, y):
                self._transport_action(name)
                return
        # EQ / preamp faders
        for i, r in enumerate(self._eq_rects):
            if _pad(r, 8).contains(x, y):
                self._drag = f"eq{i}"
                self._on_drag(pos, state)
                return
        # volume / seek
        if _pad(self.L.volume_fader, 10).contains(x, y):
            self._drag = "volume"
            self._on_drag(pos, state)
            return
        if _pad(self.L.seek_fader, 10).contains(x, y):
            self._drag = "seek"
            self._on_drag(pos, state)
            return
        # -- the color touchscreen: depends on which view is showing -------- #
        view = getattr(browse, "view", "playlist")
        if view == "library":
            for i, r in enumerate(self._library_rects):
                if r.contains(x, y):
                    self.on_action("open_playlist", index=i)
                    return
            return
        # track view
        if self._back_rect and self._back_rect.contains(x, y):
            self.on_action("show_library")
            return
        pl = self.L.playlist
        if pl.contains(x, y):
            row_h = 22
            idx = (y - pl.y) // row_h
            if 0 <= idx < len(state.playlist):
                self.on_action("select_track", index=int(idx))

    def _on_release(self) -> None:
        self._drag = None

    def _on_drag(self, pos: tuple[int, int], state: PlayerState) -> None:
        x, y = pos
        if self._drag and self._drag.startswith("eq"):
            i = int(self._drag[2:])
            r = self._eq_rects[i]
            frac = _clamp01(1.0 - (y - r.y) / r.h)
            gain = (frac - 0.5) * 24.0     # -12 .. +12 dB
            if i < EQ_BANDS:
                self.on_action("set_eq_band", band=i, gain_db=gain)
            else:
                self.on_action("set_preamp", gain_db=gain)
        elif self._drag == "volume":
            r = self.L.volume_fader
            self.on_action("set_volume", volume=_clamp01((x - r.x) / r.w))
        elif self._drag == "seek":
            r = self.L.seek_fader
            frac = _clamp01((x - r.x) / r.w)
            self.on_action("seek", position_ms=int(frac * state.track.duration_ms))

    def _transport_action(self, name: str) -> None:
        mapping = {
            "prev": ("prev", {}), "next": ("next", {}),
            "play": ("play", {}), "pause": ("play_pause", {}),
            "stop": ("stop", {}), "eject": ("show_library", {}),  # eject = browse library
        }
        action, kw = mapping[name]
        self.on_action(action, **kw)

    # ------------------------------------------------------------------ #
    # render
    # ------------------------------------------------------------------ #
    def draw(self, state: PlayerState, browse=None, images=None) -> None:
        self._images = images
        s = self.surface
        s.fill(skin.BG)
        self._panel(self.L.main_panel)
        self._panel(self.L.eq_panel)
        self._panel(self.L.bottom_panel)

        self._draw_title_bar(state)
        self._draw_lcd(state)
        self._draw_spectrum(state)
        self._draw_transport(state)
        self._draw_screen(state, browse)
        self._draw_eq(state)
        self._draw_hfaders(state)

        if self.show_legend:
            self._draw_legend()

    # -- panels & chrome -------------------------------------------------- #
    def _panel(self, r: Rect) -> None:
        pygame.draw.rect(self.surface, skin.METAL, r.as_tuple())
        pygame.draw.line(self.surface, skin.BEVEL_LIGHT, (r.x, r.y), (r.x + r.w, r.y))
        pygame.draw.line(self.surface, skin.BEVEL_DARK,
                         (r.x, r.y + r.h - 1), (r.x + r.w, r.y + r.h - 1))

    def _draw_title_bar(self, state: PlayerState) -> None:
        r = self.L.title_bar
        pygame.draw.rect(self.surface, skin.METAL_LO, r.as_tuple())
        # little pinstripes, WinAmp-style
        for i in range(6):
            yy = r.y + 8 + i * 2
            pygame.draw.line(self.surface, skin.BEVEL_LIGHT, (10, yy), (r.w - 90, yy))
        label = self.f_title.render("WINAMP  ·  PHYSICAL EDITION", True, skin.ACCENT)
        self.surface.blit(label, (r.w // 2 - label.get_width() // 2, 7))

    def _draw_lcd(self, state: PlayerState) -> None:
        r = self.L.lcd
        _inset(self.surface, r, skin.LCD_BG)
        # elapsed time, big green digits
        t = _mmss(state.position_ms)
        self.surface.blit(self.f_lcd_big.render(t, True, skin.LCD_GREEN), (r.x + 10, r.y + 8))
        # stream info, right-aligned
        info = f"{state.bitrate_kbps} kbps"
        khz = f"{state.sample_rate_hz // 1000} kHz  {'stereo' if state.stereo else 'mono'}"
        self._blit_right(self.f_tiny, info, r.x + r.w - 10, r.y + 8, skin.LCD_GREEN_DIM)
        self._blit_right(self.f_tiny, khz, r.x + r.w - 10, r.y + 22, skin.LCD_GREEN_DIM)
        # scrolling title
        title = f"{state.track.display}    ★    "
        surf = self.f_lcd.render(title, True, skin.LCD_GREEN)
        clip = pygame.Rect(r.x + 10, r.y + 44, r.w - 20, 24)
        prev = self.surface.get_clip()
        self.surface.set_clip(clip)
        if surf.get_width() > clip.width:
            off = int(self._scroll) % surf.get_width()
            self.surface.blit(surf, (clip.x - off, clip.y))
            self.surface.blit(surf, (clip.x - off + surf.get_width(), clip.y))
        else:
            self.surface.blit(surf, (clip.x, clip.y))
        self.surface.set_clip(prev)

    def _draw_spectrum(self, state: PlayerState) -> None:
        r = self.L.spectrum
        _inset(self.surface, r, skin.LCD_BG)
        bars = state.spectrum if state.spectrum else self._spectrum
        n = len(bars)
        if n == 0:
            return
        bw = (r.w - 8) / n
        for i, v in enumerate(bars):
            v = _clamp01(v)
            bx = int(r.x + 4 + i * bw)
            bh = int(v * (r.h - 8))
            for yy in range(bh):
                frac = yy / max(1, r.h - 8)
                col = _lerp(skin.SPECTRUM_BOT, skin.SPECTRUM_TOP, frac)
                self.surface.set_at((bx, r.y + r.h - 4 - yy), col)
                if bw > 3:
                    self.surface.set_at((bx + 1, r.y + r.h - 4 - yy), col)
            # peak cap
            pk = int(self._peaks[i] * (r.h - 8)) if i < len(self._peaks) else 0
            if pk > 0:
                py = r.y + r.h - 4 - pk
                pygame.draw.line(self.surface, skin.SPECTRUM_PEAK,
                                 (bx, py), (bx + int(bw) - 1, py))

    def _draw_transport(self, state: PlayerState) -> None:
        r = self.L.transport
        self._transport_rects.clear()
        n = len(_TRANSPORT)
        gap = 6
        bw = (r.w - gap * (n - 1)) // n
        for i, name in enumerate(_TRANSPORT):
            br = Rect(r.x + i * (bw + gap), r.y, bw, r.h)
            self._transport_rects[name] = br
            active = (
                (name == "play" and state.status is PlaybackStatus.PLAYING) or
                (name == "pause" and state.status is PlaybackStatus.PAUSED) or
                (name == "stop" and state.status is PlaybackStatus.STOPPED)
            )
            self._button(br, _GLYPH[name], active)

    def _button(self, r: Rect, glyph: str, active: bool) -> None:
        top = skin.ACCENT if active else skin.METAL_HI
        pygame.draw.rect(self.surface, skin.METAL_LO, r.as_tuple(), border_radius=3)
        inner = _pad(r, 2)
        pygame.draw.rect(self.surface, top if active else skin.METAL,
                         inner.as_tuple(), border_radius=3)
        g = self.f_small.render(glyph, True, skin.BG if active else skin.TEXT)
        self.surface.blit(g, (r.cx - g.get_width() // 2, r.cy - g.get_height() // 2))

    # -- the color touchscreen region ----------------------------------- #
    def _draw_screen(self, state: PlayerState, browse) -> None:
        r = self.L.screen
        _inset(self.surface, r, (16, 18, 24))
        view = getattr(browse, "view", "playlist")
        if view == "library":
            self._draw_library(browse)
        else:
            self._draw_track_view(state, browse)

    def _draw_library(self, browse) -> None:
        """The playlist picker — your real Spotify playlists."""
        r = self.L.screen
        self._library_rects = []
        self._back_rect = None
        header = self.f_title.render("YOUR PLAYLISTS", True, skin.ACCENT)
        self.surface.blit(header, (r.x + 12, r.y + 8))

        if getattr(browse, "loading", False):
            self._center_text(r, "Loading your playlists…")
            return
        if getattr(browse, "error", ""):
            self._center_text(r, "Spotify error — see console", skin.LCD_AMBER)
            return
        playlists = getattr(browse, "playlists", [])
        if not playlists:
            self._center_text(r, "No playlists found")
            return

        row_h = 38
        top = r.y + 32
        max_rows = (r.y + r.h - top - 8) // row_h
        for i, pl in enumerate(playlists[:max_rows]):
            row = Rect(r.x + 8, top + i * row_h, r.w - 16, row_h - 6)
            self._library_rects.append(row)
            pygame.draw.rect(self.surface, skin.METAL_LO, row.as_tuple(), border_radius=4)
            # thumbnail
            thumb = Rect(row.x + 4, row.y + 4, row.h - 8, row.h - 8)
            self._blit_art(getattr(pl, "image_url", None), thumb, "♫")
            # name + status. Dev Mode can't read non-owned playlists' tracks.
            owned = getattr(pl, "owned", True)
            name = _ellipsize(pl.name, 30)
            self.surface.blit(self.f_small.render(name, True,
                              skin.TEXT if owned else skin.TEXT_DIM),
                              (thumb.x + thumb.w + 10, row.y + 8))
            if owned:
                sub, col = f"{pl.track_count} tracks", skin.TEXT_DIM
            elif getattr(browse, "can_play_followed", False):
                sub, col = "tap to play · no tracklist", skin.LCD_GREEN_DIM
            else:
                sub, col = "dev-mode locked (not owned)", skin.LCD_AMBER
            self.surface.blit(self.f_tiny.render(sub, True, col),
                              (thumb.x + thumb.w + 10, row.y + 24))

    def _draw_track_view(self, state: PlayerState, browse) -> None:
        self._library_rects = []
        # back button (only if a real library exists to go back to)
        if getattr(browse, "has_library", False):
            r = self.L.screen
            self._back_rect = Rect(r.x + 8, r.y + 6, 96, 20)
            pygame.draw.rect(self.surface, skin.METAL_LO, self._back_rect.as_tuple(),
                             border_radius=3)
            self.surface.blit(self.f_tiny.render("‹ LIBRARY", True, skin.ACCENT),
                              (self._back_rect.x + 8, self._back_rect.y + 5))
            name = _ellipsize(getattr(browse, "current_playlist", ""), 24)
            self._blit_right(self.f_tiny, name, r.x + r.w - 10, r.y + 11, skin.TEXT_DIM)
        else:
            self._back_rect = None
        if state.playlist:                       # owned playlist: show tracklist
            self._draw_album_art(state)
            self._draw_playlist(state)
        elif state.track.title and state.track.title != "—" \
                and state.status is not PlaybackStatus.STOPPED:
            self._draw_now_playing(state)        # followed playlist: now playing
        elif getattr(browse, "note", ""):
            self._center_text(self.L.screen, browse.note, skin.LCD_AMBER)

    def _draw_now_playing(self, state: PlayerState) -> None:
        r = self.L.screen
        size = min(r.w - 200, 128)
        art = Rect(r.cx - size // 2, r.y + 24, size, size)
        self._blit_art(state.track.art_url, art, "♪")
        y = art.y + art.h + 12
        self._center_line(state.track.title, r, y, self.f_title, skin.TEXT)
        self._center_line(state.track.artist, r, y + 22, self.f_small, skin.TEXT_DIM)
        bar = Rect(r.x + 40, y + 44, r.w - 80, 6)
        _inset(self.surface, bar, skin.METAL_LO)
        fill = Rect(bar.x, bar.y, int(bar.w * state.progress), bar.h)
        pygame.draw.rect(self.surface, skin.ACCENT, fill.as_tuple())
        self._draw_queue(state, bar.y + 18)

    def _draw_queue(self, state: PlayerState, top: int) -> None:
        """'Up next' from the playback queue — a tracklist for anything playing."""
        r = self.L.screen
        if not state.queue:
            return
        self.surface.blit(self.f_tiny.render("UP NEXT", True, skin.ACCENT), (r.x + 12, top))
        row_h = 20
        y0 = top + 16
        max_rows = max(0, (r.y + r.h - y0 - 6) // row_h)
        for i, tr in enumerate(state.queue[:max_rows]):
            ry = y0 + i * row_h
            self.surface.blit(self.f_tiny.render(f"{i + 1:2}.", True, skin.TEXT_DIM), (r.x + 12, ry))
            self.surface.blit(self.f_small.render(_ellipsize(tr.display, 38), True, skin.TEXT),
                              (r.x + 38, ry - 1))
            self._blit_right(self.f_tiny, _mmss(tr.duration_ms), r.x + r.w - 10, ry, skin.TEXT_DIM)

    def _center_line(self, text: str, r: Rect, y: int, font, col) -> None:
        surf = font.render(_ellipsize(text, 40), True, col)
        self.surface.blit(surf, (r.cx - surf.get_width() // 2, y))

    def _draw_album_art(self, state: PlayerState) -> None:
        r = self.L.album_art
        art = self._blit_art(state.track.art_url, r, "♪")
        if not art:
            pygame.draw.rect(self.surface, skin.BEVEL_LIGHT, r.as_tuple(), 1)
        # album / artist below
        alb = self.f_small.render(_ellipsize(state.track.album, 26), True, skin.TEXT)
        self.surface.blit(alb, (r.x, r.y + r.h + 6))

    def _blit_art(self, url, r: Rect, placeholder: str) -> bool:
        """Draw album/playlist art at rect r. Returns True if real art was drawn."""
        surf = self._images.get(url, (r.w, r.h)) if self._images else None
        if surf is not None:
            self.surface.blit(surf, (r.x, r.y))
            return True
        # gradient placeholder until the image downloads
        for yy in range(r.h):
            col = _lerp((40, 44, 60), (18, 20, 30), yy / max(1, r.h))
            pygame.draw.line(self.surface, col, (r.x, r.y + yy), (r.x + r.w, r.y + yy))
        note = self.f_lcd_big.render(placeholder, True, skin.ACCENT)
        self.surface.blit(note, (r.cx - note.get_width() // 2, r.cy - note.get_height() // 2))
        return False

    def _center_text(self, r: Rect, text: str, col=skin.TEXT_DIM) -> None:
        surf = self.f_small.render(text, True, col)
        self.surface.blit(surf, (r.cx - surf.get_width() // 2, r.cy - surf.get_height() // 2))

    def _draw_playlist(self, state: PlayerState) -> None:
        r = self.L.playlist
        row_h = 22
        rows = min(len(state.playlist), r.h // row_h)
        for i in range(rows):
            tr = state.playlist[i]
            row = Rect(r.x, r.y + i * row_h, r.w, row_h)
            if i == state.playlist_index:
                pygame.draw.rect(self.surface, (30, 60, 40), row.as_tuple())
                col = skin.LCD_GREEN
            else:
                col = skin.TEXT if i % 2 == 0 else skin.TEXT_DIM
            num = self.f_tiny.render(f"{i + 1:2}.", True, skin.TEXT_DIM)
            self.surface.blit(num, (row.x + 4, row.y + 5))
            name = _ellipsize(f"{tr.display}", 40)
            self.surface.blit(self.f_small.render(name, True, col), (row.x + 30, row.y + 4))
            self._blit_right(self.f_tiny, _mmss(tr.duration_ms), row.x + row.w - 6, row.y + 5,
                             skin.TEXT_DIM)

    # -- physical fader banks -------------------------------------------- #
    def _draw_eq(self, state: PlayerState) -> None:
        panel = self.L.eq_panel
        self._eq_rects = []
        label = self.f_tiny.render("GRAPHIC EQ", True, skin.TEXT_DIM)
        self.surface.blit(label, (panel.x + 14, panel.y + 6))

        cols = _NUM_EQ_COLS
        margin = 20
        col_w = (panel.w - margin * 2) // cols
        track_h = panel.h - 44
        top = panel.y + 24
        labels = [f"{f}" if f < 1000 else f"{f // 1000}k"
                  for f in [60, 150, 400, 1000, 2400, 6000, 15000]] + ["PRE"]
        for i in range(cols):
            cx = panel.x + margin + i * col_w + col_w // 2
            track = Rect(cx - 3, top, 6, track_h)
            self._eq_rects.append(track)
            gain = state.eq_preamp if i == EQ_BANDS else state.eq_bands[i]
            frac = _clamp01(gain / 24.0 + 0.5)
            self._vfader(track, frac, i == EQ_BANDS)
            lab = self.f_tiny.render(labels[i], True, skin.TEXT_DIM)
            self.surface.blit(lab, (cx - lab.get_width() // 2, top + track_h + 4))

    def _vfader(self, track: Rect, frac: float, is_preamp: bool) -> None:
        # slot
        _inset(self.surface, track, skin.METAL_LO)
        # center (0 dB) tick
        mid_y = track.y + track.h // 2
        pygame.draw.line(self.surface, skin.TEXT_DIM,
                         (track.x - 4, mid_y), (track.x + track.w + 4, mid_y))
        # knob (this is a MOTORIZED fader on the device)
        ky = int(track.y + (1 - frac) * track.h)
        knob = Rect(track.x - 8, ky - 6, track.w + 16, 12)
        col = skin.LCD_AMBER if is_preamp else skin.ACCENT
        pygame.draw.rect(self.surface, skin.METAL_HI, knob.as_tuple(), border_radius=3)
        pygame.draw.line(self.surface, col,
                         (knob.x + 2, knob.cy), (knob.x + knob.w - 2, knob.cy), 2)

    def _draw_hfaders(self, state: PlayerState) -> None:
        # volume
        vr = self.L.volume_fader
        self._hfader(vr, state.volume, skin.ACCENT)
        self._blit_label("VOL", vr)
        # seek — the motorized fader that tracks song position
        sr = self.L.seek_fader
        self._hfader(sr, state.progress, skin.LCD_AMBER)
        self._blit_label("SEEK", sr)

    def _hfader(self, track: Rect, frac: float, col) -> None:
        _inset(self.surface, track, skin.METAL_LO)
        fill = Rect(track.x, track.y, int(track.w * _clamp01(frac)), track.h)
        pygame.draw.rect(self.surface, (col[0] // 3, col[1] // 3, col[2] // 3), fill.as_tuple())
        kx = int(track.x + _clamp01(frac) * track.w)
        knob = Rect(kx - 5, track.y - 4, 10, track.h + 8)
        pygame.draw.rect(self.surface, skin.METAL_HI, knob.as_tuple(), border_radius=3)
        pygame.draw.line(self.surface, col, (knob.cx, knob.y + 2),
                         (knob.cx, knob.y + knob.h - 2), 2)

    def _blit_label(self, text: str, r: Rect) -> None:
        lab = self.f_tiny.render(text, True, skin.TEXT_DIM)
        self.surface.blit(lab, (r.x, r.y - 14))

    def _blit_right(self, font, text: str, right_x: int, y: int, color) -> None:
        surf = font.render(text, True, color)
        self.surface.blit(surf, (right_x - surf.get_width(), y))

    # -- hardware legend -------------------------------------------------- #
    def _draw_legend(self) -> None:
        overlay = pygame.Surface((self.L.W, self.L.H), pygame.SRCALPHA)
        for r in (self.L.main_panel, self.L.eq_panel, self.L.bottom_panel):
            overlay.fill(skin.PHYSICAL_TINT, r.as_tuple())
        overlay.fill(skin.SCREEN_TINT, self.L.screen.as_tuple())
        self.surface.blit(overlay, (0, 0))
        tags = [
            ("● PHYSICAL — buttons · faders · pots", skin.PHYSICAL_TINT[:3], self.L.eq_panel.y + 2),
            ("● SCREEN — color LCD touchscreen", skin.SCREEN_TINT[:3], self.L.screen.y + 2),
        ]
        for text, col, y in tags:
            self.surface.blit(self.f_tiny.render(text, True, (200, 210, 230)),
                              (self.L.W - 210, y))

    # ------------------------------------------------------------------ #
    # per-frame animation (spectrum + scroll)
    # ------------------------------------------------------------------ #
    def update(self, state: PlayerState, dt: float) -> None:
        if state.is_playing:
            self._scroll += dt * 40.0
        # simulate a spectrum if hardware isn't feeding one
        if not state.spectrum:
            for i in range(len(self._spectrum)):
                if state.is_playing:
                    target = abs(math.sin((self._scroll / 30.0) + i * 0.6))
                    target *= 0.4 + 0.6 * random.random()
                else:
                    target = 0.0
                self._spectrum[i] += (target - self._spectrum[i]) * min(1.0, dt * 12)
        src = state.spectrum if state.spectrum else self._spectrum
        for i in range(min(len(self._peaks), len(src))):
            self._peaks[i] = max(src[i], self._peaks[i] - dt * 0.8)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _pad(r: Rect, p: int) -> Rect:
    return Rect(r.x - p, r.y - p, r.w + 2 * p, r.h + 2 * p)


def _inset(surf: pygame.Surface, r: Rect, color) -> None:
    pygame.draw.rect(surf, color, r.as_tuple())
    pygame.draw.line(surf, skin.BEVEL_DARK, (r.x, r.y), (r.x + r.w, r.y))
    pygame.draw.line(surf, skin.BEVEL_DARK, (r.x, r.y), (r.x, r.y + r.h))
    pygame.draw.line(surf, skin.BEVEL_LIGHT, (r.x, r.y + r.h), (r.x + r.w, r.y + r.h))
    pygame.draw.line(surf, skin.BEVEL_LIGHT, (r.x + r.w, r.y), (r.x + r.w, r.y + r.h))


def _lerp(a, b, t: float):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _mmss(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


def _ellipsize(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"
