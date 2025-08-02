# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup
```bash
# Install dependencies using uv
uv sync

# Run GUI application
uv run python main_gui.py

# Run console application
uv run python main_console.py
```

### Building and Packaging
```bash
# Build Windows executable (GUI version)
.\build.bat

# Manual build with PyInstaller
uv run pyinstaller push_to_talk.spec

# For console executable: modify push_to_talk.spec to use main_console.py and set console=True
```

### Code Quality
```bash
# Format code with ruff
uv run ruff format

# Lint code with ruff
uv run ruff check

# Fix linting issues automatically
uv run ruff check --fix

# Setup pre-commit hooks
uv run pre-commit install

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

## Architecture Overview

This is a cross-platform push-to-talk speech-to-text application with dual interfaces (GUI and console) that uses OpenAI's API for transcription and text refinement. **Now supports Windows, MacOS, and Linux.**

### Core Components
- **PushToTalkApp** (`src/push_to_talk.py`): Main orchestrator with configuration management and dynamic updates
- **ConfigurationGUI** (`src/config_gui.py`): Persistent GUI interface with real-time status management
- **AudioRecorder** (`src/audio_recorder.py`): PyAudio-based recording with configurable audio settings
- **Transcriber** (`src/transcription.py`): OpenAI Whisper integration for speech-to-text
- **TextRefiner** (`src/text_refiner.py`): GPT-based text improvement and correction
- **TextInserter** (`src/text_inserter.py`): Cross-platform text insertion via pyautogui and pyperclip
- **HotkeyService** (`src/hotkey_service.py`): Global hotkey detection (Windows admin privileges required)
- **Utils** (`src/utils.py`): Cross-platform audio feedback using pygame and numpy

### Entry Points
- **main_gui.py**: GUI application with persistent configuration interface
- **main_console.py**: Console-based application for command-line usage
- **Built executable**: `dist/PushToTalk.exe` (GUI version, no console window)

### Data Flow
1. User presses hotkey → Audio recording starts with optional audio feedback
2. User releases hotkey → Recording stops, audio saved to temp file
3. Audio sent to OpenAI Whisper for transcription
4. Raw text optionally refined using GPT models
5. Refined text inserted into active window via cross-platform APIs

### Configuration System
- **File-based**: `push_to_talk_config.json` for persistent settings
- **Environment**: `OPENAI_API_KEY` environment variable support
- **GUI**: Real-time configuration with validation and testing
- **Dynamic updates**: Application can update configuration without restart

## Key Technical Details

### Cross-Platform Support
- **Text insertion**: Uses pyautogui and pyperclip for cross-platform compatibility
- **Audio feedback**: Uses pygame mixer with numpy tone generation
- **Hotkey detection**: Uses keyboard library (Windows admin privileges still required)
- **GUI**: Tkinter for cross-platform interface

### Audio Processing
- **Sample rates**: 8kHz-44.1kHz supported, 16kHz recommended for Whisper
- **Formats**: WAV files for temporary audio storage
- **Feedback**: Cross-platform audio cues using pygame with pure tone generation (880Hz start, 660Hz stop)

### Text Insertion Methods
- **sendkeys**: Character-by-character simulation using pyautogui, better for special characters
- **clipboard**: Faster method using pyperclip + pyautogui Ctrl+V, may not work in all applications

### Configuration Parameters
Key settings in `PushToTalkConfig` class:
- `openai_api_key`: Required for transcription and refinement
- `stt_model`: "gpt-4o-transcribe" or "whisper-1"
- `refinement_model`: "gpt-4.1-nano", "gpt-4o-mini", or "gpt-4o"
- `hotkey`/`toggle_hotkey`: Customizable key combinations
- `insertion_method`: "sendkeys" or "clipboard"
- `enable_text_refinement`: Toggle GPT text improvement
- `enable_audio_feedback`: Toggle audio feedback sounds

## Development Workflow

### Making Changes
1. Test changes with both GUI and console applications
2. Ensure proper cross-platform compatibility for new features
3. Validate OpenAI API integration with proper error handling
4. Test text insertion in various applications across platforms
5. Pre-commit hooks automatically format and lint code

### Building for Distribution
1. Use `build.bat` for Windows GUI executable
2. Modify `push_to_talk.spec` for console builds or customization
3. Test executable on clean systems without Python installed
4. Consider antivirus false positives with PyInstaller executables
5. Update hiddenimports in `.spec` file when adding new dependencies

### Configuration Testing
- Use GUI "Test Configuration" button for API validation
- Test hotkey combinations don't conflict with system shortcuts
- Verify text insertion works in target applications across platforms
- Check audio settings produce clear recordings for transcription accuracy
- Test audio feedback works across different audio systems

### Dependencies Management
- Core dependencies: keyboard, numpy, openai, pyaudio, pyautogui, pyperclip, pygame
- Dev dependencies: pre-commit, pyinstaller, python-dotenv, ruff
- PyInstaller spec may need updates for cross-platform builds (currently Windows-focused)
