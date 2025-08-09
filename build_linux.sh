#!/usr/bin/env bash
set -euo pipefail

echo "Building PushToTalk Linux executable with PyInstaller..."

# Ensure we're in the repo root (script directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous artifacts
rm -f "dist/PushToTalk" "dist/PushToTalk-linux.zip" || true

# Build using PyInstaller (one-file, windowed)
uv run pyinstaller \
  --name PushToTalk \
  --onefile \
  --noconsole \
  --clean \
  --add-data "src:src" \
  --add-data "icon.ico:." \
  main.py

# Verify build and package
if [[ -f "dist/PushToTalk" ]]; then
  (cd dist && zip -q -r PushToTalk-linux.zip PushToTalk)
  echo "Build successful: dist/PushToTalk"
  echo "Packaged: dist/PushToTalk-linux.zip"
  echo "To run: ./dist/PushToTalk"
else
  echo "Build failed. Check PyInstaller output above." >&2
  exit 1
fi
