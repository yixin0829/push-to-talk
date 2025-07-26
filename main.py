#!/usr/bin/env python3
"""
PushToTalk Application Entry Point

Run this script to start the push-to-talk speech-to-text application.

Requirements:
- Set OPENAI_API_KEY environment variable
- Ensure microphone permissions are granted
- Run with administrator privileges on Windows for hotkey detection

Usage:
    python main.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src import main

if __name__ == "__main__":
    print("=" * 60)
    print("PushToTalk - Speech-to-Text Push-to-Talk Application")
    print("=" * 60)
    print()
    print("Instructions:")
    print("1. Make sure your OPENAI_API_KEY environment variable is set")
    print("2. Press and hold Ctrl+Shift+Space to record audio")
    print("3. Release the key to process and insert text")
    print("4. Press Ctrl+C to exit")
    print()
    print("Starting application...")
    print()

    main()
