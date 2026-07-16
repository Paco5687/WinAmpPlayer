#!/bin/bash
# Download every part's datasheet / mechanical drawing into this folder.
# PDFs are NOT committed (manufacturer copyright) — this script makes the set
# reproducible for anyone building the project. Run from this directory:
#   cd hardware/datasheets && bash fetch.sh
set -u
fetch() {  # fetch <output-name> <url>
  local out="$1" url="$2"
  if curl -fsSL --retry 2 -o "$out" "$url"; then
    printf 'ok   %-42s %8d bytes\n' "$out" "$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")"
  else
    printf 'FAIL %-42s %s\n' "$out" "$url"
  fi
}

# --- ICs (wiring verification) --------------------------------------------- #
fetch pca9685-pwm-driver.pdf        "https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf"
fetch mpr121-cap-touch.pdf          "https://www.nxp.com/docs/en/data-sheet/MPR121.pdf"
fetch mcp23017-gpio-expander.pdf    "https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf"
fetch cd74hc4067-mux.pdf            "https://www.ti.com/lit/ds/symlink/cd74hc4067.pdf"
fetch drv8833-motor-driver.pdf      "https://www.ti.com/lit/ds/symlink/drv8833.pdf"
fetch ws2812b-led.pdf               "https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf"

# --- Boards / compute (case design) ---------------------------------------- #
fetch pico-datasheet.pdf            "https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf"
fetch pico-pinout.pdf               "https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf"
fetch pi4-mechanical-drawing.pdf    "https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf"
fetch pi4-reduced-schematics.pdf    "https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-reduced-schematics.pdf"

# --- Controls (panel cutouts) ----------------------------------------------- #
fetch alps-rs60n-motorized-fader.pdf "https://datasheet.octopart.com/RS60N11M9A0F-ALPS-datasheet-21183685.pdf"
# Adafruit #377 is a Bourns PEC11-series encoder (bourns.com 403s scripted
# downloads, so this uses Adafruit's mirror).
fetch bourns-pec11-encoder.pdf       "https://cdn-shop.adafruit.com/datasheets/pec11.pdf"

# --- Displays ---------------------------------------------------------------- #
fetch ssd1322-oled-controller.pdf   "https://newhavendisplay.com/content/app_notes/SSD1322.pdf"
fetch nhd-3.12-25664-oled-module.pdf "https://newhavendisplay.com/content/specs/NHD-3.12-25664UCY2.pdf"

echo
echo "HTML-only references (no stable PDF) — see README.md:"
echo "  Geekworm X728:   https://wiki.geekworm.com/X728"
echo "  HyperPixel 4 Sq: https://shop.pimoroni.com/products/hyperpixel-4-square"
