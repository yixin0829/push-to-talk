import sys
import types
from unittest.mock import Mock, patch

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

from src.gui import ConfigurationWindow  # noqa: E402
from src.push_to_talk import PushToTalkConfig  # noqa: E402

# Alias for consistency with test code
ConfigurationGUI = ConfigurationWindow


def _prepare_gui(config: PushToTalkConfig) -> ConfigurationGUI:
    """
    Prepare a GUI instance with mocked sections.

    Note: The new architecture uses modular sections, so we need to create
    them with the config values for testing.
    """
    import tkinter as tk

    gui = ConfigurationGUI(config)

    # Create mocked sections that respond to get/set operations
    from src.gui.api_section import APISection
    from src.gui.audio_section import AudioSection
    from src.gui.hotkey_section import HotkeySection
    from src.gui.settings_section import TextInsertionSection, FeatureFlagsSection
    from src.gui.glossary_section import GlossarySection
    from src.gui.status_section import StatusSection

    # Create a real Tk root for Tkinter variables to work
    try:
        test_root = tk.Tk()
        test_root.withdraw()  # Hide the window
    except Exception:
        # If Tk fails (e.g., no display), skip tests
        import pytest

        pytest.skip("Cannot create Tk root window")

    gui.root = test_root

    # Create real section instances (they're lightweight without actual widgets)
    # We'll mock their frames to avoid creating actual Tk widgets
    with patch("tkinter.ttk.LabelFrame"):
        gui.api_section = APISection(Mock())
        gui.api_section.set_values(
            config.stt_provider,
            config.openai_api_key,
            config.deepgram_api_key,
            config.stt_model,
            config.refinement_model,
        )

        gui.audio_section = AudioSection(Mock())
        gui.audio_section.set_values(
            config.sample_rate,
            config.chunk_size,
            config.channels,
        )

        gui.hotkey_section = HotkeySection(Mock())
        gui.hotkey_section.set_values(
            config.hotkey,
            config.toggle_hotkey,
        )

        gui.text_insertion_section = TextInsertionSection(Mock())
        gui.text_insertion_section.set_value(config.insertion_delay)

        gui.feature_flags_section = FeatureFlagsSection(Mock())
        gui.feature_flags_section.set_values(
            config.enable_text_refinement,
            config.enable_logging,
            config.enable_audio_feedback,
            config.debug_mode,
        )

        gui.glossary_section = GlossarySection(
            Mock(), test_root, config.custom_glossary
        )

        gui.status_section = StatusSection(Mock())

    return gui


def test_gui_updates_running_app_when_config_changes():
    config = PushToTalkConfig(openai_api_key="test-key")
    gui = _prepare_gui(config)

    gui.app_instance = Mock()
    gui.on_config_changed = Mock()
    gui.is_running = True

    # Change hotkey through the hotkey section
    gui.hotkey_section.hotkey_var.set("ctrl+alt+h")
    # Call _notify_config_changed directly to bypass debouncing
    gui._notify_config_changed()

    gui.app_instance.update_configuration.assert_called_once()
    updated_config = gui.app_instance.update_configuration.call_args[0][0]
    assert updated_config.hotkey == "ctrl+alt+h"
    assert gui.config.hotkey == "ctrl+alt+h"
    gui.on_config_changed.assert_called_once_with(updated_config)

    # Trigger callback again without changing values and ensure nothing happens
    gui.app_instance.update_configuration.reset_mock()
    gui.on_config_changed.reset_mock()
    gui._notify_config_changed()
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
    gui.glossary_section.glossary_terms.append("beta")
    assert gui.config.custom_glossary == ["alpha"]

    # Notify again and confirm the change is propagated
    gui._notify_config_changed()
    assert gui.config.custom_glossary == ["alpha", "beta"]


