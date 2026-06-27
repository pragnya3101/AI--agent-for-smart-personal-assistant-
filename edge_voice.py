import pyttsx3
import speech_recognition as sr


def _create_engine():
    try:
        engine = pyttsx3.init("sapi5")
        engine.setProperty("rate", 180)

        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        return engine
    except Exception as e:
        print(f"Voice engine failed: {e}")
        return None


engine = None


def _get_engine():
    global engine

    if engine is None:
        engine = _create_engine()

    return engine


def speak(text):
    print(f"Will: {text}")

    engine = _get_engine()

    if engine is None:
        return

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Speak failed: {e}")


def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            text = recognizer.recognize_google(audio)
            return text.lower()
    except Exception as e:
        print(f"Listen failed: {e}")
        return ""
