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
    "openai_api_key",
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
    "enable_audio_processing",
    "debug_mode",
    "silence_threshold",
    "min_silence_duration",
    "speed_factor",
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
