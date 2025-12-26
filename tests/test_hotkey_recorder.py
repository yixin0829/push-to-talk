"""Tests for HotkeyRecorder class."""

import sys
import types
from unittest.mock import MagicMock


from tests.test_helpers import DummyKey, DummyKeyCode, create_keyboard_stub

# Setup keyboard stub for pynput imports
keyboard_stub = create_keyboard_stub()
sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules["pynput.keyboard"] = keyboard_stub

from src.gui.hotkey_recorder import HotkeyRecorder, MODIFIER_ORDER  # noqa: E402


class TestHotkeyRecorder:
    """Tests for the HotkeyRecorder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.on_complete = MagicMock()
        self.on_cancelled = MagicMock()
        self.on_keys_changed = MagicMock()

        self.recorder = HotkeyRecorder(
            on_recording_complete=self.on_complete,
            on_recording_cancelled=self.on_cancelled,
            on_keys_changed=self.on_keys_changed,
        )

    def teardown_method(self):
        """Clean up after each test."""
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def test_initialization(self):
        """Recorder should initialize in idle state."""
        assert self.recorder.is_recording is False
        assert self.recorder._listener is None

    def test_start_recording_success(self):
        """Starting recording should create listener and change state."""
        result = self.recorder.start_recording()

        assert result is True
        assert self.recorder.is_recording is True
        assert self.recorder._listener is not None

    def test_start_recording_already_recording(self):
        """Starting while already recording should return False."""
        self.recorder.start_recording()
        result = self.recorder.start_recording()

        assert result is False

    def test_stop_recording_cleans_up(self):
        """Stopping recording should clean up resources."""
        self.recorder.start_recording()
        self.recorder.stop_recording()

        assert self.recorder.is_recording is False
        assert self.recorder._listener is None

    def test_single_key_press(self):
        """Single key press should be captured and reported."""
        self.recorder.start_recording()

        # Simulate key press
        key = DummyKey("f12")
        self.recorder._on_key_press(key)

        self.on_keys_changed.assert_called_with("f12")

    def test_modifier_combination(self):
        """Modifier combination should be captured in correct order."""
        self.recorder.start_recording()

        # Simulate pressing ctrl+shift+space
        self.recorder._on_key_press(DummyKey("shift"))
        self.recorder._on_key_press(DummyKey("ctrl"))
        self.recorder._on_key_press(DummyKey("space"))

        # Check last call has all keys in correct order
        last_call = self.on_keys_changed.call_args_list[-1]
        assert last_call[0][0] == "ctrl+shift+space"

    def test_escape_cancels_recording(self):
        """Pressing Escape should cancel recording."""
        self.recorder.start_recording()

        # Simulate pressing Escape
        self.recorder._on_key_press(DummyKey("esc"))

        assert self.recorder.is_recording is False
        self.on_cancelled.assert_called_once()

    def test_key_release_triggers_finalization(self):
        """Releasing all keys should trigger finalization after delay."""
        self.recorder.start_recording()

        # Simulate pressing and releasing a key
        key = DummyKey("f12")
        self.recorder._on_key_press(key)
        self.recorder._on_key_release(key)

        # Manually trigger finalization (normally happens after delay)
        self.recorder._finalize_recording()

        self.on_complete.assert_called_with("f12")

    def test_format_hotkey_string_modifiers_first(self):
        """Modifiers should appear before regular keys."""
        keys = {"space", "ctrl", "shift"}
        result = HotkeyRecorder._format_hotkey_string(keys)

        assert result == "ctrl+shift+space"

    def test_format_hotkey_string_modifier_order(self):
        """Modifiers should be in predefined order: ctrl, alt, shift, cmd."""
        keys = {"cmd", "shift", "alt", "ctrl", "a"}
        result = HotkeyRecorder._format_hotkey_string(keys)

        # Should follow MODIFIER_ORDER
        assert result == "ctrl+alt+shift+cmd+a"

    def test_format_hotkey_string_single_key(self):
        """Single key should format correctly."""
        keys = {"f12"}
        result = HotkeyRecorder._format_hotkey_string(keys)

        assert result == "f12"

    def test_format_hotkey_string_empty(self):
        """Empty set should return empty string."""
        result = HotkeyRecorder._format_hotkey_string(set())

        assert result == ""

    def test_format_hotkey_string_regular_keys_sorted(self):
        """Regular keys should be sorted alphabetically."""
        keys = {"z", "a", "m"}
        result = HotkeyRecorder._format_hotkey_string(keys)

        assert result == "a+m+z"

    def test_keycode_with_char(self):
        """KeyCode with char should be normalized."""
        self.recorder.start_recording()

        key = DummyKeyCode(char="a")
        self.recorder._on_key_press(key)

        self.on_keys_changed.assert_called_with("a")

    def test_keycode_with_vk(self):
        """KeyCode with only vk should fall back to vk format."""
        self.recorder.start_recording()

        key = DummyKeyCode(vk=65)  # Virtual key code
        self.recorder._on_key_press(key)

        # Should be called with some key representation
        assert self.on_keys_changed.called

    def test_multiple_modifiers_captured(self):
        """Multiple modifier keys should all be captured."""
        self.recorder.start_recording()

        self.recorder._on_key_press(DummyKey("ctrl"))
        self.recorder._on_key_press(DummyKey("alt"))

        last_call = self.on_keys_changed.call_args_list[-1]
        assert last_call[0][0] == "ctrl+alt"

    def test_key_release_removes_from_current(self):
        """Releasing a key should remove it from current set."""
        self.recorder.start_recording()

        ctrl_key = DummyKey("ctrl")
        space_key = DummyKey("space")

        self.recorder._on_key_press(ctrl_key)
        self.recorder._on_key_press(space_key)
        self.recorder._on_key_release(ctrl_key)

        # Current keys should only have space
        assert "ctrl" not in self.recorder._current_keys
        assert "space" in self.recorder._current_keys

    def test_captured_keys_preserved_after_release(self):
        """Captured keys should be preserved even after partial release."""
        self.recorder.start_recording()

        ctrl_key = DummyKey("ctrl")
        space_key = DummyKey("space")

        self.recorder._on_key_press(ctrl_key)
        self.recorder._on_key_press(space_key)
        self.recorder._on_key_release(ctrl_key)

        # Captured keys should still have both
        assert "ctrl" in self.recorder._captured_keys
        assert "space" in self.recorder._captured_keys

    def test_finalization_uses_captured_keys(self):
        """Finalization should use captured keys, not current keys."""
        self.recorder.start_recording()

        ctrl_key = DummyKey("ctrl")
        space_key = DummyKey("space")

        self.recorder._on_key_press(ctrl_key)
        self.recorder._on_key_press(space_key)
        self.recorder._on_key_release(ctrl_key)
        self.recorder._on_key_release(space_key)

        # Manually trigger finalization
        self.recorder._finalize_recording()

        self.on_complete.assert_called_with("ctrl+space")

    def test_shift_number_converted_to_symbol(self):
        """Shift+number should be converted to symbol (e.g., shift+6 -> ^)."""
        self.recorder.start_recording()

        # Simulate Ctrl+Shift+6
        self.recorder._on_key_press(DummyKey("ctrl"))
        self.recorder._on_key_press(DummyKey("shift"))
        self.recorder._on_key_press(DummyKeyCode(char="6"))

        # Finalize and check result - 6 should become ^
        self.recorder._finalize_recording()
        self.on_complete.assert_called_with("ctrl+shift+^")

    def test_shift_1_converted_to_exclamation(self):
        """Shift+1 should be converted to !."""
        self.recorder.start_recording()

        self.recorder._on_key_press(DummyKey("ctrl"))
        self.recorder._on_key_press(DummyKey("shift"))
        self.recorder._on_key_press(DummyKeyCode(char="1"))

        self.recorder._finalize_recording()
        self.on_complete.assert_called_with("ctrl+shift+!")

    def test_caret_char_directly(self):
        """^ character should be captured as ^."""
        self.recorder.start_recording()

        # When Shift+6 is pressed without Ctrl, char='^' is produced
        caret_key = DummyKeyCode(char="^")
        self.recorder._on_key_press(caret_key)

        assert "^" in self.recorder._captured_keys


class TestModifierOrder:
    """Tests for the MODIFIER_ORDER constant."""

    def test_modifier_order_contains_expected_keys(self):
        """MODIFIER_ORDER should contain standard modifiers."""
        assert "ctrl" in MODIFIER_ORDER
        assert "alt" in MODIFIER_ORDER
        assert "shift" in MODIFIER_ORDER
        assert "cmd" in MODIFIER_ORDER

    def test_modifier_order_is_correct(self):
        """Modifier order should be ctrl, alt, shift, cmd."""
        assert MODIFIER_ORDER == ["ctrl", "alt", "shift", "cmd"]
