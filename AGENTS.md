# AGENTS.md

This file provides comprehensive guidance for AI code agents (Claude Code, OpenAI Codex, GitHub Copilot, etc.) when working with the PushToTalk codebase.

## Project Overview

**PushToTalk** is a Python-based speech-to-text application with AI-powered transcription refinement and automatic text insertion. It features:

- **Core Purpose**: Push-to-talk hotkey → audio recording → Whisper transcription → GPT refinement → auto text insertion
- **Architecture**: Multi-threaded GUI application with persistent configuration interface
- **Key Technologies**: PyAudio, pydub, OpenAI APIs, tkinter, threading
- **Platform Support**: Windows (primary), macOS/Linux (planned)
- **Package Manager**: uv (Python package manager)

### Key Business Logic
1. User holds hotkey → starts recording
2. Audio processed (silence removal, speed adjustment)
3. OpenAI Whisper transcribes audio
4. GPT models refine transcription (with optional custom glossary)
5. Text automatically inserted into active window

## Build and Test Commands

### Essential Commands
```bash
# Run application (development)
uv run python main.py

# Run all tests
uv run pytest tests/ -v

# Code quality checks (REQUIRED before PR)
uv run ruff format .       # Format code
uv run ruff check . --fix  # Lint and auto-fix issues

# Build executable
build.bat                  # Windows
uv run python build.py -p all  # Cross-platform
```

### Testing Commands
```bash
# Unit tests only (mocked components)
uv run pytest tests/ -v -m "not integration"

# Integration tests (uses real audio files)
uv run pytest tests/ -v -m integration

# Coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Specific test file
uv run pytest tests/test_audio_recorder.py -v
```

## Code Style Guidelines

### Python Standards
- **Package Manager**: ALWAYS use `uv` for dependency management and script execution
- **Script Execution**: Use `uv run` prefix for all Python scripts and command line tools
- **Type Hints**: Use PEP604 union types (`str | None`) and PEP585 generics (`list[str]` not `List[str]`)
- **Imports**: Prefer absolute imports, group by standard/third-party/local
- **Linting**: Follow ruff configuration (equivalent to black + flake8)
- **Line Length**: 88 characters (black default)

### Pre-PR Requirements
**CRITICAL**: Before creating any pull request, ALWAYS run:
```bash
uv run ruff format .       # Format all code
uv run ruff check . --fix  # Lint and auto-fix issues
```

### Logging System
- **CRITICAL**: Use loguru, NOT standard logging
```python
# ✅ Correct
from loguru import logger
logger.info("message")

# ❌ Wrong
import logging
logging.getLogger(__name__).info("message")
```

### Architecture Patterns
- **Configuration**: Centralized in `PushToTalkConfig` dataclass
- **Error Handling**: Graceful fallbacks with centralized cleanup
- **Threading**: Daemon threads for non-blocking operations
- **GUI**: tkinter with real-time status updates

## Testing Instructions

### Test Structure
- **Unit Tests**: `test_*.py` files with mocking via unittest.mock
- **Integration Tests**: `test_integration.py` using real audio fixtures
- **Fixtures**: `fixtures/audio*.wav` with corresponding expected transcripts
- **Configuration**: `conftest.py` sets up loguru logging and Python path

### Writing New Tests
1. **Unit Tests**: Mock external dependencies (OpenAI, PyAudio, file system)
2. **Integration Tests**: Use real audio files in `fixtures/` directory
3. **Thread Safety**: Test with `threading.Lock()` and daemon threads
4. **Configuration**: Test component reinitialization on config changes

### Test Data Management
- Audio fixtures are committed to repository (small WAV files)
- Expected transcripts stored as constants in test files
- Sensitive data (API keys) use environment variables or mocking

## Security Considerations

