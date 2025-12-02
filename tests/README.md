# Testing Guide

This document provides guidance on writing and running tests for the Push-to-Talk project.

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run unit tests only (exclude integration tests)
uv run pytest tests/ -v -m "not integration"

# Run integration tests only
uv run pytest tests/ -v -m integration

# Run specific test file
uv run pytest tests/test_audio_recorder.py -v

# Run with coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Run tests matching a pattern
uv run pytest tests/ -k "test_transcribe" -v
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_helpers.py          # Centralized mocks, stubs, and builders
├── fixtures/                # Test data (audio files, scripts)
│   ├── audio1.wav
│   ├── audio2.wav
│   └── audio3.wav
├── test_*.py                # Test modules
└── README.md                # This file
```

### Test Files

- **`test_*_service.py`** - Service layer tests (may use class-based structure for complex state)
- **`test_*_gui.py`** - GUI component tests (fixture-based)
- **`test_integration.py`** - Integration tests with real audio files (marked with `@pytest.mark.integration`)
- **`conftest.py`** - Shared fixtures and pytest configuration
- **`test_helpers.py`** - Reusable mocks, stubs, and test data builders

## Writing Tests

### Use Pytest Fixtures

Fixtures provide a clean way to set up test dependencies. They're preferred over class-based `setup_method`/`teardown_method`.

**Good** (fixture-based):
```python
@pytest.fixture
def transcriber():
    return OpenAITranscriber(api_key="test-key", model="whisper-1")

def test_transcribe(transcriber):
    result = transcriber.transcribe_audio("test.wav")
    assert result is not None
```

**Acceptable** (class-based, for complex state):
```python
class TestComplexComponent:
    def setup_method(self):
        self.component = ComplexComponent()
        self.state = ComplexState()

    def test_something(self):
        # Test with complex setup
        pass
```

### Use Test Helpers

The `test_helpers.py` module provides centralized mocks and builders. Always use these instead of creating duplicates.

```python
from tests.test_helpers import (
    build_openai_transcription_response,
    build_deepgram_transcription_response,
    build_openai_refinement_response,
    create_test_config,
)

def test_openai_transcription(mocker):
    mock_response = build_openai_transcription_response("transcribed text")
    # Use the mock_response in your test
```

#### Available Test Helpers

**Keyboard/GUI Mocks:**
- `create_keyboard_stub()` - Complete pynput keyboard stub
- `create_pyautogui_stub()` - PyAutoGUI stub for GUI tests
- `DummyKey`, `DummyKeyCode`, `DummyListener` - Individual keyboard mocks

**API Response Builders:**
- `build_openai_transcription_response(text)` - OpenAI transcription response
- `build_openai_transcription_response_with_text_attr(text)` - OpenAI response with .text attribute
- `build_deepgram_transcription_response(text)` - Deepgram response structure
- `build_openai_refinement_response(text)` - OpenAI text refinement response

**Fixtures:**
- `pynput_stub` - Auto-inject pynput keyboard mocks
- `pyautogui_stub` - Auto-inject pyautogui mocks

**Test Data Factories:**
- `create_test_config(**overrides)` - Create PushToTalkConfig with test defaults
- `create_test_audio_file(tmp_path, content, suffix)` - Create temporary audio files

### Use pytest-mock for Mocking

We use `pytest-mock` for a cleaner, more pytest-native mocking style. The `mocker` fixture provides all mocking capabilities.

**Before** (unittest.mock):
```python
from unittest.mock import patch, mock_open

@patch("builtins.open", mock_open(read_data=b"fake audio data"))
@patch("os.path.exists")
@patch("os.remove")
def test_transcribe_audio(mock_remove, mock_exists):
    mock_exists.return_value = True
    # test code...
