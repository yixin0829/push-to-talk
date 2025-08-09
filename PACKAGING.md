# Packaging PushToTalk for Windows, macOS, and Linux

This guide explains how to package the PushToTalk application as standalone executables for all supported platforms using PyInstaller.

> Note: PyInstaller does not cross-compile. You must run the build on the target operating system.

## Prerequisites

1. uv: Ensure you have `uv` installed (`https://docs.astral.sh/uv/`).
2. Project dependencies: install with:
   ```bash
   uv sync
   ```
3. Platform-specific build prerequisites for PyAudio (PortAudio):
   - macOS: `brew install portaudio`
   - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y portaudio19-dev` (plus build tools if needed)

## Quick Builds (recommended)

We provide a master build script and per-platform scripts. All builds use `uv` to run PyInstaller.

### Master script (current host only)
```bash
uv run python build.py -p all
```
or select a specific platform:
```bash
uv run python build.py -p windows
uv run python build.py -p macos
uv run python build.py -p linux
```

### Windows
```powershell
build.bat
```
This script cleans artifacts, runs PyInstaller with `push_to_talk.spec`, and zips the result.

### macOS
```bash
chmod +x build_macos.sh
./build_macos.sh
```

### Linux
```bash
chmod +x build_linux.sh
./build_linux.sh
```

## Manual Builds

### Windows (spec file)
```bash
uv run pyinstaller push_to_talk.spec
```

### macOS/Linux (one-file CLI flags)
```bash
uv run pyinstaller \
  --name PushToTalk \
  --onefile \
  --noconsole \
  --clean \
  --add-data "src:src" \
  --add-data "icon.ico:." \
  main.py
```

## What the build includes

- Entry point: `main.py`
- Data files: `src` directory (includes assets under `src/assets/audio`) and `icon.ico`
- Windowed/GUI mode (no console window)
- UPX compression enabled on Windows via the spec

## Outputs

- Windows: `dist/PushToTalk.exe` (and `dist/PushToTalk.zip` when using `build.bat`)
- macOS: `dist/PushToTalk` and `dist/PushToTalk-macos.zip`
- Linux: `dist/PushToTalk` and `dist/PushToTalk-linux.zip`

Typical size is ~50–100 MB as the Python runtime and dependencies are bundled.

## Running the Executable

1. Configure your OpenAI API key via the in-app GUI on first run, or set the `OPENAI_API_KEY` environment variable.
2. Windows: for global hotkey detection, run as Administrator.
3. macOS: the binary is unsigned. If blocked by Gatekeeper, right-click → Open, or allow it in System Settings → Privacy & Security. You may also need to remove quarantine: `xattr -r -d com.apple.quarantine dist/PushToTalk`.
4. Linux: ensure execute permission (`chmod +x dist/PushToTalk`) and required audio libraries are installed.

## Troubleshooting

1. Missing modules at runtime: ensure dependencies are installed (`uv sync`). Add missing packages to project dependencies if needed.
2. Audio issues (PyAudio): install PortAudio dev packages (see prerequisites). On Linux, also check ALSA/PulseAudio setup.
3. Hotkey not working on Windows: run as Administrator.
4. Large file size: normal for PyInstaller; consider `--onedir` mode to reduce duplication across versions.
5. Build failures: try a clean build (`rm -rf build dist`) and/or enable debug (Windows spec: set `debug=True` in `push_to_talk.spec`).

## Customization

### Icon
- Place an `.ico` file in the project root and update references if you rename it.
- Windows spec already sets `icon='icon.ico'`.

### Windowed vs console
- Windows is configured as a GUI app in `push_to_talk.spec` (`console=False`).
- macOS/Linux scripts pass `--noconsole` to hide the console.

### One-file vs one-dir
- Current scripts use one-file. For faster startup and easier patching, consider `--onedir` or adjusting the spec accordingly.

## Files referenced

- `push_to_talk.spec`: Windows PyInstaller specification (includes `src` and `icon.ico`).
- `build.bat`: Windows build and zip script.
- `build_macos.sh`: macOS build and zip script.
- `build_linux.sh`: Linux build and zip script.
- `build.py`: Master script to build selected platforms (runs only on matching host OS).