### API Key Management
- **Primary**: Store in `push_to_talk_config.json` (user's local config)
- **Fallback**: Environment variable `OPENAI_API_KEY`
- **Never**: Commit API keys to repository
- **Testing**: Mock all OpenAI API calls

### Sensitive Data Protection
- **Audio Files**: Temporary files are cleaned up centrally in `_process_recorded_audio()`
- **Configuration**: Local JSON file, not version controlled
- **Logging**: Avoid logging sensitive information (API keys, audio content)

### External Dependencies
- **OpenAI APIs**: Whisper (transcription) and GPT (refinement)
- **Audio System**: PyAudio requires PortAudio (platform-specific)
- **System Integration**: Global hotkeys, clipboard access, window focus

## Development Workflows

### Adding New Features
1. **Configuration**: Update `PushToTalkConfig` dataclass
2. **GUI**: Add controls in `config_gui.py`
3. **Core Logic**: Modify relevant component classes
4. **Integration**: Update `update_configuration()` for component reinitialization
5. **Testing**: Add unit tests with mocking + integration tests if needed

### Modifying Audio Pipeline
- **Components**: Initialized in `_initialize_components()`
- **Processing**: Runs in daemon threads (non-blocking)
- **Cleanup**: Centralized temporary file management
- **Testing**: Use integration tests with real audio fixtures

### Configuration Changes
- Auto-save when "Start Application" clicked
- Component reinitialization when relevant settings change
- GUI shows real-time status with visual indicators
- Platform-specific defaults handled in dataclass factories

## Commit and PR Guidelines

### Commit Message Format
```
type(scope): brief description

- Bullet point details if needed
- Reference issue numbers: #123

Examples:
feat(audio): add pitch-preserving speed adjustment
fix(gui): resolve hotkey display on macOS
refactor(config): migrate to dataclass structure
test(integration): add audio processing fixtures
```

### Pull Request Guidelines
1. **Pre-PR Linting**: MANDATORY - Run `uv run ruff format .` and `uv run ruff check . --fix`
2. **Title**: Clear, descriptive summary
3. **Description**: Problem solved, approach taken, testing done
4. **Testing**: Include test results and coverage impact
5. **Breaking Changes**: Document any API or configuration changes
6. **Dependencies**: Note any new package requirements (managed via `uv`)

## Large Components and Gotchas

### Threading Architecture Complexity
- **5+ Threads**: GUI, hotkey detection, audio recording, processing, feedback
- **Critical**: Audio processing thread is daemon (doesn't block shutdown)
- **Synchronization**: Use `threading.Lock()` for shared resources
- **Testing**: Mock threading components carefully

### Cross-Platform Considerations
- **Hotkeys**: Different defaults (cmd vs ctrl) per platform
- **Audio**: PortAudio dependencies vary by OS
- **Text Insertion**: Clipboard vs sendkeys compatibility
- **Building**: Platform-specific scripts and dependencies

### OpenAI API Integration
- **Rate Limits**: Handle API errors gracefully
- **Cost Management**: Audio processing affects API usage
- **Model Updates**: GPT model changes may affect refinement quality
- **Testing**: Always mock API calls in automated tests

### Custom Glossary System
- **Dual Prompts**: Automatic switching between glossary/non-glossary prompts
- **Dynamic Updates**: Real-time glossary changes affect active TextRefiner
- **Performance**: Glossary terms are sorted alphabetically in prompts
- **Integration**: Changes trigger component reinitialization

## Development Environment Setup

### Prerequisites
```bash
# Install uv (Python package manager) - REQUIRED
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix
# or download from https://github.com/astral-sh/uv

# Install dependencies (ALWAYS use uv)
uv sync

# Set up pre-commit hooks (optional)
uv run pre-commit install

# IMPORTANT: Always use `uv run` for any Python scripts or CLI tools
# Examples:
uv run python main.py
uv run pytest tests/
uv run ruff format .
```

### Platform-Specific Requirements
- **Windows**: Visual Studio Build Tools (for PyAudio)
- **macOS**: Xcode Command Line Tools, PortAudio via homebrew
- **Linux**: ALSA development headers, PortAudio libraries

### Environment Variables
```bash
# Required for API access
export OPENAI_API_KEY="your-api-key-here"

# Optional: Override default config path
export PUSHTOALK_CONFIG_PATH="/custom/path/config.json"
```

## File Organization and Key Paths

### Core Application Files
- `main.py`: Entry point and loguru configuration
- `src/push_to_talk.py`: Main orchestrator and configuration dataclass
- `src/config_gui.py`: Persistent GUI interface
- `push_to_talk_config.json`: User configuration (not version controlled)

### Component Modules
- `src/audio_recorder.py`: PyAudio recording with threading
- `src/audio_processor.py`: Silence removal and speed adjustment
- `src/transcription.py`: OpenAI Whisper integration
- `src/text_refiner.py`: GPT-based text improvement
- `src/text_inserter.py`: Cross-platform text insertion
- `src/hotkey_service.py`: Global hotkey detection
- `src/config/prompts.py`: Text refinement prompt templates

### Build and Test Infrastructure
- `build.py`, `build.bat`, `build_*.sh`: Platform-specific build scripts
- `tests/`: Unit and integration test suites
- `fixtures/`: Audio test data with expected transcripts
- `pyproject.toml`: Project dependencies and tool configuration

## Integration Points and APIs

### OpenAI Integration
- **Whisper API**: Audio transcription (supports various audio formats)
- **GPT Models**: Text refinement with custom glossary integration
- **Error Handling**: Graceful fallbacks for API failures
- **Configuration**: Model selection via config file

### System Integration
- **Global Hotkeys**: Cross-platform via `keyboard` library
- **Audio System**: PyAudio for recording, pydub for processing
- **Text Insertion**: Clipboard and SendKeys methods
- **GUI Framework**: tkinter with threading for responsiveness

### Configuration Integration
- **JSON Config**: All settings persisted locally
- **Real-time Updates**: GUI changes trigger component reinitialization
- **Platform Defaults**: OS-specific hotkey and path defaults
- **Validation**: Input validation in GUI with error handling

## Performance and Scalability Notes

### Audio Processing Performance
- **Speed Adjustment**: Pitch-preserving 1.5x speedup reduces API costs
- **Silence Removal**: dBFS-based detection reduces processing time
- **Temporary Files**: Automatic cleanup prevents disk usage buildup
- **Threading**: Daemon threads prevent blocking user interface

### Memory Management
- **Audio Buffers**: Cleaned up immediately after processing
- **Configuration**: Lightweight dataclass structure
- **GUI**: Minimal state retention, real-time updates
- **Threading**: Proper thread cleanup on application shutdown

### API Cost Optimization
- **Audio Processing**: Speed adjustment reduces transcription time/cost
- **Silence Removal**: Eliminates unnecessary API calls
- **Caching**: No caching implemented (single-use transcription)
- **Model Selection**: Configurable models for cost/quality tradeoffs
