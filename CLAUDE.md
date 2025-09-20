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

The application implements a sophisticated auto-update system that applies configuration changes in real-time while the application is running, using **variable tracing** and **debouncing** mechanisms.

#### Variable Tracing System

**What it does**: Automatically detects when any GUI field changes and triggers update callbacks.

**Implementation** (`src/config_gui.py:238-250`):
```python
def _setup_variable_traces(self):
    """Attach trace callbacks to configuration variables for live updates."""
    for var in self.config_vars.values():
        trace_id = var.trace_add("write", self._on_config_var_changed)
        self._variable_traces.append((var, trace_id))
```

**Key Components**:
- **Trace Registration**: Each Tkinter variable (StringVar, IntVar, BooleanVar, etc.) gets a "write" trace
- **Automatic Detection**: No manual polling needed - changes are detected instantly
- **Event-Driven**: Triggers `_on_config_var_changed()` whenever any field changes
- **Trace Management**: Traces can be suspended via `_suspend_change_events` to prevent infinite loops during programmatic GUI updates

#### Debouncing System

**What it does**: Prevents excessive updates during rapid user input (e.g., typing).

**Problem Without Debouncing**:
```
User types "ctrl+alt+space":
'c' → Update triggered → Component reinitialization
't' → Update triggered → Component reinitialization
'r' → Update triggered → Component reinitialization
... (16 total updates for one hotkey change!)
```

**Solution With Debouncing**:
```
User types "ctrl+alt+space":
'c' → Schedule update after debounce delay
't' → Cancel previous, schedule new update after debounce delay
'r' → Cancel previous, schedule new update after debounce delay
... (continue canceling and rescheduling)
User stops typing → Debounce delay passes → Single update executed
```

**Implementation** (`src/config_gui.py:251-267`):
```python
def _on_config_var_changed(self, *args):
    """Handle configuration variable changes from the GUI."""
    if self._suspend_change_events:
        return

    # Cancel any pending update
    if self._pending_update_job:
        self.root.after_cancel(self._pending_update_job)

    # Schedule new update with debounce delay (see code for exact timing)
    self._pending_update_job = self.root.after(1000, self._apply_config_changes)
```

#### Configuration Update Pipeline

**Step 1: Trace Fires** → `_on_config_var_changed()`
- Cancels any pending update timer
- Schedules new update after debounce delay

**Step 2: Timer Expires** → `_apply_config_changes()`
- Clears timer reference
- Calls `_notify_config_changed()`

**Step 3: Configuration Processing** → `_notify_config_changed()`
- Builds new `PushToTalkConfig` from current GUI state
- Short-circuits if no actual changes detected
- Updates internal config reference
- Calls optional `on_config_changed` callback
- Updates running application via `app_instance.update_configuration()`
- **Saves configuration to JSON file asynchronously** via `_save_config_to_file_async()`
- Refreshes status display

**Step 4: Application Update** → `PushToTalkApp.update_configuration()`
- Compares old vs new config using `requires_component_reinitialization()`
- Only reinitializes components when critical settings change
- Automatically restarts services (like hotkey detection) if they were running

#### Smart Component Reinitialization

The system intelligently determines which changes require expensive component reinitialization:

**Critical Fields** (require reinitialization):
- API keys, model settings, audio parameters, hotkeys, processing settings

**Non-Critical Fields** (runtime-only changes):
- `insertion_method`, `enable_logging`, `enable_audio_feedback`

**Implementation** (`src/push_to_talk.py:81-109`):
```python
def requires_component_reinitialization(self, other: "PushToTalkConfig") -> bool:
    """Check if component reinitialization is required."""
    non_critical_fields = {
        "insertion_method",
        "enable_logging",
        "enable_audio_feedback",
    }

    all_fields = {f.name for f in fields(self)}
    critical_fields = all_fields - non_critical_fields

    for field_name in critical_fields:
        if getattr(self, field_name) != getattr(other, field_name):
            return True
    return False
```

#### Service Continuity During Updates

**Problem**: When components are reinitialized, services like hotkey detection get stopped.

**Solution**: The system remembers service states and automatically restarts them:

```python
def _initialize_components(self):
    # Remember if hotkey service was running
    hotkey_service_was_running = (
        self.hotkey_service and self.hotkey_service.is_service_running()
    )

    # Stop and recreate components
    if self.hotkey_service:
        self.hotkey_service.stop_service()

    self.hotkey_service = HotkeyService(...)

    # Restart if it was running before and app is still running
    if hotkey_service_was_running and self.is_running:
        self.hotkey_service.start_service()
```

#### Non-Blocking Configuration Persistence

**What it does**: Automatically saves configuration changes to JSON file during runtime without blocking the GUI.

**Problem**: Previously, configuration changes during runtime were applied to the running application but not persisted to the JSON file, meaning changes would be lost on restart.

**Solution**: Asynchronous file saving with thread safety and deduplication.

**Implementation** (`src/config_gui.py:346-391`):
```python
def _save_config_to_file_async(self, filepath: str = "push_to_talk_config.json"):
    """Save configuration to JSON file asynchronously for persistence."""
    def _save_worker():
        try:
            with self._save_lock:
                if not self._save_pending:
                    return  # Another thread already completed the save

                config_data = asdict(self.config)
                with open(filepath, "w") as f:
                    json.dump(config_data, f, indent=2)

                self._save_pending = False
        except Exception as error:
            logger.error(f"Failed to auto-save configuration: {error}")
            self._save_pending = False

    # Thread-safe deduplication
    with self._save_lock:
        if self._save_pending:
            return  # Save already in progress
        self._save_pending = True

    # Start background save
    threading.Thread(target=_save_worker, daemon=True).start()
```

**Key Features**:
- **Thread-Safe**: Uses locks to prevent race conditions
- **Non-Blocking**: Saves happen in background daemon threads
- **Deduplication**: Multiple rapid changes trigger only one save
- **Error Handling**: Failures are logged but don't interrupt the GUI
- **Automatic**: Triggered by any configuration change during runtime

#### Development Guidelines

**When adding new config fields**:
1. Add the field to `PushToTalkConfig` dataclass
2. Add corresponding Tkinter variable in `ConfigurationGUI.config_vars`
3. Update `tests/test_config_gui.CONFIG_VAR_KEYS` for test coverage
4. Determine if the field requires component reinitialization and update the logic accordingly

**Testing auto-update behavior**:
- Unit tests validate trace setup and debouncing logic
- Integration tests verify end-to-end configuration updates
- Mock stubs simulate component reinitialization for reliable testing

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
