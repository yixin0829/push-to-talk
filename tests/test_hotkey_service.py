import sys
import types
from typing import Optional
from unittest.mock import MagicMock, patch



class DummyKey:
    def __init__(self, name: Optional[str] = None):
        if name is not None:
            self.name = name


class DummyKeyCode:
    def __init__(self, char: Optional[str] = None, vk: Optional[int] = None):
        self.char = char
        self.vk = vk

    @classmethod
    def from_vk(cls, vk: int):
        return cls(vk=vk)


class DummyListener:
    def __init__(self, on_press=None, on_release=None):
        self.on_press = on_press
        self.on_release = on_release
        self._alive = False

    def start(self):  # pragma: no cover - trivial
        self._alive = True

    def stop(self):  # pragma: no cover - trivial
        self._alive = False

    def join(self, timeout=None):  # pragma: no cover - trivial
        return None

    def is_alive(self):  # pragma: no cover - trivial
        return self._alive


# Populate common key objects used by the service
Key = DummyKey
Key.ctrl = DummyKey("ctrl")
Key.shift = DummyKey("shift")
Key.space = DummyKey("space")
Key.alt = DummyKey("alt")
Key.cmd = DummyKey("cmd")
Key.ctrl_l = DummyKey("ctrl_l")
Key.ctrl_r = DummyKey("ctrl_r")
Key.shift_l = DummyKey("shift_l")
Key.shift_r = DummyKey("shift_r")
Key.cmd_l = DummyKey("cmd_l")
Key.cmd_r = DummyKey("cmd_r")

keyboard_stub = types.SimpleNamespace(
    Listener=DummyListener,
    Key=Key,
    KeyCode=DummyKeyCode,
)

sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules["pynput.keyboard"] = keyboard_stub

from src.hotkey_service import HotkeyService

pynput_keyboard = keyboard_stub


