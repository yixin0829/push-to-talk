"""Shared test utilities and mock infrastructure

This module provides:
- Pynput keyboard mocks (DummyKey, DummyKeyCode, DummyListener)
- PyAutoGUI stub
- API response builders for OpenAI and Deepgram
- Reusable pytest fixtures
- Test data factories
"""

import sys
import types
from typing import Optional
from unittest.mock import MagicMock

import pytest


# === Pynput Keyboard Mocks ===


class DummyKey:
    """Mock pynput.keyboard.Key"""

    def __init__(self, name: Optional[str] = None):
        if name is not None:
            self.name = name


class DummyKeyCode:
    """Mock pynput.keyboard.KeyCode"""

    def __init__(self, char: Optional[str] = None, vk: Optional[int] = None):
        self.char = char
        self.vk = vk

    @classmethod
    def from_vk(cls, vk: int):
        return cls(vk=vk)


class DummyListener:
    """Mock pynput.keyboard.Listener"""

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


def create_keyboard_stub():
    """Create a complete pynput keyboard stub with common keys

    Returns:
        types.SimpleNamespace with Listener, Key, and KeyCode attributes
    """
    # Populate common key objects used by services
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

    return types.SimpleNamespace(
        Listener=DummyListener,
        Key=Key,
        KeyCode=DummyKeyCode,
    )


# === PyAutoGUI Stub ===


def create_pyautogui_stub():
    """Create pyautogui stub for GUI tests

    Returns:
        types.SimpleNamespace with common pyautogui methods stubbed
    """
    return types.SimpleNamespace(
        hotkey=lambda *_, **__: None,
        write=lambda *_, **__: None,
        getActiveWindow=lambda: None,
    )


# === API Response Builders ===


def build_openai_transcription_response(text: str):
    """Build mock OpenAI transcription response

    OpenAI's transcription API returns either:
    - A string directly (most common)
    - An object with .text attribute
    - An object with __str__ method

    Args:
        text: The transcribed text to return

    Returns:
        str: The transcription text (most common OpenAI response format)
    """
    return text


def build_openai_transcription_response_with_text_attr(text: str):
    """Build mock OpenAI transcription response with .text attribute

    Some OpenAI responses return an object with a .text attribute.

    Args:
        text: The transcribed text to return

    Returns:
        MagicMock with .text attribute
    """
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


def build_deepgram_transcription_response(text: str):
    """Build mock Deepgram transcription response

    Deepgram responses have structure:
    response.results.channels[0].alternatives[0].transcript

    Args:
        text: The transcribed text to return

    Returns:
        MagicMock with nested Deepgram response structure
    """
    mock_response = MagicMock()
    mock_response.results.channels = [MagicMock()]
    mock_response.results.channels[0].alternatives = [MagicMock()]
    mock_response.results.channels[0].alternatives[0].transcript = text
    return mock_response


def build_openai_refinement_response(text: str):
    """Build mock OpenAI text refinement response

    OpenAI's text refinement (GPT) returns an object with .output_text attribute.

    Args:
        text: The refined text to return

    Returns:
        MagicMock with .output_text attribute
    """
    mock_response = MagicMock()
    mock_response.output_text = text
    return mock_response


# === Reusable Pytest Fixtures ===


@pytest.fixture
def pynput_stub(monkeypatch):
    """Provide pynput keyboard stub for tests

    Automatically injects keyboard stub into sys.modules to avoid
    import errors from real pynput library.

    Usage:
        def test_something(pynput_stub):
            # pynput.keyboard is now available
            from pynput import keyboard
            ...

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        types.SimpleNamespace with Listener, Key, and KeyCode
    """
    keyboard_stub = create_keyboard_stub()
    monkeypatch.setitem(
        sys.modules, "pynput", types.SimpleNamespace(keyboard=keyboard_stub)
    )
    monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard_stub)
    return keyboard_stub


@pytest.fixture
def pyautogui_stub(monkeypatch):
    """Provide pyautogui stub for tests

    Automatically injects pyautogui stub into sys.modules to avoid
    import errors from real pyautogui library.

    Usage:
        def test_something(pyautogui_stub):
            # pyautogui is now available
            import pyautogui
            ...

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        types.SimpleNamespace with common pyautogui methods
    """
    stub = create_pyautogui_stub()
    monkeypatch.setitem(sys.modules, "mouseinfo", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "pyautogui", stub)
    return stub


# === Test Data Factories ===


def create_test_config(**overrides):
    """Factory for PushToTalkConfig with test defaults

    Creates a minimal valid PushToTalkConfig for testing. Override any
    fields as needed.

    Usage:
        config = create_test_config(stt_provider="deepgram")

    Args:
        **overrides: Any PushToTalkConfig field to override

    Returns:
        PushToTalkConfig instance
    """
    from src.push_to_talk import PushToTalkConfig

    defaults = {
        "stt_provider": "openai",
        "openai_api_key": "test-key",
        "stt_model": "whisper-1",
        "refinement_model": "gpt-4o-mini",
        "sample_rate": 16000,
        "chunk_size": 1024,
        "channels": 1,
    }
    defaults.update(overrides)
    return PushToTalkConfig(**defaults)


def create_test_audio_file(tmp_path, content=b"fake audio", suffix=".wav"):
    """Create a temporary audio file for testing

    Usage:
        def test_something(tmp_path):
            audio_file = create_test_audio_file(tmp_path)
            # Use audio_file path in tests

    Args:
        tmp_path: pytest tmp_path fixture
        content: bytes to write to file (default: b"fake audio")
        suffix: file extension (default: ".wav")

    Returns:
        Path object to the created audio file
    """
    audio_file = tmp_path / f"test_audio{suffix}"
    audio_file.write_bytes(content)
    return audio_file
