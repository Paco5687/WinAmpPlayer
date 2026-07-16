#!/bin/bash
# WinAmp Physical Edition — kiosk launcher (run by the systemd user service).
# Self-sufficient: sets the Wayland env, waits for the compositor socket, rotates
# the panel 180° at the COMPOSITOR level (so touch rotates with the display), then
# starts the UI. Adjust the user/path and drop/keep the wlr-randr line per your
# panel's mounting orientation.
#
# Install: cp deploy/winamp-kiosk.sh ~/.config/winamp-kiosk.sh && chmod +x it.
export XDG_RUNTIME_DIR=/run/user/1000
export WAYLAND_DISPLAY=wayland-0
export SDL_VIDEODRIVER=wayland
cd /home/bkern/WinAmpPlayer/pi || exit 1
for _ in $(seq 1 30); do
  [ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ] && break
  sleep 1
done
wlr-randr --output DPI-1 --transform 180 2>/dev/null   # display + touch together
exec venv/bin/python -m winamp_player
