# Pi app — `winamp_player`

The Python/Pygame application: the WinAmp-style UI, Spotify control, and the
bridge to the microcontroller. Runs **fully mocked on a laptop** so you can build
the UI with no hardware and no Spotify account.

## Run (mock mode — default)

```bash
cd pi
pip install -r requirements.txt   # pygame is all you need for mock mode
python -m winamp_player
```

Requires **Python 3.11+** (uses the stdlib `tomllib`).

A square (720×720) **multi-view** window opens — the device screen: **Now Playing**,
**Playlists**, **Up Next**. On the real device these views are switched by dedicated
physical buttons; transport/EQ/faders are hardware, not on screen.

**Controls in the window (dev):**

| Input | Action |
|---|---|
| Tabs / `1` `2` `3` / `Tab` | switch view (Now Playing / Playlists / Up Next) |
| Tap a playlist row | open + play that playlist |
| `space` | play/pause |
| `←` / `→` | prev / next |
| `↑` / `↓` | volume |
| `s` | stop · `q` / `Esc` quit |

## Connect Spotify (Web API — playlists & album art)

No website or hosting needed — it uses a **loopback redirect + PKCE**.

1. Create an app at https://developer.spotify.com/dashboard.
2. Add this **exact** redirect URI (Spotify banned `localhost`; loopback HTTP is fine):
   ```
   http://127.0.0.1:8888/callback
   ```
3. Put the app's **Client ID** in `config.toml` as `spotify_client_id` (no secret needed).
4. Authorize once:
   ```bash
   python -m winamp_player.authorize
   ```
   A browser opens, you approve, and a refresh token is cached to
   `pi/spotify_token.json` (gitignored). The device refreshes tokens forever after that.

`go-librespot` (the audio playback) authenticates **separately and standalone** —
using its own one-time **interactive OAuth** login (no phone required; a phone via
Spotify Connect is only an optional alternative). It needs Premium. See
[../docs/spotify-setup.md](../docs/spotify-setup.md) for both one-time logins.

## Run against real hardware

Copy `config.example.toml` → `config.toml` and set:

```toml
backend  = "librespot"      # needs a running go-librespot + Spotify Premium
controls = "serial"         # needs the RP2040 flashed and connected
serial_port = "/dev/ttyACM0"
fullscreen = true           # on the device LCD
```

`requests` and `pyserial` (in `requirements.txt`) are only needed for real
hardware; they're imported lazily so mock mode doesn't require them.

## Layout

```
winamp_player/
├── __main__.py      # python -m winamp_player
├── app.py           # main loop, action routing, MOTOR SYNC
├── config.py        # config.toml loader (zero-config defaults)
├── models.py        # PlayerState / Track — the source of truth
├── spotify.py       # MockPlayer + LibrespotPlayer behind PlayerBackend
├── controls.py      # serial protocol + MockControls / SerialControls
└── ui/
    ├── skin.py      # palette + portrait layout rectangles
    └── display.py   # rendering + mouse/touch -> actions
```

See [../docs/architecture.md](../docs/architecture.md) for how it all fits.

## Playlist browser

Once authorized (above), the touchscreen opens on **your real Spotify
playlists** with album-art thumbnails (loaded async so the UI never blocks).
Tap a playlist → tap a track → it plays. The **eject** button (or `b`) returns
to the library. Without a token it falls back to a demo playlist.

### Playing followed playlists (`backend = "webapi"`)

Spotify Dev Mode can't *read the track list* of playlists you don't own, but it
**can play them**. So there are two playback modes (set `backend` in `config.toml`):

| `backend` | Owned playlists | Followed / editorial playlists | Audio |
|---|---|---|---|
| `mock` (default) | tracklist + simulated playback | flagged "dev-mode locked" | none (simulated) |
| `webapi` | tracklist + **real playback** | **plays** (now-playing view, no tracklist) | real, on an active device |

To use `webapi` **now**, on your laptop:
1. Set `backend = "webapi"` in `config.toml`.
2. **Open the Spotify desktop or phone app** (it becomes the "active device" to play on).
3. Run the app. Owned playlists play with a tracklist; followed playlists show a
   **now-playing** card (art, title, progress) mirrored from the real player.

On the Pi, the "active device" becomes **go-librespot** instead of the Spotify
app — same code path, no phone. If you see *"No active Spotify device,"* nothing
is available to play on yet.

### "Up Next" tracklist

In `webapi` mode the now-playing view shows an **UP NEXT** list from the Spotify
**playback queue** (`GET /me/player/queue`). This gives you a tracklist for
*anything* playing — including followed/editorial playlists whose tracks Dev Mode
won't let us read directly, and whatever's playing on another device. It shows
what's coming up (not the full playlist history).

## Notes / TODO

- **Album art** is now real (fetched + cached from the Web API in `images.py`).
  Placeholder gradient shows only until each image finishes downloading.
- **Spectrum** is simulated when no audio tap is present; on the Pi, feed real
  FFT magnitudes into `PlayerState.spectrum`.
- **EQ** currently just stores band gains; the ALSA software-EQ pipeline that
  applies them is milestone M5 (see architecture roadmap).
