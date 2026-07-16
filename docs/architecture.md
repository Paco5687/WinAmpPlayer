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
Spotify ──▶ go-librespot ──▶ ALSA (software graphic EQ) ──▶ USB DAC ──▶ switched 3.5mm jack
                                    ▲                  │                     │ (no plug)
                          EQ gains from faders         │              TPA2016 amp ──▶ internal
                                                       │             (I2C, RP2040 bus)  speakers
                                          audio tap ──▶ FFT ──▶ spectrum bars (UI)
```

> The DAC is **USB** (not a GPIO I2S HAT) because the HyperPixel display's DPI
> interface consumes all 40 GPIO pins, including I2S. The Pi's 3.5 mm jack works
> for bring-up. **Standalone playback** comes from internal enclosed speakers via
> a TPA2016 Class-D amp; inserting headphones mutes the amp (jack detect →
> firmware). External outputs are software: **Spotify Connect transfer** (Sonos &
> co. via the Web API — no audio plumbing) and **Bluetooth A2DP** from the Pi 4's
> onboard radio.

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
| `spotify.py` | `MockPlayer` (simulation), `WebApiPlayer` (drive any Connect device), `LibrespotPlayer` (the on-device player) behind one `PlayerBackend` interface |
| `spotify_web.py` / `spotify_auth.py` | Web API client (playlists, queue, control) + loopback-PKCE auth |
| `library.py` / `images.py` / `power.py` | Async playlist browsing, album-art cache, battery sources |
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
same methods onto go-librespot's local HTTP API (the on-device path);
`WebApiPlayer` drives any active Spotify Connect device through the Web API
(useful for laptop dev with real audio). Swap via `config.toml`.

## Central screen & UI direction

The device is **physical-first**: transport, EQ, and faders are hardware; the
screen is a small **square** LCD (**HyperPixel 4.0 Square, 720×720**) showing the
compact **multi-view** UI in `ui/screen.py` — one view at a time, switched by
**dedicated physical buttons** (ButtonId 9–11 in the serial protocol; on-screen
tabs and keys `1`/`2`/`3` in dev). v1 views: Now Playing, Playlist selector, Play
Queue (Search later). Playback control uses `backend = "librespot"`
(go-librespot's local API on :3678), so control stays on the Pi — no cloud
round-trip. The HyperPixel's DPI takes all GPIO, so audio → USB DAC and battery
sensing → RP2040 (see hardware/BOM.md).

## Deployment on the Pi

The full, tested procedure is **[pi-bringup.md](pi-bringup.md)**. In short:

1. `go-librespot` as a systemd service, authenticated once via interactive
   OAuth (standalone; see [spotify-setup.md](spotify-setup.md)).
2. HyperPixel 4.0 Square via the `vc4-kms-dpi-hyperpixel4sq` overlay; rotation
   done at the **compositor** level so touch follows the display.
3. The UI as a systemd **user** service (kiosk): boots straight into the app,
   fullscreen, cursor hidden (`deploy/winamp-kiosk.*`).
4. *(Phase 4)* ALSA EQ between librespot and the USB DAC.
5. *(Phase 5)* RP2040 flashed and enumerated at `/dev/ttyACM0`.

## Roadmap

Tracked live on the **[project board](https://github.com/users/Paco5687/projects/4)**
(milestones Phase 1–9 plus "UI Redesign & Central Screen"). Done so far: desktop
mock, Spotify integration (auth/browse/playback/queue), standalone audio on the
Pi, HyperPixel + kiosk autostart, the multi-view screen UI. Next up:
playlist-detail view + list scrolling, RP2040 physical controls, motorized
faders, software EQ + real spectrum, power/battery, enclosure.
