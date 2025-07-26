"""
PushNTalk - A Speech-to-Text Push-to-Talk Application

A Python application that provides push-to-talk speech-to-text functionality
with OpenAI Whisper transcription, GPT text refinement, and automatic text
insertion into the active window.

Main Components:
- AudioRecorder: Records audio using pyaudio
- Transcriber: Converts speech to text using OpenAI Whisper
- TextRefiner: Improves transcription using GPT models
- TextInserter: Inserts text into active windows using pywin32
- HotkeyService: Handles push-to-talk hotkey detection
- PushNTalkApp: Main application orchestrator
"""

__version__ = "1.0.0"
__author__ = "Assistant"
__description__ = "Speech-to-Text Push-to-Talk Application"

from dotenv import load_dotenv

load_dotenv()

from .push_n_talk import PushNTalkApp, PushNTalkConfig, main
from .audio_recorder import AudioRecorder
from .transcription import Transcriber
from .text_refiner import TextRefiner
from .text_inserter import TextInserter
from .hotkey_service import HotkeyService

__all__ = [
    'PushNTalkApp',
    'PushNTalkConfig',
    'AudioRecorder',
    'Transcriber',
    'TextRefiner',
    'TextInserter',
    'HotkeyService',
    'main'
] 