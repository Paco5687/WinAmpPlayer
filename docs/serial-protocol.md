# Serial protocol (Pi ⇄ RP2040)

A deliberately simple, human-readable, newline-delimited ASCII protocol over USB
serial (CDC-ACM). ASCII because you can debug the whole thing with a serial
monitor. **115200 baud, 8N1.** Every message ends with `\n`.

The Python side is `pi/winamp_player/controls.py`; the firmware side is
`firmware/src/main.cpp`. Keep both in sync with this document.

## Pi → microcontroller (commands)

| Command | Meaning |
|---|---|
| `FADER <id> <pos>` | Drive motorized fader `id` to position `pos` (0–1023). Engages the PID loop toward that target. |
| `FADER_RELEASE <id>` | Cut motor power on fader `id` so the user can move it freely. |
| `LED <index> <r> <g> <b>` | Set indicator LED color (0–255 each). |
| `DISP TITLE <text>` | Scrolling title line on the amber OLED readout (single line; sent on track change). |
| `DISP TIME <pos_ms> <dur_ms>` | Elapsed/total time for the OLED (sent ~1/s). |
| `DISP INFO <kbps> <khz>` | Stream info readout (bitrate / sample rate). |
| `PING` | Liveness check; expects `PONG`. |

## Microcontroller → Pi (events)

All events are `EV <TYPE> <id> <value>`:

| Type | `value` | Meaning |
|---|---|---|
| `EV BTN <id> <0\|1>` | 1 = pressed, 0 = released | Button state change (debounced). |
| `EV FADER <id> <0..1023>` | ADC position | A fader was moved **by the user** (only sent while touched/released, not while the motor is driving it). |
| `EV TOUCH <id> <0\|1>` | 1 = grabbed | User is touching a motorized fader. The Pi stops driving it until `0`. |
| `EV ENC <id> <±delta>` | signed detent count | Rotary encoder moved. |
| `EV POT <id> <0..1023>` | ADC value | Potentiometer moved (0 = balance). |
| `EV BAT 0 <0..1000>` | state-of-charge ×10 | Battery SoC from the X728's MAX17040 (on the RP2040 I2C bus), every ~5 s. |
| `EV CHG 0 <0\|1>` | 1 = on AC/charging | X728 power-loss-detect line. |
| `EV JACK 0 <0\|1>` | 1 = headphones in | Jack insertion. Firmware mutes the speaker amp itself; informational for the UI. |

Plus out-of-band: `PONG` (reply to `PING`) and `LOG <text>` (firmware debug,
ignored by the parser).

## IDs

**Faders** (`FaderId` in `controls.py`):

| id | fader | motorized |
|---|---|---|
| 0–6 | EQ bands (60, 150, 400, 1k, 2.4k, 6k, 15k Hz) | ✅ |
| 7 | Preamp | ✅ |
| 8 | Volume | ✅ |
| 9 | Seek (tracks song position) | ✅ |

**Buttons** (`ButtonId`): 0 prev · 1 play · 2 pause · 3 stop · 4 next ·
5 eject (spare) · 6 shuffle · 7 repeat · 8 eq-on/off · **9 view:now-playing ·
10 view:playlists · 11 view:queue** (the dedicated view-switch buttons for the
central screen) · 12 eq-preset (cycles presets; the motorized faders animate
into each curve) · **13/14 encoder push switches**.

**Pots** (`PotId`, via `EV POT`): 0 balance (L/R, non-motorized).

## Example exchange

```
→ PING
← PONG
← EV TOUCH 8 1            # user grabbed the volume fader
← EV FADER 8 742          # ...and moved it
← EV TOUCH 8 0            # let go
→ FADER 9 512            # Pi: glide the seek fader to 50% (new track)
← EV BTN 4 1             # user pressed NEXT
→ FADER 9 0             # Pi: seek fader back to start
```

## Design notes

- **Idempotent targets.** The Pi resends a fader target only when it changes
  (see `App._last_sent`), so the link stays quiet at idle.
- **User wins.** While a fader reports `TOUCH 1`, the Pi never fights it. This is
  what makes the motorized feel right.
- **Framing.** One message per line. The firmware ignores unknown verbs; the Pi
  ignores unparseable lines. Forward-compatible by construction.
- **Future:** if ASCII bandwidth ever bottlenecks (it won't at these rates),
  switch to a COBS-framed binary packet with the same semantics.
