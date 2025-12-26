"""Application-wide constants and default values.

This module centralizes all magic numbers and configuration constants
used throughout the PushToTalk application.
"""

# Audio Processing
AUDIO_DURATION_MIN_THRESHOLD_SECONDS = 0.5
"""Skip audio clips shorter than this duration (in seconds).

Rationale: Very short audio clips (<0.5s) typically don't contain
meaningful speech and would waste API credits.
"""

AUDIO_RECORDING_THREAD_TIMEOUT_SECONDS = 5.0
"""Maximum time to wait for recording thread to stop (in seconds).

Rationale: Gives recording thread ample time to clean up PyAudio
resources while preventing indefinite blocking.
"""

# Text Insertion Timing
TEXT_INSERTION_DELAY_AFTER_COPY_SECONDS = 0.05
"""Delay after copying text to clipboard (in seconds).

Rationale: Allows clipboard manager to sync the copied content
across the system before attempting paste operation.
"""

TEXT_INSERTION_DELAY_AFTER_PASTE_SECONDS = 0.1
"""Delay after triggering paste command (in seconds).

Rationale: Gives target application time to process and complete
the paste operation before returning control.
"""

# Configuration Management
CONFIG_CHANGE_DEBOUNCE_DELAY_MS = 1000
"""Debounce delay for configuration changes (in milliseconds).

Rationale: Prevents excessive component reinitialization while user
is typing or rapidly changing settings. 1 second provides good balance
between responsiveness and avoiding redundant updates.
"""

CONFIG_AUTOSAVE_FILENAME = "push_to_talk_config.json"
"""Default filename for configuration persistence."""

# GUI Dimensions
WINDOW_MIN_WIDTH = 700
"""Minimum window width (in pixels).

Rationale: Ensures all GUI elements are visible without horizontal scrolling.
"""

WINDOW_MIN_HEIGHT = 800
"""Minimum window height (in pixels).

Rationale: Ensures all sections (API keys, audio settings, hotkeys, glossary)
fit comfortably in the visible area.
"""

# Audio Defaults
DEFAULT_SAMPLE_RATE = 16000
"""Default audio sample rate in Hz.

Rationale: 16kHz is optimal for speech recognition - high enough for
clear speech capture while keeping file sizes manageable.
"""

DEFAULT_CHUNK_SIZE = 1024
"""Default audio chunk size in frames.

Rationale: 1024 frames provides good balance between latency and
processing efficiency for real-time audio recording.
"""

DEFAULT_CHANNELS = 1
"""Default number of audio channels (1 = mono).

Rationale: Mono is sufficient for speech and reduces file size.
Most STT services process mono audio.
"""

# Supported Values (for validation)
SUPPORTED_SAMPLE_RATES = [8000, 16000, 24000, 32000, 44100, 48000]
"""Audio sample rates supported by the application.

Standard rates supported by most audio hardware and STT APIs.
"""

SUPPORTED_CHUNK_SIZES = [512, 1024, 2048, 4096]
"""Audio chunk sizes supported by the application.

Powers of 2 are preferred for efficient audio buffer processing.
"""

# Text Refinement
TEXT_REFINEMENT_MIN_LENGTH = 20
"""Minimum text length (in characters) to send for refinement.

Rationale: Very short text (<20 characters) is typically not worth
the API cost and latency of refinement. Return as-is instead.
"""

# Service Timeouts
HOTKEY_SERVICE_THREAD_TIMEOUT_SECONDS = 5.0
"""Maximum time to wait for hotkey service thread to stop (in seconds).

Rationale: Gives hotkey listener thread ample time to clean up
resources while preventing indefinite blocking.
"""