class TestHotkeyService:
    def setup_method(self):
        """Initialize a hotkey service instance for each test."""

        # Use explicit hotkeys for deterministic tests
        self.service = HotkeyService(
            hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+t"
        )

    def teardown_method(self):
        """Ensure the service is stopped after each test."""

        if getattr(self.service, "is_running", False):
            self.service.stop_service()

    def test_initialization(self):
        """Verify that initialization populates expected defaults."""

        assert self.service.hotkey == "ctrl+shift+space"
        assert self.service.toggle_hotkey == "ctrl+shift+t"
        assert self.service.hotkey_keys == {"ctrl", "shift", "space"}
        assert self.service.toggle_hotkey_keys == {"ctrl", "shift", "t"}
        assert self.service.is_running is False
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        assert self.service.service_thread is None

    def test_set_callbacks(self):
        """Callbacks should be stored for later invocation."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        assert self.service.on_start_recording is start_cb
        assert self.service.on_stop_recording is stop_cb

    def test_start_service_requires_callbacks(self):
        """Service should not start without configured callbacks."""

        assert self.service.start_service() is False
        assert self.service.is_running is False

    @patch("src.hotkey_service.threading.Thread")
    def test_start_service_success(self, mock_thread):
        """Starting the service should create and start a listener thread."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        assert self.service.start_service() is True
        assert self.service.is_running is True
        thread_instance.start.assert_called_once()

    def test_start_service_already_running(self):
        """Starting while running should be a no-op."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        self.service.is_running = True
        assert self.service.start_service() is False

    @patch("src.hotkey_service.threading.Thread", side_effect=Exception("boom"))
    def test_start_service_thread_failure(self, mock_thread):
        """Thread creation failures should be surfaced as False."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        assert self.service.start_service() is False
        assert self.service.is_running is False
        mock_thread.assert_called_once()

    def test_stop_service_when_not_running(self):
        """Stopping when idle should simply log and return."""

        self.service.stop_service()
        assert self.service.is_running is False

    def test_stop_service_cleans_state(self):
        """Stopping should terminate listener thread and clear key state."""

        self.service.is_running = True
        self.service.is_recording = True
        self.service.current_keys.update({"ctrl", "shift", "space"})
        self.service._listener = MagicMock()

        thread_mock = MagicMock()
        thread_mock.is_alive.return_value = True
        self.service.service_thread = thread_mock

        self.service.stop_service()

        self.service._listener.stop.assert_called_once()
        thread_mock.join.assert_called_once()
        assert self.service.current_keys == set()
        assert self.service.is_running is False
        assert self.service.is_recording is False

    def test_push_to_talk_flow(self):
        """Pressing and releasing the push-to-talk hotkey should start/stop recording."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)
        self.service.is_running = True

        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.Key.space)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is False
        start_cb.assert_called_once()

        self.service._on_key_release(pynput_keyboard.Key.space)
        self.service._on_key_release(pynput_keyboard.Key.shift)
        self.service._on_key_release(pynput_keyboard.Key.ctrl)

        assert self.service.is_recording is False
        stop_cb.assert_called_once()

    def test_toggle_hotkey_flow(self):
        """Toggle hotkey should start and stop recording on subsequent presses."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)
        self.service.is_running = True

        # First press starts toggle recording
        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.KeyCode(char="t"))

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True
        start_cb.assert_called_once()

        # Release without pressing again should keep recording
        self.service._on_key_release(pynput_keyboard.KeyCode(char="t"))
        self.service._on_key_release(pynput_keyboard.Key.shift)
        self.service._on_key_release(pynput_keyboard.Key.ctrl)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True

        # Second activation stops toggle mode
        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.KeyCode(char="t"))

        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        stop_cb.assert_called_once()

    def test_change_hotkey_success(self):
        """Changing the push-to-talk hotkey should update internal state."""

        assert self.service.change_hotkey("ctrl+alt+r") is True
        assert self.service.hotkey == "ctrl+alt+r"
        assert self.service.hotkey_keys == {"ctrl", "alt", "r"}

    def test_change_hotkey_invalid(self):
        """Invalid hotkeys should be rejected."""

        assert self.service.change_hotkey("") is False
        assert self.service.hotkey == "ctrl+shift+space"

    def test_change_hotkey_invalid_while_running_restores_service(self):
        """Changing to an invalid hotkey while running should restart the listener."""

        self.service.is_running = True
        with patch.object(self.service, "stop_service") as stop_mock, patch.object(
            self.service, "start_service", return_value=True
        ) as start_mock:
            assert self.service.change_hotkey(" + ") is False

        stop_mock.assert_called_once()
        start_mock.assert_called_once()
        assert self.service.hotkey == "ctrl+shift+space"

    def test_change_toggle_hotkey(self):
        """Toggle hotkey should be reconfigurable."""

        assert self.service.change_toggle_hotkey("ctrl+alt+y") is True
        assert self.service.toggle_hotkey == "ctrl+alt+y"
        assert self.service.toggle_hotkey_keys == {"ctrl", "alt", "y"}

    def test_change_toggle_hotkey_invalid(self):
        """Invalid toggle combinations should return False."""

        assert self.service.change_toggle_hotkey("") is False
        assert self.service.toggle_hotkey == "ctrl+shift+t"

    def test_change_toggle_hotkey_invalid_while_running_restores_service(self):
        """Invalid toggle combinations should stop and restart the service when running."""

        self.service.is_running = True
        with patch.object(self.service, "stop_service") as stop_mock, patch.object(
            self.service, "start_service", return_value=True
        ) as start_mock:
            assert self.service.change_toggle_hotkey(" + ") is False

        stop_mock.assert_called_once()
        start_mock.assert_called_once()
        assert self.service.toggle_hotkey == "ctrl+shift+t"

    def test_key_normalization_handles_caret(self):
        """Caret key should normalize to a canonical representation."""

        service = HotkeyService(hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+^")
        assert "caret" in service.toggle_hotkey_keys
        assert (
            service._key_to_name(pynput_keyboard.KeyCode(char="^"))
            == "caret"
        )

    def test_key_normalization_variants(self):
        """_normalize_key_name should handle whitespace, aliases, and casing."""

        normalize = HotkeyService._normalize_key_name
        assert normalize("") is None
        assert normalize(" ") is None
        assert normalize("\n") is None
        assert normalize("\t") is None
        assert normalize("Left Ctrl") == "ctrl"
        assert normalize("shift_r") == "shift"
        assert normalize("print screen") == "print_screen"
        assert normalize("custom key") == "custom_key"

    def test_parse_hotkey_combination_with_empty_parts(self):
        """Hotkey strings containing only separators should be ignored."""

        key_set = {"ctrl"}
        self.service._parse_hotkey_combination(" +  + ", key_set)
        assert key_set == set()

    def test_parse_hotkey_combination_with_unrecognized_keys(self):
        """Unknown keys should not add entries to the key set."""

        with patch.object(
            self.service, "_normalize_key_name", return_value=None
        ) as normalize_mock:
            key_set = set()
            self.service._parse_hotkey_combination("mystery", key_set)

        normalize_mock.assert_called_once()
        assert key_set == set()

    def test_parse_hotkey_compatibility_wrapper(self):
        """Legacy _parse_hotkey helper should continue to function."""

        self.service.hotkey = "ctrl+alt+space"
        self.service.hotkey_keys.clear()
        self.service._parse_hotkey()
        assert self.service.hotkey_keys == {"ctrl", "alt", "space"}

    def test_stop_service_handles_listener_stop_exceptions(self):
        """Listener.stop errors during shutdown should be suppressed."""

        self.service.is_running = True
        listener = MagicMock()
        listener.stop.side_effect = RuntimeError("boom")
        listener.join = MagicMock()
        self.service._listener = listener

        thread_mock = MagicMock()
        thread_mock.is_alive.return_value = False
        self.service.service_thread = thread_mock
        self.service.current_keys.update({"ctrl"})
        self.service._push_hotkey_active = True
        self.service._toggle_hotkey_active = True

        self.service.stop_service()

        listener.stop.assert_called_once()
        listener.join.assert_not_called()
        assert self.service.current_keys == set()
        assert self.service._push_hotkey_active is False
        assert self.service._toggle_hotkey_active is False

    def test_run_service_restarts_listener_and_cleans_state(self):
        """_run_service should restart dead listeners and reset state."""

        class FlakyListener:
            instances = []

            def __init__(self, on_press=None, on_release=None):
                self.on_press = on_press
                self.on_release = on_release
                self.stops = 0
                self.joins = 0
                self.started = False
                self._alive = False
                self.index = len(FlakyListener.instances)
                FlakyListener.instances.append(self)

            def start(self):
                self.started = True
                if self.index == 0:
                    self._alive = False
                else:
                    self._alive = True

            def stop(self):
                self.stops += 1
                self._alive = False

            def join(self, timeout=None):
                self.joins += 1

            def is_alive(self):
                return self._alive

        sleep_calls = []

        def fake_sleep(duration):
            sleep_calls.append(duration)
            if len(sleep_calls) >= 2:
                self.service.is_running = False

        self.service.current_keys.update({"ctrl"})
        self.service._push_hotkey_active = True
        self.service._toggle_hotkey_active = True

        with patch.object(pynput_keyboard, "Listener", FlakyListener), patch(
            "src.hotkey_service.time.sleep", side_effect=fake_sleep
        ):
            self.service.is_running = True
            self.service._run_service()

        first, second = FlakyListener.instances[:2]
        assert first.stops == 1
        assert first.joins == 1
        assert second.stops == 1
        assert second.joins == 1
        assert self.service.current_keys == set()
        assert self.service._push_hotkey_active is False
        assert self.service._toggle_hotkey_active is False
        assert self.service._listener is None

    def test_run_service_handles_listener_start_failures(self):
        """Listener start errors should be retried and handled safely."""

        class FailingListener:
            def __init__(self, *_, **__):
                self.start_calls = 0

            def start(self):
                self.start_calls += 1
                raise RuntimeError("listener boom")

            def stop(self):  # pragma: no cover - trivial
                pass

            def join(self, timeout=None):  # pragma: no cover - trivial
                pass

            def is_alive(self):
                return False

        def fake_sleep(_):
            self.service.is_running = False

        with patch.object(pynput_keyboard, "Listener", FailingListener), patch(
            "src.hotkey_service.time.sleep", side_effect=fake_sleep
        ):
            self.service.is_running = True
            self.service._run_service()

    def test_run_service_catches_unexpected_errors(self):
        """Unexpected errors should trigger cleanup and not propagate."""

        class StableListener:
            def __init__(self, *_, **__):
                self.stops = 0
                self.joins = 0
                self._alive = True

            def start(self):  # pragma: no cover - trivial
                pass

            def stop(self):
                self.stops += 1
                self._alive = False

            def join(self, timeout=None):
                self.joins += 1

            def is_alive(self):
                return self._alive

        self.service.current_keys.update({"ctrl"})
        self.service._push_hotkey_active = True
        self.service._toggle_hotkey_active = True

        with patch.object(pynput_keyboard, "Listener", StableListener), patch(
            "src.hotkey_service.time.sleep", side_effect=RuntimeError("sleep crash")
        ):
            self.service.is_running = True
            self.service._run_service()

        assert self.service.current_keys == set()
        assert self.service._listener is None

    def test_on_key_press_ignores_unknown_keys(self):
        """_on_key_press should ignore keys that cannot be normalized."""

        self.service.is_running = True
        with patch.object(self.service, "_key_to_name", return_value=None):
            self.service._on_key_press(object())

        assert self.service.current_keys == set()

    def test_on_key_release_ignores_unknown_keys(self):
        """_on_key_release should ignore unrecognized keys."""

        self.service.is_running = True
        with patch.object(self.service, "_key_to_name", return_value=None):
            self.service._on_key_release(object())

        assert self.service.current_keys == set()

    def test_key_to_name_from_vk_variants(self):
        """KeyCode instances with virtual keys should be normalized appropriately."""

        key = pynput_keyboard.KeyCode(vk=65)
        assert self.service._key_to_name(key) == "vk65"

        class CharKey:
            char = "x"
            name = None

        class NamedKey:
            char = None
            name = "space"

        with patch.object(pynput_keyboard.KeyCode, "from_vk", return_value=CharKey()):
            key = pynput_keyboard.KeyCode(vk=70)
            assert self.service._key_to_name(key) == "x"

        with patch.object(pynput_keyboard.KeyCode, "from_vk", return_value=NamedKey()):
            key = pynput_keyboard.KeyCode(vk=71)
            assert self.service._key_to_name(key) == "space"

        with patch.object(
            pynput_keyboard.KeyCode, "from_vk", side_effect=RuntimeError("fail")
        ):
            key = pynput_keyboard.KeyCode(vk=72)
            assert self.service._key_to_name(key) == "vk72"

    def test_key_to_name_with_generic_objects(self):
        """Objects with name or char attributes should be normalized."""

        custom = types.SimpleNamespace(name="My Key")
        assert self.service._key_to_name(custom) == "my_key"

        char_obj = types.SimpleNamespace(char="Z")
        assert self.service._key_to_name(char_obj) == "z"

        assert self.service._key_to_name(object()) is None

        with patch.object(
            self.service, "_normalize_key_name", side_effect=RuntimeError("boom")
        ):
            assert self.service._key_to_name(pynput_keyboard.Key.space) is None

    def test_are_keys_active_with_empty_requirements(self):
        """_are_keys_active should return False when no keys are required."""

        assert self.service._are_keys_active(set()) is False

    def test_start_recording_exception_resets_state(self):
        """Errors in the start callback should reset recording flags."""

        self.service.on_start_recording = MagicMock(side_effect=RuntimeError("boom"))
        self.service._start_recording(toggle_mode=True)
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False

    def test_stop_recording_exception_is_swallowed(self):
        """Errors during stop should be handled gracefully."""

        self.service.is_recording = True
        self.service.is_toggle_mode = True
        self.service.on_stop_recording = MagicMock(side_effect=RuntimeError("boom"))
        self.service._stop_recording()
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False

    def test_change_hotkey_while_running(self):
        """Changing the push-to-talk hotkey while running should restart the service."""

        self.service.is_running = True
        with patch.object(self.service, "stop_service") as stop_mock, patch.object(
            self.service, "start_service", return_value=True
        ) as start_mock:
            assert self.service.change_hotkey("ctrl+alt+k") is True

        stop_mock.assert_called_once()
        start_mock.assert_called_once()
        assert self.service.hotkey == "ctrl+alt+k"
        assert self.service.hotkey_keys == {"ctrl", "alt", "k"}

    def test_change_toggle_hotkey_while_running(self):
        """Changing the toggle hotkey while running should restart the service."""

        self.service.is_running = True
        with patch.object(self.service, "stop_service") as stop_mock, patch.object(
            self.service, "start_service", return_value=True
        ) as start_mock:
            assert self.service.change_toggle_hotkey("ctrl+alt+u") is True

        stop_mock.assert_called_once()
        start_mock.assert_called_once()
        assert self.service.toggle_hotkey == "ctrl+alt+u"
        assert self.service.toggle_hotkey_keys == {"ctrl", "alt", "u"}

    def test_accessor_helpers(self):
        """Getter helpers should expose the current configuration."""

        assert self.service.get_hotkey() == "ctrl+shift+space"
        assert self.service.get_toggle_hotkey() == "ctrl+shift+t"
        assert self.service.is_toggle_recording() is False

        self.service.is_recording = True
        self.service.is_toggle_mode = True
        assert self.service.is_toggle_recording() is True

    def test_is_service_running_property(self):
        """Helper accessor should reflect running state."""

        assert self.service.is_service_running() is False
        self.service.is_running = True
        assert self.service.is_service_running() is True

    def test_get_recording_mode(self):
        """Recording mode helper should reflect toggle state."""

        assert self.service.get_recording_mode() == "idle"
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        assert self.service.get_recording_mode() == "push-to-talk"
        self.service.is_toggle_mode = True
        assert self.service.get_recording_mode() == "toggle"


class TestHotkeyServicePlatformSupport:
    @patch("sys.platform", "darwin")
    def test_macos_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "cmd+shift+space"
        assert service.toggle_hotkey == "cmd+shift+^"
        assert HotkeyService.get_platform_name() == "macOS"
        assert HotkeyService.get_platform_modifier_key() == "cmd"

    @patch("sys.platform", "win32")
    def test_windows_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+space"
        assert service.toggle_hotkey == "ctrl+shift+^"
        assert HotkeyService.get_platform_name() == "Windows"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"

    @patch("sys.platform", "linux")
    def test_linux_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+space"
        assert service.toggle_hotkey == "ctrl+shift+^"
        assert HotkeyService.get_platform_name() == "Linux"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"

    @patch("sys.platform", "freebsd")
    def test_unknown_platform_name_and_defaults(self):
        assert HotkeyService.get_platform_name() == "freebsd"
        assert HotkeyService.get_platform_default_hotkey().endswith("space")
        assert HotkeyService.get_platform_default_toggle_hotkey().endswith("^")
