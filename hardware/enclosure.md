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
| **Fader body is ~106.5 mm LONG (M3 mounts 80 mm apart)** — found drawing the DXF | A *vertical* EQ fader needs ~110 mm of panel height, not the ~66 mm sketched earlier. The honest full stack (top module + volume + 73 mm screen + seek + EQ bank) sets the panel at **175 × 280 mm (6.9″ × 11″)** — which matches the Yanko render's real proportions. The laid-out proof: [cad/front-panel.dxf](cad/). |

### EQ-bank width options (decision pending)

| Option | Panel math | Trade-off |
|---|---|---|
| **A. Widen the body to ~165 mm (6.5″)** | 8 × 20 = 160 ✓ | keeps all 7 bands + preamp motorized; body is no longer "small book" |
| **B. 5 bands + preamp** | 6 × 20 = 120 ✓ fits 127 | fewer bands; protocol/firmware are per-band so it's a config change |
| **C. Reduced build** (motorized volume + seek only, slim non-motorized pots for EQ) | narrow pots ~10 mm pitch ✓ | loses the animated-EQ showpiece |

> **Current direction (2026-07-17, pending 1:1 print approval): the ONE-MOTOR
> design — 127 × 246 × ~30 mm** (`cad/front-panel-final.*`). EQ/volume/balance
> use slim non-motorized pots (full classic PRE + 10-band bank fits the beloved
> 127 mm width); **seek keeps the single motorized RS60N** (song-tracking
> showpiece). Yanko-faithful details: 4 sculpted apertures over the one OLED,
> WinAmp stack order, ON/AUTO/PRESET EQ header, ribbed caps, recessed wells.
> Electronics collapse: no PCA9685s, 1× DRV8833, ~−$220. The earlier 175 × 280
> all-motorized drawing (`cad/front-panel.*`) is superseded on approval.

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

## Kickstand (added 2026-07-17 — this is a DESKTOP device)

Per the concept's pop-out stand: the device lives on a desk, leaning back —
portable between rooms, not pocket-portable. Design decisions:

- **Type**: a flat **fold-out leg** hinged across the rear at the EQ-module
  height (lower third), Surface-style. In aluminum it's a machined flat plate —
  looks fantastic anodized; on the prototype it's the same geometry printed.
- **Hinges**: 2× **adjustable-torque (position-control) hinges** so the angle is
  continuously adjustable and holds anywhere (~$6–12 ea). Cheaper fallback: a
  plain piano hinge + a fold-out wire strut into detent notches (two angles).
- **Angle range**: 0° (flush) to ~40° open → face angle ~70–80° from the desk,
  matching the render and comfortable for fader reach + screen viewing.
- **Tip resistance — the physics that matters**: users *push* faders and buttons
  (1–3 N) near the top of a 280 mm face. The leg tip must land **well behind the
  center of mass** (leg ≥ 120 mm long), with **rubber feet on the leg tip and the
  body's bottom edge**. The battery pack (the heaviest part) mounts LOW in the
  body — it's the counterweight.
- **Flush stowage**: the rear tray gets a **recessed pocket** so the closed leg
  sits flush (machinable pocket — large corner radii; printable as-is). A small
  **magnet + steel disc** holds it closed with a satisfying snap.
- **Don't-block list**: the leg (open or closed) must not cover the USB-C charge
  port, the power switch, the thermal-pad zone (rear tray = heatsink), or the
  **Wi-Fi antenna window** — place the pocket accordingly in CAD.
- The rear tray + stand get their own generated drawing when we do the body CAD
  (the parametric generator extends to it — same source of truth as the panel).

## The OLED aperture cluster (how the "multiple displays" work)

One 256×64 OLED sits behind **four sculpted apertures** (time+spectrum window,
title strip, two kbps/kHz pills) — the panel mask turns one display into four.
Implementation notes:
- The apertures must land inside the OLED's **76.78 × 19.18 mm active area**;
  positions in `cad/generate_panel.py` are derived from it. Mask alignment
  tolerance ±0.5 mm — locate the OLED with pins/bosses, not adhesive guesswork.
- Put a **smoked/amber acrylic layer** (~1 mm) behind the apertures so off
  pixels vanish into black and the windows read as separate lit instruments.
- Firmware renders each element at fixed pixel regions matching the mask (the
  `DISP` data already carries everything; the region map is a table in
  `firmware/src/config.h` when formalized).

## The seek mechanism (owner's design, 2026-07-17): custom belt drive

Off-the-shelf motorized faders package the motor IN-LINE with the track — the
RS60N wastes 46 mm of length beyond its travel, and the 100 mm RSA0N is 146.5 mm
long. **We build the drive ourselves instead** (this is how flying faders work
internally anyway):

- **Panel part**: a slim **manual long-travel slide pot** (~85–90 mm travel,
  body ≤ 118 mm — VERIFY candidate part) → the slot spans ~70 % of the face at
  the 127 mm width. Wiper = position feedback (mux, as always); metal knob =
  touch electrode (MPR121).
- **Drive**: micro gearmotor (N20-class) + 2× GT2 16T pulleys + a GT2 belt loop
  behind the panel, with a printed clamp tying the belt to the fader lever — a
  miniature 3D-printer axis. Motor mounts beside/behind; envelope ~120 × 14 mm
  (REF box in the cut drawing).
- **Electronics/firmware unchanged**: DRV8833 + the existing PID loop drive it
  identically to a packaged motorized fader.
- ⚠️ **The critical detail — backdrivability**: the user must be able to grab
  the fader anytime. High-ratio gearmotors lock. Prototype in this order:
  (1) **slip-clutch pulley** — printed friction hub on the motor pulley (what
  ALPS does internally); (2) low-ratio (≤30:1) or coreless motor that
  backdrives freely; (3) touch-triggered release as backup. **Bench-prove the
  clutch before committing the panel.**
- Benefits: −$20 ALPS fader → +~$15 of motor/belt/pulleys, every mechanical
  part printable now and machinable later, and the seek slot finally matches
  the concept's proportions.

### Why output-side sensing (and not a servo indicator)

Considered and rejected (2026-07-17): a servo-driven progress pointer ("the
motor knows the position"). Three reasons the pot-on-the-knob topology wins:
1. **The pot measures the actual knob** — belt slip is cosmetic and
   self-correcting (PID drives until the *output* arrives). A servo knows only
   its motor-side pot; a loose linkage lies with no sensor to catch it.
2. **Touch-gating means motor motion can never seek the song** — position
   events only fire while the MPR121 senses a grab. The song clock lives in
   go-librespot; the fader follows it, not vice-versa.
3. **Servos aren't back-drivable** — grab-to-scrub (the whole point) dies.

**De-risk path**: the panel is identical with or without the motor — if the
slip-clutch prototype disappoints, v1 ships seek as a manual-scrub fader and
the belt drive lands in v1.1 with zero panel changes.

## Knobs & finish

- **Final build**: aluminum fader caps (T-bar or rectangular, for the ALPS 9-T
  lever) + knurled aluminum encoder knobs, anodized to match or contrast the body.
- **Prototype**: 3D-print the same knob geometry so the CAD is shared — print to
  fit, then order/machine the aluminum versions from the identical model.
- Fader caps must clear adjacent slots at 20 mm pitch — cap width ≤ 16 mm.

Grab the **ALPS STEP model** from the product page when CAD starts — it's the
part everything else packs around.