```

**After** (pytest-mock):
```python
def test_transcribe_audio(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.remove")
    # test code...
```

#### Common pytest-mock Patterns

**Patch a function:**
```python
mocker.patch("os.path.exists", return_value=True)
```

**Patch with side effects:**
```python
mocker.patch("time.time", side_effect=[1000.0, 1002.5, 1003.0])
```

**Patch dictionary (environment variables):**
```python
mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
```

**Mock file operations:**
```python
mocker.patch("builtins.open", mocker.mock_open(read_data=b"file content"))
```

**Patch object attributes:**
```python
mocker.patch.object(obj, "method_name", return_value="mocked")
```

**Create mock objects:**
```python
mock_client = mocker.MagicMock()
mock_client.transcribe.return_value = "result"
```

### Mark Integration Tests

Tests that use real files or external resources should be marked as integration tests.

```python
@pytest.mark.integration
def test_with_real_audio_files():
    # Uses fixtures/audio1.wav
    pass
```

Run only unit tests:
```bash
uv run pytest tests/ -m "not integration"
```

### GUI Testing Patterns

GUI tests use the `prepared_config_gui` fixture from `conftest.py`:

```python
def test_gui_behavior(prepared_config_gui):
    gui = prepared_config_gui

    # GUI is ready with all sections initialized
    gui.hotkey_section.hotkey_var.set("ctrl+alt+h")
    gui._notify_config_changed()

    assert gui.config.hotkey == "ctrl+alt+h"
```

The fixture provides:
- Real Tk root (withdrawn/hidden) or skips on headless systems
- Mocked GUI sections (no actual widgets created)
- Pre-initialized configuration

### Test Data and Fixtures

**Use tmp_path for temporary files:**
```python
def test_config_save(tmp_path):
    config_file = tmp_path / "test_config.json"
    # Use config_file for testing
```

**Use fixtures/ directory for test data:**
```python
@pytest.mark.integration
def test_with_real_audio():
    audio_file = "fixtures/audio1.wav"
    # Test with real audio file
```

## Testing Best Practices

### 1. Test One Thing at a Time

Each test should verify a single behavior.

**Good:**
```python
def test_transcribe_returns_text():
    result = transcriber.transcribe("audio.wav")
    assert result == "expected text"

def test_transcribe_handles_empty_file():
    result = transcriber.transcribe("empty.wav")
    assert result is None
```

**Bad:**
```python
def test_transcribe():
    # Tests multiple things - hard to debug when it fails
    result1 = transcriber.transcribe("audio.wav")
    assert result1 == "text"
    result2 = transcriber.transcribe("empty.wav")
    assert result2 is None
    result3 = transcriber.transcribe("missing.wav")
    assert result3 is None
```

### 2. Use Descriptive Test Names

Test names should describe what they test and the expected outcome.

**Good:**
- `test_transcribe_audio_success`
- `test_transcribe_audio_file_not_found`
- `test_config_saves_custom_glossary`

**Bad:**
- `test_1`
- `test_audio`
- `test_works`

### 3. Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_something(mocker):
    # Arrange - Set up test data and mocks
    mocker.patch("os.path.exists", return_value=True)
    transcriber = OpenAITranscriber(api_key="test-key")

    # Act - Perform the action being tested
    result = transcriber.transcribe_audio("test.wav")

    # Assert - Verify the outcome
    assert result == "expected text"
```

### 4. Don't Test Implementation Details

Test behavior, not internal implementation.

**Good:**
```python
def test_saves_configuration(tmp_path):
    config_file = tmp_path / "config.json"
    config.save(config_file)

    # Verify behavior - file was created with correct content
    assert config_file.exists()
    loaded = PushToTalkConfig.load(config_file)
    assert loaded.hotkey == config.hotkey
```

**Bad:**
```python
def test_save_calls_json_dump(mocker):
    # Tests implementation detail, not behavior
    mock_dump = mocker.patch("json.dump")
    config.save("file.json")
    mock_dump.assert_called_once()
```

### 5. Avoid Test Interdependence

Tests should be independent and runnable in any order.

**Good:**
```python
def test_feature_a():
    # Self-contained test
    pass

def test_feature_b():
    # Self-contained test
    pass
```

**Bad:**
```python
shared_state = None

def test_feature_a():
    global shared_state
    shared_state = "value"

def test_feature_b():
    # Depends on test_feature_a running first!
    assert shared_state == "value"
```

## Common Test Patterns

### Testing Error Handling

```python
def test_handles_missing_api_key(mocker):
    mocker.patch.dict(os.environ, {}, clear=True)

    with pytest.raises(ValueError) as exc_info:
        OpenAITranscriber()

    assert "API key is required" in str(exc_info.value)
```

### Testing Async Operations

```python
def test_async_save(tmp_path, mocker):
    import time

    config_file = tmp_path / "config.json"
    gui.config.hotkey = "ctrl+alt+test"

    # Trigger async save
    gui._notify_config_changed()

    # Wait for async operation
    time.sleep(0.5)

    # Verify result
    assert config_file.exists()
```

### Testing with Real Files (Integration)

```python
@pytest.mark.integration
def test_transcribe_real_audio():
    transcriber = OpenAITranscriber(api_key=os.getenv("OPENAI_API_KEY"))

    # Uses real audio file from fixtures/
    result = transcriber.transcribe_audio("fixtures/audio1.wav")

    # Verify general properties (exact text may vary)
    assert result is not None
    assert len(result) > 10
```

## Troubleshooting Tests

### Tests Fail on Headless Systems

GUI tests automatically skip on headless systems:
```python
def test_gui_feature(prepared_config_gui):
    # This test will skip if no Tk display is available
    pass
```

### Tests Are Slow

- Use `pytest-xdist` to run tests in parallel (not currently configured)
- Mark slow tests with `@pytest.mark.slow` and exclude them in dev runs
- Mock expensive operations (API calls, file I/O)

### Flaky Tests

Timing-sensitive tests may be flaky. Solutions:
- Increase timeouts
- Use mocked time instead of real time
- Avoid real threading in tests when possible

### Import Errors

Module-level imports may fail if dependencies aren't mocked. Use `test_helpers.py` stubs:
```python
# In test file, before imports
from tests.test_helpers import create_keyboard_stub, create_pyautogui_stub
import sys
import types

keyboard_stub = create_keyboard_stub()
sys.modules["pynput.keyboard"] = keyboard_stub
```

## Future Improvements

- [ ] Add performance/load tests with markers
- [ ] Set up pytest-xdist for parallel test execution
- [ ] Increase test coverage in edge cases
- [ ] Add mutation testing with `mutmut`

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
