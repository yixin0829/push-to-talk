# CLAUDE.md/GEMINI.md/AGENTS.md

Coding agent guidance for working with this codebase for Claude, Gemini and other LLM coding agents. This file is used to guide the LLM coding agents on how to work with this codebase including high-level structure, development conventions, testing, preferred packages, and other development guidelines.

## Development Commands

```bash
# Run application
uv run python main.py

# Run tests
uv run pytest tests/ -v                          # All tests
uv run pytest tests/ -v -m "not integration"     # Unit tests only
uv run pytest tests/ --cov=src --cov-report=html # With coverage

# Code quality
uv run ruff check    # Lint
uv run ruff format   # Format

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
- [src/transcription_openai.py](src/transcription_openai.py) - OpenAI Whisper
- [src/transcription_deepgram.py](src/transcription_deepgram.py) - Deepgram API
- [src/transcriber_factory.py](src/transcriber_factory.py) - Provider factory

**Text Refinement:**
- [src/text_refiner_base.py](src/text_refiner_base.py) - Abstract refiner interface
- [src/text_refiner_openai.py](src/text_refiner_openai.py) - OpenAI GPT refinement
- [src/text_refiner_cerebras.py](src/text_refiner_cerebras.py) - Cerebras API refinement
- [src/text_refiner_factory.py](src/text_refiner_factory.py) - Refinement provider factory

**Text Insertion & Utilities:**
- [src/text_inserter.py](src/text_inserter.py) - Clipboard and keyboard text insertion

**Services & Config:**
- [src/hotkey_service.py](src/hotkey_service.py) - Global hotkey detection
- [src/config/hotkey_aliases.json](src/config/hotkey_aliases.json) - Key alias mappings
- [src/config/prompts.py](src/config/prompts.py) - Refinement prompts
- [src/utils.py](src/utils.py) - Audio feedback utilities

### GUI Modular Structure
See [src/gui/](src/gui/) for all modules. Each module under 350 lines for maintainability.
- [src/gui/prompt_section.py](src/gui/prompt_section.py) - Custom refinement prompt editor

### Key Patterns

**Pydantic Validation** - See `PushToTalkConfig` in [src/push_to_talk.py](src/push_to_talk.py)
- Runtime validation on creation and assignment
- Custom validators for provider, hotkeys, numeric ranges

**Dependency Injection** - See `PushToTalkApp.__init__()` in [src/push_to_talk.py](src/push_to_talk.py)
- Optional component parameters for testing
- Injected components preserved during lifecycle
- Default factory methods create production instances

**Multi-Provider STT** - See [src/transcriber_factory.py](src/transcriber_factory.py)
- Factory pattern for provider abstraction
- OpenAI: whisper-1, gpt-4o-transcribe, gpt-4o-mini-transcribe
- Deepgram: nova-3 (default), nova-2, base, enhanced, whisper-medium

**Multi-Provider Text Refinement** - See [src/text_refiner_factory.py](src/text_refiner_factory.py)
- Factory pattern for provider abstraction
- OpenAI: gpt-4.1-nano, gpt-4o-mini, gpt-4o
- Cerebras: llama-3.3-70b (default), llama-3.1-70b, and other Cerebras models

**Configuration System**
- Primary: `push_to_talk_config.json` (all settings + glossary)
- Fallback: Environment variables for API keys
- Live updates: GUI variable tracing → debounced updates → component reinitialization
- See [src/gui/configuration_window.py](src/gui/configuration_window.py) for implementation

**Threading**
1. Main: GUI control
2. Hotkey Service: Global detection (Producer) -> Pushes commands to Queue
3. Worker Thread: Consumes commands -> Handles Audio Recording & Feedback (Consumer)
4. Audio Recording: PyAudio operations (initialized once at startup)
5. Transcription: Daemon processing pipeline

## Development Guidelines

### Adding New Config Fields
1. Add to `PushToTalkConfig` Pydantic model in [src/push_to_talk.py](src/push_to_talk.py)
2. Add GUI control in appropriate [src/gui/](src/gui/) section
3. Update `requires_component_reinitialization()` if needed
4. Add tests to [tests/test_config_gui.py](tests/test_config_gui.py)

### Adding New Transcription Providers
1. Create new class inheriting from [src/transcription_base.py](src/transcription_base.py)
2. Implement `transcribe()` method
3. Register provider in [src/transcriber_factory.py](src/transcriber_factory.py)
4. Add configuration field and validation in `PushToTalkConfig`
5. Add GUI section in [src/gui/api_section.py](src/gui/api_section.py)
6. Add tests to [tests/test_transcription_[provider].py](tests/)
7. Update [README.md](README.md) with new models and configuration

### Adding New Text Refinement Providers
1. Create new class inheriting from [src/text_refiner_base.py](src/text_refiner_base.py)
2. Implement `refine()` and `set_glossary()` methods
3. Implement `_get_appropriate_prompt()` for dual-prompt support
4. Register provider in [src/text_refiner_factory.py](src/text_refiner_factory.py)
5. Add configuration fields (`refinement_provider`, `refinement_model`, `[provider]_api_key`) to `PushToTalkConfig`
6. Add GUI sections in [src/gui/api_section.py](src/gui/api_section.py)
7. Add tests to [tests/test_text_refiner.py](tests/test_text_refiner.py)
8. Update [README.md](README.md) with new models and configuration

### Modifying Audio Pipeline
- Components initialized in `_initialize_components()` - see [src/push_to_talk.py](src/push_to_talk.py)
- Transcription runs in daemon threads (non-blocking)
- Temp file cleanup in `_process_recorded_audio()`
- Test with integration tests in [tests/](tests/) using real audio fixtures

### Custom Glossary
- Stored in `PushToTalkConfig.custom_glossary` as `List[str]`
- GUI management in [src/gui/glossary_section.py](src/gui/glossary_section.py)
- Prompt selection in base refiner classes (`TextRefinerBase`, `TextRefinerOpenAI`, `CerebrasTextRefiner`) via `_get_appropriate_prompt()`
- Prompts in [src/config/prompts.py](src/config/prompts.py) with dual-prompt system for glossary vs. non-glossary modes

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
The application uses a flexible prompt system with default and custom prompt support:

**Default Prompts** (`src/config/prompts.py`):
- `text_refiner_prompt_w_glossary`: Used when custom glossary terms are configured
- `text_refiner_prompt_wo_glossary`: Used when no glossary terms are present
- TextRefiner automatically switches between prompts via `_get_default_developer_prompt()` method

**Custom Prompts**:
- Users can configure `custom_refinement_prompt` in `PushToTalkConfig`
- When set, custom prompt overrides the default prompt selection
- The `{custom_glossary}` placeholder can be used in custom prompts
- Placeholder is substituted with formatted glossary terms via `_format_custom_prompt()` method
- If placeholder is absent, glossary is simply not included (user's choice)

**Implementation**:
- Base class: `set_custom_prompt()`, `get_current_prompt()` in [src/text_refiner_base.py](src/text_refiner_base.py)
- Custom prompt formatting: `_format_custom_prompt()` in each refiner implementation
- GUI: [src/gui/prompt_section.py](src/gui/prompt_section.py) - multiline text editor with copy default buttons
