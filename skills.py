import datetime
import os
import re
import urllib.parse
import webbrowser

import psutil
import pyautogui
import speedtest

import config
import messenger
import news_reader
import spotify_control


KNOWN_WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "w3schools": "https://www.w3schools.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "spotify": "https://open.spotify.com",
}


def _clean_command_text(text):
    text = text.strip()

    if text.startswith("hey will "):
        return text[len("hey will "):].strip()

    if text.startswith("will "):
        return text[len("will "):].strip()

    return text


def _parse_email_command(original_text):
    text = original_text.strip()
    lower_text = text.lower()

    for prefix in (
        "send an email to ",
        "send email to ",
        "send mail to ",
        "send an email ",
        "send email ",
        "send mail ",
        "email to ",
        "mail to ",
        "email ",
        "mail ",
    ):
        if lower_text.startswith(prefix):
            payload = text[len(prefix):].strip()
            break
    else:
        return None

    if not payload:
        return None

    contact, _, rest = payload.partition(" ")

    if not contact or not rest:
        return None

    subject = "Message from Will"
    body = rest.strip()

    for marker in (" saying ", " message ", " body "):
        if marker in f" {body.lower()} ":
            parts = re.split(marker.strip(), body, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                body = parts[1].strip()
            break

    subject_match = re.search(
        r"\bsubject\s+(.+?)\s+(?:message|body)\s+(.+)$",
        rest,
        flags=re.IGNORECASE,
    )

    if subject_match:
        subject = subject_match.group(1).strip()
        body = subject_match.group(2).strip()

    return contact.lower(), subject, body


def _normalize_site_url(site):
    site = site.strip().lower()
    site = re.sub(r"\s+website$", "", site).strip()
    site = re.sub(r"^(this|the)\s+", "", site).strip()

    if site in KNOWN_WEBSITES:
        return KNOWN_WEBSITES[site]

    site = site.replace(" dot ", ".").replace(" ", "")

    if not site:
        return None

    if "." not in site:
        site = f"{site}.com"

    if not site.startswith(("http://", "https://")):
        site = f"https://{site}"

    return site


def _parse_open_website_command(text):
    match = re.search(
        r"^(?:open|go to|launch)\s+(?:this\s+)?(?:website\s+)?(.+?)(?:\s+website)?$",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    target = match.group(1).strip()

    if target in {"website", "site", "web page", "page"}:
        return "Say the website name, for example: open w3schools website"

    url = _normalize_site_url(target)

    if not url:
        return "Say the website name, for example: open google.com"

    webbrowser.open(url)
    return f"Opening {url}"


def play_youtube_video(query):
    query = query.strip()

    if not query:
        return "Say the video name"

    try:
        import pywhatkit

        pywhatkit.playonyt(query)
        return f"Playing {query} on YouTube"
    except Exception as e:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        webbrowser.open(url)
        return f"Opening YouTube results for {query}"


def _parse_youtube_play_command(text):
    patterns = (
        r"^(?:play|search|open)\s+(.+?)\s+(?:video\s+)?(?:on|in)\s+youtube$",
        r"^youtube\s+(?:play|search|open)\s+(.+)$",
        r"^(?:play|open)\s+youtube\s+video\s+(.+)$",
    )

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    if text in {"play video in youtube", "play video on youtube", "youtube video"}:
        return ""

    return None


def _parse_whatsapp_command(original_text):
    text = original_text.strip()
    lower_text = text.lower()

    for prefix in ("send whatsapp to ", "send whatsapp ", "whatsapp to ", "whatsapp "):
        if lower_text.startswith(prefix):
            payload = text[len(prefix):].strip()
            break
    else:
        return None

    if not payload:
        return None

    contact, _, message = payload.partition(" ")

    if not contact or not message:
        return None

    if message.lower().startswith("message "):
        message = message[8:].strip()

    return contact.lower(), message.strip()


def get_time():
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")


def open_chrome():
    path = config.APPS["chrome"]

    if os.path.exists(path):
        os.startfile(path)
        return "Opening Chrome"

    webbrowser.open("https://google.com/chrome")
    return "Chrome was not found locally, so I opened it in the browser"


def open_youtube():
    webbrowser.open("https://youtube.com")
    return "Opening YouTube"


def get_battery():
    battery = psutil.sensors_battery()

    if battery is None:
        return "Battery information is not available"

    return f"Battery is {int(battery.percent)} percent"


def take_screenshot():
    try:
        img = pyautogui.screenshot()
        img.save("screenshot.png")
        return "Screenshot taken"
    except Exception as e:
        print(e)
        return "Screenshot failed"


def check_speed():
    try:
        st = speedtest.Speedtest()
        download = st.download() / 1_000_000
        return f"Download speed is {download:.2f} Mbps"
    except Exception as e:
        print(e)
        return "Internet speed test failed"


def get_volume():
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    comtypes.CoInitialize()
    try:
        devices = AudioUtilities.GetSpeakers()
        volume = getattr(devices, "EndpointVolume", None)
        if volume is None:
            raise RuntimeError("Audio endpoint volume is not available")
        return int(round(volume.GetMasterVolumeLevelScalar() * 100))
    finally:
        comtypes.CoUninitialize()


def set_volume(level):
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    level = max(0, min(100, level))
    comtypes.CoInitialize()
    try:
        devices = AudioUtilities.GetSpeakers()
        volume = getattr(devices, "EndpointVolume", None)
        if volume is None:
            raise RuntimeError("Audio endpoint volume is not available")
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        actual_level = int(round(volume.GetMasterVolumeLevelScalar() * 100))
    finally:
        comtypes.CoUninitialize()

    return f"Volume set to {actual_level}"


def change_volume(delta):
    return set_volume(get_volume() + delta)


def set_mute(should_mute):
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    comtypes.CoInitialize()
    try:
        devices = AudioUtilities.GetSpeakers()
        volume = getattr(devices, "EndpointVolume", None)
        if volume is None:
            raise RuntimeError("Audio endpoint volume is not available")
        volume.SetMute(1 if should_mute else 0, None)
    finally:
        comtypes.CoUninitialize()

    return "Muted" if should_mute else "Unmuted"


def handle_volume_command(text):
    if "unmute" in text:
        return set_mute(False)

    if "mute" in text:
        return set_mute(True)

    if "increase" in text or "volume up" in text or "raise" in text:
        return change_volume(10)

    if "decrease" in text or "volume down" in text or "lower" in text:
        return change_volume(-10)

    match = re.search(r"\b(?:volume|sound)\s*(?:to|at|is)?\s*(\d{1,3})\b", text)
    if match:
        return set_volume(int(match.group(1)))

    return "Say volume 50, volume up, volume down, mute, or unmute"


def detect_news_topic(text):
    if "telangana" in text:
        return "telangana"

    if "hyderabad" in text:
        return "hyderabad"

    if "tech" in text or "technology" in text:
        return "technology"

    if "sports" in text:
        return "sports"

    return "india"


def handle_command(text):
    original_text = _clean_command_text(text)
    text = original_text.lower()

    if text in {"exit", "quit", "goodbye", "bye", "stop assistant"}:
        return "EXIT"

    if text in {"clear memory", "reset memory", "forget everything"}:
        return "CLEAR_MEMORY"

    if text.startswith("python ") or text.startswith("pip ") or text.startswith("cd "):
        return "Run that command in PowerShell, not inside Will"

    email_command = _parse_email_command(original_text)

    if email_command:
        contact, subject, body = email_command
        return messenger.send_email(contact, subject, body)

    if "email" in text or "mail" in text:
        return "Say: send email to pragnya subject Test message Hello"

    whatsapp_command = _parse_whatsapp_command(original_text)

    if whatsapp_command:
        contact, message = whatsapp_command
        return messenger.send_whatsapp(contact, message)

    if "whatsapp" in text:
        return "Say: send whatsapp to amma Hello"

    if "time" in text:
        return get_time()

    youtube_query = _parse_youtube_play_command(text)
    if youtube_query is not None:
        return play_youtube_video(youtube_query)

    if "open chrome" in text:
        return open_chrome()

    if text in {"youtube", "open youtube"}:
        return open_youtube()

    if "battery" in text:
        return get_battery()

    if "screenshot" in text:
        return take_screenshot()

    if "internet speed" in text:
        return check_speed()

    if "open spotify" in text:
        return spotify_control.open_spotify()

    website_response = _parse_open_website_command(text)
    if website_response:
        return website_response

    spotify_match = re.search(r"^(?:play|search)\s+(.+?)\s+(?:on|in)\s+spotify$", text)
    if spotify_match:
        return spotify_control.play_song(spotify_match.group(1).strip())

    if text == "play music":
        return spotify_control.open_spotify()

    if text == "play" or text.startswith("play "):
        song = text.replace("play", "", 1).strip()
        return spotify_control.play_song(song)

    if "pause music" in text:
        return spotify_control.pause_music()

    if "next song" in text or "skip" in text:
        return spotify_control.next_song()

    if "news" in text or "headlines" in text:
        topic = detect_news_topic(text)
        headlines = news_reader.get_news(topic=topic, limit=5)
        return ". ".join(headlines) if headlines else "News is not available right now"

    if "volume" in text or "sound" in text or "mute" in text:
        try:
            return handle_volume_command(text)
        except Exception as e:
            print(e)
            return "Volume control failed"

    return None
