# Changelog

All notable changes to PushToTalk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Context manager support to `AudioRecorder` for reliable resource cleanup with `__enter__` and `__exit__` methods
- Custom exception hierarchy in `src/exceptions.py` with `PushToTalkError`, `ConfigurationError`, `APIError`, `AudioRecordingError`, `TranscriptionError`, `TextRefinementError`, `TextInsertionError`, and `HotkeyError`
- Constants for magic numbers: `TEXT_REFINEMENT_MIN_LENGTH` (20 characters) and `HOTKEY_SERVICE_THREAD_TIMEOUT_SECONDS` (5.0 seconds)

### Changed
- Replaced heavyweight `pyautogui` dependency with lightweight `pyperclip` + `pynput` for clipboard operations and keyboard control
- Improved exception handling to use `ConfigurationError` instead of generic `ValueError` for configuration issues
- Enhanced audio cleanup error handling to prevent `NameError` during nested exception handling

### Removed
- `pyautogui` dependency (replaced with `pynput` for keyboard operations)
- `get_active_window_title()` functionality from text inserter (was only used for logging)

### Fixed
- Resource leaks in `AudioRecorder` by implementing proper context manager protocol
- Potential `NameError` in nested exception handlers by checking variable existence before use
- Exception variable shadowing in error cleanup paths

### Technical
- Optimized hotkey alias loading by replacing `@functools.lru_cache(maxsize=1)` with class-level caching
- Added Windows DPI awareness support with fallback mechanisms
- Improved error categorization and debugging with custom exception types

### Documentation
### Security

## [0.5.0] - 2025-12-26

### Added
- **Multi-provider STT support**: Choose between OpenAI (whisper-1, gpt-4o-transcribe) and Deepgram (nova-3, nova-2, enhanced) transcription services
- **Modular GUI Architecture**: Configuration interface refactored into focused, single-responsibility components
  - Separated GUI into 8 specialized modules: API settings, audio configuration, hotkeys, text insertion, glossary, status display, validation, and persistence
  - Each module under 350 lines for improved maintainability
  - Clear separation of concerns with reusable section components
- **Pydantic Configuration Validation**: Robust runtime validation for all configuration settings
  - Automatic type coercion and validation on attribute assignment
  - Built-in field constraints (numeric ranges, allowed values)
  - Custom validators for provider selection, hotkey uniqueness, and parameter ranges
  - Clear, structured error messages for invalid configurations
- **Dependency Injection Pattern**: Constructor-based component injection for better testability
  - Optional component parameters in `PushToTalkApp.__init__()` with default factory methods
  - Injected components preserved throughout application lifecycle
  - Enables mock injection in tests without affecting production code
- **Hotkey Aliases Configuration**: Externalized key mappings to JSON for easier customization
  - User-editable `src/config/hotkey_aliases.json` file
  - LRU caching for efficient alias lookups
  - Non-developers can add aliases without code changes
- **Hotkey Recording UI**: Interactive "Record" button for capturing hotkey combinations
  - Visual feedback during recording with countdown timer
  - Easy hotkey configuration without manual typing
- **Multi-provider Text Refinement**: Support for OpenAI GPT and Cerebras for text refinement
  - Factory pattern for dynamic provider selection
  - Provider-specific configuration in GUI
- Factory pattern for transcriber abstraction with dynamic provider selection in GUI
- Enhanced debug mode saves recorded audio files with timestamps for troubleshooting
- Live configuration updates with automatic JSON persistence
- Unit tests for utils, push_to_talk, and transcription providers (80%+ coverage)
- **Custom Refinement Prompt**: User-configurable text refinement prompts
  - GUI section for editing custom system prompts with multiline text input
  - Support for `{custom_glossary}` placeholder to include glossary terms dynamically
  - "Copy Default" buttons to use default prompts as starting point
  - Collapsible reference section showing default prompt templates
  - Clear button to revert to default behavior

### Changed
- **Configuration System**: Migrated from dataclass to Pydantic BaseModel with validation
  - `PushToTalkConfig` now validates all fields on creation and assignment
  - Changed serialization from `asdict()` to `model_dump()`
  - Enhanced error handling with structured validation errors
