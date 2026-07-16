"""The device screen UI — a compact multi-view app for the square LCD.

This replaces the temporary full-window WinAmp skin. The real device is
physical-first (transport, EQ, faders are hardware); the screen is a small
**square** panel (HyperPixel 4.0 Square, 720×720) showing one **view** at a time:

    Now Playing · Playlists · Up Next (Queue)

Layout (square):
    ┌───────────────────────────┐
    │ status bar: ♪ title  · 🔋 │  persistent
    ├───────────────────────────┤
    │                           │
    │        ACTIVE VIEW        │
    │                           │
    ├───────────────────────────┤
    │ [Now Playing][Lists][Next]│  tab strip (active highlighted)
    └───────────────────────────┘

Views are switched by dedicated physical buttons on the real device (via serial
-> ``on_action("set_view", name=...)``); in dev, keys 1/2/3 or Tab, or tapping
the tab strip.
"""

from __future__ import annotations

from typing import Callable

import pygame

from ..models import PlaybackStatus, PlayerState
from . import skin
from .skin import Rect

Action = Callable[..., None]

VIEWS = [
    ("now_playing", "Now Playing"),
    ("playlists", "Playlists"),
    ("queue", "Up Next"),
]
_STATUS_H = 46
_TAB_H = 52


class ScreenUI:
    def __init__(self, surface: pygame.Surface, on_action: Action, images=None) -> None:
        self.surface = surface
        self.W, self.H = surface.get_size()
        self.on_action = on_action
        self.images = images
        self.view = "now_playing"

        self._scroll = 0.0
        self._tab_rects: dict[str, Rect] = {}
        self._row_rects: list[tuple[Rect, int]] = []

        self.f_h1 = pygame.font.SysFont("segoeui", 30, bold=True)
        self.f_h2 = pygame.font.SysFont("segoeui", 22)
        self.f_body = pygame.font.SysFont("segoeui", 18)
        self.f_small = pygame.font.SysFont("segoeui", 15)
        self.f_tiny = pygame.font.SysFont("consolas", 13, bold=True)

    # ------------------------------------------------------------------ #
    # view control
    # ------------------------------------------------------------------ #
    def set_view(self, name: str) -> None:
        if name in (v[0] for v in VIEWS):
            self.view = name

    def cycle_view(self, step: int = 1) -> None:
        names = [v[0] for v in VIEWS]
        self.view = names[(names.index(self.view) + step) % len(names)]

    # ------------------------------------------------------------------ #
    # input
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event, state: PlayerState, browse=None) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            for name, r in self._tab_rects.items():
                if r.contains(x, y):
                    self.set_view(name)
                    return
            if self.view == "playlists":
                for r, idx in self._row_rects:
                    if r.contains(x, y):
                        self.on_action("open_playlist", index=idx)
                        return

    # ------------------------------------------------------------------ #
    # per-frame animation
    # ------------------------------------------------------------------ #
    def update(self, state: PlayerState, dt: float) -> None:
        if state.is_playing:
            self._scroll += dt * 45.0

    # ------------------------------------------------------------------ #
    # render
    # ------------------------------------------------------------------ #
    def draw(self, state: PlayerState, browse=None) -> None:
        self.surface.fill(skin.BG)
        self._draw_status_bar(state)
        area = Rect(0, _STATUS_H, self.W, self.H - _STATUS_H - _TAB_H)
        if self.view == "now_playing":
            self._view_now_playing(area, state)
        elif self.view == "playlists":
            self._view_playlists(area, state, browse)
        else:
            self._view_queue(area, state)
        self._draw_tabs()

    # -- status bar ------------------------------------------------------ #
    def _draw_status_bar(self, state: PlayerState) -> None:
        r = Rect(0, 0, self.W, _STATUS_H)
        pygame.draw.rect(self.surface, skin.METAL_LO, r.as_tuple())
        pygame.draw.line(self.surface, skin.BEVEL_DARK, (0, r.h - 1), (self.W, r.h - 1))
        self._play_indicator(20, r.cy, state.status)
        title = state.track.display if state.track.title != "—" else "WINAMP · PHYSICAL EDITION"
        self._scroll_text(title, Rect(38, 12, self.W - 130, 24), skin.TEXT, self.f_body)
        self._draw_battery(state, r)

    def _draw_battery(self, state: PlayerState, bar: Rect) -> None:
        if state.battery_percent is None:
            return
        pct = max(0.0, min(100.0, state.battery_percent))
        w, h = 30, 14
        x, y = self.W - 16 - w, bar.cy - h // 2
        pygame.draw.rect(self.surface, skin.TEXT_DIM, (x, y, w, h), 1)
        pygame.draw.rect(self.surface, skin.TEXT_DIM, (x + w, y + 4, 2, h - 8))
        col = skin.ACCENT if pct > 20 else skin.LCD_AMBER if pct > 10 else (220, 60, 60)
        pygame.draw.rect(self.surface, col, (x + 1, y + 1, int((w - 2) * pct / 100), h - 2))
        self._blit_right(self.f_tiny, f"{int(pct)}%", x - 6, bar.cy - 7, skin.TEXT_DIM)

    # -- Now Playing ----------------------------------------------------- #
    def _view_now_playing(self, area: Rect, state: PlayerState) -> None:
        self._row_rects = []
        size = min(area.w - 200, area.h - 220)
        art = Rect(area.cx - size // 2, area.y + 24, size, size)
        self._blit_art(state.track.art_url, art, "♪")
        y = art.y + art.h + 22
        self._center(state.track.title, y, self.f_h1, skin.TEXT)
        self._center(state.track.artist, y + 38, self.f_h2, skin.TEXT_DIM)
        self._center(state.track.album, y + 68, self.f_small, skin.TEXT_DIM)
        # progress
        bar = Rect(area.x + 60, area.y + area.h - 34, area.w - 120, 6)
        pygame.draw.rect(self.surface, skin.METAL_LO, bar.as_tuple(), border_radius=3)
        fill_w = int(bar.w * state.progress)
        pygame.draw.rect(self.surface, skin.ACCENT, (bar.x, bar.y, fill_w, bar.h), border_radius=3)
        self.surface.blit(self.f_tiny.render(_mmss(state.position_ms), True, skin.TEXT_DIM),
                          (bar.x, bar.y + 12))
        self._blit_right(self.f_tiny, _mmss(state.track.duration_ms), bar.x + bar.w, bar.y + 12,
                         skin.TEXT_DIM)

    # -- Playlists ------------------------------------------------------- #
    def _view_playlists(self, area: Rect, state: PlayerState, browse) -> None:
        self._row_rects = []
        self._header(area, "PLAYLISTS")
        playlists = getattr(browse, "playlists", []) if browse else []
        if getattr(browse, "loading", False):
            self._center("Loading your playlists…", area.cy, self.f_body, skin.TEXT_DIM)
            return
        if not playlists:
            self._center("No playlists (run authorize for your library)", area.cy,
                         self.f_small, skin.TEXT_DIM)
            return
        row_h = 62
        top = area.y + 40
        rows = min(len(playlists), (area.y + area.h - top) // row_h)
        for i in range(rows):
            pl = playlists[i]
            row = Rect(area.x + 16, top + i * row_h, area.w - 32, row_h - 8)
            self._row_rects.append((row, i))
            pygame.draw.rect(self.surface, skin.METAL_LO, row.as_tuple(), border_radius=6)
            thumb = Rect(row.x + 6, row.y + 6, row.h - 12, row.h - 12)
            self._blit_art(getattr(pl, "image_url", None), thumb, "♫")
            tx = thumb.x + thumb.w + 14
            self.surface.blit(self.f_body.render(_ellipsize(pl.name, 30), True, skin.TEXT),
                              (tx, row.y + 10))
            # Dev Mode strips track counts from /me/playlists, so show a hint
            # instead of a bogus "0 tracks".
            sub = f"{pl.track_count} tracks" if pl.track_count else "tap to play"
            self.surface.blit(self.f_small.render(sub, True, skin.TEXT_DIM), (tx, row.y + 32))

    # -- Queue ----------------------------------------------------------- #
    def _view_queue(self, area: Rect, state: PlayerState) -> None:
        self._row_rects = []
        self._header(area, "UP NEXT")
        items = state.queue or state.playlist
        if not items:
            self._center("Nothing queued", area.cy, self.f_body, skin.TEXT_DIM)
            return
        row_h = 46
        top = area.y + 40
        rows = min(len(items), (area.y + area.h - top) // row_h)
        for i in range(rows):
            tr = items[i]
            ry = top + i * row_h
            self.surface.blit(self.f_tiny.render(f"{i + 1:2}", True, skin.TEXT_DIM),
                              (area.x + 18, ry + 6))
            self.surface.blit(self.f_body.render(_ellipsize(tr.display, 40), True, skin.TEXT),
                              (area.x + 52, ry))
            self._blit_right(self.f_tiny, _mmss(tr.duration_ms), area.x + area.w - 18, ry + 6,
                             skin.TEXT_DIM)

    # -- tab strip ------------------------------------------------------- #
    def _draw_tabs(self) -> None:
        self._tab_rects = {}
        y = self.H - _TAB_H
        pygame.draw.rect(self.surface, skin.METAL_LO, (0, y, self.W, _TAB_H))
        pygame.draw.line(self.surface, skin.BEVEL_LIGHT, (0, y), (self.W, y))
        tw = self.W // len(VIEWS)
        for i, (name, label) in enumerate(VIEWS):
            r = Rect(i * tw, y, tw, _TAB_H)
            self._tab_rects[name] = r
            active = name == self.view
            if active:
                pygame.draw.rect(self.surface, skin.BG, _pad(r, -6).as_tuple(), border_radius=8)
                pygame.draw.rect(self.surface, skin.ACCENT, (r.x + 18, y + 4, r.w - 36, 3))
            col = skin.ACCENT if active else skin.TEXT_DIM
            g = self.f_body.render(label, True, col)
            self.surface.blit(g, (r.cx - g.get_width() // 2, r.cy - g.get_height() // 2))

    # -- drawn icons (no unreliable glyph fonts) ------------------------- #
    def _play_indicator(self, x: int, cy: int, status) -> None:
        if status is PlaybackStatus.PLAYING:
            pygame.draw.polygon(self.surface, skin.ACCENT,
                                [(x - 5, cy - 6), (x - 5, cy + 6), (x + 6, cy)])
        elif status is PlaybackStatus.PAUSED:
            pygame.draw.rect(self.surface, skin.LCD_AMBER, (x - 5, cy - 6, 4, 12))
            pygame.draw.rect(self.surface, skin.LCD_AMBER, (x + 2, cy - 6, 4, 12))
        else:
            pygame.draw.rect(self.surface, skin.TEXT_DIM, (x - 5, cy - 5, 11, 11))

    def _note(self, cx: int, cy: int, s: int) -> None:
        col = skin.LCD_GREEN_DIM
        pygame.draw.ellipse(self.surface, col, (cx - s, cy + s // 3, s, int(s * 0.72)))
        pygame.draw.rect(self.surface, col, (cx - 3, cy - s, 3, int(s * 1.6)))
        pygame.draw.rect(self.surface, col, (cx - 3, cy - s, s, 4))

    # -- helpers --------------------------------------------------------- #
    def _header(self, area: Rect, text: str) -> None:
        self.surface.blit(self.f_tiny.render(text, True, skin.ACCENT), (area.x + 18, area.y + 12))

    def _center(self, text: str, y: int, font, col) -> None:
        if not text:
            return
        surf = font.render(_ellipsize(text, 34), True, col)
        self.surface.blit(surf, (self.W // 2 - surf.get_width() // 2, y))

    def _scroll_text(self, text: str, r: Rect, col, font) -> None:
        surf = font.render(text, True, col)
        prev = self.surface.get_clip()
        self.surface.set_clip(r.as_tuple())
        if surf.get_width() > r.w:
            off = int(self._scroll) % (surf.get_width() + 40)
            self.surface.blit(surf, (r.x - off, r.y))
            self.surface.blit(surf, (r.x - off + surf.get_width() + 40, r.y))
        else:
            self.surface.blit(surf, (r.x, r.y))
        self.surface.set_clip(prev)

    def _blit_right(self, font, text: str, right_x: int, y: int, col) -> None:
        surf = font.render(text, True, col)
        self.surface.blit(surf, (right_x - surf.get_width(), y))

    def _blit_art(self, url, r: Rect, placeholder: str) -> None:
        surf = self.images.get(url, (r.w, r.h)) if self.images else None
        if surf is not None:
            self.surface.blit(surf, (r.x, r.y))
            return
        for yy in range(r.h):
            c = _lerp((44, 48, 66), (18, 20, 30), yy / max(1, r.h))
            pygame.draw.line(self.surface, c, (r.x, r.y + yy), (r.x + r.w, r.y + yy))
        pygame.draw.rect(self.surface, skin.BEVEL_LIGHT, r.as_tuple(), 1)
        self._note(r.cx, r.cy, max(8, min(r.w, r.h) // 6))


def _pad(r: Rect, p: int) -> Rect:
    return Rect(r.x - p, r.y - p, r.w + 2 * p, r.h + 2 * p)


def _lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _mmss(ms: int) -> str:
    s = max(0, ms) // 1000
    return f"{s // 60}:{s % 60:02d}"


def _ellipsize(text: str, n: int) -> str:
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"
