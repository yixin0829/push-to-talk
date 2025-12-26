import os
import wave
from loguru import logger
from pathlib import Path
from playsound3 import playsound

from src.config.constants import AUDIO_DURATION_MIN_THRESHOLD_SECONDS


# Audio file paths
_ASSETS_DIR = Path(__file__).parent / "assets" / "audio"
_START_SOUND_PATH = _ASSETS_DIR / "start_feedback.wav"
_STOP_SOUND_PATH = _ASSETS_DIR / "stop_feedback.wav"


def play_start_feedback():
    """Play a high-pitched beep for recording start."""

    try:
        if _START_SOUND_PATH.exists():
            playsound(str(_START_SOUND_PATH), block=False)
        else:
            logger.warning(f"Start feedback audio file not found: {_START_SOUND_PATH}")
    except Exception as e:
        logger.error(f"Failed to play start feedback sound: {e}")


def play_stop_feedback():
    """Play a lower-pitched confirmation beep for recording stop."""

    try:
        if _STOP_SOUND_PATH.exists():
            playsound(str(_STOP_SOUND_PATH), block=False)
        else:
            logger.warning(f"Stop feedback audio file not found: {_STOP_SOUND_PATH}")
    except Exception as e:
        logger.error(f"Failed to play stop feedback sound: {e}")


def validate_audio_file_exists(file_path: str) -> bool:
    """
    Check if audio file exists at the given path.

    Args:
        file_path: Path to the audio file

    Returns:
        True if file exists, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"Audio file not found: {file_path}")
        return False
    return True


def validate_audio_duration(
    file_path: str, min_duration: float = AUDIO_DURATION_MIN_THRESHOLD_SECONDS
) -> bool:
    """
    Validate audio file duration is acceptable for transcription.

    Skips very short audio clips to avoid unnecessary API calls.
    If duration cannot be determined, allows transcription to proceed.

    Args:
        file_path: Path to the audio file
        min_duration: Minimum required duration in seconds

    Returns:
        True if audio should be transcribed, False if too short
    """
    try:
        with wave.open(file_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate() or 0
            duration_seconds = frames / float(rate) if rate else 0.0

        if duration_seconds < min_duration:
            logger.info(
                f"Audio too short ({duration_seconds:.3f}s); skipping transcription"
            )
            return False

        return True

    except Exception as e:
        # If duration cannot be determined (e.g., not a valid WAV), allow transcription
        logger.debug(f"Could not determine audio duration for {file_path}: {e}")
        return True
