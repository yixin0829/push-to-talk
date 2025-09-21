# Changelog

All notable changes to PushToTalk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### TODOs
- [ ] Fix exe build cannot download whisper.cpp model issue. Even if I downloaded the model in advance, the system failed to load it during transcription.
- [ ] Processes are not closed gracefully when the application is stopped or closed directly.

### Added
- **Enhanced Logging and Observability**: Comprehensive improvements to logging system for better debugging and performance monitoring
  - Added correlation IDs to track operations end-to-end across the audio processing pipeline
  - Performance timing and metrics for all major operations (audio processing, transcription, text refinement)
  - Enhanced error messages with contextual information and suggested remediation steps
  - User-friendly status logs for long-running operations with progress indicators
  - Startup validation logging with configuration checks and warnings
  - Optimized log levels to reduce verbosity while maintaining essential information
  - Detailed performance metrics including processing ratios, throughput rates, and efficiency statistics
  - Migrated to loguru for enhanced logging capabilities with better formatting and features
- **Local Whisper Model Support**: Comprehensive local speech-to-text transcription using whisper.cpp (via pywhispercpp) with GPU acceleration capabilities, on-demand model downloads, and seamless integration with existing workflow.
  - Local Whisper transcriber with automatic GPU/CPU detection and optimization
  - Model management system with download progress dialogs and status indicators
  - Enhanced GUI with model type selection (OpenAI API vs Local Whisper)
  - Support for 12 Whisper model variants matching whisper.cpp make targets: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3, large-v3-turbo
  - GPU acceleration support with automatic device and compute type selection
  - Transcriber factory pattern for flexible model switching
- **Enhanced Model Download UX**: Improved user experience for local Whisper model downloads
  - Pre-start confirmation dialog when attempting to start with undownloaded models
  - Smart download options: download model, switch to OpenAI API, or cancel
  - Progress dialogs with automatic closure (3 seconds) and real-time status updates
  - Automatic application startup after successful model downloads
- Added unit tests for utils and push_to_talk to reach 80% coverage.
- Live configuration callbacks in the GUI so running sessions immediately pick up updated settings and glossary edits.
- **Non-blocking configuration persistence**: Runtime GUI changes are now automatically saved to JSON file asynchronously, ensuring changes persist across application restarts without blocking the user interface.
- **Enhanced Debug Mode**: Debug mode now provides dual functionality - saves processed audio files for debugging AND enables DEBUG level logging for detailed execution traces. Logging level changes are applied dynamically during runtime via the `set_debug_logging()` function in `src/utils.py`.

### Changed
- **Refactored local Whisper implementation**: Migrated from faster-whisper to whisper.cpp (via pywhispercpp) for improved performance and simplicity
- **Updated model cache directory**: Windows users now have models stored in `%LOCALAPPDATA%\pywhispercpp\pywhispercpp\models` for better platform compliance
- **Updated documentation**: All references to "faster-whisper" in documentation, comments, and variable names have been updated to reflect the migration to "pywhispercpp"
- **Updated hotkey system**: Migrated from `keyboard` library to `pynput` library for more reliable global hotkey detection across platforms
- **Lightweight GPU detection**: Replaced heavy PyTorch-based GPU detection with zero-dependency subprocess nvidia-smi calls, reducing memory footprint by ~2GB while maintaining full CUDA acceleration support
- **Refactored logging system**: Migrated to loguru for enhanced logging capabilities. Global logger configuration centralized in `main.py` and `tests/conftest.py`
- Configuration GUI now traces Tk variables, debounces updates, and refreshes the status banner whenever settings change mid-session.

### Deprecated

### Removed

### Fixed
- **Fixed hotkey service reliability**: Migrated from `keyboard` library to `pynput` library for improved global hotkey detection and cross-platform stability
- **Fixed pywhispercpp API compatibility**: Resolved model downloading error ("_pywhispercpp.whisper_full_params' object has no attribute 'model_path'") by updating to correct pywhispercpp API usage with `WhisperModel(model=..., n_threads=..., print_realtime=..., print_progress=...)`
- **Fixed GPU detection system**: Replaced heavy PyTorch dependency with lightweight subprocess-based nvidia-smi calls for CUDA GPU detection, reducing memory footprint by ~2GB while maintaining full GPU acceleration support
- **Fixed CMD window suppression**: Improved GPU detection to suppress console windows during nvidia-smi calls for cleaner user experience

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
- Comprehensive test suite for local Whisper components (60+ tests covering LocalWhisperManager, LocalWhisperTranscriber, and TranscriberFactory)
- Updated test infrastructure to support pywhispercpp API testing with proper mocking and subprocess simulation

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
