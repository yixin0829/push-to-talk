import sys
import logging
from unittest.mock import patch, MagicMock
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from text_inserter import TextInserter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestTextInserter:
    def setup_method(self):
        """Setup for each test method"""
        logger.info("Setting up TextInserter test")
        self.inserter = TextInserter(insertion_delay=0.1)

    def test_initialization(self):
        """Test TextInserter initialization"""
        logger.info("Testing TextInserter initialization")

        assert self.inserter.insertion_delay == 0.1

        logger.info("TextInserter initialization test passed")

    def test_custom_initialization(self):
        """Test TextInserter with custom parameters"""
        logger.info("Testing TextInserter custom initialization")

        custom_inserter = TextInserter(insertion_delay=0.05)

        assert custom_inserter.insertion_delay == 0.05

        logger.info("TextInserter custom initialization test passed")

    def test_insert_text_empty(self):
        """Test inserting empty text"""
        logger.info("Testing insert empty text")

        result = self.inserter.insert_text("")

        assert result is False

        logger.info("Insert empty text test passed")

    def test_insert_text_none(self):
        """Test inserting None text"""
        logger.info("Testing insert None text")

        result = self.inserter.insert_text(None)

        assert result is False

        logger.info("Insert None text test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    def test_insert_via_clipboard_success(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test successful text insertion via clipboard"""
        logger.info("Testing successful clipboard insertion")

        mock_paste.return_value = "original clipboard content"

        result = self.inserter.insert_text("Hello, World!", method="clipboard")

        assert result is True

        # Verify clipboard operations
        mock_paste.assert_called()  # Get original content
        mock_copy.assert_any_call("Hello, World!")  # Set our text
        mock_copy.assert_any_call("original clipboard content")  # Restore original

        # Verify paste operation
        mock_hotkey.assert_called_once()

        # Verify sleep calls for timing
        assert mock_sleep.call_count >= 2

        logger.info("Clipboard insertion success test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    @patch("sys.platform", "darwin")
    def test_insert_via_clipboard_macos(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test clipboard insertion on macOS (different hotkey)"""
        logger.info("Testing clipboard insertion on macOS")

        mock_paste.return_value = "original content"

        result = self.inserter.insert_text("macOS text", method="clipboard")

        assert result is True

        # Verify macOS hotkey (Command+V instead of Ctrl+V)
        mock_hotkey.assert_called_once_with("command", "v")

        logger.info("Clipboard insertion macOS test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    @patch("sys.platform", "win32")
    def test_insert_via_clipboard_windows(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test clipboard insertion on Windows"""
        logger.info("Testing clipboard insertion on Windows")

        mock_paste.return_value = "original content"

        result = self.inserter.insert_text("Windows text", method="clipboard")

        assert result is True

        # Verify Windows hotkey (Ctrl+V)
        mock_hotkey.assert_called_once_with("ctrl", "v")

        logger.info("Clipboard insertion Windows test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    def test_insert_via_clipboard_exception(self, mock_hotkey, mock_copy, mock_paste):
        """Test clipboard insertion with exception"""
        logger.info("Testing clipboard insertion with exception")

        mock_paste.side_effect = Exception("Clipboard access failed")

        result = self.inserter.insert_text("Text with error", method="clipboard")

        assert result is False

        logger.info("Clipboard insertion exception test passed")

    @patch("pyautogui.write")
    def test_insert_via_sendkeys_success(self, mock_write):
        """Test successful text insertion via sendkeys"""
        logger.info("Testing successful sendkeys insertion")

        result = self.inserter.insert_text("Hello SendKeys!", method="sendkeys")

        assert result is True

        # Verify pyautogui.write was called with correct parameters
        mock_write.assert_called_once_with("Hello SendKeys!", interval=0.1)

        logger.info("SendKeys insertion success test passed")

    @patch("pyautogui.write")
    def test_insert_via_sendkeys_exception(self, mock_write):
        """Test sendkeys insertion with exception"""
        logger.info("Testing sendkeys insertion with exception")

        mock_write.side_effect = Exception("SendKeys failed")

        result = self.inserter.insert_text("Error text", method="sendkeys")

        assert result is False

        logger.info("SendKeys insertion exception test passed")

    def test_insert_text_invalid_method(self):
        """Test insertion with invalid method"""
        logger.info("Testing insertion with invalid method")

        result = self.inserter.insert_text("Test text", method="invalid_method")

        assert result is False

        logger.info("Insert text invalid method test passed")

    def test_insert_text_default_method(self):
        """Test insertion with default method (clipboard)"""
        logger.info("Testing insertion with default method")

        with patch.object(self.inserter, "_insert_via_clipboard") as mock_clipboard:
            mock_clipboard.return_value = True

            result = self.inserter.insert_text("Default method test")

            assert result is True
            mock_clipboard.assert_called_once_with("Default method test")

        logger.info("Insert text default method test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    def test_clipboard_restoration_no_original(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test clipboard restoration when there was no original content"""
        logger.info("Testing clipboard restoration with no original content")

        mock_paste.return_value = None  # No original clipboard content

        result = self.inserter.insert_text("New text", method="clipboard")

        assert result is True

        # Verify our text was copied
        mock_copy.assert_any_call("New text")

        # Verify that restoration was attempted (even with None)
        call_args_list = mock_copy.call_args_list
        assert len(call_args_list) >= 1

        logger.info("Clipboard restoration no original test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    def test_clipboard_restoration_empty_original(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test clipboard restoration when original content is empty"""
        logger.info("Testing clipboard restoration with empty original content")

        mock_paste.return_value = ""  # Empty original clipboard content

        result = self.inserter.insert_text("New text", method="clipboard")

        assert result is True

        # Should not attempt to restore empty clipboard
        mock_copy.assert_called_once_with("New text")

        logger.info("Clipboard restoration empty original test passed")

    @patch("pyperclip.paste")
    def test_get_clipboard_text(self, mock_paste):
        """Test getting clipboard text"""
        logger.info("Testing get clipboard text")

        mock_paste.return_value = "clipboard content"

        result = self.inserter._get_clipboard_text()

        assert result == "clipboard content"
        mock_paste.assert_called_once()

        logger.info("Get clipboard text test passed")

    @patch("pyperclip.paste")
    def test_get_clipboard_text_exception(self, mock_paste):
        """Test getting clipboard text with exception"""
        logger.info("Testing get clipboard text with exception")

        mock_paste.side_effect = Exception("Cannot access clipboard")

        result = self.inserter._get_clipboard_text()

        assert result is None

        logger.info("Get clipboard text exception test passed")

    @patch("pyperclip.copy")
    def test_set_clipboard_text(self, mock_copy):
        """Test setting clipboard text"""
        logger.info("Testing set clipboard text")

        self.inserter._set_clipboard_text("test content")

        mock_copy.assert_called_once_with("test content")

        logger.info("Set clipboard text test passed")

    @patch("pyautogui.getActiveWindow")
    def test_get_active_window_title_success(self, mock_get_window):
        """Test getting active window title successfully"""
        logger.info("Testing get active window title success")

        mock_window = MagicMock()
        mock_window.title = "Test Window Title"
        mock_get_window.return_value = mock_window

        result = self.inserter.get_active_window_title()

        assert result == "Test Window Title"

        logger.info("Get active window title success test passed")

    @patch("pyautogui.getActiveWindow")
    def test_get_active_window_title_no_window(self, mock_get_window):
        """Test getting active window title when no window is active"""
        logger.info("Testing get active window title with no window")

        mock_get_window.return_value = None

        result = self.inserter.get_active_window_title()

        assert result is None

        logger.info("Get active window title no window test passed")

    @patch("pyautogui.getActiveWindow")
    def test_get_active_window_title_no_title(self, mock_get_window):
        """Test getting active window title when window has no title"""
        logger.info("Testing get active window title with no title")

        mock_window = MagicMock()
        mock_window.title = None
        mock_get_window.return_value = mock_window

        result = self.inserter.get_active_window_title()

        assert result is None

        logger.info("Get active window title no title test passed")

    @patch("pyautogui.getActiveWindow")
    def test_get_active_window_title_empty_title(self, mock_get_window):
        """Test getting active window title when window has empty title"""
        logger.info("Testing get active window title with empty title")

        mock_window = MagicMock()
        mock_window.title = ""
        mock_get_window.return_value = mock_window

        result = self.inserter.get_active_window_title()

        assert result is None

        logger.info("Get active window title empty title test passed")

    @patch("pyautogui.getActiveWindow")
    def test_get_active_window_title_exception(self, mock_get_window):
        """Test getting active window title with exception"""
        logger.info("Testing get active window title with exception")

        mock_get_window.side_effect = Exception("Cannot get active window")

        result = self.inserter.get_active_window_title()

        assert result is None

        logger.info("Get active window title exception test passed")

    def test_insertion_delay_custom_value(self):
        """Test that insertion delay is properly used"""
        logger.info("Testing insertion delay custom value")

        custom_inserter = TextInserter(insertion_delay=0.05)

        with patch("pyautogui.write") as mock_write:
            custom_inserter.insert_text("Delay test", method="sendkeys")

            # Verify the custom delay was used
            mock_write.assert_called_once_with("Delay test", interval=0.05)

        logger.info("Insertion delay custom value test passed")

    @patch("pyperclip.paste")
    @patch("pyperclip.copy")
    @patch("pyautogui.hotkey")
    @patch("time.sleep")
    def test_insert_text_general_exception(
        self, mock_sleep, mock_hotkey, mock_copy, mock_paste
    ):
        """Test general exception handling in insert_text"""
        logger.info("Testing general exception handling in insert_text")

        # Mock an exception in the main insert_text logic
        mock_paste.side_effect = Exception("General insertion failure")

        result = self.inserter.insert_text("Test text", method="clipboard")

        assert result is False

        logger.info("Insert text general exception test passed")
