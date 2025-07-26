import time
import logging
from typing import Optional
import win32gui
import win32con
import win32clipboard
import win32api

logger = logging.getLogger(__name__)

class TextInserter:
    def __init__(self, insertion_delay: float = 0.1):
        """
        Initialize the text inserter.
        
        Args:
            insertion_delay: Delay between keystrokes in seconds
        """
        self.insertion_delay = insertion_delay
        
    def insert_text(self, text: str, method: str = "clipboard") -> bool:
        """
        Insert text into the currently active window.
        
        Args:
            text: Text to insert
            method: Method to use for insertion ("clipboard" or "sendkeys")
            
        Returns:
            True if insertion was successful, False otherwise
        """
        if not text:
            logger.warning("Empty text provided for insertion")
            return False
            
        try:
            if method == "clipboard":
                return self._insert_via_clipboard(text)
            elif method == "sendkeys":
                return self._insert_via_sendkeys(text)
            else:
                logger.error(f"Unknown insertion method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Text insertion failed: {e}")
            return False
    
    def _insert_via_clipboard(self, text: str) -> bool:
        """
        Insert text by copying to clipboard and pasting.
        This is generally more reliable for longer texts.
        """
        try:
            # Get the current active window
            active_window = win32gui.GetForegroundWindow()
            if not active_window:
                logger.error("No active window found")
                return False
            
            # Save current clipboard content
            original_clipboard = self._get_clipboard_text()
            
            # Copy text to clipboard
            self._set_clipboard_text(text)
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)
            
            # Send Ctrl+V to paste
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Small delay before restoring clipboard
            time.sleep(0.1)
            
            # Restore original clipboard content
            if original_clipboard is not None:
                self._set_clipboard_text(original_clipboard)
            
            logger.info(f"Text inserted via clipboard: {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"Clipboard insertion failed: {e}")
            return False
    
    def _insert_via_sendkeys(self, text: str) -> bool:
        """
        Insert text by simulating individual keystrokes.
        Better for short texts but slower for longer ones.
        """
        try:
            active_window = win32gui.GetForegroundWindow()
            if not active_window:
                logger.error("No active window found")
                return False
            
            # Send each character individually
            for char in text:
                if char == '\n':
                    # Send Enter for newlines
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                elif char == '\t':
                    # Send Tab for tabs
                    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    # Convert character to virtual key code
                    vk_code = win32api.VkKeyScan(char)
                    if vk_code != -1:
                        # Handle shift modifier for uppercase letters and symbols
                        if vk_code & 0x100:  # Shift key needed
                            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                            win32api.keybd_event(vk_code & 0xFF, 0, 0, 0)
                            win32api.keybd_event(vk_code & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)
                            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                        else:
                            win32api.keybd_event(vk_code & 0xFF, 0, 0, 0)
                            win32api.keybd_event(vk_code & 0xFF, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                # Small delay between keystrokes
                if self.insertion_delay > 0:
                    time.sleep(self.insertion_delay)
            
            logger.info(f"Text inserted via sendkeys: {len(text)} characters")
            return True
            
        except Exception as e:
            logger.error(f"SendKeys insertion failed: {e}")
            return False
    
    def _get_clipboard_text(self) -> Optional[str]:
        """Get current clipboard text content."""
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
            win32clipboard.CloseClipboard()
            return data.decode('utf-8') if isinstance(data, bytes) else data
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    
    def _set_clipboard_text(self, text: str):
        """Set clipboard text content."""
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
    
    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window.
        
        Returns:
            Window title or None if no active window
        """
        try:
            active_window = win32gui.GetForegroundWindow()
            if active_window:
                window_title = win32gui.GetWindowText(active_window)
                return window_title if window_title else None
            return None
        except Exception as e:
            logger.error(f"Failed to get active window title: {e}")
            return None 