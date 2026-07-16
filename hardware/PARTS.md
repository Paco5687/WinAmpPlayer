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
| 16-Ch 12-bit PWM driver (PCA9685) ✓ | [815](https://www.adafruit.com/product/815) | 2 | 14.95 | 29.90 | motor PWM (20 ch) |
| 12-key capacitive touch (MPR121) | [1982](https://www.adafruit.com/product/1982) | 1 | 7.95 | 7.95 | fader touch-sense |
| MCP23017 GPIO expander breakout | [5346](https://www.adafruit.com/product/5346) | 1 | 5.95 | 5.95 | 13 panel buttons |
| DRV8833 dual motor driver breakout | [3297](https://www.adafruit.com/product/3297) | 5 | 4.95 | 24.75 | fader motors ×10 |
| Raspberry Pi Pico | [4864](https://www.adafruit.com/product/4864) | 1 | 4.00 | 4.00 | controls brain |
| USB audio adapter (USB DAC) | [1475](https://www.adafruit.com/product/1475) | 1 | 4.95 | 4.95 | audio out |
| Rotary encoder w/ push (24-det) | [377](https://www.adafruit.com/product/377) | 2 | 4.50 | 9.00 | scroll/select |
| Tactile buttons, 12 mm assortment | [1119](https://www.adafruit.com/product/1119) | 1 pk | 5.95 | 5.95 | 13 panel buttons |
| NeoPixel Stick (8× WS2812) | [1426](https://www.adafruit.com/product/1426) | 1 | 5.95 | 5.95 | VU/status glow |
| Slide potentiometer, 45 mm | [4271](https://www.adafruit.com/product/4271) | 1 | 1.95 | 1.95 | balance |
| **Stereo 2.8 W Class-D amp, I2C AGC (TPA2016)** ✓ | [1712](https://www.adafruit.com/product/1712) | 1 | 9.95 | 9.95 | internal speakers (on the RP2040 I2C bus) |
| **Enclosed stereo speaker set, 3 W 4 Ω** ✓ | [1669](https://www.adafruit.com/product/1669) | 1 | 7.50 | 7.50 | 70×30×17 mm each, sealed backs — ⚠️ out of stock at check (notify list; alt: 2× mono enclosed [3351](https://www.adafruit.com/product/3351)) |
| Switched 3.5 mm stereo jack (headphone detect) | generic panel-mount TRS w/ switch | 1 | 2 | 2.00 | headphones optional — insert mutes the amp |
| Perma-Proto half-size ×3 | [571](https://www.adafruit.com/product/571) | 1 pk | 12.50 | 12.50 | interconnect boards |
| Hook-up wire, JST kits, headers | misc | — | — | ~15 | wiring |
| **Adafruit subtotal** | | | | **≈ 148** | |

> Adafruit doesn't stock: motorized faders, the SSD1322 OLED, the UPS, or bare
> 18650 cells — those come from the vendors below.

## 🛒 DigiKey (or Mouser) — the faders

| Part | SKU | Qty | ~$ ea | ~$ |
|---|---|---|---|---|
| ALPS **RS60N11M9A0F** — 60 mm-travel motorized fader, 10 kΩ, touch-sense lever | [DigiKey](https://www.digikey.com/en/products/detail/alps-alpine/RS60N11M9A0F/19529099) | 10 | 20–25 | 200–250 |

- **Buy 1 first, test, then buy 9** (per the BOM's sourcing advice).
- Alternate if stock is thin: **Bourns PSM60-081A-103B2** (60 mm motorized, similar
  footprint — re-verify touch-sense wiring).
- ⚠️ Do **not** substitute the RSA0N11M9 series — that's the 100 mm-travel version
  and won't fit the body.

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

## Totals

| | ~$ |
|---|---|
| Adafruit (incl. amp + speakers) | 148 |
| Faders (DigiKey) | 200–250 |
| Power (Geekworm + cells) | 60 |
| OLED | 22–38 |
| Misc | 18 |
| **New parts total** | **≈ 450–515** |

(On top of the already-owned Pi/HyperPixel/SD ≈ $110 — consistent with the
[BOM](BOM.md) estimate of $490–540 all-in.)

**Reduced build** (volume + seek motorized only, plain slide pots for EQ): drop 8
faders (−$160+), 3 DRV8833s, 1 PCA9685, MPR121 optional → new-parts total ≈ **$240–280**.

## Suggested order of orders

1. **Adafruit cart + 1× fader from DigiKey** → bring up one motorized fader end to
   end (PID, touch, PCA9685) before committing to ten.
2. **X728 + cells** → battery/power milestone (Phase 7).
3. **Remaining 9 faders + OLED** once the single-fader rig works.
