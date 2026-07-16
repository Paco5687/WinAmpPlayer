# Bill of Materials

Prices are rough USD, mid-2020s, single-unit hobby quantities. This is a
**buildable** BOM for the full build you chose: motorized graphic EQ + motorized
volume + motorized seek, single integrated body.

> 🛒 **Ready to order?** [PARTS.md](PARTS.md) is the vendor shopping list (real
> SKUs, Adafruit-first). Datasheets: [datasheets/](datasheets/). Case rules +
> dimension findings: [enclosure.md](enclosure.md).

> ⚠️ **Read the fader note first — it's the biggest cost and space driver.**

## Compute & display

| Part | Notes | ~$ |
|---|---|---|
| **Raspberry Pi 4 Model B (2–4 GB)** | The build target. Ample for Pygame + ALSA EQ + FFT, has a 3.5 mm jack, and is easier on the battery than a Pi 5. | 45 |
| microSD 32 GB (A1) | OS + app | 8 |
| RP2040 (Raspberry Pi Pico) | Real-time controls + motor PID + the OLED readout. Cheap, 26 GPIO, PIO, 3 ADC. | 4 |
| **Pimoroni HyperPixel 4.0 Square** (720×720, DPI, touch) | The center screen — a small square LCD showing a multi-view UI (now playing / playlists / queue). ⚠️ DPI uses **all 40 GPIO** — see notes below. | 55 |
| **Amber OLED readout strip** (SSD1322, 256×64, SPI) | The retro top readout: elapsed time, scrolling title, mini-spectrum. Driven by the **RP2040** (`DISP` serial commands), not the Pi. | 25 |
| **USB DAC** (e.g. Sabrent/generic) | Audio out. A GPIO I2S HAT can't be used (HyperPixel's DPI takes the I2S pins). Pi 3.5 mm jack works for early testing. | 15 |
| **TPA2016 stereo 2.8 W Class-D amp** | Internal speakers. I2C gain/AGC/mute — rides the **RP2040 expander bus** (5th device). | 10 |
| **Enclosed stereo speakers, 3 W 4 Ω** (70×30×17 mm ea.) | Sealed backs = no custom acoustic chamber. Standalone playback, no headphones needed. | 8 |
| **Switched 3.5 mm headphone jack** | Insert detection (→ MCP23017 spare input) mutes the amp — headphones optional. | 2 |

> **HyperPixel I/O note:** the HyperPixel's DPI interface consumes all 40 GPIO
> pins (incl. standard I2C and I2S). That's fine here because everything else is on
> **USB**: controls/pots/faders **and battery sensing** run on the **RP2040** (USB
> serial), **audio** goes to a **USB DAC**, and the **UPS powers the Pi via USB-C**
> rather than stacking on the header. An alternate I2C is broken out on BCM 10/11 if
> ever needed. This is exactly why the two-brain (Pi + RP2040) split pays off.

## The motorized faders (the expensive part)

Full build = **10 motorized faders**: 7 EQ + 1 preamp + 1 volume + 1 seek.

| Part | Qty | Notes | ~$ ea | ~$ |
|---|---|---|---|---|
| ALPS RSA0N11M9 **60 mm motorized** fader | 10 | 100 mm won't fit a 5″ body — use 60 mm. Each has a motor + a wiper pot for position feedback + a touch-sense pin. | 18 | 180 |
| DRV8833 dual H-bridge motor driver | 5 | One drives two fader motors. | 2 | 10 |
| CD74HC4067 16-ch analog mux | 1–2 | The Pico has only 3 ADC channels; mux the 10 fader wipers + balance pot through one ADC. | 1.5 | 3 |
| **PCA9685 16-ch PWM driver** | 2 | ⚠️ **Required** — 10 motors need 20 PWM lines; the Pico doesn't have them. Drives the DRV8833 inputs over I2C. Caveat: ~1.5 kHz max PWM = brief audible buzz *while a fader moves* (moves are short; the reduced build avoids this entirely). | 5 | 10 |
| **MPR121 12-ch capacitive touch** | 1 | All 10 fader touch-sense lines over I2C (the ALPS conductive-knob pin is exactly what this reads). | 8 | 8 |
| **MCP23017 16-ch GPIO expander** | 1 | All 13 panel buttons over the same I2C bus — keeps the Pico's pin budget closing. | 2 | 2 |

