<p align="center">
  <img src="icon.ico" width="128" height="128" alt="PushToTalk Icon">
</p>


# PushToTalk - AI Refined Speech-to-Text Dictation
[![codecov](https://codecov.io/gh/yixin0829/push-to-talk/graph/badge.svg?token=ZXD777GTHS)](https://codecov.io/gh/yixin0829/push-to-talk)

A Python application that provides push-to-talk speech-to-text functionality with AI speech to text transcription, smart text refinement, and automatic text insertion into the active window on Windows, MacOS (to be built), and Linux (to be built). **Now features a persistent GUI configuration interface with real-time status management and easy application control.**

## Features

- **🎯 GUI Interface**: Integrated configuration control and application status monitoring in one window
- **🔄 Live Config Sync**: GUI edits instantly push updates to the running background service—no restart required
- **📚 Custom Glossary**: Add domain-specific terms and acronyms to improve transcription accuracy
- **✨ Text Refinement**: Improves transcription quality using Refinement Models
- **🤖 Speech-to-Text**: Choose between OpenAI or Deepgram transcription services for accurate transcription
- **🎤 Push-to-Talk Recording**: Hold a customizable hotkey to record audio
- **📝 Auto Text Insertion**: Automatically inserts refined text into the active window

## Demos
- v0.3.0 - v0.4.0: https://www.loom.com/share/71ecc05d4bb440ecb708d980505b9000
- v0.2.0: https://www.loom.com/share/fbabb2da83c249d3a0a09b3adcc4a4e6

## Roadmap
See [issues](https://github.com/yixin0829/push-to-talk/issues) for more details.

## Requirements

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API key (https://platform.openai.com/docs/api-reference/introduction) **OR** Deepgram API key (https://deepgram.com/)
- Microphone access (for recording)

## Quick Start (GUI Application)

### For End Users (Recommended)

1. **Download and launch**:
   - Download `PushToTalk.exe` from releases
   - Double-click to launch the configuration interface

2. **One-window setup and control**:
   - **Welcome section** explains the application at the top
   - **Configure your settings** in the organized sections below
   - **Click "Start Application"** to begin - the GUI stays open
   - **Monitor status** with real-time indicators (green = running, gray = stopped)
   - **View active settings** displayed when running
   - **Easy control** with "Stop Application" button to terminate
   - **Tweak settings live**—changes made while running apply instantly

3. **Daily usage**:
   - GUI provides persistent control and status monitoring
   - Use your configured hotkeys to record and transcribe
   - Tune preferences without stopping the service; hotkeys update in real time
   - Start/stop the service anytime from the GUI

### For Developers

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd push-to-talk
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the GUI application**:
   ```bash
   uv run python main.py
   ```

## GUI Configuration Interface

The application features a comprehensive, persistent configuration GUI with organized sections:

### Welcome & Status
- **Real-Time Status**: Visual indicators show current application state
  - **Gray circle + "Ready to start"**: Application stopped
  - **Green circle + "Running - Use your configured hotkeys"**: Application running
- **Active Settings Display**: Shows current hotkeys and enabled features when running
- **Live Updates Banner**: Status automatically refreshes when settings change mid-session

### Live Configuration Updates

The application features a sophisticated real-time configuration system that applies changes instantly while running:

#### How It Works
- **Variable Tracing**: Every GUI field (text boxes, checkboxes, dropdowns) automatically detects changes using Tkinter variable traces
- **Smart Debouncing**: Rapid typing is intelligently handled with configurable delay to prevent excessive updates
- **Selective Reinitialization**: Only components affected by changes are reinitialized (e.g., hotkey changes → restart hotkey service)
- **Service Continuity**: Critical services like hotkey detection automatically restart after updates

#### Technical Features
- **Instant Propagation**: Editing any field triggers a debounced update to the running PushToTalk service
- **Persistent Storage**: Changes are automatically saved to JSON file asynchronously for permanent persistence
- **Callback Support**: Optional listeners receive validated Pydantic configuration models whenever values change
- **Glossary Sync**: Glossary edits are copied before rebuilds to prevent UI/model divergence
- **Safe Programmatic Updates**: GUI refreshes suspend traces to avoid infinite callback loops
- **Thread-Safe Saves**: Non-blocking background saves with deduplication prevent file conflicts

#### Example Scenarios
- **Hotkey Change**: Type "ctrl+alt+space" → Only final result triggers one hotkey service restart
- **Non-Critical Change**: Toggle "Audio Feedback" → Updates instantly without restarting core components
- **API Key Change**: Update OpenAI key → Only transcription/refinement components reinitialize

### Speech-to-Text Settings
- **STT Provider Selection**: Choose between OpenAI or Deepgram
- **API Key**: Secure entry with show/hide functionality (dynamically shows OpenAI or Deepgram field based on provider)
- **Model Selection**: Choose provider-specific models:
  - **OpenAI**: whisper-1, gpt-4o-transcribe, gpt-4o-mini-transcribe
  - **Deepgram**: nova-3 (recommended), nova-2, base, enhanced, whisper-medium
- **Refinement Model**: GPT models for text refinement (OpenAI)

### Audio Settings
- **Sample Rate**: 8kHz to 44.1kHz options (16kHz recommended)
- **Chunk Size**: Buffer size configuration
- **Channels**: Mono/stereo recording options
- **Helpful Recommendations**: Built-in guidance for optimal settings

### Hotkey Configuration
- **Push-to-Talk Hotkey**: Hold to record (default: Ctrl+Shift+Space)
- **Toggle Recording Hotkey**: Press once to start/stop (default: Ctrl+Shift+^)
- **Validation**: Prevents duplicate hotkey assignments
- **Examples**: Common hotkey combinations provided

### Text Insertion Settings
- **Insertion Delay**: Fine-tune timing for clipboard paste operation

### Custom Glossary
- **Domain-Specific Terms**: Add specialized vocabulary, acronyms, and proper names
- **Easy Management**: Add, edit, and delete glossary terms through the GUI
- **Search Functionality**: Quickly find and manage existing terms
- **Automatic Integration**: Glossary terms are automatically included in transcription refinement


## How to Use

1. **Build**: Build the application using `build.bat` if first time running on Windows
2. **Launch**: Double-click the built `PushToTalk.exe` or run `uv run python main.py`
3. **Configure**: Use the integrated setup interface with welcome guidance
4. **Start**: Click "Start Application" - GUI stays open with status indicators
5. **Monitor**: Watch real-time status and active settings display
6. **Use**: Background operation with your configured hotkeys
7. **Control**: Use "Stop Application" button to terminate, or restart anytime

## Building the Application

```bash
.\build.bat
```
This creates `dist\PushToTalk.exe` - a standalone GUI application.


## Configuration

The application supports both GUI and file-based configuration:

### Via GUI (Recommended)
- Launch the application to access the integrated configuration interface
- **All settings** validated and saved automatically to `push_to_talk_config.json`
- **Real-time status** shows application state with visual indicators
- **Auto-sync**: Edits instantly update the running background service and any registered callbacks
- Every time you start the application, your configuration is saved and overwrites the old configuration in the JSON file `push_to_talk_config.json`

### File-Based Configuration
The application creates a `push_to_talk_config.json` file. Example configuration file:

```json
{
  "openai_api_key": "your_api_key_here",
  "stt_model": "gpt-4o-transcribe",
  "refinement_model": "gpt-4.1-nano",
  "sample_rate": 16000,
  "chunk_size": 1024,
  "channels": 1,
  "hotkey": "ctrl+shift+space",
  "toggle_hotkey": "ctrl+shift+^",
  "insertion_delay": 0.005,
  "enable_text_refinement": true,
  "enable_logging": true,
  "enable_audio_feedback": true,
  "debug_mode": false,
  "custom_glossary": ["API", "OAuth", "microservices", "PostgreSQL"]
}
```

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stt_provider` | string | `"openai"` | Speech-to-text provider. Options: `openai`, `deepgram`. Determines which transcription service to use. |
| `openai_api_key` | string | `""` | Your OpenAI API key for Whisper and GPT services. Required when using OpenAI provider. Can be set via GUI, config file, or `OPENAI_API_KEY` environment variable. |
| `deepgram_api_key` | string | `""` | Your Deepgram API key for transcription services. Required when using Deepgram provider. Can be set via GUI, config file, or `DEEPGRAM_API_KEY` environment variable. |
| `stt_model` | string | `"gpt-4o-mini-transcribe"` | STT Model for speech-to-text. For OpenAI: `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`. For Deepgram: `nova-3`, `nova-2`, `base`, `enhanced`, `whisper-medium`. |
| `refinement_model` | string | `"gpt-4.1-nano"` | Refinement Model for text refinement (OpenAI). Options: `gpt-4.1-nano`, `gpt-4o-mini`, `gpt-4o`. |
| `sample_rate` | integer | `16000` | Audio sampling frequency in Hz. 16kHz is optimal for speech recognition with Whisper. |
| `chunk_size` | integer | `1024` | Audio buffer size in samples. Determines how much audio is read at once (affects latency vs performance). |
| `channels` | integer | `1` | Number of audio channels. Use `1` for mono recording (recommended for speech). |
| `hotkey` | string | `"ctrl+shift+space"` | Hotkey combination for push-to-talk. See [Hotkey Options](#hotkey-options) for examples. |
| `toggle_hotkey` | string | `"ctrl+shift+^"` | Hotkey combination for toggle recording mode. Press once to start, press again to stop. |
| `insertion_delay` | float | `0.005` | Delay in seconds before text insertion via clipboard. Helps ensure target window is ready. |
| `enable_text_refinement` | boolean | `true` | Whether to use GPT to refine transcribed text. Disable for faster processing without refinement. |
| `enable_logging` | boolean | `true` | Whether to enable detailed logging to `push_to_talk.log` file using loguru. |
| `enable_audio_feedback` | boolean | `true` | Whether to play sophisticated audio cues when starting/stopping recording. Provides immediate feedback for hotkey interactions. |
| `debug_mode` | boolean | `false` | Whether to enable debug mode. When enabled, recorded audio files are saved to timestamped debug directories (e.g., `debug_audio_20231215_143022_456/`) with recording metadata for troubleshooting. |
| `custom_glossary` | array | `[]` | List of domain-specific terms, acronyms, and proper names to improve transcription accuracy. Terms are automatically included in text refinement prompts. |

#### Audio Quality Settings

- **sample_rate**:
  - `16000` (16kHz) - Recommended for speech (Whisper optimized)
  - `8000` (8kHz) - Lower quality but faster processing
  - `44100` (44.1kHz) - CD quality (overkill for speech, slower)

- **chunk_size**:
  - `512` - Lower latency, more CPU overhead
  - `1024` - Balanced (recommended)
  - `2048` - Higher latency, less CPU usage

- **channels**:
  - `1` - Mono recording (recommended for speech)
  - `2` - Stereo recording (unnecessary for speech-to-text)

### Hotkey Options

You can configure different hotkey combinations for both modes:

**Push-to-talk hotkey** (hold to record):
- `ctrl+shift+space` (default)
- `ctrl+alt+r`
- `f12`

**Toggle hotkey** (press once to start, press again to stop):
- `ctrl+shift+^` (default)
- `ctrl+shift+t`

Both hotkeys support any combination from the `keyboard` library.

### Custom Glossary

The application supports custom glossary terms to improve transcription accuracy for domain-specific vocabulary:

- **Add Terms**: Use the GUI to add specialized vocabulary, acronyms, and proper names
- **Automatic Integration**: Glossary terms are automatically included in text refinement prompts
- **Smart Processing**: TextRefiner switches between prompts with and without glossary automatically
- **Persistent Storage**: Terms are saved in the configuration file and restored on startup
- **Easy Management**: Add, edit, delete, and search glossary terms through the GUI interface

**Example use cases**:
- Technical terms: "API", "OAuth", "microservices", "PostgreSQL"
- Company names: "Anthropic", "OpenAI"
- Acronyms: "CEO", "CTO", "AI/ML", "SaaS"
- Domain-specific vocabulary: Medical terms, legal terminology, etc.

### Audio Feedback

The application includes clean and simple audio feedback:

- **Recording Start**: A crisp high-pitched beep (880 Hz) that signals recording has begun
- **Recording Stop**: A lower confirmation beep (660 Hz) that confirms recording completion
- **Non-Blocking**: Audio playback runs in separate threads to avoid interfering with recording or transcription
- **Configurable**: Can be toggled on/off via GUI or configuration JSON file
- **Cross-Platform**: Uses `playsound3` for audio playback - works on Windows, MacOS, and Linux

## Architecture

For detailed architecture and development information, see:
- [CLAUDE.md](CLAUDE.md) - Developer guide with architecture details
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines and project structure

## Troubleshooting

### GUI Application Issues

1. **Application won't start**:
   - Make sure you're running as Administrator for hotkey detection
   - Check that the executable isn't blocked by antivirus
   - Try running from command line to see error messages

2. **Status indicators not updating**:
   - The GUI should show real-time status changes when starting/stopping
   - If stuck, try restarting the application
   - Check `push_to_talk.log` for error details

3. **Start/Stop button not working**:
   - Ensure all required fields are filled (especially OpenAI API key)
   - Use "Test Configuration" to validate settings
   - Check that no other instance is running

4. **Settings not saving**:
   - Ensure the application has write permissions in its directory
   - Check that the configuration file isn't marked as read-only
   - Try running as Administrator

### Common Issues

1. **"No module named 'pyautogui' or 'pyperclip'"** (Development):
   ```bash
   uv add pyautogui pyperclip
   ```

2. **"Could not find PyAudio"** (Development):
   - Install PyAudio: `uv add pyaudio`
   - On Windows, you may need Visual C++ build tools

3. **Hotkey not working**:
   - Run as administrator (required for global hotkey detection)
   - Check if another application is using the same hotkey
   - Try a different hotkey combination in the GUI
   - Ensure the application shows "Running" status in the GUI

4. **OpenAI API errors**:
   - Use the "Test Configuration" button in the GUI to validate settings
   - Verify your API key is valid and has sufficient credits
   - Check your OpenAI account has access to the models you're using
   - Ensure internet connectivity

5. **Text not inserting**:
   - Make sure the target window is active and has a text input field
   - Check Windows permissions for clipboard access
   - Increase insertion delay if text appears truncated

6. **GUI appearance issues**:
   - Try restarting the application
   - Check display scaling settings (recommended: 100-150%)
   - Ensure Windows is up to date

### Logging

Logs are written to `push_to_talk.log` using loguru's enhanced formatting. The GUI application logs only to file for cleaner user experience.


## Performance Tips

1. **Optimize audio settings**: Lower sample rates (8000-16000 Hz) for faster processing
2. **Enable audio processing**: Smart silence removal and speed adjustment can significantly reduce transcription time
3. **Adjust silence threshold**: Fine-tune -16 dBFS for your environment (higher for noisy environments)
4. **Disable text refinement**: For faster transcription without GPT processing
5. **Short recordings**: Keep recordings under 30 seconds for optimal performance
6. **Monitor via GUI**: Use the status indicators to verify application is running efficiently

## Security Considerations

- **API Key Security**: GUI stores API keys securely; avoid sharing configuration files
- **Administrator Rights**: Required for global hotkey detection
- **Microphone Access**: Application needs microphone permissions
- **Network Access**: Required for OpenAI API calls
- **File Permissions**: Ensure configuration files have appropriate access controls

## Testing

For comprehensive testing information, see [CONTRIBUTING.md](CONTRIBUTING.md#testing).

**Quick Start:**
```bash
uv run pytest tests/ -v                       # All tests
uv run pytest tests/ --cov=src --cov-report=html # With coverage
```
