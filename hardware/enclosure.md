# Enclosure design notes

The case will be **3D-printed for the prototype** and, if it earns it,
**CNC-machined in anodized aluminum** for the final build. Every enclosure
decision must work for **both** processes — design for machining from day one,
print the same geometry.

## ⚠️ Findings from the real datasheets (2026-07-16)

Reading the ALPS RS60N11M9A0F drawing (see [datasheets/](datasheets/)) surfaced
three facts that change the body:

| Finding | Consequence |
|---|---|
| Fader body is **18.5 mm wide** → min pitch ~19–20 mm | An 8-fader bank needs **~155 mm**, but the panel is 127 mm. **The 7-band + preamp bank does not fit a 5″ width.** Options below. |
| Fader is **26 mm deep below the panel** | Body thickness grows from 25 mm to **~32 mm (1.25″)** (panel + 26 + wiring clearance), or the fader zone gets a raised rear bulge. |
| Fader motor rated **10 V / ≤800 mA** | On our 5 V rail the slew is slower/weaker (workable, common in DIY). Optional: a small 9 V boost for the motor rail. Bench-test with fader #1 before deciding. |

### EQ-bank width options (decision pending)

| Option | Panel math | Trade-off |
|---|---|---|
| **A. Widen the body to ~165 mm (6.5″)** | 8 × 20 = 160 ✓ | keeps all 7 bands + preamp motorized; body is no longer "small book" |
| **B. 5 bands + preamp** | 6 × 20 = 120 ✓ fits 127 | fewer bands; protocol/firmware are per-band so it's a config change |
| **C. Reduced build** (motorized volume + seek only, slim non-motorized pots for EQ) | narrow pots ~10 mm pitch ✓ | loses the animated-EQ showpiece |

> The user's earlier call: "a little bigger than my initial dimensions is fine" —
> so **Option A (~165 × 210 × 32 mm)** is the working default until CAD says
> otherwise. The front-panel diagram will be redrawn at final dimensions in CAD.

## Design-for-machining rules (apply from the first CAD sketch)

1. **Two flat-dominant halves**: front panel (all cutouts) + rear tray (cavity).
   Both machinable from plate stock on a 3-axis mill; both printable flat.
2. **Internal corner radii ≥ 2 mm** everywhere a cutter must reach (an end mill
   can't cut a sharp inside corner). Exterior corners can be sharp or chamfered.
3. **No snap-fits, no living hinges, no print-in-place** — those are FDM-only.
   Fasten with **machine screws from the rear** into bosses: heat-set inserts in
   the printed version, **drilled + tapped** in aluminum (M3, ≥6 mm thread).
4. **Wall thickness ≥ 2 mm** (aluminum) / ≥ 2.4 mm (FDM, 6 perimeters at 0.4 mm).
5. **Through-cutouts are cheap in both processes** (fader slots, screen window,
   button holes, OLED window). **Deep pockets** with small tools are expensive —
   keep pocket depth ≤ 4× tool diameter where possible.
6. **Anodizing allowances**: type II adds ~5–10 µm/surface (negligible), but
   **mask or re-tap threads after anodizing** (anodized threads gall);
   bead-blast before anodize for the matte look. Black or clear both look right;
   colored fill on engraved labels is an option (engrave → anodize → fill).
7. **Labels**: engrave (V-bit or laser) rather than print/silkscreen — works on
   both plastic and aluminum, and survives handling.
8. 📡 **Wi-Fi in an aluminum box does not work.** The Pi's antenna will be
   completely shielded. Plan one of:
   - a **plastic antenna window** (the screen bezel area can be polymer trim),
   - the **kickstand slot / speaker grille** doubling as an RF aperture near the
     Pi's antenna corner,
   - or an **external/relocated antenna** (Pi 4 antenna mod is invasive — prefer
     the window). The FDM prototype hides this problem; **test Wi-Fi with the
     aluminum rear tray fitted** before finalizing.
9. **Serviceability**: the fader bank should mount to the panel with its M3
   screws (per the ALPS drawing: 2× M3 per fader, mounting-hole pattern in the
   datasheet) so a failed fader is replaceable without disassembling the stack.
10. **Thermals**: Pi 4 + motor drivers in a sealed metal box is actually *good*
    (the case is the heatsink) — add a thermal pad from the Pi SoC to the rear
    tray in the aluminum version; the printed version needs vent slots instead.

## Reference dimensions for CAD

| Component | Envelope | Source |
|---|---|---|
| ALPS RS60N fader | 18.5 w × ~88 l × 26 mm below panel; lever +8.2 mm | datasheet drawing |
| HyperPixel 4.0 Square | ~85 × 85.5 × 12 mm | product page (verify) |
| Pi 4 B | 85 × 56 mm, holes 58 × 49 mm grid | `pi4-mechanical-drawing.pdf` |
| X728 UPS | HAT: 85 × 56 mm + 18650 holders | wiki.geekworm.com/X728 |
| Pico | 51 × 21 mm | `pico-datasheet.pdf` |
| OLED module | ≈ 88 × 27.8 mm | NHD spec (verify) |

## Speakers (added 2026-07-16 — standalone playback, headphones optional)

- **Drivers**: enclosed stereo pair, **70 × 30 × 17 mm each** (sealed backs — no
  custom acoustic chamber needed; they just bolt in). Fits the 32 mm depth.
- **Placement**: side edges of the top module firing outward, or flanking the
  screen — decide in CAD around the fader bank. Keep them away from the
  HyperPixel's rear (magnet clearance) and off the fader axis (vibration).
- **Grilles**: a drilled hole pattern looks *great* in anodized aluminum and is
  trivially machinable (≥1.5 mm holes, ≥2× diameter spacing). The FDM version
  prints the same pattern.
- **Headphone jack**: panel-mount switched TRS; insertion detect → MCP23017
  spare input → firmware mutes the TPA2016 over I2C. Jack near the bottom edge
  (cable hangs naturally when handheld).
- **Vibration**: mount drivers on thin foam gaskets so the aluminum panel
  doesn't buzz at volume.
- **Loudness upgrade slot (decided 2026-07-16)**: v1 ships the TPA2016; the CAD
  reserves space for a **MAX9744 (I2C, same bus) + 5→12 V boost** and grille area
  for ~2″/5 W drivers — the "small boombox" tier is a one-board swap after bench
  listening, no redesign.

## Knobs & finish

- **Final build**: aluminum fader caps (T-bar or rectangular, for the ALPS 9-T
  lever) + knurled aluminum encoder knobs, anodized to match or contrast the body.
- **Prototype**: 3D-print the same knob geometry so the CAD is shared — print to
  fit, then order/machine the aluminum versions from the identical model.
- Fader caps must clear adjacent slots at 20 mm pitch — cap width ≤ 16 mm.

Grab the **ALPS STEP model** from the product page when CAD starts — it's the
part everything else packs around.
