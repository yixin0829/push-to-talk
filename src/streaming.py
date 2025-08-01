"""
Example of STT streaming
"""

import websocket
import threading
import json
import pyaudio
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

# Set up audio stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
)


def on_message(ws, message):
    print("🔁 Transcript:", message)


def on_open(ws):
    def run(*args):
        # Step 1: send config
        config = {
            "type": "config",
            "config": {"language": "en", "encoding": "linear16", "sample_rate": RATE},
        }
        ws.send(json.dumps(config))

        # Step 2: send audio chunks
        while True:
            data = stream.read(CHUNK)
            ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    threading.Thread(target=run).start()


def on_close(ws, close_status_code, close_msg):
    print("❌ Closed")


# Open the WebSocket
headers = {"Authorization": f"Bearer {API_KEY}"}

ws = websocket.WebSocketApp(
    "wss://api.openai.com/v1/audio/transcriptions/gpt-4o-transcribe",
    on_message=on_message,
    on_open=on_open,
    on_close=on_close,
    header=headers,
)

ws.run_forever()