def test_config_changes_trigger_async_save(tmp_path):
    """Test that configuration changes trigger asynchronous save to JSON file."""
    import time
    import json

    config = PushToTalkConfig(openai_api_key="test-key", hotkey="ctrl+shift+space")
    gui = _prepare_gui(config)

    # Use a temporary file for testing
    test_config_file = tmp_path / "test_config.json"

    # Mock the GUI to be running so changes trigger saves
    gui.is_running = True

    # Patch the save method to use our test file
    with patch.object(gui._config_persistence, "save_async") as mock_save:
        # Change a configuration value
        gui.hotkey_section.hotkey_var.set("ctrl+alt+h")
        # Call _notify_config_changed directly to bypass debouncing
        gui._notify_config_changed()

        # Verify async save was called
        mock_save.assert_called_once()

    # Test the actual async save functionality
    gui.hotkey_section.hotkey_var.set("ctrl+alt+test")
    gui._notify_config_changed()

    # Save to our test file
    gui._config_persistence.save_async(gui.config, str(test_config_file))

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

    # Start multiple concurrent saves
    threads = []
    for i in range(5):
        thread = threading.Thread(
            target=lambda: gui._config_persistence.save_async(
                gui.config, str(test_config_file)
            )
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
    """Test that _update_sections_from_config updates stt_provider and deepgram_api_key."""
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
    assert gui.api_section.stt_provider_var.get() == "openai"
    assert gui.api_section.openai_api_key_var.get() == "openai-key"
    assert gui.api_section.deepgram_api_key_var.get() == ""

    # Create a new config with Deepgram provider
    new_config = PushToTalkConfig(
        stt_provider="deepgram",
        openai_api_key="openai-key",
        deepgram_api_key="deepgram-key",
    )

    # Update GUI from new config
    gui._update_sections_from_config(new_config)

    # Verify provider and deepgram key were updated
    assert gui.api_section.stt_provider_var.get() == "deepgram"
    assert gui.api_section.deepgram_api_key_var.get() == "deepgram-key"
    assert gui.config.stt_provider == "openai"  # config not updated yet

    # Notify to update the config
    gui._notify_config_changed(force=True)
    assert gui.config.stt_provider == "deepgram"
    assert gui.config.deepgram_api_key == "deepgram-key"

    # Change back to OpenAI
    openai_config = PushToTalkConfig(
        stt_provider="openai",
        openai_api_key="new-openai-key",
        deepgram_api_key="deepgram-key",  # Should remain
    )

    gui._update_sections_from_config(openai_config)

    # Verify all fields updated correctly
    assert gui.api_section.stt_provider_var.get() == "openai"
    assert gui.api_section.openai_api_key_var.get() == "new-openai-key"
    assert gui.api_section.deepgram_api_key_var.get() == "deepgram-key"

    gui._notify_config_changed(force=True)
    assert gui.config.stt_provider == "openai"
    assert gui.config.openai_api_key == "new-openai-key"
    assert gui.config.deepgram_api_key == "deepgram-key"


def test_stt_model_preserved_when_switching_providers():
    """Test that STT model selection is preserved when switching between providers."""
    # Start with OpenAI provider and gpt-4o-transcribe model
    config = PushToTalkConfig(
        stt_provider="openai",
        stt_model="gpt-4o-transcribe",
        openai_api_key="test-key",
    )
    gui = _prepare_gui(config)

    # Mock the stt_model_combo widget
    gui.api_section.stt_model_combo = Mock()
    gui.api_section.stt_model_combo.__setitem__ = Mock()

    # Verify initial OpenAI model is stored
    assert gui.api_section.openai_stt_model == "gpt-4o-transcribe"
    assert gui.api_section.deepgram_stt_model == "nova-3"  # Default

    # User changes OpenAI model to gpt-4o-mini-transcribe
    gui.api_section.stt_model_var.set("gpt-4o-mini-transcribe")
    gui.api_section._on_stt_model_changed()

    # Verify the OpenAI model was saved
    assert gui.api_section.openai_stt_model == "gpt-4o-mini-transcribe"

    # Switch to Deepgram provider
    gui.api_section.stt_provider_var.set("deepgram")
    gui.api_section._update_stt_model_options()

    # Verify Deepgram model is restored (default nova-3)
    assert gui.api_section.stt_model_var.get() == "nova-3"

    # User changes Deepgram model to nova-2
    gui.api_section.stt_model_var.set("nova-2")
    gui.api_section._on_stt_model_changed()

    # Verify the Deepgram model was saved
    assert gui.api_section.deepgram_stt_model == "nova-2"

    # Switch back to OpenAI provider
    gui.api_section.stt_provider_var.set("openai")
    gui.api_section._update_stt_model_options()

    # Verify OpenAI model is restored (should be gpt-4o-mini-transcribe, not whisper-1)
    assert gui.api_section.stt_model_var.get() == "gpt-4o-mini-transcribe"
    assert gui.api_section.openai_stt_model == "gpt-4o-mini-transcribe"

    # Switch back to Deepgram again
    gui.api_section.stt_provider_var.set("deepgram")
    gui.api_section._update_stt_model_options()

    # Verify Deepgram model is still nova-2
    assert gui.api_section.stt_model_var.get() == "nova-2"
    assert gui.api_section.deepgram_stt_model == "nova-2"
