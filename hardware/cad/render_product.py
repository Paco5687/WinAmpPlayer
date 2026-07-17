"""SpotAmp compact (127x300) — product-style front elevation render.

Draws the physical device: anodized body, lit amber OLED, aluminum fader caps,
and the REAL multi-view UI rendered onto the screen. 4 px = 1 mm.
"""
import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, r"C:\Users\VNET\Documents\repos\winamp-player\pi")

import pygame
pygame.init()

S = 4                      # px per mm
PW, PH = 127 * S, 300 * S  # panel
CW, CH = PW + 220, PH + 260
OX, OY = 110, 110          # panel origin on canvas

canvas = pygame.Surface((CW, CH))

# ---------- studio background ------------------------------------------------ #
for y in range(CH):
    t = y / CH
    g = int(214 - 38 * t)
    pygame.draw.line(canvas, (g, g + 2, g + 6), (0, y), (CW, y))
# floor shadow
sh = pygame.Surface((CW, 130), pygame.SRCALPHA)
pygame.draw.ellipse(sh, (20, 20, 26, 90), (OX - 40, 30, PW + 80, 80))
canvas.blit(sh, (0, OY + PH - 40))

def rr(surf, color, rect, rad, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=rad)

# ---------- body -------------------------------------------------------------- #
# drop shadow
for i, a in ((14, 26), (9, 40), (5, 60)):
    shd = pygame.Surface((PW + 2 * i, PH + 2 * i), pygame.SRCALPHA)
    rr(shd, (10, 10, 14, a), shd.get_rect(), 26 + i)
    canvas.blit(shd, (OX - i, OY - i + 6))
# anodized front plate (vertical sheen)
plate = pygame.Surface((PW, PH), pygame.SRCALPHA)
for y in range(PH):
    t = y / PH
    base = 34 + int(10 * math.sin(t * math.pi))       # subtle sheen band
    rrcol = (base, base + 1, base + 4)
    pygame.draw.line(plate, rrcol, (0, y), (PW, y))
mask = pygame.Surface((PW, PH), pygame.SRCALPHA)
rr(mask, (255, 255, 255), mask.get_rect(), 24)
plate.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
canvas.blit(plate, (OX, OY))
rr(canvas, (74, 78, 86), (OX, OY, PW, PH), 24, 2)          # edge
rr(canvas, (16, 17, 20), (OX + 2, OY + 2, PW - 4, PH - 4), 22, 1)

def mm(x, y):  # panel mm -> canvas px
    return (OX + int(x * S), OY + int(y * S))

def mmr(x, y, w, h):
    return pygame.Rect(OX + int(x * S), OY + int(y * S), int(w * S), int(h * S))

F_ENG = pygame.font.SysFont("segoeui", 13)
F_ENG_S = pygame.font.SysFont("segoeui", 11)
F_OLED = pygame.font.SysFont("consolas", 26, bold=True)
F_OLED_S = pygame.font.SysFont("consolas", 13, bold=True)

