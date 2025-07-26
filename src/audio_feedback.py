import winsound
import threading
import logging

logger = logging.getLogger(__name__)

class AudioFeedbackService:
    """Service for providing audio feedback during hotkey interactions using built-in Windows sounds."""
    
    def __init__(self):
        """Initialize the audio feedback service."""
        self.is_initialized = True
        logger.info("Audio feedback service initialized")
    
    def play_start_feedback(self):
        """Play a high-pitched beep for recording start."""
        def play_sound():
            try:
                # High-pitched ascending beep (tech-like)
                winsound.Beep(880, 150)  # A5 note for 150ms
            except Exception as e:
                logger.error(f"Failed to play start feedback sound: {e}")
        
        # Play in separate thread to avoid blocking
        threading.Thread(target=play_sound, daemon=True).start()
    
    def play_stop_feedback(self):
        """Play a lower-pitched confirmation beep for recording stop."""
        def play_sound():
            try:
                # Lower-pitched descending confirmation (Steve Jobs-like simplicity)
                winsound.Beep(660, 100)  # E5 note for 100ms - crisp and clean
            except Exception as e:
                logger.error(f"Failed to play stop feedback sound: {e}")
        
        # Play in separate thread to avoid blocking
        threading.Thread(target=play_sound, daemon=True).start()
    
    def cleanup(self):
        """Clean up resources (nothing to clean up for winsound)."""
        logger.info("Audio feedback service cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup() 