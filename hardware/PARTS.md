# Parts List (vendor shopping list)

The buyable version of [BOM.md](BOM.md) — real SKUs, grouped by vendor,
**Adafruit-first** where they stock it. Prices are USD as checked **2026-07-16**
(spot-verified where marked ✓; others are recent typicals — confirm at checkout).

Datasheets for everything here: run [`datasheets/fetch.sh`](datasheets/) and see
[datasheets/README.md](datasheets/README.md).

## Already owned ✅

| Part | Note |
|---|---|
| Raspberry Pi 4 B | running the player today |
| Pimoroni HyperPixel 4.0 Square | mounted + working |
| microSD 32 GB | flashed |

## 🛒 Adafruit (one cart)

| Part | SKU | Qty | ~$ ea | ~$ | For |
|---|---|---|---|---|---|
| 12-key capacitive touch (MPR121) | [1982](https://www.adafruit.com/product/1982) | 1 | 7.95 | 7.95 | seek-knob touch electrode (1 ch used) |
| MCP23017 GPIO expander breakout | [5346](https://www.adafruit.com/product/5346) | 1 | 5.95 | 5.95 | 13 panel buttons |
| DRV8833 dual motor driver breakout ✓ | [3297](https://www.adafruit.com/product/3297) | 1 | 5.95 | 5.95 | the ONE seek motor (direct Pico PWM — no PCA9685s in the build) |
| Raspberry Pi Pico | ⚠️ **OOS at Adafruit (all variants, 2026-07)** — Micro Center/PiShop/Amazon ~$4 | 1 | 4.00 | 4.00 | controls brain |
| USB audio adapter (USB DAC) | [1475](https://www.adafruit.com/product/1475) | 1 | 4.95 | 4.95 | audio out |
| Tactile switches 12 mm (10-pack) ✓ | [1119](https://www.adafruit.com/product/1119) | 2 pk | 2.50 | 5.00 | 13 panel buttons + spares |
| **Stereo 2.8 W Class-D amp, I2C AGC (TPA2016)** ✓ | [1712](https://www.adafruit.com/product/1712) | 1 | 9.95 | 9.95 | internal speakers (on the RP2040 I2C bus) |
| **Mono enclosed speaker 3 W 4 Ω ×2** ✓ | [3351](https://www.adafruit.com/product/3351) | 2 | 3.95 | 7.90 | stereo pair; the 1669 set stays OOS (DigiKey stocks it if preferred) |
| Switched 3.5 mm stereo jack (headphone detect) | generic panel-mount TRS w/ switch | 1 | 2 | 2.00 | headphones optional — insert mutes the amp |
| Perma-Proto half-size (singles ×3 — 3-pack OOS) ✓ | [1609](https://www.adafruit.com/product/1609) | 3 | 4.50 | 13.50 | interconnect boards |
| Hook-up wire, JST kits, headers | misc | — | — | ~15 | wiring |
| **Adafruit subtotal (cart built 2026-07-17: $61.15 + wire/misc)** | | | | **≈ 76** | |

> Adafruit doesn't stock: motorized faders, the SSD1322 OLED, the UPS, or bare
> 18650 cells — those come from the vendors below.

## 🛒 The seek mechanism (custom belt drive — see enclosure.md)

| Part | Source | Qty | ~$ |
|---|---|---|---|
| Manual long-travel slide pot, 10 kΩ linear, ~85–90 mm travel, body ≤118 mm (**VERIFY**) | DigiKey/Mouser (Bourns PTB-class) or Soundwell | 1 (+1 spare) | 4–8 |
| N20 micro gearmotor, 6 V, low ratio (≤30:1) — backdrivable | Amazon/Pololu | 2 (spare) | 8 |
| GT2 16T pulleys ×2 + GT2 belt (200 mm loop) | printer-parts vendors | 1 set | 6 |
| Slip-clutch hub | 3D-printed (design ours) | — | — |

> **No packaged motorized faders in the build anymore** — the EQ/volume/balance
> are slim manual pots and seek is the custom drive. Bench-prove the slip clutch
> with these parts before cutting the panel.

## 🛒 Slim pots (EQ ×11 + volume + balance)

| Part | Source | Qty | ~$ |
|---|---|---|---|
| Slim slide pot, 45 mm travel, 10 kΩ linear (9 mm body) | DigiKey/Mouser/Soundwell | 13 (11 EQ + vol + spare) | 20–30 |
| Mini slide pot, 20 mm travel (balance) | same | 1 | 2 |

## 🛒 Geekworm — power

| Part | Source | Qty | ~$ |
|---|---|---|---|
| X728 UPS/BMS HAT (current rev, V2.5+) | [geekworm.com](https://geekworm.com/products/x728) / [Amazon](https://www.amazon.com/dp/B087FXLZZH) | 1 | 36 |

## 🛒 Battery vendor (18650BatteryStore / Illumn)

| Part | Qty | ~$ ea | ~$ |
|---|---|---|---|
| Samsung 35E 18650 (3500 mAh, button-top per X728 holder spec) | 4 | 6 | 24 |

> Buy cells from a reputable battery house, not marketplace listings — counterfeit
> 18650s are endemic. Verify button vs flat top against the X728 holder.

## 🛒 OLED readout (pick one)

| Option | Source | ~$ | Note |
|---|---|---|---|
| Generic SSD1322 3.12″ 256×64 SPI | [Amazon](https://www.amazon.com/Display-Module-Graphic-SSD1322-Monochrome/dp/B0CHP98SVP) / [BuyDisplay ER-OLED032-1](https://www.buydisplay.com/3-2-inch-oled-display-module-ssd1322-controller-256x64-dot-green-on-black) | 22–28 | fastest/cheapest |
| Newhaven **NHD-3.12-25664UCY2** (yellow/amber) | [newhavendisplay.com](https://newhavendisplay.com/3-12-inch-yellow-graphic-oled-module/) | ~38 | premium, proper datasheet + mechanical drawing — best for the aluminum build |

> Order the **SPI** interface variant, and amber/yellow for the retro look.

## Misc (Amazon/local)

| Part | ~$ |
|---|---|
| Electrolytic caps 2200 µF/10 V ×2, inline fuse + holder, rocker/slide power switch | 8 |
| M2.5/M3 machine screws, standoffs, heat-set inserts (for the printed case) | 10 |
| **Aluminum knobs** (final build): 11× fader caps + 2× knurled encoder knobs — 3D-printed on the prototype | 25–40 |
| **Kickstand hardware**: 2× adjustable-torque (position-control) hinges, rubber bumper feet ×6, 2× ø8 magnets + steel discs | 20 |

## Totals

| | ~$ |
|---|---|
| Adafruit (incl. amp + speakers) | 98 |
| Seek mechanism (pot + N20 + GT2) | 20 |
| Slim pots (EQ + vol + bal) | 25–35 |
| Power (Geekworm + cells) | 60 |
| OLED | 22–38 |
| Misc | 18 |
| **New parts total** | **≈ 245–270** |

(On top of the already-owned Pi/HyperPixel/SD ≈ $110 — consistent with the
[BOM](BOM.md) estimate of $490–540 all-in.)

## Suggested order of orders

1. **Adafruit cart + the seek-mechanism kit** (long-travel pot, N20, GT2 set) →
   bench-prove the belt drive + slip clutch (issue #65) before cutting the panel.
2. **Slim pots + OLED** → the full control surface.
3. **X728 + cells** → battery/power milestone (Phase 7).
