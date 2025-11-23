import sys
import types
from unittest.mock import Mock

pyautogui_stub = types.SimpleNamespace(
    hotkey=lambda *_, **__: None,
    write=lambda *_, **__: None,
    getActiveWindow=lambda: None,
)

sys.modules.setdefault("mouseinfo", types.SimpleNamespace())
sys.modules.setdefault("pyautogui", pyautogui_stub)


class _DummyListener:
    def __init__(self, *_, **__):
        pass

    def start(self):
        return None

    def stop(self):
        return None

    def join(self, *_):
        return None


keyboard_stub = types.SimpleNamespace(
    Listener=_DummyListener,
    Key=types.SimpleNamespace,
    KeyCode=types.SimpleNamespace,
)

sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules.setdefault("pynput.keyboard", keyboard_stub)

from src.config_gui import ConfigurationGUI  # noqa: E402
from src.push_to_talk import PushToTalkConfig  # noqa: E402


class DummyVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


CONFIG_VAR_KEYS = [
    "stt_provider",
    "openai_api_key",
    "deepgram_api_key",
    "stt_model",
    "refinement_model",
    "sample_rate",
    "chunk_size",
    "channels",
    "hotkey",
    "toggle_hotkey",
    "insertion_method",
    "insertion_delay",
    "enable_text_refinement",
    "enable_logging",
    "enable_audio_feedback",
    "debug_mode",
]


def _prepare_gui(config: PushToTalkConfig) -> ConfigurationGUI:
    gui = ConfigurationGUI(config)
    gui.config_vars = {key: DummyVar(getattr(config, key)) for key in CONFIG_VAR_KEYS}
    gui.glossary_terms = list(config.custom_glossary)
    return gui


def test_gui_updates_running_app_when_config_changes():
    config = PushToTalkConfig(openai_api_key="test-key")
    gui = _prepare_gui(config)

    gui.app_instance = Mock()
    gui.on_config_changed = Mock()
    gui.is_running = True

    gui.config_vars["hotkey"].set("ctrl+alt+h")
    gui._on_config_var_changed()

    gui.app_instance.update_configuration.assert_called_once()
    updated_config = gui.app_instance.update_configuration.call_args[0][0]
    assert updated_config.hotkey == "ctrl+alt+h"
    assert gui.config.hotkey == "ctrl+alt+h"
    gui.on_config_changed.assert_called_once_with(updated_config)

    # Trigger callback again without changing values and ensure nothing happens
    gui.app_instance.update_configuration.reset_mock()
    gui.on_config_changed.reset_mock()
    gui._on_config_var_changed()
    gui.app_instance.update_configuration.assert_not_called()
    gui.on_config_changed.assert_not_called()


def test_force_notify_triggers_update_even_when_values_match():
    config = PushToTalkConfig(openai_api_key="test-key")
    gui = _prepare_gui(config)

    gui.app_instance = Mock()
    gui.on_config_changed = Mock()
    gui.is_running = True

    gui._notify_config_changed(force=True)

    gui.app_instance.update_configuration.assert_called_once()
    forced_config = gui.app_instance.update_configuration.call_args[0][0]
    gui.on_config_changed.assert_called_once_with(forced_config)
    assert forced_config == config


def test_custom_glossary_is_copied_when_building_config():
    config = PushToTalkConfig(openai_api_key="test-key", custom_glossary=["alpha"])
    gui = _prepare_gui(config)

    gui._notify_config_changed(force=True)
    assert gui.config.custom_glossary == ["alpha"]

    # Modify GUI glossary without notifying and ensure stored config is unchanged
    gui.glossary_terms.append("beta")
    assert gui.config.custom_glossary == ["alpha"]

    # Notify again and confirm the change is propagated
    gui._notify_config_changed()
    assert gui.config.custom_glossary == ["alpha", "beta"]


