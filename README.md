# WinAmp · Physical Edition

A handheld, book-sized (≈8″ × 5″ × 1″) physical Spotify player styled after the
classic WinAmp interface. Color LCD touchscreen for the playlist and album art;
everything else is **real hardware** — buttons, pots, and **motorized faders**
for a graphic EQ plus volume and a seek fader that physically follows the song.

Inspired by [Eslam Mohamed's modular WinAmp concept](https://www.yankodesign.com/2024/04/27/modular-media-player-concept-brings-iconic-winamp-design-to-the-physical-world/)
— but built as a single integrated unit, and actually real.

> *It really whips the llama's ass.*

**Open source (MIT).** Built on a **Raspberry Pi 4 B**. Code, full parts list, and
3D models are being published so you can build your own — see the
**[Wiki](https://github.com/Paco5687/WinAmpPlayer/wiki)** and
[CONTRIBUTING.md](CONTRIBUTING.md).

## Architecture at a glance

Two brains, because Linux is bad at real-time motor control and a microcontroller
is great at it:

```
        ┌───────────────────────────┐        USB serial        ┌──────────────────────┐
        │     Raspberry Pi 4 B       │◀───────(ASCII)──────────▶│  RP2040 (Pico)       │
        │                            │                          │                      │
        │  go-librespot ─▶ ALSA EQ ─▶│─▶ I2S DAC ─▶ 🎧          │  buttons / pots      │
        │        │            ▲      │                          │  encoders            │
        │  Spotify Web API    │      │   FADER <id> <pos> ──────▶  motorized faders    │
        │        │            │      │                          │   (PID position loop)│
        │  Pygame UI (this) ──┘      │◀──── EV FADER/BTN/TOUCH ──│  ← wiper ADCs (mux)  │
        └───────────────────────────┘                          └──────────────────────┘
              color LCD touchscreen
```

- **[`pi/`](pi/)** — the Python/Pygame player app. Runs **fully mocked on a
  laptop today** (no hardware, no Spotify account needed). This is where the UI
  and app logic live.
- **[`firmware/`](firmware/)** — the RP2040 firmware: reads controls, runs the
  closed-loop control for the motorized faders, speaks the serial protocol.
- **[`hardware/`](hardware/)** — bill of materials, wiring, enclosure notes.
- **[`docs/`](docs/)** — [architecture](docs/architecture.md) and the
  [serial protocol spec](docs/serial-protocol.md).

## Try it right now (no hardware)

```bash
cd pi
pip install -r requirements.txt
python -m winamp_player
```

A square (720×720) window opens with the device's **multi-view UI** — the same
screen that runs on the HyperPixel: **Now Playing**, **Playlists**, and **Up Next**.
Switch views with the bottom tabs (or keys `1`/`2`/`3`). Transport/EQ/faders are
physical hardware on the real device, not on the screen.

Keys: `1/2/3` switch views · `space` play/pause · `←/→` prev/next · `↑/↓` volume · `s` stop · `q` quit.

Requires **Python 3.11+** (uses `tomllib`).

## Status

**Standalone on a Pi 4 B and playing** — full [project board](https://github.com/users/Paco5687/projects/4).

Done:
- [x] Desktop mock app end-to-end (UI, Spotify Web API browse, playback, queue)
- [x] **go-librespot** on the Pi — standalone audio, no phone (see [docs/pi-bringup.md](docs/pi-bringup.md))
- [x] App running on the device's screen (portrait), controlling the local player

Next up:
- [ ] **Central screen redesign** — HyperPixel 4.0 Square + compact multi-view UI (now playing / playlists / queue) with physical view buttons
- [ ] RP2040 firmware: buttons, pots, encoders, motorized-fader PID
- [ ] ALSA software EQ + real FFT spectrum
- [ ] Power (USB-C UPS, battery via RP2040) and enclosure CAD

See [docs/pi-bringup.md](docs/pi-bringup.md) and per-directory READMEs for details.

## The honest hard parts

- **Spotify needs Premium + go-librespot.** There's no official "play a playlist
  on a Pi" API. go-librespot is a full Spotify client that runs on the Pi and
  authenticates **standalone — no phone** (one-time OAuth, then cached). See
  [docs/spotify-setup.md](docs/spotify-setup.md).
- **Motorized faders are the cost/complexity center.** A full motorized EQ +
  volume + seek is ~10 motorized faders (~$180+) plus motor drivers, position
  ADCs (via a mux), and a PID loop. A 10-band EQ won't physically fit a 5″ width,
  so this build uses a **7-band** EQ. See [hardware/BOM.md](hardware/BOM.md).
- **Spotify exposes no EQ**, so the graphic EQ is a software EQ in the Pi's ALSA
  pipeline, applied to go-librespot's output before the DAC.
