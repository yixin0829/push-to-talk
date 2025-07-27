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

from src import ConfigGUI

if __name__ == "__main__":
    ConfigGUI().mainloop()