> **Why the expanders:** direct-wiring everything needs ~55 signals; the Pico has
> 26 GPIO. With PCA9685 (motor PWM) + MPR121 (touch) + MCP23017 (buttons) sharing
> one 2-pin I2C bus, the budget closes with room for the OLED. Full pin map in
> [wiring.md](wiring.md).

**Why 7-band EQ, not 10:** eleven fader bodies (18.5 mm wide each, per the ALPS
datasheet) would need ~220 mm of width. Seven EQ + preamp (8 in the bank) need
~155 mm — which sets the body width at **~165 mm** (the original 127 mm/5″ target
can't hold a motorized bank; options in [enclosure.md](enclosure.md)). Volume +
seek mount horizontally. See [wiring.md](wiring.md).

**Want to cut cost/scope?** Make only **volume + seek** motorized (2 faders) and
use plain (non-motorized) slide pots for EQ. Saves ~$140 and most of the motor
drivers/PID work. The firmware already separates "motorized" from "read-only"
faders, so this is a config change, not a rewrite.

## Buttons, knobs, encoders

| Part | Qty | Notes | ~$ |
|---|---|---|---|
| Momentary tactile buttons (12 mm) | 13 | 5 transport + shuffle + repeat + eq-on + **eq-preset** + **3 view-switch** + eject/spare (ButtonId 0–12, read via the MCP23017) | 7 |
| Rotary encoder w/ push (EC11) | 2 | playlist scroll + select; menu | 4 |
| **Balance slide pot (non-motorized, 45 mm)** | 1 | The L/R slider from the concept — read via the mux as `POT 0`. | 2 |
| Addressable LED (WS2812) strip/segment | 1 | VU / status glow | 3 |

## Power (handheld) — see [power.md](power.md) for the full design

| Part | Notes | ~$ |
|---|---|---|
| UPS/BMS HAT for Pi (Geekworm X728 or Waveshare UPS HAT B) | 5 V/5 A out, 18650 holders, I2C battery monitoring + safe shutdown. | 30 |
| 18650 Li-ion cells ×4 (3500 mAh, e.g. Samsung 35E) | ~50 Wh ≈ 6 h runtime. Use 2 for ~3 h, 6 for ~9 h. | 40 |
| Bulk caps (1000–2200 µF) + fuse + power switch | Absorb motor-slew spikes at the driver rail. | 5 |

## Body & misc

| Part | Notes | ~$ |
|---|---|---|
| Enclosure (book form, working envelope ~165×210×32 mm — see [enclosure.md](enclosure.md)) | FDM prototype (PETG/ABS), CNC anodized aluminum final. | 15+ |
| Fader knob caps, standoffs, JST wiring, protoboard/PCB | | 20 |

## Rough total

| Group | ~$ |
|---|---|
| Compute & display & audio (incl. OLED, amp, speakers) | 172 |
| Motorized faders + drivers + mux + I2C expanders | 213 |
| Buttons/knobs/LEDs | 16 |
| Power (UPS + 4×18650, see [power.md](power.md)) | 75 |
| Body & misc | 35 |
| **Total (full motorized build)** | **≈ 510–560** |
| *Reduced (only volume+seek motorized, plain EQ pots)* | *≈ 360–390* |

## Sourcing notes

- Motorized faders: Mouser/Digikey for genuine ALPS; budget clones exist on
  AliExpress but wiper quality/backlash varies — buy one and test before ten.
- Confirm the fader's touch-sense wiring; some variants need a capacitive
  touch IC, others expose a conductive-knob pin.
- HyperPixel: verify the `vc4-kms-dpi-hyperpixel4sq` overlay + touch on your OS
  version before committing to the enclosure cutout (see docs/pi-bringup.md).
- SSD1322 OLED strips ship in SPI/parallel variants — order the **SPI** one.
