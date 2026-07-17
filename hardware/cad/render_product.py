"""SpotAmp — Yanko-faithful product render (127x246, one motor, slim pots)."""
import os, sys, math, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, r"C:\Users\VNET\Documents\repos\winamp-player\pi")
import pygame
pygame.init()

S = 4
PW, PH = 127 * S, 246 * S
CW, CH = PW + 220, PH + 240
OX, OY = 110, 100
canvas = pygame.Surface((CW, CH))

for y in range(CH):
    g = int(216 - 40 * y / CH)
    pygame.draw.line(canvas, (g, g + 2, g + 6), (0, y), (CW, y))
sh = pygame.Surface((CW, 130), pygame.SRCALPHA)
pygame.draw.ellipse(sh, (18, 18, 24, 95), (OX - 40, 30, PW + 80, 80))
canvas.blit(sh, (0, OY + PH - 40))

def rr(surf, color, rect, rad, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=rad)

for i, a in ((14, 26), (9, 42), (5, 62)):
    shd = pygame.Surface((PW + 2 * i, PH + 2 * i), pygame.SRCALPHA)
    rr(shd, (10, 10, 14, a), shd.get_rect(), 26 + i)
    canvas.blit(shd, (OX - i, OY - i + 6))
plate = pygame.Surface((PW, PH), pygame.SRCALPHA)
for y in range(PH):
    base = 33 + int(9 * math.sin((y / PH) * math.pi))
    pygame.draw.line(plate, (base, base, base + 3), (0, y), (PW, y))
mask = pygame.Surface((PW, PH), pygame.SRCALPHA)
rr(mask, (255, 255, 255), mask.get_rect(), 22)
plate.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
canvas.blit(plate, (OX, OY))
rr(canvas, (70, 73, 80), (OX, OY, PW, PH), 22, 2)

def mm(x, y): return (OX + int(x * S), OY + int(y * S))
def mmr(x, y, w, h): return pygame.Rect(OX + int(x * S), OY + int(y * S), int(w * S), int(h * S))

F_ENG = pygame.font.SysFont("segoeui", 12)
F_TINY = pygame.font.SysFont("segoeui", 10)
F_TIME = pygame.font.SysFont("consolas", 30, bold=True)
F_OLED = pygame.font.SysFont("consolas", 14, bold=True)
F_PILL = pygame.font.SysFont("consolas", 12, bold=True)
AMB, AMB_D = (255, 172, 52), (140, 90, 24)

