import logging
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hotkey_service import HotkeyService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestHotkeyService:
    def setup_method(self):
        """Setup for each test method"""
        logger.info("Setting up HotkeyService test")
        self.service = HotkeyService(
            hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+t"
        )

    def teardown_method(self):
        """Cleanup after each test method"""
        logger.info("Tearing down HotkeyService test")
        if hasattr(self.service, "is_running") and self.service.is_running:
            self.service.stop_service()

    def test_initialization(self):
        """Test HotkeyService initialization"""
        logger.info("Testing HotkeyService initialization")

        assert self.service.hotkey == "ctrl+shift+space"
        assert self.service.toggle_hotkey == "ctrl+shift+t"
        assert self.service.is_running is False
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        assert self.service.service_thread is None
        assert self.service.on_start_recording is None
        assert self.service.on_stop_recording is None

        logger.info("HotkeyService initialization test passed")

    def test_custom_initialization(self):
        """Test HotkeyService with custom hotkeys"""
        logger.info("Testing HotkeyService custom initialization")

        custom_service = HotkeyService(hotkey="ctrl+alt+r", toggle_hotkey="ctrl+alt+t")

        assert custom_service.hotkey == "ctrl+alt+r"
        assert custom_service.toggle_hotkey == "ctrl+alt+t"

        logger.info("HotkeyService custom initialization test passed")

    @patch("keyboard.parse_hotkey")
    def test_parse_hotkeys_success(self, mock_parse):
        """Test successful hotkey parsing"""
        logger.info("Testing successful hotkey parsing")

        # Mock parse_hotkey to return a structure representing the key combination
        mock_key1 = MagicMock()
        mock_key1.name = "ctrl"
        mock_key2 = MagicMock()
        mock_key2.name = "shift"
        mock_key3 = MagicMock()
        mock_key3.name = "space"

        mock_parse.return_value = [[mock_key1, mock_key2, mock_key3]]

        HotkeyService("ctrl+shift+space")

        mock_parse.assert_called()
        # Should have parsed both hotkeys
        assert mock_parse.call_count >= 2

        logger.info("Parse hotkeys success test passed")

    @patch("keyboard.parse_hotkey")
    def test_parse_hotkeys_fallback(self, mock_parse):
        """Test hotkey parsing fallback for common combinations"""
        logger.info("Testing hotkey parsing fallback")

        # Mock parse_hotkey to fail
        mock_parse.side_effect = Exception("Parse failed")

        service = HotkeyService("ctrl+shift+space", "ctrl+shift+t")

        # Should have fallback keys for common combinations
        assert "ctrl" in service.hotkey_keys or "space" in service.hotkey_keys

        logger.info("Parse hotkeys fallback test passed")

    def test_set_callbacks(self):
        """Test setting callback functions"""
        logger.info("Testing setting callback functions")

        start_callback = MagicMock()
        stop_callback = MagicMock()

        self.service.set_callbacks(start_callback, stop_callback)

        assert self.service.on_start_recording == start_callback
        assert self.service.on_stop_recording == stop_callback

        logger.info("Set callbacks test passed")

    def test_start_service_no_callbacks(self):
        """Test starting service without callbacks"""
        logger.info("Testing start service without callbacks")

        result = self.service.start_service()

        assert result is False
        assert self.service.is_running is False

        logger.info("Start service no callbacks test passed")

    @patch("threading.Thread")
    def test_start_service_success(self, mock_thread):
        """Test successful service start"""
        logger.info("Testing successful service start")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        result = self.service.start_service()

        assert result is True
        assert self.service.is_running is True
        mock_thread_instance.start.assert_called_once()

        logger.info("Start service success test passed")

    def test_start_service_already_running(self):
        """Test starting service when already running"""
        logger.info("Testing start service when already running")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        # Manually set running state
        self.service.is_running = True

        result = self.service.start_service()

        assert result is False

        logger.info("Start service already running test passed")

    @patch("threading.Thread")
    def test_start_service_exception(self, mock_thread):
        """Test service start with exception"""
        logger.info("Testing service start with exception")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        mock_thread.side_effect = Exception("Thread creation failed")

        result = self.service.start_service()

        assert result is False
        assert self.service.is_running is False

        logger.info("Start service exception test passed")

    @patch("keyboard.unhook_all")
    def test_stop_service_not_running(self, mock_unhook):
        """Test stopping service when not running"""
        logger.info("Testing stop service when not running")

        self.service.stop_service()

        # Should not call unhook since service wasn't running
        mock_unhook.assert_not_called()

        logger.info("Stop service not running test passed")

    @patch("keyboard.unhook_all")
    def test_stop_service_success(self, mock_unhook):
        """Test successful service stop"""
        logger.info("Testing successful service stop")

        # Set up running service
        self.service.is_running = True
        self.service.is_recording = True

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        self.service.service_thread = mock_thread

        self.service.stop_service()

        assert self.service.is_running is False
        mock_unhook.assert_called_once()
        mock_thread.join.assert_called_once()

        logger.info("Stop service success test passed")

    @patch("keyboard.unhook_all")
    def test_stop_service_unhook_exception(self, mock_unhook):
        """Test service stop with unhook exception"""
        logger.info("Testing service stop with unhook exception")

        self.service.is_running = True
        mock_unhook.side_effect = Exception("Unhook failed")

        # Should handle exception gracefully
        self.service.stop_service()

        assert self.service.is_running is False

        logger.info("Stop service unhook exception test passed")

    def test_on_hotkey_press_not_recording(self):
        """Test hotkey press when not recording"""
        logger.info("Testing hotkey press when not recording")

        self.service.is_running = True
        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._on_hotkey_press()

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is False
        start_callback.assert_called_once()

        logger.info("Hotkey press not recording test passed")

    def test_on_hotkey_press_already_recording(self):
        """Test hotkey press when already recording"""
        logger.info("Testing hotkey press when already recording")

        self.service.is_running = True
        self.service.is_recording = True
        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._on_hotkey_press()

        # Should not start recording again
        start_callback.assert_not_called()

        logger.info("Hotkey press already recording test passed")

    def test_on_toggle_hotkey_press_start_recording(self):
        """Test toggle hotkey press to start recording"""
        logger.info("Testing toggle hotkey press to start recording")

        self.service.is_running = True
        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._on_toggle_hotkey_press()

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True
        start_callback.assert_called_once()

        logger.info("Toggle hotkey press start recording test passed")

    def test_on_toggle_hotkey_press_stop_recording(self):
        """Test toggle hotkey press to stop recording"""
        logger.info("Testing toggle hotkey press to stop recording")

        self.service.is_running = True
        self.service.is_recording = True
        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._on_toggle_hotkey_press()

        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        stop_callback.assert_called_once()

        logger.info("Toggle hotkey press stop recording test passed")

    def test_on_toggle_hotkey_press_not_running(self):
        """Test toggle hotkey press when service not running"""
        logger.info("Testing toggle hotkey press when service not running")

        self.service.is_running = False
        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._on_toggle_hotkey_press()

        # Should not do anything
        start_callback.assert_not_called()
        stop_callback.assert_not_called()

        logger.info("Toggle hotkey press not running test passed")

    def test_on_key_release_push_to_talk_mode(self):
        """Test key release in push-to-talk mode"""
        logger.info("Testing key release in push-to-talk mode")

        self.service.is_running = True
        self.service.is_recording = True
        self.service.is_toggle_mode = False  # Push-to-talk mode
        self.service.hotkey_keys = {"ctrl", "shift", "space"}

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        # Mock key release event
        mock_event = MagicMock()
        mock_event.name = "space"

        self.service._on_key_release(mock_event)

        assert self.service.is_recording is False
        stop_callback.assert_called_once()

        logger.info("Key release push-to-talk mode test passed")

    def test_on_key_release_toggle_mode(self):
        """Test key release in toggle mode (should not stop)"""
        logger.info("Testing key release in toggle mode")

        self.service.is_running = True
        self.service.is_recording = True
        self.service.is_toggle_mode = True  # Toggle mode

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        # Mock key release event
        mock_event = MagicMock()
        mock_event.name = "space"

        self.service._on_key_release(mock_event)

        # Should not stop recording in toggle mode
        assert self.service.is_recording is True
        stop_callback.assert_not_called()

        logger.info("Key release toggle mode test passed")

    def test_on_key_release_not_hotkey(self):
        """Test key release for non-hotkey key"""
        logger.info("Testing key release for non-hotkey key")

        self.service.is_running = True
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        self.service.hotkey_keys = {"ctrl", "shift", "space"}

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        # Mock key release event for non-hotkey
        mock_event = MagicMock()
        mock_event.name = "a"  # Not part of hotkey

        self.service._on_key_release(mock_event)

        # Should not stop recording
        assert self.service.is_recording is True
        stop_callback.assert_not_called()

        logger.info("Key release not hotkey test passed")

    def test_on_key_release_ctrl_variations(self):
        """Test key release with ctrl key variations"""
        logger.info("Testing key release with ctrl key variations")

        self.service.is_running = True
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        self.service.hotkey_keys = {"ctrl", "shift", "space"}

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        # Test left ctrl
        mock_event = MagicMock()
        mock_event.name = "left ctrl"

        self.service._on_key_release(mock_event)

        assert self.service.is_recording is False
        stop_callback.assert_called_once()

        logger.info("Key release ctrl variations test passed")

    def test_start_recording_push_to_talk(self):
        """Test starting recording in push-to-talk mode"""
        logger.info("Testing start recording push-to-talk mode")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._start_recording(toggle_mode=False)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is False
        start_callback.assert_called_once()

        logger.info("Start recording push-to-talk test passed")

    def test_start_recording_toggle_mode(self):
        """Test starting recording in toggle mode"""
        logger.info("Testing start recording toggle mode")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._start_recording(toggle_mode=True)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True
        start_callback.assert_called_once()

        logger.info("Start recording toggle mode test passed")

    def test_start_recording_exception(self):
        """Test start recording with exception"""
        logger.info("Testing start recording with exception")

        start_callback = MagicMock()
        start_callback.side_effect = Exception("Start recording failed")
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._start_recording()

        # Should handle exception and reset state
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False

        logger.info("Start recording exception test passed")

    def test_stop_recording_success(self):
        """Test successful stop recording"""
        logger.info("Testing successful stop recording")

        self.service.is_recording = True
        self.service.is_toggle_mode = True

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._stop_recording()

        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        stop_callback.assert_called_once()

        logger.info("Stop recording success test passed")

    def test_stop_recording_not_recording(self):
        """Test stop recording when not recording"""
        logger.info("Testing stop recording when not recording")

        start_callback = MagicMock()
        stop_callback = MagicMock()
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._stop_recording()

        stop_callback.assert_not_called()

        logger.info("Stop recording not recording test passed")

    def test_stop_recording_exception(self):
        """Test stop recording with exception"""
        logger.info("Testing stop recording with exception")

        self.service.is_recording = True

        start_callback = MagicMock()
        stop_callback = MagicMock()
        stop_callback.side_effect = Exception("Stop recording failed")
        self.service.set_callbacks(start_callback, stop_callback)

        self.service._stop_recording()

        # Should handle exception gracefully
        stop_callback.assert_called_once()

        logger.info("Stop recording exception test passed")

    @patch("keyboard.parse_hotkey")
    def test_change_hotkey_success(self, mock_parse):
        """Test successful hotkey change"""
        logger.info("Testing successful hotkey change")

        mock_parse.return_value = [[]]  # Valid parse result

        result = self.service.change_hotkey("ctrl+alt+r")

        assert result is True
        assert self.service.hotkey == "ctrl+alt+r"

        logger.info("Change hotkey success test passed")

    @patch("keyboard.parse_hotkey")
    def test_change_hotkey_invalid(self, mock_parse):
        """Test hotkey change with invalid hotkey"""
        logger.info("Testing hotkey change with invalid hotkey")

        mock_parse.side_effect = Exception("Invalid hotkey")

        original_hotkey = self.service.hotkey
        result = self.service.change_hotkey("invalid-hotkey")

        assert result is False
        assert self.service.hotkey == original_hotkey

        logger.info("Change hotkey invalid test passed")

    @patch("keyboard.parse_hotkey")
    def test_change_toggle_hotkey_success(self, mock_parse):
        """Test successful toggle hotkey change"""
        logger.info("Testing successful toggle hotkey change")

        mock_parse.return_value = [[]]  # Valid parse result

        result = self.service.change_toggle_hotkey("ctrl+alt+x")

        assert result is True
        assert self.service.toggle_hotkey == "ctrl+alt+x"

        logger.info("Change toggle hotkey success test passed")

    def test_get_hotkey(self):
        """Test getting current hotkey"""
        logger.info("Testing get hotkey")

        hotkey = self.service.get_hotkey()

        assert hotkey == "ctrl+shift+space"

        logger.info("Get hotkey test passed")

    def test_get_toggle_hotkey(self):
        """Test getting current toggle hotkey"""
        logger.info("Testing get toggle hotkey")

        toggle_hotkey = self.service.get_toggle_hotkey()

        assert toggle_hotkey == "ctrl+shift+t"

        logger.info("Get toggle hotkey test passed")

    def test_is_toggle_recording(self):
        """Test checking if in toggle recording mode"""
        logger.info("Testing is toggle recording")

        # Not recording
        assert self.service.is_toggle_recording() is False

        # Recording in push-to-talk mode
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        assert self.service.is_toggle_recording() is False

        # Recording in toggle mode
        self.service.is_toggle_mode = True
        assert self.service.is_toggle_recording() is True

        logger.info("Is toggle recording test passed")

    def test_get_recording_mode(self):
        """Test getting recording mode"""
        logger.info("Testing get recording mode")

        # Not recording
        assert self.service.get_recording_mode() == "idle"

        # Recording in push-to-talk mode
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        assert self.service.get_recording_mode() == "push-to-talk"

        # Recording in toggle mode
        self.service.is_toggle_mode = True
        assert self.service.get_recording_mode() == "toggle"

        logger.info("Get recording mode test passed")

    def test_is_service_running(self):
        """Test checking if service is running"""
        logger.info("Testing is service running")

        assert self.service.is_service_running() is False

        self.service.is_running = True
        assert self.service.is_service_running() is True

        logger.info("Is service running test passed")

    @patch("keyboard.add_hotkey")
    @patch("keyboard.on_release")
    @patch("time.sleep")
    def test_run_service_loop(self, mock_sleep, mock_on_release, mock_add_hotkey):
        """Test the main service loop"""
        logger.info("Testing main service loop")

        self.service.is_running = True

        # Mock sleep to break the loop after a few iterations
        call_count = [0]

        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] >= 3:  # Break after 3 iterations
                self.service.is_running = False

        mock_sleep.side_effect = side_effect

        self.service._run_service()

        # Verify hotkeys were registered
        mock_add_hotkey.assert_any_call(
            self.service.hotkey, self.service._on_hotkey_press
        )
        mock_add_hotkey.assert_any_call(
            self.service.toggle_hotkey, self.service._on_toggle_hotkey_press
        )
        mock_on_release.assert_called_once()

        # Verify sleep was called (service loop ran)
        assert mock_sleep.call_count >= 1

        logger.info("Main service loop test passed")

    @patch("keyboard.add_hotkey")
    @patch("keyboard.on_release")
    @patch("keyboard.unhook_all")
    def test_run_service_exception(self, mock_unhook, mock_on_release, mock_add_hotkey):
        """Test service loop with exception"""
        logger.info("Testing service loop with exception")

        self.service.is_running = True
        mock_add_hotkey.side_effect = Exception("Hotkey registration failed")

        self.service._run_service()

        # Should call cleanup even after exception
        mock_unhook.assert_called_once()

        logger.info("Service loop exception test passed")
