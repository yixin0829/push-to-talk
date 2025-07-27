# Packaging PushToTalk as Windows Executable

This guide explains how to package the PushToTalk application as a standalone Windows executable (.exe) file.

## Prerequisites

1. **uv**: Ensure you have [uv](https://docs.astral.sh/uv/) installed
2. **Dependencies**: Install all project dependencies:
   ```bash
   uv sync
   ```

## Quick Build

The easiest way to build the executable is using the provided batch script:

```bash
build.bat
```

This will:
- Clean any previous builds
- Package the application using PyInstaller
- Create `dist/PushToTalk.exe`

## Manual Build

If you prefer to build manually:

```bash
pyinstaller push_to_talk.spec
```

## Configuration Files

### `push_to_talk.spec`
The PyInstaller specification file that defines:
- Entry point: `main.py`
- Hidden imports for all project modules
- Data files to include (src directory, .env.example)
- Executable configuration (console mode, no windowed mode)

### `build.bat`
Windows batch script that:
- Cleans previous builds
- Runs PyInstaller with the spec file
- Reports build status

## Output

After successful build:
- Executable: `dist/PushToTalk.exe`
- Size: ~50-100 MB (includes Python runtime and all dependencies)

## Running the Executable

1. **Environment Setup**: Create a `.env` file in the same directory as the executable with:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. **Administrator Rights**: Run as Administrator for hotkey detection to work properly

3. **Execution**: Double-click `PushToTalk.exe` or run from command line

## Troubleshooting

### Common Issues

1. **Missing Modules**: If you get import errors, add missing modules to `hiddenimports` in `push_to_talk.spec`

2. **Audio Issues**: Ensure PyAudio dependencies are properly included. The spec file already includes `pyaudio` in hidden imports.

3. **Hotkey Not Working**: Make sure to run as Administrator on Windows

4. **Large File Size**: The executable includes the entire Python runtime. This is normal for PyInstaller packages.

### Build Errors

If the build fails:
1. Check that all dependencies are installed: `uv sync`
2. Try building with debug mode: change `debug=False` to `debug=True` in the spec file

## Customization

### Adding an Icon
1. Place an `.ico` file in the project root
2. Update the spec file: `icon='your_icon.ico'`

### Creating a Windowed Application
To hide the console window:
1. Change `console=True` to `console=False` in the spec file
2. Consider adding logging to a file for debugging

### Reducing File Size
1. Use `--onedir` instead of `--onefile` (modify spec file)
2. Exclude unnecessary packages in the `excludes` list
3. Use UPX compression (already enabled in spec file)

## Distribution

The final `PushToTalk.exe` can be distributed as a standalone application. Users will need:
- Windows 10/11
- Microphone access permissions
- Administrator privileges for hotkey functionality
- OpenAI API key (configured in .env file or set in the JSON config file after running the application once)

## Security Note

Windows Defender or other antivirus software may flag PyInstaller executables as potentially unwanted programs. This is a false positive common with packaged Python applications. You may need to add an exception or submit the file for analysis.
