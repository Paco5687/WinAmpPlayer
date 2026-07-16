# Datasheets

Run `bash fetch.sh` in this directory to download every part's datasheet /
mechanical drawing (~26 MB). **The PDFs are gitignored** — they're manufacturer
copyright, so the repo ships the script + this index instead of the files.

## Index + key facts for case design

| File | Part | Key mechanical / electrical facts |
|---|---|---|
| `alps-rs60n-motorized-fader.pdf` | ALPS RS60N11M9A0F | ⚠️ **Body 18.5 mm wide** (min pitch ~19–20 mm), **26 mm deep below panel**, mounting 2× M3, lever 8.2 mm above panel, motor **rated 10 V DC / ≤800 mA**, travel 60 mm, touch-sense track. See [../enclosure.md](../enclosure.md) for the layout consequences. |
| `pca9685-pwm-driver.pdf` | NXP PCA9685 | 16-ch 12-bit PWM, I2C (up to 62 addrs), ~24–1526 Hz PWM |
| `mpr121-cap-touch.pdf` | NXP MPR121 | 12 electrodes, I2C 0x5A–0x5D |
| `mcp23017-gpio-expander.pdf` | Microchip MCP23017 | 16 GPIO, I2C 0x20–0x27, interrupt outs |
| `cd74hc4067-mux.pdf` | TI CD74HC4067 | 16:1 analog mux, ~70 Ω on-resistance |
| `drv8833-motor-driver.pdf` | TI DRV8833 | dual H-bridge, 2.7–10.8 V, 1.5 A RMS/bridge |
| `tpa2016-speaker-amp.pdf` | TI TPA2016D2 | stereo Class-D 2.8 W@4Ω/5 V, I2C 0x58, AGC, shutdown |
| `ws2812b-led.pdf` | WS2812B | 800 kHz single-wire, 5 V |
| `pico-datasheet.pdf` / `pico-pinout.pdf` | Raspberry Pi Pico | board 51 × 21 mm, pin functions |
| `pi4-mechanical-drawing.pdf` | Pi 4 B | board 85 × 56 mm, port + hole positions |
| `pi4-reduced-schematics.pdf` | Pi 4 B | connector-level schematics |
| `bourns-pec11-encoder.pdf` | Bourns PEC11 (= Adafruit 377) | panel hole ⌀7 mm, shaft dims |
| `ssd1322-oled-controller.pdf` | SSD1322 | controller registers/commands (firmware) |
| `nhd-3.12-25664-oled-module.pdf` | NHD-3.12-25664UCY2 | module ≈ 88 × 27.8 mm (verify drawing page), 4-wire SPI |

## HTML-only references (no stable PDF)

- **Geekworm X728**: https://wiki.geekworm.com/X728 — HAT form (~85 × 56 mm) +
  pogo/header stack height; schematic + safe-shutdown scripts on the wiki.
- **HyperPixel 4.0 Square**: https://shop.pimoroni.com/products/hyperpixel-4-square —
  ~85 × 85.5 × 12 mm per product page (verify before cutting the bezel).
- **ALPS 3D CAD (STEP)** for the fader is downloadable from the ALPS product page —
  grab it when starting CAD: https://tech.alpsalpine.com/e/products/detail/RS60N11M9A0F/