- **GUI Architecture**: Refactored from monolithic `config_gui.py` to modular `src/gui/` package
  - `configuration_window.py`: Main orchestrator (~516 lines, down from 1500+)
  - `api_section.py`: API configuration (~586 lines)
  - `audio_section.py`: Audio settings (~100 lines)
  - `hotkey_section.py`: Hotkey configuration (~210 lines)
  - `hotkey_recorder.py`: Interactive hotkey recording (~282 lines)
  - `prompt_section.py`: Custom refinement prompts (~278 lines)
  - `glossary_section.py`: Glossary management (~281 lines)
  - `settings_section.py`: Text insertion & feature flags (~151 lines)
  - `status_section.py`: Application status display (~123 lines)
  - `validators.py`: Configuration validation (~153 lines)
  - `config_persistence.py`: Async file I/O (~98 lines)
- **Component Initialization**: Added smart reinitialization logic that preserves injected dependencies
  - Components only recreated when configuration changes require it
  - Injected test mocks preserved throughout lifecycle
  - Service states maintained during updates (auto-restart)
- Refactored to use loguru for logging
- GUI now uses variable tracing with debounced updates
- Renamed `transcription.py` → `transcription_openai.py`
- Renamed `text_refiner.py` → `text_refiner_openai.py`
- Simplified integration tests (removed 221 lines)
- Text insertion now always uses clipboard method (removed sendkeys option)
- Replaced `keyboard` library with `pynput` for more reliable hotkey detection

### Removed
- Removed Text Insertion Settings section from GUI (insertion delay is now fixed at 0.005 seconds)
- Removed `insertion_delay` configuration parameter from config file and PushToTalkConfig
- Audio processing layer (`audio_processor.py`) for architectural simplification (no silence removal or pitch-preserving speed adjustment)
- Dependencies: numpy, soundfile, psola, pydub, keyboard
- CLAUDE.md and GEMINI.md (consolidated into AGENTS.md using symbolic links)
- `insertion_method` configuration field - application now exclusively uses clipboard pasting for text insertion

### Fixed
- Hotkey service inactivity by switching from `keyboard` to `pynput` library
- Config overwrite during initialization and in tests

### Technical
- **Type Safety**: Added comprehensive type hints including `TranscriberBase` and `TextRefinerBase` abstract classes
- **Component Lifecycle**: Implemented `force_recreate` parameter for controlled component reinitialization
- **Thread Safety**: Injected component preservation during configuration updates
- **Testing Infrastructure**: Mock components can now be injected and persist through app lifecycle
- **Factory Pattern**: Introduced `TranscriberFactory` and `TextRefinerFactory` for provider abstraction
- **Command Queue Pattern**: Implemented command queue and worker thread pattern for audio recording

### Documentation
- Added `AGENTS.md` for LLM coding agent guidance
- Added `docs/development_guides.md` for extending the application with custom providers
- Updated CLAUDE.md with comprehensive architecture documentation
  - Added "Modular GUI Architecture" section with package structure
  - Added "Configuration Validation with Pydantic" section with examples
  - Added "Dependency Injection Pattern" section with usage guidelines
  - Added "Hotkey Aliases Configuration" section
  - Updated all references from dataclass to Pydantic model
- Updated README.md to mention validated Pydantic configuration models and multi-provider support
- Updated CONTRIBUTING.md with new project structure showing modular GUI package
- Enhanced `tests/README.md` with comprehensive testing documentation

### Security

## [0.4.0] - 2025-09-06

### Added
- **Custom Glossary System**: Comprehensive glossary management for domain-specific terms, acronyms, and pronunciations
  - GUI interface for adding, editing, and deleting glossary terms
  - Search functionality for managing existing terms
  - Automatic integration with text refinement prompts
  - Persistent storage in configuration files
- **Voice Formatting Instruction**: Customizable tone and how the transcription will get formatted (e.g. email, to-do, bullet points, etc.)

### Changed
- Enhanced text refinement system to automatically include glossary terms
- Improved TextRefiner to switch between prompts with and without glossary automatically
- Updated GUI configuration interface with dedicated Language settings section

### Technical
- Extended configuration schema to support custom glossary arrays
- Enhanced prompt management system for context-aware text refinement

## [0.3.0] - 2025-08-02

### Added
- **Smart Audio Processing Pipeline**: Automatic silence removal and pitch-preserving speed adjustment
  - Configurable silence threshold (-16 dBFS default) for noise removal
  - Minimum silence duration settings (400ms default) for natural speech patterns
  - Pitch-preserving time-scale modification using PSOLA algorithm
  - Speed factor adjustment (1.5x default) for faster transcription
- **Debug Mode**: Optional debug file generation for audio processing analysis
  - Processed audio files saved to current directory when enabled
  - Detailed processing metadata logging

