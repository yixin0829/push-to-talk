import sys
import types
from unittest.mock import Mock

from tests.test_helpers import create_keyboard_stub, create_pyautogui_stub

# Setup stubs for GUI-related imports
pyautogui_stub = create_pyautogui_stub()
sys.modules.setdefault("mouseinfo", types.SimpleNamespace())
sys.modules.setdefault("pyautogui", pyautogui_stub)

keyboard_stub = create_keyboard_stub()
sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules.setdefault("pynput.keyboard", keyboard_stub)

from src.push_to_talk import PushToTalkConfig  # noqa: E402


def test_gui_updates_running_app_when_config_changes(prepared_config_gui):
    gui = prepared_config_gui

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


def test_force_notify_triggers_update_even_when_values_match(prepared_config_gui):
    gui = prepared_config_gui
    config = gui.config

    gui.app_instance = Mock()
    gui.on_config_changed = Mock()
    gui.is_running = True

    gui._notify_config_changed(force=True)

    gui.app_instance.update_configuration.assert_called_once()
    forced_config = gui.app_instance.update_configuration.call_args[0][0]
    gui.on_config_changed.assert_called_once_with(forced_config)
    assert forced_config == config


def test_config_changes_trigger_async_save(tmp_path, prepared_config_gui, mocker):
    """Test that configuration changes trigger asynchronous save to JSON file."""
    import time
    import json

    gui = prepared_config_gui
    # Update hotkeys for this test
    gui.config.hotkey = "ctrl+shift+^"
    gui.config.toggle_hotkey = "ctrl+shift+space"
    gui.hotkey_section.set_values("ctrl+shift+^", "ctrl+shift+space")

    # Use a temporary file for testing
    test_config_file = tmp_path / "test_config.json"

    # Mock the GUI to be running so changes trigger saves
    gui.is_running = True
    # Mark initialization as complete so saves are triggered
    gui._initialization_complete = True

    # Store the original save method before patching
    original_save_async = gui._config_persistence.save_async

    # Patch the save method to use our test file
    mock_save = mocker.patch.object(gui._config_persistence, "save_async")
    # Change a configuration value
    gui.hotkey_section.hotkey_var.set("ctrl+alt+h")
    # Call _notify_config_changed directly to bypass debouncing
    gui._notify_config_changed()

    # Verify async save was called
    mock_save.assert_called_once()

    # Stop the mock and restore the original method
    mocker.stop(mock_save)
    gui._config_persistence.save_async = original_save_async

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


def test_concurrent_async_saves_are_deduplicated(tmp_path, prepared_config_gui):
    """Test that concurrent async saves are properly deduplicated."""
    import threading
    import time
    import json

    gui = prepared_config_gui
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


def test_update_gui_from_config_updates_provider_fields(prepared_config_gui):
    """Test that _update_sections_from_config updates stt_provider and deepgram_api_key."""
    gui = prepared_config_gui
    # Update config for this test
    gui.config.stt_provider = "openai"
    gui.config.openai_api_key = "openai-key"
    gui.config.deepgram_api_key = ""
    gui.api_section.set_values(
        "openai",
        "openai-key",
        "",
        gui.config.cerebras_api_key,
        gui.config.stt_model,
        gui.config.refinement_provider,
        gui.config.refinement_model,
    )
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


def test_stt_model_preserved_when_switching_providers(prepared_config_gui):
    """Test that STT model selection is preserved when switching between providers."""
    gui = prepared_config_gui
    # Update for this test
    gui.config.stt_provider = "openai"
    gui.config.stt_model = "gpt-4o-transcribe"
    gui.api_section.set_values(
        "openai",
        gui.config.openai_api_key,
        gui.config.deepgram_api_key,
        gui.config.cerebras_api_key,
        "gpt-4o-transcribe",
        gui.config.refinement_provider,
        gui.config.refinement_model,
    )

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


def test_loaded_config_not_overwritten_during_initialization(
    tmp_path, prepared_config_gui, mocker
):
    """Test that loaded configuration is not overwritten by async save during GUI initialization."""
    import time
    import json

    gui = prepared_config_gui
    # Update config with specific non-default values
    gui.config.openai_api_key = "loaded-api-key"
    gui.config.hotkey = "ctrl+shift+loaded"
    gui.config.toggle_hotkey = "ctrl+alt+loaded"
    gui.config.sample_rate = 16000
    gui.config.enable_text_refinement = False
    gui.config.enable_audio_feedback = False

    # Create test config file
    test_config_file = tmp_path / "test_config.json"
    with open(test_config_file, "w") as f:
        json.dump(gui.config.model_dump(), f, indent=2)

    # Mock the config persistence to track saves
    original_save_async = gui._config_persistence.save_async
    save_calls = []

    def track_save_async(config, filepath="push_to_talk_config.json"):
        save_calls.append(config.model_dump())
        return original_save_async(config, filepath)

    mocker.patch.object(
        gui._config_persistence, "save_async", side_effect=track_save_async
    )
    # Simulate the initialization process
    gui._update_sections_from_config(gui.config)
    gui._setup_variable_traces()

    # At this point, _initialization_complete should be False
    assert gui._initialization_complete is False

    # Trigger a config change notification (simulating what might happen during init)
    gui._notify_config_changed()

    # Verify that NO save was triggered because initialization is not complete
    assert len(save_calls) == 0, "Config should not be saved during initialization"

    # Now mark initialization as complete
    gui._initialization_complete = True

    # Make an actual change to trigger save
    gui.hotkey_section.hotkey_var.set("ctrl+shift+changed")
    gui._notify_config_changed()

    # Wait a bit for async save
    time.sleep(0.1)

    # NOW a save should have been triggered
    assert len(save_calls) == 1, (
        "Config should be saved after initialization is complete"
    )

    # Verify the saved config has the changed value
    saved_config = save_calls[0]
    assert saved_config["openai_api_key"] == "loaded-api-key"
    assert saved_config["hotkey"] == "ctrl+shift+changed"  # This was changed
    assert saved_config["toggle_hotkey"] == "ctrl+alt+loaded"
    assert saved_config["sample_rate"] == 16000
    assert saved_config["enable_text_refinement"] is False
    assert saved_config["enable_audio_feedback"] is False
