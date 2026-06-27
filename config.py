import os

from dotenv import load_dotenv

load_dotenv()


def env(name, default=None):
    value = os.getenv(name, default)

    if isinstance(value, str):
        return value.strip().strip('"').strip("'")

    return value

# Assistant
JARVIS_NAME = "Will"
WAKE_WORD = "hey will"

# Groq
GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL", "llama-3.1-8b-instant")

# Gmail
GMAIL_ADDRESS = env("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = env("GMAIL_APP_PASSWORD")

# Spotify
SPOTIFY_CLIENT_ID = env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = env("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = env(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback",
)

# Twilio
TWILIO_SID = env("TWILIO_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUM = env("TWILIO_WHATSAPP_NUM", "whatsapp:+14155238886")

# Contacts
CONTACTS = {
    "pragnya": {
        "phone": "+918179515869",
        "email": "pragnyabodakuntla@gmail.com",
    },
    "amma": {
        "phone": "+917416044869",
        "email": "jyothibodakuntla@gmail.com",
    },
    "akka": {
        "phone": "+917416091869",
        "email": "smithibodakuntla@gmail.com",
    },
}

CONTACT_ALIASES = {
    "mother": "amma",
    "mom": "amma",
    "mum": "amma",
    "mummy": "amma",
    "sister": "akka",
}

# Apps
_USER = os.environ.get("USERNAME", "User")

APPS = {
    "spotify": rf"C:\Users\{_USER}\AppData\Roaming\Spotify\Spotify.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad",
    "calculator": "calc",
    "vs code": rf"C:\Users\{_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
}
