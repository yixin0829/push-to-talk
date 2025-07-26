# PushNTalk - Speech-to-Text Push-to-Talk Application

A Python application that provides push-to-talk speech-to-text functionality with OpenAI Whisper transcription, GPT text refinement, and automatic text insertion into the active window on Windows.

## Features

- **Push-to-Talk Recording**: Hold a customizable hotkey to record audio
- **Speech-to-Text**: Uses OpenAI Whisper for accurate transcription
- **Text Refinement**: Improves transcription quality using gpt-4.1-nano
- **Auto Text Insertion**: Automatically inserts refined text into the active window
- **Audio Feedback**: Sophisticated sound cues for recording start/stop with a tech-inspired vibe
- **Background Operation**: Runs silently in the background
- **Configurable**: Customizable hotkeys, models, and settings
- **Logging**: Comprehensive logging for debugging and monitoring

## Requirements

- Windows 10/11
- Python 3.12+
- OpenAI API key
- Microphone access
- Administrator privileges (for global hotkey detection)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd push-n-talk
   ```

2. **Install dependencies**:
   ```bash
   # using uv
   uv sync

   # using pip
   pip install -r requirements.txt
   ```

3. **Set up your OpenAI API key**:
   ```bash
   # Option 1: .env file (preferred)
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   
   # Option 2: Edit push_n_talk_config.json after first run
   ```

## Usage

### Quick Start

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Use push-to-talk**:
   - Press and hold `Ctrl+Shift+Space` to start recording
   - Speak your message
   - Release the key to stop recording and process
   - The refined text will be inserted into the active window

3. **Exit**:
   - Press `Ctrl+C` in the terminal or close the application

### Configuration

The application creates a `push_n_talk_config.json` file on first run. You can customize:

```json
{
  "openai_api_key": "your_api_key_here",
  "whisper_model": "whisper-1",
  "gpt_model": "gpt-4.1-nano",
  "sample_rate": 16000,
  "chunk_size": 1024,
  "channels": 1,
  "hotkey": "ctrl+shift+space",
  "insertion_method": "clipboard",
  "insertion_delay": 0.01,
  "enable_text_refinement": true,
  "enable_logging": true,
  "enable_audio_feedback": true
}
```

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `openai_api_key` | string | `""` | Your OpenAI API key for Whisper and GPT services. Required for transcription and text refinement. If not set, the application will look for the `OPENAI_API_KEY` environment variable. |
| `whisper_model` | string | `"whisper-1"` | OpenAI Whisper model for speech-to-text. Options: `whisper-1` (recommended for API usage). |
| `gpt_model` | string | `"gpt-4.1-nano"` | GPT model for text refinement. Options: `gpt-4.1-nano` |
| `sample_rate` | integer | `16000` | Audio sampling frequency in Hz. 16kHz is optimal for speech recognition with Whisper. |
| `chunk_size` | integer | `1024` | Audio buffer size in samples. Determines how much audio is read at once (affects latency vs performance). |
| `channels` | integer | `1` | Number of audio channels. Use `1` for mono recording (recommended for speech). |
| `hotkey` | string | `"ctrl+shift+space"` | Hotkey combination for push-to-talk. See [Hotkey Options](#hotkey-options) for examples. |
| `insertion_method` | string | `"clipboard"` | Method for inserting text. Options: `clipboard` (faster), `sendkeys` (better for special chars). |
| `insertion_delay` | float | `0.1` | Delay in seconds before text insertion. Helps ensure target window is ready. |
| `enable_text_refinement` | boolean | `true` | Whether to use GPT to refine transcribed text. Disable for faster processing without refinement. |
| `enable_logging` | boolean | `true` | Whether to enable detailed logging to `push_n_talk.log` file and console. |
| `enable_audio_feedback` | boolean | `true` | Whether to play sophisticated audio cues when starting/stopping recording. Provides immediate feedback for hotkey interactions. |

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

You can use various hotkey combinations:
- `ctrl+shift+space` (default)
- `alt+space`
- `ctrl+alt+r`
- `f12`
- Any combination supported by the `keyboard` library

### Text Insertion Methods

- **clipboard** (default): Faster and more reliable, uses Ctrl+V
- **sendkeys**: Simulates individual keystrokes, better for special characters

### Audio Feedback

The application includes clean and simple audio feedback:

- **Recording Start**: A crisp high-pitched beep (880 Hz) that signals recording has begun
- **Recording Stop**: A lower confirmation beep (660 Hz) that confirms recording completion
- **Minimalist Design**: Simple, clean tones inspired by Apple's design philosophy of elegant simplicity
- **Non-Blocking**: Audio playback runs in separate threads to avoid interfering with recording or transcription
- **Configurable**: Can be toggled on/off via configuration or programmatically during runtime
- **Zero Dependencies**: Uses Windows' built-in `winsound` module - no additional packages required

The audio feedback provides immediate, unobtrusive confirmation of your interactions without adding complexity or dependencies.

## Architecture

The application consists of several modular components:

### Core Components

- **AudioRecorder** (`src/audio_recorder.py`): Handles audio recording using PyAudio
- **Transcriber** (`src/transcription.py`): Converts speech to text using OpenAI Whisper
- **TextRefiner** (`src/text_refiner.py`): Improves transcription using GPT models
- **TextInserter** (`src/text_inserter.py`): Inserts text into active windows using pywin32
- **HotkeyService** (`src/hotkey_service.py`): Manages global hotkey detection
- **Audio Feedback** (`src/audio_feedback.py`): Provides simple, clean audio feedback using Windows built-in sounds via utility functions
- **PushNTalkApp** (`src/push_n_talk.py`): Main application orchestrator

### Data Flow

1. User presses hotkey → Audio recording starts
2. User releases hotkey → Recording stops
3. Audio file is sent to OpenAI Whisper for transcription
4. Raw transcription is refined using gpt-4.1-nano
5. Refined text is inserted into the active window

## Dependencies

- **keyboard**: Global hotkey detection
- **pyaudio**: Audio recording
- **openai**: Speech-to-text and text refinement
- **pywin32**: Windows-specific text insertion and audio feedback (winsound)

## Troubleshooting

### Common Issues

1. **"No module named 'pywin32'"**:
   ```bash
   uv add pywin32
   ```

2. **"Could not find PyAudio"**:
   - Install PyAudio: `uv add pyaudio`
   - On Windows, you may need Visual C++ build tools

3. **Hotkey not working**:
   - Run as administrator
   - Check if another application is using the same hotkey
   - Try a different hotkey combination

4. **OpenAI API errors**:
   - Verify your API key is valid
   - Check your OpenAI account has credits
   - Ensure internet connectivity

5. **Text not inserting**:
   - Make sure the target window is active and has a text field
   - Try switching insertion method in config
   - Check Windows permissions

### Logging

Logs are written to `push_n_talk.log` and console. Log levels:
- INFO: Normal operation events
- WARNING: Non-critical issues
- ERROR: Critical errors

## Advanced Usage

### Custom Text Refinement Prompts

You can customize the text refinement behavior:

```python
from src import PushNTalkApp, PushNTalkConfig

