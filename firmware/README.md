# Firmware (RP2040 / Raspberry Pi Pico)

Owns all physical I/O and the real-time motor loops for the motorized faders.
Talks to the Pi over USB serial using the [serial protocol](../docs/serial-protocol.md).

## Build

Uses [PlatformIO](https://platformio.org/) with the Arduino core for RP2040
(`earlephilhower/arduino-pico`):

```bash
cd firmware
pio run                 # build
pio run -t upload       # flash (hold BOOTSEL on first flash, or use the reset)
pio device monitor      # watch the serial link
```

## What it does

- Reads buttons (via MCP23017), encoders, the balance pot, and all fader wiper
  positions (through a CD74HC4067 analog mux, since the Pico has only 3 ADC
  channels).
- Runs a per-fader **PID loop** at ~1 kHz driving each motorized fader toward the
  target the Pi last sent (`FADER <id> <pos>`), and yields the motor while the
  user is touching that fader (MPR121 touch electrodes).
- Drives the **amber OLED readout** (SSD1322 over SPI) from `DISP` commands the
  Pi streams (title / time / stream info).
- Emits `EV …` events upstream (button presses, user fader moves, touch, encoders).

> **I/O architecture:** motor PWM goes through **2× PCA9685** and buttons/touch
> through **MCP23017/MPR121**, all on one I2C bus — direct-wiring doesn't fit the
> Pico's 26 GPIO. Full pin budget in [../hardware/wiring.md](../hardware/wiring.md).
> The `main.cpp` skeleton still drives one fader on direct pins for bring-up;
> switch to the PCA9685 when scaling past one.

The firmware is **fully built out** (desk-written 2026-07-16, compiles clean,
untested on hardware): every I2C device driver, the OLED readout with the `DISP`
marquee, buttons/encoders/touch/battery events, and the per-fader PID against
the PCA9685. `src/config.h` holds all pins, addresses, and tuning constants —
including **feature flags** (`HAS_PCA9685`, `HAS_OLED`, …) so bench bring-up can
enable one subsystem at a time. A missing I2C board logs `... MISSING` and
degrades instead of hanging.

## Bring-up order (with the full firmware)

1. Flash with **all `HAS_*` flags off except none needed** — `PING`→`PONG` over
   USB proves the link (`LOG winamp-fw ready`).
2. Enable `HAS_MCP23017` → press buttons, watch `EV BTN`. Encoders are always
   on (direct GPIO) — turn them, watch `EV ENC`.
3. Wire fader #1 (wiper → mux ch0, motor → PCA A ch0/1, touch → MPR121 e0);
   enable `HAS_PCA9685` + `HAS_MPR121`. Send `FADER 0 512` — tune `PID_KP/KD`
   and `PWM_MIN_MOVE` (stiction floor) in `config.h` until it glides.
4. Enable `HAS_OLED` — the Pi's `DISP` stream should show time + title.
5. Enable `HAS_TPA2016` + `HAS_MAX17040` — battery `EV BAT` every 5 s, jack
   insert mutes the amp.
6. Scale to all 10 faders.

⚠️ Safety built in: PCA9685 **/OE is held high (motors disabled) until the
firmware has zeroed all channels** — no fader slam on boot.
