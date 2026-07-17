# Wiring & physical layout

## Schematics

| Diagram | What it shows |
|---|---|
| [**System wiring**](diagrams/system-wiring.svg) | Full power + data topology: battery → UPS → Pi/motor rail; USB to the RP2040 + DAC; the I2C expander bus (PCA9685/MPR121/MCP23017) out to the faders |
| [**Pico pinout**](diagrams/pico-pinout.svg) | Every RP2040 pin assignment (19 of 26 used, spares marked) |
| [**Front panel (authoritative)**](cad/) | The dimensioned cut drawing — `cad/front-panel.dxf` / `.svg` |

![System wiring](diagrams/system-wiring.svg)

![Pico pinout](diagrams/pico-pinout.svg)

![Front panel](cad/front-panel.svg)

> ⚠️ **Dimension findings** (ALPS datasheet + the dimensioned cut drawing):
> fader bodies are **18.5 mm wide × 26 mm deep × 106.5 mm long (M3 span 80 mm)**.
> The 8-fader bank therefore needs ~155 mm of width and **~110 mm of height** —
> honest envelope: **175 × 280 × 32 mm (6.9″ × 11″ × 1.25″)**, proven with real
> clearances in **[cad/front-panel.dxf](cad/)** (the authoritative drawing).
> Full analysis + the compact fallback: [enclosure.md](enclosure.md).

## Front-panel layout (ASCII summary — superseded by cad/, kept for orientation)

Mirrors the software's regions so the code and the hardware agree:

```
┌───────────────────────────────────────────┐  ← ~127 mm wide
│  SPOTAMP       (title)   │
├───────────────────────────────────────────┤
│  0:42   [ amber OLED readout ]   320 kbps  │   PHYSICAL panel
│  ░░▓▓██▓░ title + spectrum       44 kHz    │   SSD1322 256×64 SPI OLED on the
│  |◀ ▶ ▮▮ ■ ▶| SHUF LOOP PRESET [==BAL==]   │   RP2040 (`DISP` commands) +
│  [====VOL (motorized)====]                 │   buttons + balance pot + volume
├───────────────────────────────────────────┤
│  [NP] [PL] [Q]  (view-switch buttons)     │   PHYSICAL (ButtonId 9–11)
│   ┌─────────────────────────────┐         │
│   │                             │         │   SCREEN
│   │   HyperPixel 4.0 Square     │         │   720×720 DPI touchscreen
│   │   (multi-view UI: now       │         │   ⚠ occupies ALL 40 GPIO —
│   │   playing/playlists/queue)  │         │   controls/battery on RP2040,
│   └─────────────────────────────┘         │   audio via USB DAC
│                                           │
├───────────────────────────────────────────┤
│  EQ:  ▮ ▮ ▮ ▮ ▮ ▮ ▮   ▮(pre)              │   PHYSICAL panel
│      60 150 400 1k 2k4 6k 15k              │   8 motorized 60 mm faders
├───────────────────────────────────────────┤
│  [====VOL====]      [====SEEK====]         │   2 motorized faders (horizontal)
└───────────────────────────────────────────┘
```

## Pico (RP2040) pin plan — expander architecture

**Direct-wiring does not fit**: 10 motors × 2 PWM + 10 touch + 13 buttons +
mux + encoders ≈ **55 signals vs the Pico's 26 GPIO**. Everything high-count
rides one I2C bus instead:

```
                        ┌── PCA9685 #1 ──▶ DRV8833 ×3 ──▶ fader motors 0–5
                        ├── PCA9685 #2 ──▶ DRV8833 ×2 ──▶ fader motors 6–9
Pico I2C (2 pins) ──────┼── MPR121  ──▶ 10 fader touch-sense lines
                        ├── MCP23017 ──▶ 13 panel buttons + headphone-jack detect
                        └── TPA2016 amp ──▶ internal stereo speakers (gain/AGC/mute)
```

| Function | Pico pins | Count |
|---|---|---|
| I2C bus (PCA9685 ×2, MPR121, MCP23017, TPA2016) | GP4/GP5 | 2 |
| Mux (CD74HC4067) select S0–S3 | GP6–GP9 | 4 |
| Mux common out → ADC (wipers + balance pot) | GP26 (ADC0) | 1 |
| OLED readout (SSD1322, SPI + DC/CS/RST) | GP10–GP14 | 5 |
| Encoders (EC11) ×2 + push | GP16–GP21 | 6 |
| WS2812 LEDs | GP22 (PIO) | 1 |
| USB | to Pi (CDC serial + power) | — |
| **Total** | | **19 of 26** ✅ |

