# AGENTS.md

This is the context file for guiding coding agents like Claude Sonnet/Opus, Gemini on how to work with this codebase.

## Project Overview
PushToTalk is an open-source AI dictation tool. The goal of this project is to build a frictionless AI dictation tool that streams thinking (in speech) into clear and polished text. PushToTalk uses AI to refine the transcription output and adapt to each user by incorporating custom vocabularies that reflect their specific domain knowledge. We focus on building PushToTalk as a Windows desktop application first, but the goal is to make it a cross-platform application eventually. PushToTalk is built with Python and uses `uv` as the package manager. The main dependencies are listed in [pyproject.toml](pyproject.toml).

## Development Commands

```bash
# Run application
uv run python main.py

# Run tests
uv run pytest tests/ -v                          # All tests
uv run pytest tests/ -v -m "not integration"     # Unit tests only
uv run pytest tests/ --cov=src --cov-report=html # With coverage

# Build
build_script/build.bat          # Windows
build_script/build_macos.sh     # macOS
build_script/build_linux.sh     # Linux
```

## Architecture Overview

### Application Flow
1. [main.py](main.py) → Load config → Launch GUI
2. [src/gui/](src/gui/) → Modular configuration interface
3. [src/push_to_talk.py](src/push_to_talk.py) → Orchestrate components
4. Background services → Hotkey detection + audio pipeline

### Core Components

**Application Core:**
- `PushToTalkApp` ([src/push_to_talk.py](src/push_to_talk.py)) - Main orchestrator with dependency injection
- `PushToTalkConfig` ([src/push_to_talk.py](src/push_to_talk.py)) - Pydantic model with validation
- `ConfigurationWindow` ([src/gui/configuration_window.py](src/gui/configuration_window.py)) - GUI coordinator

**Audio & Transcription:**
- [src/audio_recorder.py](src/audio_recorder.py) - PyAudio recording
- [src/transcription_base.py](src/transcription_base.py) - Abstract transcriber interface
- [src/transcriber_factory.py](src/transcriber_factory.py) - Provider factory

**Text Refinement:**
- [src/text_refiner_base.py](src/text_refiner_base.py) - Abstract refiner interface
- [src/text_refiner_factory.py](src/text_refiner_factory.py) - Refinement provider factory

**Services & Config:**
- [src/hotkey_service.py](src/hotkey_service.py) - Global hotkey detection
- [src/config/prompts.py](src/config/prompts.py) - Refinement prompts

### Key Patterns

**Pydantic Validation** - See `PushToTalkConfig` in [src/push_to_talk.py](src/push_to_talk.py)
- Runtime validation on creation and assignment

**Dependency Injection** - See `PushToTalkApp.__init__()` in [src/push_to_talk.py](src/push_to_talk.py)
- Injected components preserved during lifecycle

**Threading Architecture (Non-Blocking)**
1. **Main Thread**: GUI control and configuration
2. **Hotkey Service Thread**: Global keyboard detection (Producer) → Pushes commands to Queue
3. **Worker Thread**: Command consumer → Handles start/stop recording & audio feedback
4. **Audio Recording Thread**: Continuous PyAudio chunk reading in a loop. Separate from Worker so Worker remains responsive to STOP commands while audio is being captured.
5. **Background Processing Threads** (per-recording): Daemon threads for transcription → refinement → text insertion
   - Each recording spawns a new background thread
   - Allows immediate new recordings without waiting for API calls
   - Reduces perceived latency from 3-5s to ~100ms
6. **Initialization Threads**: Heavy components (like PyAudio) initialize in background daemon threads to prevent blocking application startup.

## Development Guidelines

For detailed guides on adding new providers or config fields, see [docs/development_guides.md](docs/development_guides.md).

### Important Instructions

#### File Creation Policy
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested by the user

#### Logging System
The application uses loguru instead of Python's standard logging:
- Import: `from loguru import logger` (not `import logging`)
- Configuration: Done centrally in `main.py` and `tests/conftest.py`
- Usage: Same API as standard logging (`logger.info()`, `logger.error()`, etc.)

#### Text Refinement Prompt System
- Default Prompts: `src/config/prompts.py` (glossary vs non-glossary)
- Custom Prompts: User configurable in GUI, overrides default. Supports `{custom_glossary}` placeholder.
