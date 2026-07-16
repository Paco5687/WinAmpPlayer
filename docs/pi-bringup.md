# Raspberry Pi bring-up (standalone player)

The exact, reproducible steps to turn a fresh Pi 4 B into the standalone player:
go-librespot for audio + the WinAmp app on the screen. Written from a real
bring-up on 2026-07-15 (Raspberry Pi OS Bookworm, 64-bit).

## 1. Flash + first boot

- **Raspberry Pi OS (64-bit), Desktop**, via Raspberry Pi Imager.
- In the Imager gear: set hostname (`winamp`), **enable SSH**, username, Wi-Fi, locale.
- First boot:
  ```bash
  sudo apt update && sudo apt full-upgrade -y
  sudo raspi-config   # Interface: enable I2C, SPI, Serial
  sudo reboot
  ```

## 2. go-librespot (the audio engine)

```bash
sudo apt-get install -y libogg-dev libvorbis-dev libflac-dev libasound2-dev curl
mkdir -p ~/go-librespot && cd ~/go-librespot
URL=$(curl -s https://api.github.com/repos/devgianlu/go-librespot/releases/latest \
      | grep -o 'https://[^"]*linux_arm64[^"]*\.tar\.gz' | head -1)
curl -L "$URL" -o go-librespot.tar.gz && tar xzf go-librespot.tar.gz && chmod +x go-librespot
```

Config `~/.config/go-librespot/config.yml` (see [../config/go-librespot.example.yaml](../config/go-librespot.example.yaml)):
```yaml
device_name: "Winamp Physical Edition"
device_type: computer
audio_backend: alsa
audio_device: plughw:CARD=Headphones   # Pi 3.5mm jack; USB DAC on the real build
credentials:
  type: interactive
server:
  enabled: true
  address: localhost
  port: 3678
```

### Headless OAuth (no browser on the Pi)

1. `cd ~/go-librespot && ./go-librespot` — prints an `accounts.spotify.com/authorize?...` URL.
2. Open that URL in a browser **on another machine**, authorize.
3. It redirects to `http://127.0.0.1:<PORT>/login?code=…` which won't load — **copy that URL**.
4. In a second SSH session on the Pi: `curl "http://127.0.0.1:<PORT>/login?code=…"`.
5. go-librespot logs in and caches `credentials.json` — standalone from now on.

### Audio device

`aplay -l` lists the cards; the 3.5mm jack is `bcm2835 Headphones` (card 2 here), so
`audio_device: plughw:CARD=Headphones`. `raspi-config`'s audio default does **not**
affect go-librespot's ALSA path — set the device explicitly. If silent, `alsamixer`
(F6 → the card → unmute `M`, raise volume). *The final build uses a USB DAC (issue #12).*

### Run as a service (auto-start on boot)

Install [../deploy/go-librespot.service](../deploy/go-librespot.service):
```bash
sudo cp ~/WinAmpPlayer/deploy/go-librespot.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now go-librespot
journalctl -u go-librespot -f
```

**Standalone check:** `curl -X POST http://localhost:3678/player/play -H 'Content-Type: application/json' -d '{"uri":"spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"}'` — music plays with no phone/Spotify app open.

## 3. The WinAmp app

```bash
cd ~ && git clone https://github.com/Paco5687/WinAmpPlayer.git
cd WinAmpPlayer/pi
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # piwheels provides arm64 pygame
cp config.example.toml config.toml       # set backend="librespot", controls="mock"
SDL_VIDEODRIVER=dummy python -c "import winamp_player.app; print('ok')"   # sanity
```

### Run on the display (labwc / Wayland)

The Pygame app needs the Pi's Wayland session (not SSH). Launch it onto the session:
```bash
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
systemd-run --user --unit=winamp-ui \
  --setenv=WAYLAND_DISPLAY=wayland-0 --setenv=SDL_VIDEODRIVER=wayland \
  --working-directory=$HOME/WinAmpPlayer/pi \
  $HOME/WinAmpPlayer/pi/venv/bin/python -m winamp_player
```
## 4. HyperPixel 4.0 Square + kiosk autostart

The real display is a **Pimoroni HyperPixel 4.0 Square (720×720, DPI)**. DPI uses
all 40 GPIO, so disable the GPIO interfaces first, then add the overlay:

```bash
sudo raspi-config nonint do_i2c 1   # DPI needs the I2C/SPI GPIO
sudo raspi-config nonint do_spi 1
echo "dtoverlay=vc4-kms-dpi-hyperpixel4sq" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

After reboot the panel is output `DPI-1` at 720×720. **Don't** rotate with the
overlay's `rotate=` — that flips the display at the KMS level but *not the touch
matrix*. Rotate at the **compositor** level instead (moves display + touch
together) — the kiosk launcher does this with `wlr-randr --output DPI-1
--transform 180`.

### Kiosk autostart (boots straight into the UI)

Use the files in [`../deploy/`](../deploy/):

```bash
mkdir -p ~/.config/systemd/user
cp ~/WinAmpPlayer/deploy/winamp-kiosk.service ~/.config/systemd/user/
cp ~/WinAmpPlayer/deploy/winamp-kiosk.sh ~/.config/winamp-kiosk.sh
chmod +x ~/.config/winamp-kiosk.sh
sudo loginctl enable-linger "$USER"       # user manager starts at boot
systemctl --user daemon-reload
systemctl --user enable --now winamp-kiosk.service
```

Set `fullscreen = true` in `config.toml` (fills the 720×720 panel and hides the
cursor). The launcher waits for the Wayland socket, so it's robust to boot timing;
`Restart=on-failure` keeps it up, while a clean `q`/Esc still exits.

> RPi's labwc runs the *system* autostart and ignores `~/.config/labwc/autostart`;
> the XDG `.desktop` route was flaky on boot too. A **systemd user service** is the
> reliable path here.

## 5. Remote control from a laptop (optional, dev)

Add the laptop's SSH public key to the Pi's `~/.ssh/authorized_keys` for passwordless
`ssh bkern@winamp.local` — handy for deploying/logging without a keyboard on the Pi.

> ⚠️ Gotcha: don't `pkill -f "python -m winamp_player"` over SSH — the pattern matches
> the SSH command's own command line and kills your session. Use
> `systemctl --user stop winamp-ui` instead.
