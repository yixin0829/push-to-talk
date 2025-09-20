# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run GUI application for end users
uv run python main.py

# Run from command line (development)
python main.py
```

### Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run unit tests only
uv run pytest tests/ -v -m "not integration"

# Run integration tests (uses real audio files)
uv run pytest tests/ -v -m integration

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_audio_recorder.py -v
```

### Code Quality
```bash
# Lint code
uv run ruff check

# Format code
uv run ruff format

# Set up pre-commit hooks (if needed)
uv run pre-commit install
```

### Building
```bash
# Windows
build.bat

# macOS
chmod +x build_macos.sh && ./build_macos.sh

# Linux
chmod +x build_linux.sh && ./build_linux.sh

# Multi-platform build script
uv run python build.py -p all
```

## Architecture Overview

PushToTalk is a Python-based speech-to-text application with a GUI configuration interface and background service architecture.

### Core Application Flow
1. **GUI Entry Point** (`main.py`) → Loads/creates config → Shows persistent configuration GUI
2. **Configuration GUI** (`src/config_gui.py`) → Manages all settings and controls application lifecycle
3. **Main Application** (`src/push_to_talk.py`) → Orchestrates all components when "Start Application" clicked
4. **Background Service** → Runs hotkey detection and audio processing pipeline

### Key Components

**Core Application Classes:**
- `PushToTalkApp` (`src/push_to_talk.py`): Main orchestrator with component lifecycle management
- `PushToTalkConfig` (`src/push_to_talk.py`): Dataclass for all configuration settings
- `ConfigurationGUI` (`src/config_gui.py`): Persistent GUI for settings and application control

**Audio Pipeline:**
- `AudioRecorder` (`src/audio_recorder.py`): PyAudio-based recording with threading
- `AudioProcessor` (`src/audio_processor.py`): Silence removal and pitch-preserving speed adjustment using pydub/psola
- `Transcriber` (`src/transcription.py`): OpenAI Whisper integration
- `TextRefiner` (`src/text_refiner.py`): GPT-based text improvement with format instructions
- `TextInserter` (`src/text_inserter.py`): Cross-platform text insertion (clipboard/sendkeys)

**Services:**
- `HotkeyService` (`src/hotkey_service.py`): Global hotkey detection with push-to-talk and toggle modes
- Audio feedback utilities (`src/utils.py`): Non-blocking start/stop sounds using playsound3
- `config/prompts.py`: Contains text refinement prompts with/without custom glossary support

### Threading Architecture

The application uses multiple threads to prevent blocking:

