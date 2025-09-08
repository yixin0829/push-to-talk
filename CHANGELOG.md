# Changelog

All notable changes to PushToTalk will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
- Refactored logging system to use loguru. Set the global logger in `main.py` and `tests/conftest.py` once is enough.

### Deprecated
### Removed
### Fixed
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
