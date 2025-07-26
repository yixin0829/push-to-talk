import winsound
import threading
import logging

logger = logging.getLogger(__name__)

def play_start_feedback():
    """Play a high-pitched beep for recording start."""
    def play_sound():
        try:
            # High-pitched ascending beep (tech-like)
            winsound.Beep(880, 150)  # A5 note for 150ms
        except Exception as e:
            logger.error(f"Failed to play start feedback sound: {e}")
    
    # Play in separate thread to avoid blocking
    threading.Thread(target=play_sound, daemon=True).start()

def play_stop_feedback():
    """Play a lower-pitched confirmation beep for recording stop."""
    def play_sound():
        try:
            # Lower-pitched descending confirmation (Steve Jobs-like simplicity)
            winsound.Beep(660, 100)  # E5 note for 100ms - crisp and clean
        except Exception as e:
            logger.error(f"Failed to play stop feedback sound: {e}")
    
    # Play in separate thread to avoid blocking
    threading.Thread(target=play_sound, daemon=True).start() 