def engrave(text, cx, y, font=F_TINY, col=(150, 152, 158)):
    s = font.render(text, True, col)
    canvas.blit(font.render(text, True, (10, 10, 12)), (cx - s.get_width() // 2 + 1, y + 1))
    canvas.blit(s, (cx - s.get_width() // 2, y))

def well(rect, rad=6):
    rr(canvas, (12, 13, 15), rect.inflate(8, 8), rad + 3)
    rr(canvas, (58, 60, 66), rect.inflate(8, 8), rad + 3, 1)
    rr(canvas, (7, 5, 2), rect, rad)

# ---------------- OLED cluster: four lit apertures over one display ----------- #
vis = mmr(8, 7.5, 26, 18)
well(vis)
canvas.blit(F_TIME.render("0:42", True, AMB), (vis.x + 8, vis.y + 4))
random.seed(11)
for i in range(15):
    h = random.randint(5, 26)
    pygame.draw.rect(canvas, AMB if i % 3 else AMB_D,
                     (vis.x + 6 + i * 6, vis.bottom - 6 - h, 4, h))
title = mmr(37.5, 7.5, 46.5, 7.5)
well(title, 10)
canvas.blit(F_OLED.render("M83 - MIDNIGHT CITY", True, AMB), (title.x + 8, title.y + 6))
for px, txt in ((37.5, "320"), (53.5, "44")):
    p = mmr(px, 17.5, 13, 6)
    well(p, 8)
    s = F_PILL.render(txt, True, AMB)
    canvas.blit(s, (p.centerx - s.get_width() // 2, p.centery - s.get_height() // 2))
engrave("KBPS", int(mm(44, 25.5)[0]), mm(44, 25.5)[1], F_TINY)
engrave("KHZ", int(mm(60, 25.5)[0]), mm(60, 25.5)[1], F_TINY)

# view toggles (EQ/PL style)
for i, lab in enumerate(["NOW", "PL", "QUE"]):
    c = mm(98 + i * 11, 13)
    pygame.draw.circle(canvas, (10, 11, 13), c, 14)
    for r_ in range(11, 0, -1):
        col = int(34 + 30 * (1 - r_ / 11))
        pygame.draw.circle(canvas, (col, col, col + 3), (c[0] - 1, c[1] - 2), r_)
    pygame.draw.circle(canvas, (110, 113, 120), c, 12, 1)
    if i == 0:
        pygame.draw.circle(canvas, AMB, (c[0], c[1] + 7), 2)   # active LED
    engrave(lab, c[0], c[1] + 20)

# ---------------- ribbed orange cap ------------------------------------------- #
def rib_cap(cx, cy, w, h, horiz=True):
    cap = pygame.Rect(0, 0, w, h)
    cap.center = (cx, cy)
    rr(canvas, (8, 9, 10), cap.inflate(6, 6), 5)
    for i in range(cap.h):
        t = i / cap.h
        pygame.draw.line(canvas, (int(252 - 96 * t), int(116 - 58 * t), int(44 - 24 * t)),
                         (cap.x, cap.y + i), (cap.right, cap.y + i))
    pygame.draw.rect(canvas, (70, 30, 12), cap, 2, border_radius=4)
    if horiz:
        for fx in range(cap.x + 5, cap.right - 4, 6):
            pygame.draw.line(canvas, (120, 48, 18), (fx, cap.y + 3), (fx, cap.bottom - 3), 2)
    else:
        for fy in range(cap.y + 5, cap.bottom - 4, 6):
            pygame.draw.line(canvas, (120, 48, 18), (cap.x + 3, fy), (cap.right - 3, fy), 2)

def hslot(x0_mm, cy_mm, len_mm, pos, capw=26, caph=40):
    slot = pygame.Rect(mm(x0_mm, cy_mm - 1.25), (int(len_mm * S), int(2.5 * S)))
    well(slot, 5)
    rib_cap(slot.x + int(slot.w * pos), slot.centery, capw, caph)
    return slot

# volume / balance / bolt
vslot = hslot(10, 42, 47, 0.6)
engrave("-", vslot.x - 12, vslot.y - 4, F_ENG)
engrave("+", vslot.right + 12, vslot.y - 4, F_ENG)
engrave("VOLUME", vslot.centerx, vslot.bottom + 12)
bslot = hslot(72, 42, 22, 0.5, 20, 34)
engrave("L", bslot.x - 10, bslot.y - 4, F_ENG)
engrave("R", bslot.right + 10, bslot.y - 4, F_ENG)
engrave("BALANCE", bslot.centerx, bslot.bottom + 12)
# brand engrave (bolt removed — SpotAmp, not WinAmp)
F_BRAND = pygame.font.SysFont("segoeui", 17, bold=True, italic=True)
bs = F_BRAND.render("SpotAmp", True, (168, 172, 180))
bd = F_BRAND.render("SpotAmp", True, (10, 10, 12))
bx, by = mm(114, 42)
canvas.blit(bd, (bx - bs.get_width() // 2 + 1, by - bs.get_height() // 2 + 1))
canvas.blit(bs, (bx - bs.get_width() // 2, by - bs.get_height() // 2))

# SEEK — custom belt-drive: near-full-width slot
sk = hslot(20, 58.5, 87, 0.14, 34, 52)
engrave("SEEK", mm(12, 53)[0], mm(52, 53)[1], F_ENG)

# transport keycaps
def keycap(x_mm, y_mm, w_mm, h_mm, glyph, gcol=AMB):
    k = mmr(x_mm, y_mm, w_mm, h_mm)
    rr(canvas, (10, 11, 13), k.inflate(6, 6), 7)
    for i in range(k.h):
        c = int(60 - 24 * i / k.h)
        pygame.draw.line(canvas, (c, c + 1, c + 4), (k.x, k.y + i), (k.right, k.y + i))
    pygame.draw.line(canvas, (100, 104, 112), (k.x + 3, k.y + 2), (k.right - 3, k.y + 2), 2)
    rr(canvas, (26, 27, 30), k, 6, 1)
    s = F_ENG.render(glyph, True, gcol)
    canvas.blit(s, (k.centerx - s.get_width() // 2, k.centery - s.get_height() // 2))

for i, g in enumerate(["◄◄", "►", "▍▍", "■", "►►"]):
    keycap(9 + i * 15, 69, 13, 9, g)
keycap(85, 69, 20, 9, "SHUFFLE", (190, 193, 200))
keycap(107.5, 69, 15, 9, "LOOP", (190, 193, 200))

# ---------------- screen ------------------------------------------------------- #
from spotamp.models import PlayerState, Track, PlaybackStatus
from spotamp.library import BrowseState
from spotamp.ui.screen import ScreenUI
scr_src = pygame.display.set_mode((720, 720))
st = PlayerState(); st.status = PlaybackStatus.PLAYING
st.track = Track("Midnight City", "M83", "Hurry Up, We're Dreaming", 241000)
st.position_ms = 42000; st.battery_percent = 72.0
ui = ScreenUI(scr_src, on_action=lambda *a, **k: None)
ui.update(st, 0.03); ui.draw(st, BrowseState())
shot = pygame.transform.smoothscale(scr_src.copy(), (int(73 * S) - 8, int(73 * S) - 8))
win = mmr(27, 86, 73, 73)
rr(canvas, (10, 11, 13), win.inflate(26, 26), 12)
rr(canvas, (56, 59, 66), win.inflate(26, 26), 12, 2)
rr(canvas, (0, 0, 0), win.inflate(8, 8), 4)
canvas.blit(shot, (win.x + 4, win.y + 4))


# ---------------- EQ module ------------------------------------------------------ #
keycap(10, 168, 16, 8, "ON", (190, 193, 200))
keycap(29, 168, 16, 8, "AUTO", (190, 193, 200))
keycap(98, 168, 24, 8, "PRESET", AMB)
for lab, ymm in (("+12", 183), ("0", 205.5), ("-12", 228)):
    engrave(lab, mm(5.5, ymm)[0], mm(5.5, ymm)[1], F_TINY, (120, 122, 128))
levels = [0.62, 0.45, 0.5, 0.58, 0.63, 0.66, 0.62, 0.55, 0.5, 0.47, 0.44]
bands = ["PRE", "60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
for i, (lab, lv) in enumerate(zip(bands, levels)):
    cx = OX + int((14.5 + i * 10.4) * S)
    slot = pygame.Rect(0, 0, int(2.5 * S), int(47 * S))
    slot.center = (cx, OY + int(206.5 * S))
    well(slot, 5)
    rib_cap(cx, slot.y + int(slot.h * (1 - lv)), 30, 15, horiz=False)
    engrave(lab, cx, slot.bottom + 8, F_TINY, AMB if lab == "PRE" else (140, 143, 150))

pygame.image.save(canvas, r"C:\Users\VNET\AppData\Local\Temp\claude\C--Users-VNET-Documents-repos-winamp-player\ef0351fc-2012-48d9-b4b6-d26a47a866f1\scratchpad\product_render.png")
print("saved")