### Changed
- **Enhanced Threading Architecture**: Non-blocking, high-performance audio processing
  - Daemon threads for audio processing to prevent application hanging
  - Thread-safe processing with `threading.Lock()` protection
  - Parallel audio feedback in separate threads for immediate response
  - GUI thread remains responsive during audio processing operations
- **Reduced Transcription Latency**: Significant performance improvements through audio optimization
- **Lower API Costs**: Reduced audio duration through smart silence removal

### Technical
- Integrated `pydub` for advanced audio manipulation and silence detection
- Added `psola` library for pitch-preserving time-scale modification
- Implemented comprehensive threading architecture with proper lifecycle management
- Enhanced error handling and cleanup for audio processing pipeline

### Performance
- Up to 40% reduction in transcription time through audio processing
- Reduced OpenAI API costs through shorter audio submissions
- Improved application responsiveness with non-blocking architecture

## [0.2.0] - 2025-07-27

### Added
- **Persistent GUI Interface**: Complete graphical configuration and control system
  - Real-time status monitoring with visual indicators (green = running, gray = stopped)
  - Integrated welcome section with application guidance
  - Organized settings sections: API, Audio, Hotkeys, Text Insertion
  - Active settings display when application is running
  - Easy start/stop application control with persistent interface
- **Executable Packaging**: Standalone Windows application distribution
  - `PushToTalk.exe` for end-user deployment
  - Automated build scripts for cross-platform packaging
  - No Python installation required for end users
- **Enhanced User Experience Flow**:
  - Single-window setup and control interface
  - Multiple start/stop cycles without closing interface
  - Built-in configuration validation and testing

### Changed
- Migrated from console-based to GUI-first application architecture
- Improved configuration management with visual validation
- Enhanced error handling and user feedback through GUI notifications
- Streamlined installation process for non-technical users

### Technical
- Implemented `tkinter`-based GUI with modern design patterns
- Added comprehensive configuration validation and testing functionality
- Enhanced packaging system with PyInstaller integration
- Improved logging system optimized for GUI applications

### Demo
- **Application Walkthrough**: https://www.loom.com/share/fbabb2da83c249d3a0a09b3adcc4a4e6
  - Complete GUI interface demonstration
  - Configuration setup and validation process
  - Real-time status monitoring showcase
  - Push-to-talk functionality in action

## [0.1.0] - 2025-07-26

### Added
- **Initial Release**: Console-based speech-to-text application
- **Core Speech-to-Text**: OpenAI Whisper integration for accurate transcription
- **Text Refinement**: GPT model integration for improving transcription quality
- **Push-to-Talk Recording**: Customizable hotkey-based audio recording
- **Auto Text Insertion**: Automatic text insertion into active windows
  - Support for `clipboard` and `sendkeys` insertion methods
  - Configurable insertion delay for different applications
- **Global Hotkey Support**: System-wide hotkey detection using `keyboard` library
- **Audio Configuration**: Customizable sample rate, chunk size, and channel settings
- **OpenAI API Integration**: Support for multiple Whisper and GPT models
- **Configuration Management**: JSON-based configuration with environment variable support
- **Audio Feedback**: Optional audio cues for recording start/stop events
- **Comprehensive Logging**: Detailed logging system for debugging and monitoring

### Technical
- **Core Components**:
  - `AudioRecorder`: PyAudio-based recording with configurable parameters
  - `Transcriber`: OpenAI Whisper API integration
  - `TextRefiner`: GPT-based text improvement system
  - `TextInserter`: Cross-platform text insertion using pyautogui and pyperclip
  - `HotkeyService`: Global hotkey detection and management
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility
- **Modular Architecture**: Component-based design for maintainability and testing

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backwards compatible manner
- **PATCH** version when making backwards compatible bug fixes

## Release Types

- **Major Releases** (X.0.0): Significant architectural changes, new core features
- **Minor Releases** (X.Y.0): New features, enhancements, backwards compatible changes
- **Patch Releases** (X.Y.Z): Bug fixes, security updates, minor improvements

## Links

- [Latest Release](https://github.com/yixin0829/push-to-talk/releases/latest)
- [All Releases](https://github.com/yixin0829/push-to-talk/releases)
- [Issues and Roadmap](https://github.com/yixin0829/push-to-talk/issues)
- [Contributing Guidelines](https://github.com/yixin0829/push-to-talk/blob/main/CONTRIBUTING.md)
