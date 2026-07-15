"""Spotify Web API client — the metadata + control side.

Handles what go-librespot doesn't: listing the user's playlists, fetching tracks
and album art, finding the librespot Connect device, and telling Spotify to
start a playlist on it. Access tokens auto-refresh via the Authorizer.

This complements ``LibrespotPlayer`` (the audio sink): browse here, play there.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Track
from .spotify_auth import Authorizer, Token

API = "https://api.spotify.com/v1"


@dataclass
class Playlist:
    id: str
    name: str
    uri: str
    track_count: int
    image_url: str | None = None
    # Dev Mode can only read tracks of playlists you own or collaborate on.
    owned: bool = True


def track_from_item(t: dict) -> Track:
    """Build a Track from a Spotify track object (used by playlists + queue)."""
    album = t.get("album", {}) or {}
    images = album.get("images") or []
    return Track(
        title=t.get("name", "—"),
        artist=", ".join(a["name"] for a in t.get("artists", []) if a.get("name")),
        album=album.get("name", ""),
        duration_ms=int(t.get("duration_ms", 0)),
        uri=t.get("uri"),
        art_url=images[0]["url"] if images else None,
    )


class SpotifyWeb:
    def __init__(self, authorizer: Authorizer) -> None:
        import requests

        self._requests = requests
        self._auth = authorizer
        self._token: Token | None = authorizer.load_valid()
        self._user_id: str | None = None

    @property
    def authorized(self) -> bool:
        return self._token is not None

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self.me().get("id", "")
        return self._user_id

    # -- low-level -------------------------------------------------------- #
    def _headers(self) -> dict:
        if self._token is None or self._token.expired:
            self._token = self._auth.load_valid()
        assert self._token is not None, "not authorized — run authorize.py"
        return {"Authorization": f"Bearer {self._token.access_token}"}

    def _get(self, path: str, **params) -> dict:
        r = self._requests.get(f"{API}{path}", headers=self._headers(),
                               params=params, timeout=10)
        if r.status_code == 401:  # token rotated under us — refresh once
            self._token = self._auth.load_valid()
            r = self._requests.get(f"{API}{path}", headers=self._headers(),
                                   params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def _put(self, path: str, json: dict | None = None, **params) -> None:
        params = {k: v for k, v in params.items() if v is not None}
        r = self._requests.put(f"{API}{path}", headers=self._headers(),
                               json=json, params=params, timeout=10)
        if r.status_code not in (200, 202, 204):
            r.raise_for_status()

    def _post_player(self, path: str, **params) -> None:
        params = {k: v for k, v in params.items() if v is not None}
        r = self._requests.post(f"{API}{path}", headers=self._headers(),
                                params=params, timeout=10)
        if r.status_code not in (200, 202, 204):
            r.raise_for_status()

    # -- account / verification ------------------------------------------ #
    def me(self) -> dict:
        """Current user profile — a cheap call to prove Web API access works."""
        return self._get("/me")

    def playlist_count(self) -> int:
        return self._get("/me/playlists", limit=1).get("total", 0)

    # -- browse ----------------------------------------------------------- #
    def playlists(self, limit: int = 50) -> list[Playlist]:
        data = self._get("/me/playlists", limit=limit)
        uid = self.user_id
        out = []
        for p in data.get("items", []):
            images = p.get("images") or []
            owner_id = (p.get("owner") or {}).get("id", "")
            owned = bool(p.get("collaborative")) or owner_id == uid
            out.append(Playlist(
                id=p["id"], name=p["name"], uri=p["uri"],
                track_count=(p.get("tracks") or {}).get("total", 0),
                image_url=images[0]["url"] if images else None,
                owned=owned,
            ))
        return out

    def playlist_tracks(self, playlist_id: str, limit: int = 100) -> list[Track]:
        # Feb-2026 migration: /tracks -> /items, and each element's "track"
        # field was renamed "item". We read either for forward/backward safety.
        data = self._get(f"/playlists/{playlist_id}/items", limit=limit)
        tracks = []
        for element in data.get("items", []):
            t = element.get("item") or element.get("track") or {}
            if t:
                tracks.append(track_from_item(t))
        return tracks

    def queue(self) -> list[Track]:
        """Upcoming tracks from the playback queue. Works for any playing
        context, including followed/editorial playlists. Returns [] when nothing
        is playing; raises on a real error (e.g. a Dev-Mode 403) so the caller
        can note it."""
        r = self._requests.get(f"{API}/me/player/queue", headers=self._headers(), timeout=10)
        if r.status_code == 401:
            self._token = self._auth.load_valid()
            r = self._requests.get(f"{API}/me/player/queue", headers=self._headers(), timeout=10)
        if r.status_code == 204 or not r.content:
            return []
        r.raise_for_status()
        data = r.json()
        return [track_from_item(t) for t in (data.get("queue") or []) if t]

    # -- playback control ------------------------------------------------- #
    def devices(self) -> list[dict]:
        return self._get("/me/player/devices").get("devices", [])

    def find_device(self, name: str) -> str | None:
        for d in self.devices():
            if d.get("name") == name:
                return d.get("id")
        return None

    def current_playback(self) -> dict | None:
        """GET /me/player. Returns None if nothing is playing / no active device."""
        r = self._requests.get(f"{API}/me/player", headers=self._headers(), timeout=10)
        if r.status_code == 401:
            self._token = self._auth.load_valid()
            r = self._requests.get(f"{API}/me/player", headers=self._headers(), timeout=10)
        if r.status_code == 204 or not r.content:
            return None
        r.raise_for_status()
        return r.json()

    def play_context(self, context_uri: str, device_id: str | None = None,
                     offset_position: int | None = None) -> None:
        """Start a playlist/album (context) — plays *any* playlist you follow.
        offset_position optionally starts at a given track index."""
        body: dict = {"context_uri": context_uri}
        if offset_position is not None:
            body["offset"] = {"position": offset_position}
        self._put("/me/player/play", json=body, device_id=device_id)

    def resume(self, device_id: str | None = None) -> None:
        self._put("/me/player/play", device_id=device_id)   # no body = resume

    def pause(self) -> None:
        self._put("/me/player/pause")

    def next_track(self) -> None:
        self._post_player("/me/player/next")

    def previous_track(self) -> None:
        self._post_player("/me/player/previous")

    def seek(self, position_ms: int) -> None:
        self._put("/me/player/seek", position_ms=int(position_ms))

    def set_volume(self, volume_percent: int) -> None:
        self._put("/me/player/volume", volume_percent=int(volume_percent))

    def transfer_to(self, device_id: str, play: bool = True) -> None:
        self._put("/me/player", json={"device_ids": [device_id], "play": play})


def make_web(cfg) -> "SpotifyWeb | None":
    """Build an authorized SpotifyWeb from config + cached token, or None."""
    if not cfg.spotify_client_id or not cfg.token_path().exists():
        return None
    try:
        from .spotify_auth import Authorizer

        auth = Authorizer(cfg.spotify_client_id, cfg.spotify_redirect_uri, cfg.token_path())
        web = SpotifyWeb(auth)
        return web if web.authorized else None
    except Exception:  # noqa: BLE001
        return None