Each motorized fader needs **three** connections handled together:
1. **Motor** → a DRV8833 channel, its two inputs driven by PCA9685 outputs.
2. **Wiper** → a mux input → ADC, for the PID's position feedback.
3. **Touch** → an MPR121 electrode, so the Pi knows to stop driving it.

> **PWM-frequency caveat:** the PCA9685 tops out at ~1.5 kHz, which is audible as
> a faint buzz *while a fader is moving*. Moves last well under a second, and the
> **reduced build** (only volume + seek motorized, driven directly from Pico PWM
> pins at 20 kHz+) sidesteps it completely.

## Electrical detail notes (desk-verified against datasheets, 2026-07-16)

**I2C address map** — no conflicts ✓:

| Device | Addr | Note |
|---|---|---|
| PCA9685 #1 | 0x40 | default |
| PCA9685 #2 | 0x41 | solder jumper A0 |
| MCP23017 | 0x20 | A0–A2 → GND |
| X728 fuel gauge (MAX17040) | 0x36 | see battery note below |
| TPA2016 amp | 0x58 | fixed |
| MPR121 | 0x5A | ADDR → GND |

- **Pull-ups**: every breakout ships its own (typ. 10 k). Six in parallel ≈ 1.7 k —
  near the 3 mA sink limit. If the bus misbehaves, desolder pull-ups from all but
  one board.
- **Motor-safe boot**: PCA9685 outputs are indeterminate until configured — tie
  both boards' **/OE to GP3 with a pull-up** so motors stay disabled until the
  firmware releases them. (GP3 was spare.)
- **Simultaneous-slew current**: stagger the PCA9685 per-channel ON offsets so 10
  motors don't switch in phase; with the 2× 2200 µF bulk caps that tames rail sag.
- **Touch-sense wiring**: each fader's T terminal → an MPR121 electrode. Keep the
  runs short and away from the motor leads (they're capacitive sense lines).

**Mux channel map** (CD74HC4067 → ADC0):

| CH | Signal |
|---|---|
| 0–6 | EQ band wipers 0–6 |
| 7 | preamp wiper |
| 8 | volume wiper |
| 9 | seek wiper |
| 10 | balance pot |
| 11–15 | spare |

**Battery telemetry** — the X728 can't stack on the Pi (HyperPixel owns the
header); it runs beside it and powers the Pi over USB-C. Its **MAX17040 fuel
gauge is I2C** — so jumper the X728 header's SDA/SCL/GND over to the **RP2040
bus** (addr 0x36, no conflict) and the firmware reports real state-of-charge over
serial (`power.py` already knows the MAX17040 registers). X728's AC-loss/PLD
signal → **GP2** (was spare) for charge-state. Fallback if the jumpering fights
us: a resistor divider off the battery to **GP28/ADC2** (for a 1S pack, 4.2 V max:
39 k / 100 k → 3.0 V full-scale — **verify the X728's cell topology first**).

## Control loop (firmware)

Per motorized fader, ~1 kHz:

```
error = target - read_position(fader)
if touched(fader):        # user wins
    motor_off(fader); report EV FADER when it settles
else:
    drive = PID(error)    # tune Kp/Ki/Kd per fader
    motor_pwm(fader, clamp(drive))
```

See `firmware/src/main.cpp` for the skeleton.

## Power & audio

- LiPo → power board (5 V boost) → Pi 4; motors get their own regulated rail off
  the same pack (H-bridges draw spikes — decouple well, keep motor ground and
  logic ground joined at one star point).
- **USB DAC** on a Pi USB port (the HyperPixel's DPI takes the I2S pins, so no
  GPIO DAC) → line out → **switched headphone jack** → **TPA2016 stereo amp** →
  internal enclosed speakers. Headphone insertion is sensed (MCP23017 input) and
  firmware mutes the amp over I2C. Pi USB budget: RP2040 + DAC = 2 of 4 ports.
- External outputs are **software**: Spotify Connect transfer for Sonos/Connect
  gear (Web API `transfer_to`), and BT A2DP via the Pi 4's onboard Bluetooth.

## Enclosure

- Book form, ~200 × 127 × 25 mm. Faders and their travel set the depth — 60 mm
  faders + motor bodies are the tallest components; plan ~20 mm behind the panel.
- Print the front panel with slots for fader travel and cutouts for the LCD,
  buttons, and encoders. A kickstand echoes the Yanko concept's EQ-base stand.
- CAD lives here later (`hardware/cad/`), source + STL.
