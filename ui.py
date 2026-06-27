# ui.py - Modernized Streamlit UI wrapper for jarvis.py
# Run with: streamlit run ui.py

import streamlit as st
import threading
import queue
import html
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Jarvis OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Auto-Refresh Setup (Updates UI smoothly every 800ms without blocking) ─────
st_autorefresh(interval=800, key="jarvis_ui_refresh")

# ── Shared Queues for Thread Communication ────────────────────────────────────
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()
if "status_queue" not in st.session_state:
    st.session_state.status_queue = queue.Queue()
if "input_bypass_queue" not in st.session_state:
    st.session_state.input_bypass_queue = queue.Queue()

# ── Session State Initialisation ──────────────────────────────────────────────
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "status" not in st.session_state:
    st.session_state.status = "idle"  # idle | listening | thinking | speaking
if "jarvis_started" not in st.session_state:
    st.session_state.jarvis_started = False
if "spotify_status" not in st.session_state:
    st.session_state.spotify_status = "No track playing"
if "weather_info" not in st.session_state:
    st.session_state.weather_info = "Awaiting request..."
if "last_news" not in st.session_state:
    st.session_state.last_news = "Awaiting request..."

# ── Premium Cyberpunk / Minimalist Dark Theme CSS ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

/* Global Overrides */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #0A0A0C !important;
    color: #E4E4E7;
}
.stApp { background-color: #0A0A0C; }

/* Premium Header styling */
.jarvis-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    background: linear-gradient(135deg, rgba(20,20,25,0.8) 0%, rgba(10,10,12,0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
}
.header-left { display: flex; align-items: center; gap: 16px; }
.jarvis-logo {
    width: 44px; height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
    display: flex; align-items: center; justify-content: center;
    color: #000; font-size: 22px; font-weight: bold;
    box-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
}
.jarvis-name {
    font-size: 24px; font-weight: 600; color: #FFF; letter-spacing: -0.5px;
}
.jarvis-sub {
    font-size: 12px; color: #71717A; margin-top: 2px; font-family: 'JetBrains Mono', monospace;
}

/* Status pill configurations */
.status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 16px; border-radius: 99px;
    font-size: 12px; font-weight: 500; font-family: 'JetBrains Mono', monospace;
    border: 1px solid rgba(255,255,255,0.08);
}
.status-pill.idle { background: rgba(39, 39, 42, 0.5); color: #A1A1AA; }
.status-pill.listening { background: rgba(22, 101, 52, 0.3); color: #4ADE80; border-color: rgba(74, 222, 128, 0.4); }
.status-pill.thinking { background: rgba(146, 64, 14, 0.3); color: #FBBF24; border-color: rgba(251, 191, 36, 0.4); }
.status-pill.speaking { background: rgba(30, 64, 175, 0.3); color: #60A5FA; border-color: rgba(96, 165, 250, 0.4); }

.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-idle      { background: #71717A; }
.dot-listening { background: #4ADE80; animation: pulse 1.2s infinite; }
.dot-thinking  { background: #FBBF24; animation: pulse 0.8s infinite; }
.dot-speaking  { background: #60A5FA; animation: pulse 1s infinite; }

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.3; transform: scale(1.2); }
}

/* Ambient Visualizer Ring */
.mic-container {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 40px 0; background: rgba(20,20,25,0.4); border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.03); margin-bottom: 24px;
}
.mic-ring {
    width: 110px; height: 110px; border-radius: 50%;
    background: #141419; border: 2px solid rgba(255,255,255,0.1);
    display: flex; align-items: center; justify-content: center;
    font-size: 42px; position: relative; transition: all 0.4s ease;
}
.mic-ring.listening {
    border-color: #4ADE80; box-shadow: 0 0 30px rgba(74,222,128,0.2);
}
.mic-ring.thinking {
    border-color: #FBBF24; box-shadow: 0 0 30px rgba(251,191,36,0.2); transform: rotate(360deg);
}
.mic-ring.speaking {
    border-color: #60A5FA; box-shadow: 0 0 30px rgba(96,165,250,0.2);
}

/* Smooth Waveform Visualizer */
.waveform { display: flex; align-items: center; gap: 4px; height: 32px; margin-top: 20px; }
.waveform .bar { width: 4px; border-radius: 99px; background: #4ADE80; min-height: 6px; }
.waveform .bar:nth-child(1){ animation: wave 0.8s ease-in-out infinite alternate 0.0s; }
.waveform .bar:nth-child(2){ animation: wave 0.8s ease-in-out infinite alternate 0.15s; }
.waveform .bar:nth-child(3){ animation: wave 0.8s ease-in-out infinite alternate 0.3s; }
.waveform .bar:nth-child(4){ animation: wave 0.8s ease-in-out infinite alternate 0.45s; }
.waveform .bar:nth-child(5){ animation: wave 0.8s ease-in-out infinite alternate 0.3s; }
.waveform .bar:nth-child(6){ animation: wave 0.8s ease-in-out infinite alternate 0.15s; }
.waveform .bar:nth-child(7){ animation: wave 0.8s ease-in-out infinite alternate 0.0s; }
@keyframes wave { 0% { height: 6px; } 100% { height: 32px; } }

/* Modern Widgets Layout */
.feat-card {
    background: rgba(20, 20, 25, 0.6); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px; padding: 16px; margin-bottom: 14px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.feat-card:hover { border-color: rgba(255,255,255,0.1); }
.feat-title {
    font-size: 11px; font-weight: 600; color: #71717A;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;
    display: flex; align-items: center; gap: 6px;
}
.feat-value {
    font-size: 13.5px; color: #E4E4E7; line-height: 1.5; font-family: 'JetBrains Mono', monospace;
}

/* Clean Chips UI */
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.chip {
    font-size: 11px; padding: 4px 10px; border-radius: 6px;
    background: rgba(255,255,255,0.03); color: #A1A1AA;
    border: 1px solid rgba(255,255,255,0.06); font-family: 'JetBrains Mono', monospace;
}

/* Chat Terminal Window styling */
.transcript-wrap {
    background: #0E0E11; border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px; padding: 20px;
    height: 480px; overflow-y: auto;
    display: flex; flex-direction: column; gap: 16px;
}
.msg-row { display: flex; flex-direction: column; margin-bottom: 4px; width: 100%; }
.msg-you {
    align-self: flex-end; background: #27272A;
    border-radius: 14px 14px 2px 14px; padding: 10px 16px;
    font-size: 14px; color: #FFF; max-width: 80%; text-align: left;
}
.msg-jarvis {
    align-self: flex-start; background: linear-gradient(135deg, rgba(14,116,144,0.15) 0%, rgba(3,105,120,0.15) 100%);
    border: 1px solid rgba(6, 182, 212, 0.2);
    border-radius: 14px 14px 14px 2px; padding: 10px 16px;
    font-size: 14px; color: #22D3EE; max-width: 80%; text-align: left;
}
.msg-meta {
    font-size: 10px; color: #52525B; font-family: 'JetBrains Mono', monospace;
    margin-top: 4px; display: block;
}
.meta-you { text-align: right; padding-right: 4px; }
.meta-jarvis { text-align: left; padding-left: 4px; }

.empty-transcript {
    text-align: center; color: #3F3F46; font-family: 'JetBrains Mono', monospace;
    font-size: 13px; margin: auto 0;
}
</style>
""", unsafe_allow_html=True)


# ── Jarvis Background Loop Processor Thread ───────────────────────────────────
def run_jarvis_background(msg_q: queue.Queue, status_q: queue.Queue, bypass_q: queue.Queue):
    import time
    import config
    import memory
    import edge_voice as voice
    import will

    # ── Intercept Speech & update Status Queues ───────────────────────────────
    original_speak = voice.speak
    def patched_speak(text):
        status_q.put("speaking")
        msg_q.put(("assistant", text, datetime.now().strftime("%I:%M %p")))
        original_speak(text)
        status_q.put("listening")
    voice.speak = patched_speak

    # ── Intercept Voice Capture Loop ──────────────────────────────────────────
    original_listen = voice.listen
    def patched_listen():
        status_q.put("listening")
        
        # Non-blocking structural read check for manual UI text submissions
        try:
            manual_text = bypass_q.get_nowait()
            if manual_text:
                status_q.put("thinking")
                msg_q.put(("user", manual_text, datetime.now().strftime("%I:%M %p")))
                return manual_text
        except queue.Empty:
            pass

        # If no written override input exists, perform default hardware mic scan
        text = original_listen()
        if text:
            status_q.put("thinking")
            msg_q.put(("user", text, datetime.now().strftime("%I:%M %p")))
        return text
    voice.listen = patched_listen

    # ── CORE AGENT LOOPS (Matches Core logic setup) ───────────────────────────
    HINDI_MAP = {
        "gaana bajao": "play music", "gaana chalao": "play music",
        "mausam batao": "weather", "samay batao": "what is the time",
        "news sunao": "read the news", "band karo": "goodbye"
    }

    def normalize(text):
        t = text.lower().strip()
        for h, e in HINDI_MAP.items():
            if h in t: return e
        return text

    chat_history = memory.load_memory()
    status_q.put("listening")

    while True:
        try:
            user_input = voice.listen()
            if not user_input:
                time.sleep(0.2)
                continue

            inp = normalize(user_input.lower().strip())
            if config.WAKE_WORD.lower() in inp:
                inp = inp.replace(config.WAKE_WORD.lower(), "").strip()
                if not inp: voice.speak("Online. Awaiting command parameters."); continue

            response, should_stop, chat_history = will.respond(inp, chat_history)
            voice.speak(response)

            if should_stop:
                break
        except Exception as e:
            print(f"[Thread Runtime warning Error]: {e}")
            continue


# ── Initialization of background process threads ─────────────────────────────
if not st.session_state.jarvis_started:
    t = threading.Thread(
        target=run_jarvis_background,
        args=(st.session_state.msg_queue, st.session_state.status_queue, st.session_state.input_bypass_queue),
        daemon=True
    )
    t.start()
    st.session_state.jarvis_started = True


# ── Process Interface Queues smoothly into Layout state ───────────────────────
while not st.session_state.status_queue.empty():
    st.session_state.status = st.session_state.status_queue.get_nowait()

while not st.session_state.msg_queue.empty():
    role, text, ts = st.session_state.msg_queue.get_nowait()
    st.session_state.transcript.append({"role": role, "text": text, "time": ts})
    
    # Intelligently track state attributes based on AI outputs
    text_lower = text.lower()
    if any(w in text_lower for w in ["playing", "song", "music", "spotify"]):
        st.session_state.spotify_status = text
    elif any(w in text_lower for w in ["°", "temperature", "weather", "forecast"]):
        st.session_state.weather_info = text
    elif any(w in text_lower for w in ["headline", "news", "top story"]):
        st.session_state.last_news = text[:100] + "..."


# ── DESIGN AND LAYOUT COMPOSITIONS ────────────────────────────────────────────

# Premium Status-Aware Header Context
status_current = st.session_state.status
st.markdown(f"""
<div class="jarvis-header">
  <div class="header-left">
    <div class="jarvis-logo">⚡</div>
    <div>
      <div class="jarvis-name">JARVIS OS</div>
      <div class="jarvis-sub">INTELLIGENT VOICE LAYER // GROQ CORE</div>
    </div>
  </div>
  <div>
    <span class="status-pill {status_current}">
      <span class="status-dot dot-{status_current}"></span>
      {status_current.upper()}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.4], gap="large")

# ── LEFT PANEL: Operational Visualizers & Telemetry Cards ───────────────────
with col_left:
    mic_class = status_current if status_current in ["listening","thinking","speaking"] else ""
    mic_icon = "⏳" if status_current == "thinking" else "🎙️"
    
    label_map = {
        "idle": "SYSTEMS DORMANT // AWAITING WAKE SYNC",
        "listening": "AUDIO STREAM ACTIVE // RECORDING INTERCEPT",
        "thinking": "ALGORITHMIC ROUTING INFRASTRUCTURE SEARCHING...",
        "speaking": "SYNTHESIZING MATRIX EDGE AUDIO RESPONSE MODULE",
    }
    
    wave_html = """
    <div class="waveform">
      <div class="bar"></div><div class="bar"></div><div class="bar"></div>
      <div class="bar"></div><div class="bar"></div><div class="bar"></div>
      <div class="bar"></div>
    </div>""" if status_current == "listening" else ""

    st.markdown(f"""
    <div class="mic-container">
      <div class="mic-ring {mic_class}">{mic_icon}</div>
      <div style="margin-top:18px; font-size:11px; font-family:'JetBrains Mono', monospace; color:#71717A;">
        {label_map.get(status_current,'')}
      </div>
      {wave_html}
    </div>
    """, unsafe_allow_html=True)

    # Telemetry System Grid Cards
    st.markdown(f"""
    <div class="feat-card">
      <div class="feat-title">🎵 SPOTIFY DECK</div>
      <div class="feat-value">{html.escape(st.session_state.spotify_status)}</div>
      <div class="chips">
        <span class="chip">play [track]</span><span class="chip">pause</span><span class="chip">skip</span>
      </div>
    </div>

    <div class="feat-card">
      <div class="feat-title">🌤️ ENV ENVIRONMENT METRICS</div>
      <div class="feat-value">{html.escape(st.session_state.weather_info)}</div>
      <div class="chips">
        <span class="chip">weather data</span><span class="chip">mausam status</span>
      </div>
    </div>

    <div class="feat-card">
      <div class="feat-title">📰 WIRE DISPATCH SYNDICATE</div>
      <div class="feat-value">{html.escape(st.session_state.last_news)}</div>
      <div class="chips">
        <span class="chip">news</span><span class="chip">tech news digest</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── RIGHT PANEL: Main Realtime Terminal Logs ──────────────────────────────────
with col_right:
    # Modern Terminal Transcript Wrapper Box
    transcript_logs = st.session_state.transcript
    if not transcript_logs:
        inner_content = '<div class="empty-transcript">// SYSTEM LOG MATRIX EMPTY // BROADCAST COMPONENT ACTIVE</div>'
    else:
        rows_str = ""
        for msg in transcript_logs[-20:]:
            is_user = (msg["role"] == "user")
            class_tag = "msg-you" if is_user else "msg-jarvis"
            meta_tag = "meta-you" if is_user else "meta-jarvis"
            sender_label = "OPERATOR" if is_user else "JARVIS CORE"
            
            rows_str += f"""
            <div class="msg-row">
              <div class="{class_tag}">{html.escape(str(msg['text']))}</div>
              <span class="msg-meta {meta_tag}">{sender_label} • {msg['time']}</span>
            </div>"""
        inner_content = rows_str

    st.markdown(f'<div class="transcript-wrap">{inner_content}</div>', unsafe_allow_html=True)
    
    # Modern Intercept Bypass Interface (Allows typing directly into voice loop seamlessly)
    with st.form(key="keyboard_bypass_entry", clear_on_submit=True):
        input_col, action_col = st.columns([4, 1])
        with input_col:
            user_bypass_text = st.text_input(
                label="Keyboard input bypass console",
                placeholder="Type command manually here if mic is muted...",
                label_visibility="collapsed"
            )
        with action_col:
            submit_bypass = st.form_submit_button("SEND ↵", use_container_width=True)
            
        if submit_bypass and user_bypass_text.strip():
            st.session_state.input_bypass_queue.put(user_bypass_text.strip())
            
    # System Core Clean Utility Buttons
    btn_col_1, btn_col_2 = st.columns(2)
    with btn_col_1:
        if st.button("🗙 Clear Screen Terminal logs", use_container_width=True):
            st.session_state.transcript = []
            st.rerun()
    with btn_col_2:
        if st.session_state.transcript:
            export_data = "\n".join([f"[{m['time']}] {m['role'].upper()}: {m['text']}" for m in st.session_state.transcript])
            st.download_button("🖴 Export active log runtime", data=export_data, file_name="jarvis_sys_log.txt", mime="text/plain", use_container_width=True)
