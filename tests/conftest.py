import pytest
import sys
import tkinter as tk
from loguru import logger
from unittest.mock import Mock


# Configure loguru for tests
logger.remove()  # Remove default handler
logger.add(sys.stdout, level="DEBUG")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test"""
    import os

    # Ensure clean state for each test
    yield

    # Cleanup test config file if it exists
    test_config_file = "push_to_talk_config_test.json"
    if os.path.exists(test_config_file):
        try:
            os.remove(test_config_file)
        except Exception:
            pass  # Ignore cleanup errors


# === GUI Testing Fixtures ===


@pytest.fixture
def mock_tk_root():
    """Create a real Tk root for GUI tests that need Tkinter variables

    This creates an actual Tk root (withdrawn/hidden) to support
    Tkinter variables (StringVar, IntVar, etc.) which require a root.
    Falls back to mocking if Tk is unavailable (headless systems).

    Returns:
        tk.Tk or Mock: Real Tk root (withdrawn) or Mock if unavailable
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        # Set as default root for Tkinter variables
        original_default = tk._default_root
        tk._default_root = root
        yield root
        # Cleanup
        tk._default_root = original_default
        try:
            root.destroy()
        except Exception:
            pass
    except Exception:
        # Fallback to mock for headless environments - skip the test
        pytest.skip("Cannot create Tk root window (headless environment)")


@pytest.fixture
def mock_gui_sections(mocker):
    """Create mocked GUI sections for testing

    Mocks tkinter.ttk.LabelFrame to avoid creating actual Tk widgets.
    Sections are created as real instances but with mocked frames.

    Returns:
        dict: Dictionary of section name -> section instance
    """
    from src.gui.api_section import APISection
    from src.gui.audio_section import AudioSection
    from src.gui.hotkey_section import HotkeySection
    from src.gui.settings_section import TextInsertionSection, FeatureFlagsSection
    from src.gui.glossary_section import GlossarySection
    from src.gui.prompt_section import PromptSection
    from src.gui.status_section import StatusSection

    mocker.patch("tkinter.ttk.LabelFrame")
    sections = {
        "api": APISection,
        "audio": AudioSection,
        "hotkey": HotkeySection,
        "text_insertion": TextInsertionSection,
        "feature_flags": FeatureFlagsSection,
        "glossary": GlossarySection,
        "prompt": PromptSection,
        "status": StatusSection,
    }
    yield sections


@pytest.fixture
def prepared_config_gui(mock_tk_root, mock_gui_sections):
    """Create ConfigurationWindow with prepared GUI sections

    This fixture creates a ConfigurationWindow instance with:
    - Real Tk root (already set as default by mock_tk_root fixture)
    - Mocked section frames (no actual widgets)
    - Pre-initialized sections with test config values

    Usage:
        def test_something(prepared_config_gui):
            gui = prepared_config_gui
            # GUI is ready with all sections initialized
            ...

    Returns:
        ConfigurationWindow: Fully initialized GUI instance
    """
    from src.gui import ConfigurationWindow
    from src.push_to_talk import PushToTalkConfig

    config = PushToTalkConfig(openai_api_key="test-key")
    gui = ConfigurationWindow(config, config_file_path="push_to_talk_config_test.json")
    gui.root = mock_tk_root

    # Initialize sections with mocked frames
    gui.api_section = mock_gui_sections["api"](Mock())
    gui.api_section.set_values(
        config.stt_provider,
        config.openai_api_key,
        config.deepgram_api_key,
        config.cerebras_api_key,
        config.stt_model,
        config.refinement_provider,
        config.refinement_model,
    )

    gui.audio_section = mock_gui_sections["audio"](Mock())
    gui.audio_section.set_values(
        config.sample_rate,
        config.chunk_size,
        config.channels,
    )

    gui.hotkey_section = mock_gui_sections["hotkey"](Mock())
    gui.hotkey_section.set_values(
        config.hotkey,
        config.toggle_hotkey,
    )

    gui.text_insertion_section = mock_gui_sections["text_insertion"](Mock())
    gui.text_insertion_section.set_value(config.insertion_delay)

    gui.feature_flags_section = mock_gui_sections["feature_flags"](Mock())
    gui.feature_flags_section.set_values(
        config.enable_text_refinement,
        config.enable_logging,
        config.enable_audio_feedback,
        config.debug_mode,
    )

    gui.glossary_section = mock_gui_sections["glossary"](
        Mock(), mock_tk_root, config.custom_glossary
    )

    # For prompt_section, we need to mock the tk.Text widget behavior
    # since it doesn't use StringVar like other sections
    gui.prompt_section = mock_gui_sections["prompt"](
        Mock(), mock_tk_root, config.custom_refinement_prompt
    )
    # Store the prompt value and mock get_prompt/set_prompt to use it
    gui.prompt_section._stored_prompt = config.custom_refinement_prompt
    gui.prompt_section.get_prompt = lambda: gui.prompt_section._stored_prompt
    gui.prompt_section.set_prompt = lambda p: setattr(
        gui.prompt_section, "_stored_prompt", p
    )

    gui.status_section = mock_gui_sections["status"](Mock())

    return gui
