# Power & Battery Design

The unit is handheld, so it runs from an internal battery with a regulated 5 V
rail, safe charging, battery monitoring, and a clean shutdown that protects the
SD card. This document sizes the system, recommends a topology that's easy for
others to replicate, and lists the tradeoffs.

> Status: **design + placeholders.** Cell counts, runtimes, and part choices are
> engineering estimates — verify against the specific boards/cells you buy.

## 1. Power budget

Measured/typical draw on a **Raspberry Pi 4 B** based system. Motors are the
spiky load — they only draw current *while moving*, and our firmware cuts motor
power once a fader reaches its target, so the holding current is ~0.

| Subsystem | Typical | Peak | Notes |
|---|---:|---:|---|
| Pi 4 B (app + Wi-Fi + audio) | 4.5 W | 7 W | 4 cores + USB busy |
| 4″ DSI/HDMI LCD + backlight | 1.2 W | 2 W | backlight dominates |
| I2S DAC + headphones | 0.3 W | 0.5 W | |
| speaker amp (TPA2016, internal stereo) | 1 W | 3 W | standalone playback; ~0 W with headphones (amp muted) |
| RP2040 + mux + LEDs | 0.4 W | 1 W | |
| Motorized faders (10×) | ~0.2 W avg | **~12–15 W** | brief spikes when several move at once |
| **System** | **~6.5 W avg** | **~20 W peak** | design the 5 V rail for **5 A** headroom |

Key takeaways:
- **Average ≈ 6.5 W.** That's what sets runtime.
- **Peaks to ~20 W** for <1 s when a preset loads and many faders slew together.
  The 5 V regulator must survive that; handle it with **bulk capacitance
  (1000–2200 µF) at the motor-driver rail** so spikes come from the caps, not the
  battery/regulator.

## 2. Recommended topology

For a project other people will replicate, favor a **safe, off-the-shelf,
monitored** solution over a hand-rolled pack:

```
 18650 Li-ion cells ─▶ UPS/BMS HAT ─▶ regulated 5 V (up to 5 A) ─▶ Pi 4 B + everything
        ▲                   │  │
   USB-C / DC charge ───────┘  └── I2C: battery %, voltage, AC-loss  ─▶ Pi (safe shutdown + UI meter)
```

**Baseline:** a Pi-oriented UPS HAT that takes 18650 cells, outputs a solid
5 V/5 A, and reports battery state over I2C — e.g. **Geekworm X728** (2×18650,
auto power-on, AC-loss detect, documented safe-shutdown scripts) or **Waveshare
UPS HAT (B)** (2×18650, 5 V/5 A, INA219 fuel gauge). Verify current model numbers
and Pi 4 compatibility before buying — SKUs churn.

Why a HAT and not a bare pack: you get **cell protection, a proven 5 V boost
rated for Pi 4 peaks, charge management, and I2C monitoring** in one board — the
hard, safety-critical parts done right.

**Decision (v1): Geekworm X728.** Its MAX17040 fuel gauge (I2C `0x36`) is what
`pi/winamp_player/power.py` (`X728Battery`) reads for the on-screen meter and
safe shutdown; it has documented shutdown scripts and AC-loss detection. Waveshare
UPS HAT (B) remains a drop-in alternative — swap the reader class if you use it.
For more runtime, feed a larger 18650 pack (4–6 cells) to the board's terminals.

## 3. Sizing the battery ("large" is the goal)

18650 cell ≈ 3500 mAh @ 3.6 V ≈ **12.6 Wh** raw. After boost efficiency (~90 %)
and a safe depth-of-discharge (~85 %), figure **~9.6 Wh usable per cell**. At the
~6.5 W average:

| Pack | Raw Wh | Usable Wh | Runtime @6.5 W | Notes |
|---|---:|---:|---:|---|
| 2 × 18650 | 25 | ~19 | **~3 h** | fits a 2-cell HAT; thin |
| 4 × 18650 | 50 | ~38 | **~6 h** | sweet spot for "large" |
| 6 × 18650 | 76 | ~58 | **~9 h** | needs a bigger body/pack |
| 8 × 18650 | 101 | ~77 | **~12 h** | ⚠ **>100 Wh = no airline carry-on** |

For "large batteries," target **4–6 cells**. Options to get there:
- a **4-cell UPS board**, or
- an **external 2S2P / 2S3P 18650 pack** wired to the HAT's cell terminals, or
- higher-capacity cells (Molicel P28A, Samsung 35E, LG MJ1).

**Airline note:** keep total under **100 Wh** if the device should be flyable;
loose spare cells have their own carry-on rules.

## 4. Cells: 18650 vs LiPo pouch (a real form-factor tradeoff)

| | 18650 Li-ion | LiPo pouch |
|---|---|---|
| Shape | cylindrical Ø18 × 65 mm | flat, custom W×H, thin |
| Fit in a 1″ (25 mm) body | tight next to 60 mm faders | **better** — lies flat |
| Safety / replaceability | **excellent**, standardized, swappable | fussier, needs careful protection |
| Best for | a shareable, safe DIY build | a genuinely thin body |

**Recommendation:** default to **18650** for safety and replaceability (this is a
public build others will copy). If you insist on the slim 1″ book profile, a
**flat LiPo pouch + a good 2S BMS + 5 V buck** is mechanically nicer — but note
that **a large battery may push the body past 1″**; faders already want ~20 mm of
depth, and an 18-mm cell beside them is tight. Call this out in the enclosure CAD.

## 5. Charging

- Charge over the HAT's **USB-C (or DC) input**; the UPS provides pass-through so
  the unit can run while charging.
- Charge current is typically **1–2 A** — a big 4–6 cell pack will take **several
  hours** to fill. If that's annoying, pick a board/charger that supports higher
  charge current and use a capable USB-PD supply.
- **Never** charge unbalanced multi-cell packs without a balancing BMS.

## 6. Safe shutdown + battery UI (software milestone)

The UPS HAT exposes battery voltage / state-of-charge over **I2C**. The Pi should:
1. Read SoC periodically (INA219 / fuel gauge / board's ADC).
2. Show a **WinAmp-style battery meter** on the LCD (a natural fit for the skin).
3. On **low battery** (~5 %) or **AC-loss + threshold**, trigger a clean
   `shutdown` so the SD card isn't corrupted.

Planned code: `pi/winamp_player/power.py` (battery monitor) + a battery widget in
the UI. *Placeholder for now* — implement once the specific UPS board is chosen,
since the I2C register map is board-specific.

## 7. Grounding & wiring notes

- Join **motor ground** and **logic ground** at a single star point near the
  regulator; H-bridges inject noise.
- Put the **bulk caps physically at the DRV8833 rails**, not near the Pi.
- Fuse the battery output; add a physical **power switch** on the 5 V rail (or use
  the HAT's soft-power button + auto-boot).
- Keep motor-current wiring short and thick; keep it away from the audio/DAC lines
  to avoid whine.

## 8. Open questions / TODO

- [ ] Pick the exact UPS board (2- vs 4-cell) and confirm 5 V/5 A + I2C monitoring.
- [ ] Decide 18650 vs LiPo once the enclosure thickness is locked.
- [ ] Bench-measure real average draw (esp. motor duty cycle) to firm up runtime.
- [ ] Implement `power.py` + battery meter + safe-shutdown against the chosen board.
- [ ] Verify total Wh vs the airline limit if portability matters.
