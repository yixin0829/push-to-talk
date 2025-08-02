import threading
import logging
import numpy as np
import pygame
import pygame.sndarray
import os

logger = logging.getLogger(__name__)

# Initialize pygame mixer once
_mixer_initialized = False


def _init_mixer():
    """Initialize pygame mixer if not already done."""
    global _mixer_initialized
    if not _mixer_initialized:
        # Suppress pygame welcome message
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        pygame.mixer.pre_init(
            frequency=44100, size=-16, channels=2, buffer=512
        )  # Use stereo
        pygame.mixer.init()
        _mixer_initialized = True


def _generate_tone(
    frequency: float, duration: float, sample_rate: int = 44100
) -> np.ndarray:
    """Generate a pure tone as audio data."""
    frames = int(duration * sample_rate)
    wave_array = np.sin(2 * np.pi * frequency * np.linspace(0, duration, frames))

    # Apply envelope to avoid clicks
    fade_frames = int(0.01 * sample_rate)  # 10ms fade
    if fade_frames < frames // 2:
        wave_array[:fade_frames] *= np.linspace(0, 1, fade_frames)
        wave_array[-fade_frames:] *= np.linspace(1, 0, fade_frames)

    # Convert to 16-bit audio and create stereo (duplicate mono to both channels)
    audio_data = (wave_array * 32767).astype(np.int16)
    # Create stereo by stacking left and right channels
    stereo_data = np.column_stack((audio_data, audio_data))
    return stereo_data


def play_start_feedback():
    """Play a high-pitched beep for recording start."""

    def play_sound():
        try:
            _init_mixer()
            # High-pitched ascending beep (tech-like)
            audio_data = _generate_tone(880, 0.15)  # A5 note for 150ms
            sound = pygame.sndarray.make_sound(audio_data)
            sound.play()
        except Exception as e:
            logger.error(f"Failed to play start feedback sound: {e}")

    # Play in separate thread to avoid blocking
    threading.Thread(target=play_sound, daemon=True).start()


def play_stop_feedback():
    """Play a lower-pitched confirmation beep for recording stop."""

    def play_sound():
        try:
            _init_mixer()
            # Lower-pitched descending confirmation (Steve Jobs-like simplicity)
            audio_data = _generate_tone(
                660, 0.10
            )  # E5 note for 100ms - crisp and clean
            sound = pygame.sndarray.make_sound(audio_data)
            sound.play()
        except Exception as e:
            logger.error(f"Failed to play stop feedback sound: {e}")

    # Play in separate thread to avoid blocking
    threading.Thread(target=play_sound, daemon=True).start()