def engrave(text, cx, y, font=F_ENG, col=(148, 152, 160)):
    s = font.render(text, True, col)
    d = font.render(text, True, (12, 12, 14))
    canvas.blit(d, (cx - s.get_width() // 2 + 1, y + 1))
    canvas.blit(s, (cx - s.get_width() // 2, y))

# ---------- OLED readout ------------------------------------------------------ #
o = mmr(9, 7.5, 78, 20.5)
rr(canvas, (6, 7, 8), o.inflate(10, 10), 8)                 # glass bezel
rr(canvas, (14, 10, 4), o, 4)
amber, amber_d = (255, 176, 56), (150, 96, 24)
t1 = F_OLED.render("0:42", True, amber)
canvas.blit(t1, (o.x + 12, o.y + 8))
t2 = F_OLED_S.render("M83 - MIDNIGHT CITY", True, amber)
canvas.blit(t2, (o.x + 110, o.y + 14))
t3 = F_OLED_S.render("320kbps 44kHz", True, amber_d)
canvas.blit(t3, (o.x + 110, o.y + 34))
import random
random.seed(7)
for i in range(26):                                          # mini spectrum
    h = random.randint(4, 22)
    pygame.draw.rect(canvas, amber_d if i % 3 else amber,
                     (o.x + 12 + i * 9, o.bottom - 10 - h, 6, h))

# ---------- right key stack ---------------------------------------------------- #
def key(rect, label):
    rr(canvas, (12, 13, 15), rect.inflate(6, 6), 8)
    for i in range(rect.h):
        t = i / rect.h
        c = int(58 - 22 * t)
        pygame.draw.line(canvas, (c, c + 1, c + 3),
                         (rect.x, rect.y + i), (rect.right, rect.y + i))
    pygame.draw.line(canvas, (96, 100, 108), (rect.x + 3, rect.y + 2),
                     (rect.right - 3, rect.y + 2), 2)
    s = F_ENG_S.render(label, True, (200, 204, 210))
    canvas.blit(s, (rect.centerx - s.get_width() // 2,
                    rect.centery - s.get_height() // 2))

for i, lab in enumerate(["SHUFFLE", "LOOP", "PRESET"]):
    key(mmr(94, 8 + i * 13, 28, 9), lab)

# ---------- transport ----------------------------------------------------------- #
GLYPHS = ["◄◄", "►", "I I", "■", "►►"]
for i, g in enumerate(GLYPHS):
    c = mm(12 + i * 17, 39)
    pygame.draw.circle(canvas, (10, 11, 13), c, 30)
    for r_ in range(27, 0, -1):                            # domed cap
        t = r_ / 27
        col = int(30 + 34 * (1 - t))
        pygame.draw.circle(canvas, (col, col + 2, col + 5), (c[0] - 3, c[1] - 3), r_)
    pygame.draw.circle(canvas, (120, 124, 132), c, 27, 2)
    s = F_ENG_S.render(g, True, (44, 255, 120))
    canvas.blit(s, (c[0] - s.get_width() // 2, c[1] - s.get_height() // 2))

# ---------- fader helper --------------------------------------------------------- #
def alu_cap(cx, cy, w, h):
    cap = pygame.Rect(0, 0, w, h)
    cap.center = (cx, cy)
    rr(canvas, (8, 9, 10), cap.inflate(8, 8), 6)
    for i in range(cap.w):
        t = abs(i / cap.w - 0.5) * 2
        c = int(196 - 90 * t)
        pygame.draw.line(canvas, (c, c, c + 2), (cap.x + i, cap.y), (cap.x + i, cap.bottom))
    pygame.draw.rect(canvas, (30, 30, 34), cap, 2, border_radius=4)
    pygame.draw.line(canvas, (255, 120, 40), (cap.x + 4, cap.centery), (cap.right - 4, cap.centery), 3)

def hslot(x0, x1, cy, pos, label, label_cx):
    slot = pygame.Rect(mm(x0, cy - 1.5), ((x1 - x0) * S, 3 * S))
    rr(canvas, (8, 9, 11), slot.inflate(6, 6), 6)
    rr(canvas, (2, 2, 3), slot, 4)
    cx = slot.x + int(slot.w * pos)
    alu_cap(cx, slot.centery, 30, 46)
    engrave(label, OX + int(label_cx * S), slot.bottom + 12, F_ENG_S)

hslot(29, 91, 52, 0.45, "VOLUME", 60)

# ---------- view keys ------------------------------------------------------------- #
for i, lab in enumerate(["NOW PLAYING", "PLAYLISTS", "QUEUE"]):
    key(mmr(12 + i * 38, 66, 30, 10), lab)

# ---------- screen: render the REAL UI -------------------------------------------- #
from spotamp.models import PlayerState, Track, PlaybackStatus
from spotamp.library import BrowseState
from spotamp.ui.screen import ScreenUI
scr_src = pygame.display.set_mode((720, 720))
st = PlayerState(); st.status = PlaybackStatus.PLAYING
st.track = Track("Midnight City", "M83", "Hurry Up, We're Dreaming", 241000)
st.position_ms = 42000; st.battery_percent = 72.0
st.queue = [Track("Digital Love", "Daft Punk", "Discovery", 301000)]
ui = ScreenUI(scr_src, on_action=lambda *a, **k: None)
ui.update(st, 0.03); ui.draw(st, BrowseState())
shot = pygame.transform.smoothscale(scr_src.copy(), (int(73 * S) - 8, int(73 * S) - 8))

win = mmr(27, 82, 73, 73)
rr(canvas, (10, 11, 13), win.inflate(26, 26), 12)            # chamfered surround
rr(canvas, (52, 55, 62), win.inflate(26, 26), 12, 2)
rr(canvas, (0, 0, 0), win.inflate(8, 8), 4)
canvas.blit(shot, (win.x + 4, win.y + 4))
engrave("S P O T A M P", win.centerx, win.bottom + 26, F_ENG_S, (110, 114, 122))

# ---------- seek -------------------------------------------------------------------- #
hslot(32.5, 94.5, 172, 0.17, "SEEK", 63.5)

# ---------- EQ bank ------------------------------------------------------------------ #
levels = [0.55, 0.42, 0.65, 0.38, 0.5]
for i, (lab, lv) in enumerate(zip(["60", "400", "2K4", "15K", "PRE"], levels)):
    cx_mm = 17.5 + i * 23
    slot = pygame.Rect(0, 0, 3 * S, 62 * S)
    slot.center = (OX + int(cx_mm * S), OY + int(243 * S))
    rr(canvas, (8, 9, 11), slot.inflate(6, 6), 6)
    rr(canvas, (2, 2, 3), slot, 4)
    cy = slot.y + int(slot.h * (1 - lv))
    alu_cap(slot.centerx, cy, 62, 30)
    engrave(lab, slot.centerx, OY + int(203 * S), F_ENG_S,
            (255, 176, 56) if lab == "PRE" else (148, 152, 160))

pygame.image.save(canvas, r"C:\Users\VNET\AppData\Local\Temp\claude\C--Users-VNET-Documents-repos-winamp-player\ef0351fc-2012-48d9-b4b6-d26a47a866f1\scratchpad\product_render.png")
print("saved")
