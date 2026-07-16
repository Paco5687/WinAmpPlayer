# Architecture

## Why two brains

The Pi runs Linux, which is non-deterministic under scheduling load — fine for
UI and networking, bad for a tight motor-control loop that has to run at a
steady ~1 kHz to keep motorized faders from oscillating. So:

- **Raspberry Pi** — Spotify client, audio pipeline, the LCD UI, high-level
  logic. Sends *targets* ("move volume fader to 72%").
- **RP2040 microcontroller** — soft-real-time I/O. Owns the PID loops that drive
  each motorized fader to its target, debounces buttons, reads pots/encoders,
  and streams events up to the Pi.

They talk over a simple newline-delimited ASCII protocol on USB serial. See
[serial-protocol.md](serial-protocol.md).

## Alternative platforms (future / v2)

The **[Arduino Uno Q](https://docs.arduino.cc/hardware/uno-q/)** is architecturally
this exact design on a single board: a Qualcomm Dragonwing QRB2210 (quad
Cortex-A53, runs Debian Linux) **plus** an STM32U585 (Cortex-M33) real-time MCU,
with an internal bridge — i.e. our "Pi brain + RP2040 brain" fused, plus eMMC.

We're **staying on Pi 4 B + RP2040 for v1** because: the Uno Q's MIPI-DSI display
and analog audio come out only via a separate carrier board; it's brand-new
(Oct 2025) with an unproven ecosystem/supply — risky for a build others must
reproduce; and we already have a working Pi stack. It's a strong **v2 candidate**
if its ecosystem matures — it could collapse both boards into one.

## Audio path

```
Spotify ──▶ go-librespot ──▶ ALSA (software graphic EQ) ──▶ I2S DAC ──▶ headphones/speaker
                                    ▲                  │
                          EQ gains from faders    audio tap ──▶ FFT ──▶ spectrum bars (UI)
```

- **go-librespot** is a full Spotify client that streams and decodes audio
  directly (requires Premium). It authenticates **standalone via interactive
  OAuth** — a one-time browser login, then it reconnects on cached credentials
  forever, no phone. It exposes an HTTP + WebSocket API for transport and
  now-playing metadata. (Zeroconf/"pick it from a phone" is an optional mode we
  don't rely on.)
- The **graphic EQ is ours** — Spotify exposes no EQ over the API, so we insert a
  software EQ into the ALSA chain (e.g. an `ladspa`/`caps` multi-band plugin, or
  a custom filter). The motorized EQ faders set its band gains.
- A **loopback/monitor tap** feeds a small FFT so the spectrum analyzer reflects
  the actual audio, not a simulation. (In mock mode it's simulated.)

## The Pi app (`pi/winamp_player/`)

| Module | Responsibility |
|---|---|
| `models.py` | `PlayerState`, `Track` — the single source of truth the UI renders |
| `spotify.py` | `MockPlayer` (simulation) and `LibrespotPlayer` (real go-librespot) behind one `PlayerBackend` interface |
| `controls.py` | Serial protocol + `MockControls` / `SerialControls` |
| `ui/skin.py` | Palette + shared drawing helpers |
| `ui/screen.py` | Compact **multi-view** screen UI (Now Playing / Playlists / Queue) for the square LCD; turns touch/buttons into actions |
| `app.py` | Main loop, action routing, and **motor sync** |

### Motor sync — the signature trick

Every frame, `app._sync_motors()` computes where each motorized fader *should*
be from `PlayerState` (volume, seek progress, EQ band gains) and sends a
`FADER <id> <pos>` target — **unless the user is currently touching that fader**
(tracked via `EV TOUCH` events). So:

- Change the song → the **seek fader glides** to the new position and tracks it.
- Load an EQ preset → the **EQ faders physically animate** into the curve.
- Grab a fader → the motor yields; when you let go, it holds your value.

### Backend abstraction

`PlayerBackend` is a `Protocol`. `MockPlayer` advances a demo playlist with no
network so the entire UI is buildable on a laptop. `LibrespotPlayer` maps the
same methods onto go-librespot's `/player/*` endpoints. Swap via `config.toml`.

## Deployment on the Pi

1. `go-librespot` as a systemd service, authenticated once via interactive
   OAuth (standalone; see [spotify-setup.md](spotify-setup.md)).
2. ALSA configured with the EQ plugin between librespot and the DAC.
3. The Pygame app launched fullscreen on boot (`fullscreen = true`) against the
   DSI/HDMI LCD, kiosk-style.
4. RP2040 flashed and enumerated at `/dev/ttyACM0`.

## Central screen & UI direction

The current full-window WinAmp skin is **temporary scaffolding** that proved the
plumbing. The real device is **physical-first**: transport, EQ, and faders are
hardware; the screen is a small **square** LCD (**HyperPixel 4.0 Square, 720×720**)
showing a compact **multi-view** UI — one view at a time — switched by **dedicated
physical buttons**. v1 views: Now Playing, Playlist selector, Play Queue (Search
later). Playback control uses `backend = "librespot"` (go-librespot's local API on
:3678), so control stays on the Pi — no cloud round-trip. The HyperPixel's DPI takes
all GPIO, so audio → USB DAC and battery sensing → RP2040 (see hardware/BOM.md).

## Roadmap

1. **M1 — Desktop mock** ✅ full UI + logic, no hardware.
2. **M2 — Spotify real** — go-librespot transport + Web API playlists/art.
3. **M3 — Controls** — RP2040 buttons/pots/encoders over serial (non-motorized).
4. **M4 — Motors** — motorized faders + PID + motor sync on real hardware.
5. **M5 — Audio EQ + spectrum** — ALSA EQ the faders drive; FFT spectrum tap.
6. **M6 — Enclosure** — 3D-printed book-form body, battery, assembly.
