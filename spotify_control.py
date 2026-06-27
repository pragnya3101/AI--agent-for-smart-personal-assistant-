import subprocess
import webbrowser

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config


SCOPE = "user-modify-playback-state user-read-playback-state"


def get_spotify():
    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        raise RuntimeError("Spotify credentials are missing")

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=SCOPE,
        )
    )


def open_spotify():
    try:
        subprocess.Popen(config.APPS["spotify"])
        return "Opening Spotify"
    except Exception:
        webbrowser.open("https://open.spotify.com")
        return "Opening Spotify in browser"


def play_song(song):
    if not song:
        return "Say the song name"

    try:
        sp = get_spotify()
        devices = sp.devices()["devices"]

        if not devices:
            open_spotify()
            return "Open Spotify and start any song once, then ask me to play it again"

        device_id = devices[0]["id"]
        results = sp.search(q=song, type="track", limit=1)
        tracks = results["tracks"]["items"]

        if not tracks:
            return "Song not found"

        track = tracks[0]
        sp.start_playback(device_id=device_id, uris=[track["uri"]])

        artists = ", ".join(artist["name"] for artist in track.get("artists", []))
        return f"Playing {track['name']} by {artists}" if artists else f"Playing {track['name']}"
    except Exception as e:
        print(e)
        message = str(e)
        if "credentials" in message.lower():
            return "Spotify credentials are missing. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env"
        if "No active device" in message:
            return "Open Spotify and start any song once, then ask me again"
        return f"Spotify failed: {message[:120]}"


def pause_music():
    try:
        sp = get_spotify()
        sp.pause_playback()
        return "Music paused"
    except Exception:
        return "Pause failed"


def next_song():
    try:
        sp = get_spotify()
        sp.next_track()
        return "Next song"
    except Exception:
        return "Skip failed"
