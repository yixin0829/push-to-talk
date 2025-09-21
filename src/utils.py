from loguru import logger
from pathlib import Path
from playsound3 import playsound


# Audio file paths
_ASSETS_DIR = Path(__file__).parent / "assets" / "audio"
_START_SOUND_PATH = _ASSETS_DIR / "start_feedback.wav"
_STOP_SOUND_PATH = _ASSETS_DIR / "stop_feedback.wav"


def set_debug_logging(enabled: bool):
    """
    Enable or disable DEBUG level logging.

    Args:
        enabled: True to enable DEBUG logging, False to set back to INFO
    """
    try:
        # Remove existing handlers
        logger.remove()

        # Add new handler with appropriate level
        log_level = "DEBUG" if enabled else "INFO"
        logger.add("push_to_talk.log", level=log_level)

        if enabled:
            logger.debug("Debug logging enabled")
        else:
            logger.info("Debug logging disabled")

    except Exception as e:
        logger.error(f"Failed to update logging level: {e}")


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