1. **Main Thread**: GUI and application control
2. **Hotkey Service Thread**: Global hotkey detection (keyboard library)
3. **Audio Recording Thread**: PyAudio recording operations
4. **Audio Processing Thread**: Daemon thread for transcription pipeline (doesn't block hotkey detection)
5. **Audio Feedback Threads**: Non-blocking start/stop sound playback

### Configuration System

- **Primary**: `push_to_talk_config.json` file with all settings including custom glossary
- **Fallback**: Environment variable `OPENAI_API_KEY` for API key
- **Platform-specific defaults**: Different hotkeys for macOS (cmd) vs Windows/Linux (ctrl)
- **Real-time updates**: Tk variable traces call `_notify_config_changed()` which debounces GUI edits and pushes new `PushToTalkConfig` objects into the running app via `PushToTalkApp.update_configuration()`
- **Custom Glossary**: Stored as `custom_glossary: ["term1", "term2"]` in config JSON

### Live Configuration Updates
- `_setup_variable_traces()` attaches `trace_add("write", ...)` listeners to every Tk variable once the GUI is built.
- `_on_config_var_changed()` debounces edits via `after(300, ...)` to avoid excessive reinitialization and supports headless invocation when no Tk root exists (see `tests/test_config_gui.py`).
- `_notify_config_changed()` copies glossary lists, short-circuits when values are unchanged unless `force=True`, and relays updates to `on_config_changed` callbacks and active app instances.
- When adding new config fields, update both `ConfigurationGUI.config_vars` setup and `tests/test_config_gui.CONFIG_VAR_KEYS` so tests keep covering auto-update behaviour.

### Testing Structure

- **Unit Tests**: Mock-based testing for individual components (`test_*.py`)
- **Integration Tests**: Real audio file testing (`test_integration.py`, fixtures/ directory)
- **Test Configuration**: `conftest.py` sets up loguru logging and Python path
- **Audio Fixtures**: `fixtures/audio*.wav` files with corresponding expected transcripts

## Key Implementation Details

### Audio Processing Pipeline
1. Record audio via PyAudio with configurable sample rate/channels
2. Detect and remove silence using pydub (dBFS threshold-based)
3. Apply pitch-preserving speed-up using psola library (default 1.5x)
4. Send processed audio to OpenAI Whisper API
5. Refine transcription using GPT models with custom glossary support and format instructions
6. Insert text via clipboard or sendkeys methods

### Error Handling Patterns
- Graceful fallbacks (e.g., original audio if processing fails)
- Centralized temporary file cleanup in `_process_recorded_audio()` for simplified logic
- Thread-safe operations with threading.Lock()
- Component reinitialization on configuration changes

### Cross-Platform Considerations
- Platform-specific hotkey defaults (cmd vs ctrl)
- Different audio system requirements (PortAudio dependencies)
- Text insertion method compatibility (clipboard vs sendkeys)
- Build script variations per platform

### Custom Glossary Feature

The application supports custom glossary terms to improve transcription accuracy for domain-specific vocabulary:

**Implementation:**
- Glossary stored as `List[str]` in `PushToTalkConfig.custom_glossary`
- GUI provides add/edit/delete interface with search functionality (`_create_glossary_section`)
- TextRefiner automatically switches between prompts based on glossary availability:
  - `text_refiner_prompt_w_glossary` when terms exist (formats glossary into prompt)
  - `text_refiner_prompt_wo_glossary` when no terms configured

**Key Methods:**
- `TextRefiner.set_glossary(terms: List[str])`: Update glossary terms
- `TextRefiner._get_appropriate_prompt()`: Auto-select prompt with/without glossary
- Glossary terms are sorted alphabetically in the formatted prompt

**Configuration Integration:**
- Glossary changes trigger component reinitialization via `update_configuration()`
- Terms are persisted in JSON config and restored on app startup
- GUI changes are immediately reflected in the active TextRefiner instance

## Development Tips

### When Adding Features
1. Update `PushToTalkConfig` dataclass for new settings
2. Modify GUI sections in `config_gui.py` for user controls
3. Add component reinitialization logic in `update_configuration()` if needed
4. Include corresponding unit tests with mocking

### When Modifying Audio Pipeline
1. Components are initialized in `_initialize_components()`
2. Audio processing runs in daemon threads to avoid blocking
3. Temporary file cleanup is handled centrally in `_process_recorded_audio()` for both success and error cases
4. Test with integration tests using real audio fixtures

### Configuration Changes
- Settings auto-save when "Start Application" is clicked
- Component reinitialization occurs when relevant settings change
- GUI shows real-time application status with visual indicators
- Platform-specific defaults are handled in dataclass field factories

## Important Development Instructions

When working with this codebase, adhere to these instructions that override any default behavior:

### File Creation Policy
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested by the user

### Development Approach
- Do what has been asked; nothing more, nothing less
- Focus on the specific requirements without adding unnecessary features or optimizations

### Logging System
The application uses loguru instead of Python's standard logging:
- Import: `from loguru import logger` (not `import logging`)
- Configuration: Done centrally in `main.py` and `tests/conftest.py`
- Usage: Same API as standard logging (`logger.info()`, `logger.error()`, etc.)
- No need to create logger instances with `getLogger(__name__)` in individual files

### Text Refinement Prompt System
The application uses a dual-prompt system in `src/config/prompts.py`:
- `text_refiner_prompt_w_glossary`: Used when custom glossary terms are configured
- `text_refiner_prompt_wo_glossary`: Used when no glossary terms are present
- TextRefiner automatically switches between prompts via `_get_appropriate_prompt()` method
- Custom glossary terms are formatted into the prompt dynamically using `{custom_glossary}` placeholder
