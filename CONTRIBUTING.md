# Contributing to PushToTalk

Thank you for considering contributing to PushToTalk! This document provides guidelines and information to help you contribute effectively to our AI-powered speech-to-text application.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Features](#suggesting-features)
    - [Submitting Pull Requests](#submitting-pull-requests)
        - [Before You Start](#before-you-start)
        - [Pull Request Process](#pull-request-process)
        - [Pull Request Guidelines](#pull-request-guidelines)
- [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
        - [Platform-Specific Requirements](#platform-specific-requirements)
    - [Environment Setup](#environment-setup)
    - [Running the Application](#running-the-application)
- [Testing](#testing)
    - [Running Tests](#running-tests)
    - [Test Structure](#test-structure)
    - [Writing Tests](#writing-tests)
- [Building and Packaging](#building-and-packaging)
    - [Development Builds](#development-builds)
    - [Manual PyInstaller](#manual-pyinstaller)
- [Code Guidelines](#code-guidelines)
    - [Python Style Guide](#python-style-guide)
    - [Commit Message Format](#commit-message-format)
    - [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to a code of conduct to ensure a welcoming environment for all contributors. Please be respectful, constructive, and inclusive in all interactions.

**Expected Behavior:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report, please:

1. **Check existing issues** to avoid duplicates
2. **Test with the latest version** to ensure the bug still exists
3. **Gather relevant information** about your environment

When reporting bugs, please include:

- **Clear title and description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details**:
  - Operating System (Windows/macOS/Linux)
  - Python version
  - PushToTalk version
  - Relevant configuration settings
- **Log files** (`push_to_talk.log`) if applicable
- **Screenshots or recordings** for GUI issues

**Use this template:**
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [Windows 11/macOS 14/Ubuntu 22.04]
- Python: [3.9.x]
- PushToTalk: [0.4.0]
- STT Provider: [OpenAI/Deepgram]
- STT Model: [e.g., whisper-1, nova-3]
- Refinement Provider: [OpenAI/Cerebras]
- Refinement Model: [e.g., gpt-4.1-nano, llama-3.3-70b]

## Additional Context
Any other relevant information, logs, or screenshots
```

### Suggesting Features

We welcome feature suggestions! Before submitting:

1. **Check the roadmap** in [GitHub Issues](https://github.com/yixin0829/push-to-talk/issues)
2. **Review existing feature requests** to avoid duplicates
3. **Consider the project scope** - features should align with speech-to-text functionality

When suggesting features, include:

- **Clear use case** and problem it solves
- **Detailed description** of the proposed feature
- **User interface mockups** if relevant
- **Technical considerations** if you have insights
- **Alternative solutions** you've considered

### Submitting Pull Requests

#### Before You Start

1. **Discuss major changes** by opening an issue first
2. **Check existing pull requests** to avoid duplicates
3. **Review the codebase** to understand patterns and conventions

#### Pull Request Process

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/push-to-talk.git
   cd push-to-talk
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number
   ```

3. **Make your changes**
   - Follow the [Code Guidelines](#code-guidelines)
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   uv run pytest tests/ -v
   uv run pytest tests/ --cov=src --cov-report=term-missing
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Use a clear title and description
   - Reference related issues
   - Include testing instructions
   - Add screenshots for UI changes

#### Pull Request Guidelines

- **One feature per PR** - keep changes focused
- **Include tests** for new functionality
- **Update documentation** when needed
- **Maintain backwards compatibility** unless discussed
- **Follow semantic versioning** for breaking changes

## Development Setup

### Prerequisites

- **Python 3.9+**: Required for the application
- **uv**: Python package manager ([installation guide](https://docs.astral.sh/uv/))
- **Git**: For version control
- **API Keys** (at least one required):
  - **OpenAI API Key**: For Whisper transcription or GPT refinement ([get key](https://platform.openai.com/api-keys))
  - **Deepgram API Key**: For alternative transcription provider ([get key](https://console.deepgram.com/))
  - **Cerebras API Key**: For alternative text refinement provider ([get key](https://console.cerebras.ai/))

#### Platform-Specific Requirements

**Windows:**
- Visual C++ build tools (for PyAudio)
- Administrator privileges (for hotkey detection)

**macOS:**
```bash
brew install portaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev libasound2-dev build-essential
```

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yixin0829/push-to-talk.git
   cd push-to-talk
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Set up environment variables**
   ```bash
   # Create a .env file (optional - API keys can also be set via GUI)
   # At least one STT provider API key is required
   echo "OPENAI_API_KEY=your_openai_key_here" > .env
   echo "DEEPGRAM_API_KEY=your_deepgram_key_here" >> .env
   echo "CEREBRAS_API_KEY=your_cerebras_key_here" >> .env
   ```

   Environment variables are checked automatically if GUI or config file values are empty.

4. **Verify installation**
   ```bash
   uv run python -c "import src.push_to_talk; print('Setup successful!')"
   ```

### Running the Application

**GUI Application (Recommended):**
```bash
uv run python main.py
```

**Development Mode with Logging:**
```bash
uv run python main.py --debug
```

## Testing

Our test suite ensures code quality and functionality across all components.

### Running Tests

**All tests:**
```bash
uv run pytest tests/ -v
```

**Unit tests only:**
```bash
uv run pytest tests/ -v -m "not integration"
```

**Integration tests with real audio:**
```bash
uv run pytest tests/ -v -m integration
```

**Coverage report:**
```bash
uv run pytest tests/ --cov=src --cov-report=html
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80
```

**Specific test files:**
```bash
uv run pytest tests/test_audio_recorder.py -v
uv run pytest tests/test_transcription.py -v
```

### Test Structure

```
tests/
├── conftest.py                      # Test configuration and fixtures
├── test_push_to_talk.py             # Core app logic, config, lifecycle
├── test_config_gui.py               # GUI component integration
├── test_audio_recorder.py           # Audio recording functionality
├── test_transcription_openai.py     # OpenAI Whisper integration
├── test_transcription_deepgram.py   # Deepgram provider integration
├── test_transcriber_factory.py      # Transcriber factory pattern
├── test_text_refiner.py             # AI text refinement (OpenAI & Cerebras)
├── test_hotkey_service.py           # Hotkey detection
├── test_integration.py              # End-to-end integration tests
├── test_format_instruction.py       # Format instruction processing
├── test_helpers.py                  # Helper function tests
├── test_utils.py                    # Utility function tests
├── README.md                        # Testing documentation
└── fixtures/                        # Real audio files for testing
    └── (audio files for integration tests)
```

### Writing Tests

**Test Guidelines:**
- Use descriptive test names: `test_audio_recorder_start_success`
- Include comprehensive logging using loguru for debugging
- Use `pytest-mock` (mocker fixture) for all mocking - no `unittest.mock` decorators
- Mock external dependencies (API calls, PyAudio, network requests)
- Test both success and failure scenarios
- Use real audio fixtures for integration tests
- **Provider Testing**: Test all relevant providers (OpenAI, Deepgram for STT; OpenAI, Cerebras for refinement)
- **Factory Testing**: Ensure factory pattern correctly instantiates the right provider based on config
- See [tests/README.md](tests/README.md) for detailed testing patterns

**Test Template:**
```python
import pytest
from loguru import logger
from unittest.mock import MagicMock

from src.your_module import YourClass

class TestYourClass:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test method"""
        logger.info("Setting up YourClass test")
        self.instance = YourClass()
        yield
        # Optional teardown code here

    def test_functionality_success(self):
        """Test successful functionality"""
        logger.info("Testing successful functionality")

        # Test implementation
        result = self.instance.method()

        assert result is not None
        logger.info("Functionality test passed")

    def test_functionality_with_mock(self, mocker):
        """Test with mocked dependencies using pytest-mock"""
        mock_dependency = mocker.patch('external.dependency', return_value="expected_value")

        result = self.instance.method_with_dependency()

        assert result == "expected_value"
        mock_dependency.assert_called_once()
```

## Building and Packaging

### Development Builds

**Windows:**
```bash
.\build.bat
```

**macOS:**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

**Linux:**
```bash
chmod +x build_linux.sh
./build_linux.sh
```

**Cross-platform (current OS only):**
```bash
uv run python build.py -p all
```

### Manual PyInstaller

```bash
uv run pyinstaller push_to_talk.spec  # Windows
uv run pyinstaller --name PushToTalk --onefile --noconsole main.py  # macOS/Linux
```

See [PACKAGING.md](build_script/PACKAGING.md) for detailed build instructions.

## Code Guidelines

### Python Style Guide

We follow PEP 8 with some project-specific conventions:

**Formatting:**
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Imports**: Use absolute imports, group by standard/third-party/local
- **String quotes**: Double quotes for strings, single for character literals

**Naming Conventions:**
- **Classes**: `PascalCase` (e.g., `AudioRecorder`, `TextRefiner`)
- **Functions/Variables**: `snake_case` (e.g., `start_recording`, `api_key`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_SAMPLE_RATE`)
- **Private methods**: Leading underscore (e.g., `_process_audio`)

**Code Organization:**
- **Docstrings**: Use Google-style docstrings for all public methods
- **Type hints**: Include type annotations for function parameters and returns
- **Error handling**: Use specific exception types, log errors with loguru
- **Comments**: Explain complex logic, not obvious code

See existing code in [src/](../src/) for examples of project style.

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting (no functional changes)
- `refactor`: Code restructuring without behavior changes
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks, dependency updates

**Examples:**
```bash
feat(audio): add smart silence removal with configurable threshold
fix(gui): resolve hotkey validation preventing duplicate assignments
docs(readme): update installation instructions for macOS
test(integration): add real audio file fixtures for end-to-end testing
refactor(transcription): extract API client configuration to separate method
```

### Documentation

**Code Documentation:**
- Use Google-style docstrings for all public APIs
- Include type hints for all function parameters and returns
- Document complex algorithms and business logic
- Add inline comments for non-obvious code sections

**README Updates:**
- Update feature lists when adding new functionality
- Modify configuration examples for new settings
- Add troubleshooting entries for common issues
- Update version information and compatibility notes

**Changelog Maintenance:**
- Add entries to `CHANGELOG.md` for all user-facing changes
- Follow the [Keep a Changelog](https://keepachangelog.com/) format
- Include migration notes for breaking changes
- Reference issue numbers and pull requests

## Project Structure

For detailed component information, see [AGENTS.md](AGENTS.md).

```
push-to-talk/
├── main.py                              # Application entry point
├── pyproject.toml                       # Project configuration
├── AGENTS.md                            # Developer guide
├── CONTRIBUTING.md                      # This file
├── README.md                            # User documentation
│
├── src/                                 # Source code (4,600+ lines)
│   ├── push_to_talk.py                 # Core app + config + DI (793 lines)
│   ├── audio_recorder.py               # PyAudio recording (181 lines)
│   ├── hotkey_service.py               # Global hotkey detection (608 lines)
│   ├── text_inserter.py                # Clipboard/keyboard insertion (94 lines)
│   ├── utils.py                        # Audio feedback utilities (89 lines)
│   │
│   ├── gui/                            # Modular GUI (2,180 lines across 9 modules)
│   │   ├── configuration_window.py     # Main window coordinator (554 lines)
│   │   ├── api_section.py             # API keys & provider config (534 lines)
│   │   ├── glossary_section.py        # Custom glossary management (281 lines)
│   │   ├── settings_section.py        # Feature flags (151 lines)
│   │   ├── status_section.py          # Status display (123 lines)
│   │   ├── audio_section.py           # Audio settings (100 lines)
│   │   ├── hotkey_section.py          # Hotkey configuration with Record button
│   │   ├── hotkey_recorder.py         # Hotkey recording via key capture
│   │   ├── validators.py              # Input validation (153 lines)
│   │   ├── config_persistence.py      # Config file I/O (86 lines)
│   │   └── __init__.py                # Module exports
│   │
│   ├── transcription_base.py           # Abstract transcriber interface (50 lines)
│   ├── transcription_openai.py         # OpenAI Whisper (81 lines)
│   ├── transcription_deepgram.py       # Deepgram API (144 lines)
│   ├── transcriber_factory.py          # STT provider factory (43 lines)
│   │
│   ├── text_refiner_base.py            # Abstract refiner interface (83 lines)
│   ├── text_refiner_openai.py          # OpenAI GPT refinement (111 lines)
│   ├── text_refiner_cerebras.py        # Cerebras API refinement (115 lines)
│   ├── text_refiner_factory.py         # Refinement provider factory (46 lines)
│   │
│   └── config/
│       ├── constants.py                # App constants (96 lines)
│       ├── prompts.py                  # Refinement prompts (26 lines)
│       └── hotkey_aliases.json         # Key alias mappings (137 lines)
│
├── tests/                               # Test suite (3,900+ lines)
│   ├── conftest.py                     # Test fixtures & setup
│   ├── test_push_to_talk.py            # Core app tests
│   ├── test_config_gui.py              # GUI tests
│   ├── test_audio_recorder.py          # Audio recording tests
│   ├── test_transcription_openai.py    # OpenAI tests
│   ├── test_transcription_deepgram.py  # Deepgram tests
│   ├── test_text_refiner.py            # Text refinement tests
│   ├── test_hotkey_service.py          # Hotkey service tests
│   ├── test_hotkey_recorder.py         # Hotkey recorder tests
│   ├── test_integration.py             # End-to-end tests
│   ├── test_format_instruction.py      # Format tests
│   ├── test_helpers.py                 # Helper tests
│   ├── test_utils.py                   # Utility tests
│   ├── test_transcriber_factory.py     # Factory tests
│   ├── README.md                       # Testing documentation
│   └── fixtures/                       # Test audio files
│
├── build_script/                        # Cross-platform builds
│   ├── build.bat                       # Windows build
│   ├── build_macos.sh                  # macOS build
│   ├── build_linux.sh                  # Linux build
│   ├── build.py                        # Python build helper
│   ├── push_to_talk.spec               # PyInstaller config
│   └── PACKAGING.md                    # Packaging guide
│
└── .github/                             # GitHub configuration
    └── (workflows, templates, etc.)
```

## Release Process

**Version Numbering:**
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X.0.0): Breaking changes, major architectural updates
- **MINOR** (X.Y.0): New features, backwards compatible enhancements
- **PATCH** (X.Y.Z): Bug fixes, security updates

**Release Workflow:**
1. **Create release branch**: `git checkout -b release/v0.5.0`
2. **Update version**: Modify `pyproject.toml` version field
3. **Update changelog**: Add release notes to `CHANGELOG.md`
4. **Run full test suite**: Ensure all tests pass
5. **Build executables**: Test packaging for all platforms
6. **Create pull request**: Review and merge to main
7. **Tag release**: `git tag v0.5.0 && git push origin v0.5.0`
8. **GitHub release**: Create release with binaries and notes

**Pre-release Testing:**
- Run comprehensive test suite with coverage
- Test GUI functionality on target platforms (Windows, macOS, Linux)
- Validate audio processing with various input formats and sample rates
- Test STT providers: Verify OpenAI Whisper and Deepgram with different models
- Test refinement providers: Verify OpenAI GPT and Cerebras with different models
- Test hotkey functionality across operating systems (platform-aware defaults)
- Test configuration persistence and live config sync
- Validate custom glossary functionality with both refinement providers
- Test error handling for missing/invalid API keys
- Verify environment variable fallback for API keys

## Getting Help

**For Contributors:**
- **Questions**: Open a [Discussion](https://github.com/yixin0829/push-to-talk/discussions)
- **Issues**: Check [existing issues](https://github.com/yixin0829/push-to-talk/issues) first
- **Documentation**: Refer to README.md and inline code documentation
- **Code Review**: Tag maintainers in pull requests for review

**Resources:**
- [Project Issues](https://github.com/yixin0829/push-to-talk/issues) - Bug reports and feature requests
- [Discussions](https://github.com/yixin0829/push-to-talk/discussions) - General questions and ideas
- [Changelog](CHANGELOG.md) - Version history and release notes
- [Packaging Guide](build_script/PACKAGING.md) - Build and distribution instructions

**Community Guidelines:**
- Be patient with response times - this is maintained by volunteers
- Provide detailed information when asking for help
- Search existing issues and discussions before posting
- Follow up on your issues and pull requests

---

Thank you for contributing to PushToTalk! Your efforts help make AI-powered speech-to-text more accessible and reliable for everyone. 🎤✨
