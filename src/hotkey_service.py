import keyboard
import threading
import logging
from typing import Callable, Optional, Set
import time

logger = logging.getLogger(__name__)

class HotkeyService:
    def __init__(self, hotkey: str = "ctrl+shift+space"):
        """
        Initialize the hotkey service.
        
        Args:
            hotkey: Hotkey combination for push-to-talk (default: ctrl+shift+space)
        """
        self.hotkey = hotkey
        self.is_running = False
        self.is_recording = False
        self.service_thread: Optional[threading.Thread] = None
        
        # Track which keys are currently pressed for the hotkey combination
        self.pressed_keys: Set[str] = set()
        self.hotkey_keys: Set[str] = set()
        
        # Callbacks
        self.on_start_recording: Optional[Callable] = None
        self.on_stop_recording: Optional[Callable] = None
        
        # Lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Parse the hotkey to get individual keys
        self._parse_hotkey()
        
    def _parse_hotkey(self):
        """Parse the hotkey string to extract individual keys."""
        try:
            # Parse the hotkey combination to get individual keys
            parsed = keyboard.parse_hotkey(self.hotkey)
            self.hotkey_keys.clear()
            
            for combo in parsed:
                for key in combo:
                    # Convert scan codes to key names
                    if hasattr(key, 'name'):
                        self.hotkey_keys.add(key.name)
                    else:
                        # Handle scan codes
                        key_name = keyboard.key_to_scan_codes(key)[0] if isinstance(key, str) else key
                        self.hotkey_keys.add(str(key_name))
                        
            logger.info(f"Hotkey keys parsed: {self.hotkey_keys}")
        except Exception as e:
            logger.error(f"Error parsing hotkey '{self.hotkey}': {e}")
            # Fallback to manual parsing for common combinations
            if self.hotkey == "ctrl+shift+space":
                self.hotkey_keys = {"ctrl", "shift", "space"}
        
    def set_callbacks(self, 
                     on_start_recording: Callable, 
                     on_stop_recording: Callable):
        """
        Set callback functions for recording start and stop events.
        
        Args:
            on_start_recording: Function to call when recording starts
            on_stop_recording: Function to call when recording stops
        """
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        
    def start_service(self) -> bool:
        """
        Start the hotkey listening service.
        
        Returns:
            True if service started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Hotkey service is already running")
            return False
            
        if not self.on_start_recording or not self.on_stop_recording:
            logger.error("Callbacks must be set before starting service")
            return False
            
        try:
            self.is_running = True
            self.service_thread = threading.Thread(target=self._run_service, daemon=True)
            self.service_thread.start()
            
            logger.info(f"Hotkey service started. Press and hold '{self.hotkey}' to record.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start hotkey service: {e}")
            self.is_running = False
            return False
    
    def stop_service(self):
        """Stop the hotkey listening service."""
        if not self.is_running:
            logger.warning("Hotkey service is not running")
            return
            
        self.is_running = False
        
        # Stop any ongoing recording
        if self.is_recording:
            self._stop_recording()
        
        # Unhook all keyboard events
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.warning(f"Error unhooking keyboard events: {e}")
        
        # Wait for service thread to finish
        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5.0)
            
        logger.info("Hotkey service stopped")
    
    def _run_service(self):
        """Main service loop running in a separate thread."""
        try:
            # Register hotkey combination for press detection
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_press)
            
            # Register key release detection for all keys
            keyboard.on_release(self._on_key_release)
            
            # Keep the service running
            while self.is_running:
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in hotkey service: {e}")
        finally:
            # Clean up
            try:
                keyboard.unhook_all()
            except:
                pass
    
    def _on_hotkey_press(self):
        """Handle hotkey combination press event."""
        with self._lock:
            if not self.is_recording and self.is_running:
                self._start_recording()
    
    def _on_key_release(self, event):
        """Handle any key release event."""
        with self._lock:
            if self.is_recording and self.is_running:
                # Check if any of the hotkey keys was released
                key_name = event.name if hasattr(event, 'name') else str(event.scan_code)
                
                # Check common key name variations
                key_variations = [key_name]
                if key_name == 'left ctrl' or key_name == 'right ctrl':
                    key_variations.extend(['ctrl', 'left ctrl', 'right ctrl'])
                elif key_name == 'left shift' or key_name == 'right shift':
                    key_variations.extend(['shift', 'left shift', 'right shift'])
                elif key_name == 'ctrl':
                    key_variations.extend(['left ctrl', 'right ctrl'])
                elif key_name == 'shift':
                    key_variations.extend(['left shift', 'right shift'])
                
                # If any variation of the released key is part of our hotkey, stop recording
                if any(var in self.hotkey_keys or var == 'space' for var in key_variations):
                    self._stop_recording()
    
    def _start_recording(self):
        """Start recording audio."""
        try:
            if self.on_start_recording:
                self.is_recording = True
                logger.info("Recording started (hotkey pressed)")
                self.on_start_recording()
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
    
    def _stop_recording(self):
        """Stop recording audio."""
        try:
            if self.on_stop_recording and self.is_recording:
                self.is_recording = False
                logger.info("Recording stopped (hotkey released)")
                self.on_stop_recording()
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
    
    def change_hotkey(self, new_hotkey: str) -> bool:
        """
        Change the hotkey combination.
        
        Args:
            new_hotkey: New hotkey combination
            
        Returns:
            True if hotkey was changed successfully, False otherwise
        """
        was_running = self.is_running
        
        if was_running:
            self.stop_service()
        
        try:
            # Test if the hotkey is valid
            keyboard.parse_hotkey(new_hotkey)
            self.hotkey = new_hotkey
            self._parse_hotkey()  # Re-parse the new hotkey
            
            if was_running:
                return self.start_service()
            
            logger.info(f"Hotkey changed to: {new_hotkey}")
            return True
            
        except Exception as e:
            logger.error(f"Invalid hotkey '{new_hotkey}': {e}")
            
            # Restore service if it was running
            if was_running:
                self.start_service()
            
            return False
    
    def get_hotkey(self) -> str:
        """
        Get the current hotkey combination.
        
        Returns:
            Current hotkey string
        """
        return self.hotkey
    
    def is_service_running(self) -> bool:
        """
        Check if the hotkey service is currently running.
        
        Returns:
            True if service is running, False otherwise
        """
        return self.is_running 