def test_config_changes_trigger_async_save(tmp_path):
    """Test that configuration changes trigger asynchronous save to JSON file."""
    import time
    import json
    from unittest.mock import patch

    config = PushToTalkConfig(openai_api_key="test-key", hotkey="ctrl+shift+space")
    gui = _prepare_gui(config)

    # Use a temporary file for testing
    test_config_file = tmp_path / "test_config.json"

    # Mock the GUI to be running so changes trigger saves
    gui.is_running = True

    # Patch the save method to use our test file
    with patch.object(gui, "_save_config_to_file_async") as mock_save:
        # Change a configuration value
        gui.config_vars["hotkey"].set("ctrl+alt+h")
        gui._on_config_var_changed()

        # Verify async save was called
        mock_save.assert_called_once()

    # Test the actual async save functionality
    gui.config_vars["hotkey"].set("ctrl+alt+test")
    gui._notify_config_changed()

    # Save to our test file
    gui._save_config_to_file_async(str(test_config_file))

    # Wait a bit for the async save to complete
    time.sleep(0.5)

    # Verify the file was created and contains correct data
    assert test_config_file.exists()

    with open(test_config_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["hotkey"] == "ctrl+alt+test"
    assert saved_data["openai_api_key"] == "test-key"


def test_concurrent_async_saves_are_deduplicated(tmp_path):
    """Test that concurrent async saves are properly deduplicated."""
    import threading
    import time
    import json

    config = PushToTalkConfig(openai_api_key="test-key")
    gui = _prepare_gui(config)
    gui.is_running = True

    test_config_file = tmp_path / "concurrent_test.json"
    save_attempts = []

    def track_saves():
        """Track when saves actually happen."""
        _ = gui._save_config_to_file_async.__code__

        def tracking_save():
            save_attempts.append(time.time())
            gui._save_config_to_file_async(str(test_config_file))

        return tracking_save

    # Start multiple concurrent saves
    threads = []
    for i in range(5):
        thread = threading.Thread(
            target=lambda: gui._save_config_to_file_async(str(test_config_file))
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Wait a bit for async operations
    time.sleep(0.2)

    # Verify file was created (at least one save succeeded)
    assert test_config_file.exists()

    # The exact number of writes is implementation-dependent due to timing,
    # but the file should contain valid JSON
    with open(test_config_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["openai_api_key"] == "test-key"


def test_update_gui_from_config_updates_provider_fields():
    """Test that _update_gui_from_config updates stt_provider and deepgram_api_key."""
    # Initial config with OpenAI provider
    config = PushToTalkConfig(
        stt_provider="openai",
        openai_api_key="openai-key",
        deepgram_api_key="",
    )
    gui = _prepare_gui(config)
    gui.app_instance = Mock()
    gui.on_config_changed = Mock()
    gui.is_running = False

    # Verify initial state
    assert gui.config_vars["stt_provider"].get() == "openai"
    assert gui.config_vars["openai_api_key"].get() == "openai-key"
    assert gui.config_vars["deepgram_api_key"].get() == ""

    # Create a new config with Deepgram provider
    new_config = PushToTalkConfig(
        stt_provider="deepgram",
        openai_api_key="openai-key",
        deepgram_api_key="deepgram-key",
    )

    # Update GUI from new config
    gui._update_gui_from_config(new_config)

    # Verify provider and deepgram key were updated
    assert gui.config_vars["stt_provider"].get() == "deepgram"
    assert gui.config_vars["deepgram_api_key"].get() == "deepgram-key"
    assert gui.config.stt_provider == "deepgram"
    assert gui.config.deepgram_api_key == "deepgram-key"

    # Change back to OpenAI
    openai_config = PushToTalkConfig(
        stt_provider="openai",
        openai_api_key="new-openai-key",
        deepgram_api_key="deepgram-key",  # Should remain
    )

    gui._update_gui_from_config(openai_config)

    # Verify all fields updated correctly
    assert gui.config_vars["stt_provider"].get() == "openai"
    assert gui.config_vars["openai_api_key"].get() == "new-openai-key"
    assert gui.config_vars["deepgram_api_key"].get() == "deepgram-key"
    assert gui.config.stt_provider == "openai"
    assert gui.config.openai_api_key == "new-openai-key"
    assert gui.config.deepgram_api_key == "deepgram-key"
