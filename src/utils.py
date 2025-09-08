from loguru import logger
from pathlib import Path
from playsound3 import playsound


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