app = PushNTalkApp()
app.text_refiner.set_custom_prompt(
    "Your custom refinement instructions here..."
)
```

### Programmatic Control

```python
from src import PushNTalkApp, PushNTalkConfig

# Create custom config
config = PushNTalkConfig()
config.hotkey = "f12"
config.enable_text_refinement = False

# Run application
app = PushNTalkApp(config)

# Toggle audio feedback
app.toggle_audio_feedback()  # Disable audio feedback
app.toggle_audio_feedback()  # Re-enable audio feedback

# Check status including audio feedback state
status = app.get_status()
print(f"Audio feedback enabled: {status['audio_feedback_enabled']}")

app.run()
```

## Performance Tips

1. **Optimize audio settings**: Lower sample rates (8000-16000 Hz) for faster processing
2. **Disable text refinement**: For faster transcription without GPT processing
3. **Use clipboard method**: Generally faster than sendkeys for text insertion
4. **Short recordings**: Keep recordings under 30 seconds for optimal performance

## Security Considerations

- **API Key Security**: Store your OpenAI API key securely
- **Administrator Rights**: Required for global hotkey detection
- **Microphone Access**: Application needs microphone permissions
- **Network Access**: Required for OpenAI API calls

## Version History

- **1.0.0**: Initial release with core functionality
