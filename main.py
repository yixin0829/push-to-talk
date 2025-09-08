#!/usr/bin/env python3
"""
PushToTalk GUI Application Entry Point

Run this script to start the push-to-talk speech-to-text application with GUI configuration.

Requirements:
- Set OPENAI_API_KEY environment variable or configure in GUI
- Ensure microphone permissions are granted
- Run with administrator privileges on Windows for hotkey detection

Usage:
    python main.py
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from loguru import logger

from src.push_to_talk import PushToTalkConfig
from src.config_gui import show_configuration_gui

# Configure loguru for GUI mode - only log to file
logger.remove()  # Remove default handler
logger.add("push_to_talk.log", level="INFO")


def main():
    """Main entry point for the GUI application."""
    try:
        # Load existing config if it exists
        config_file = "push_to_talk_config.json"
        if os.path.exists(config_file):
            config = PushToTalkConfig.load_from_file(config_file)
            logger.info(f"Loaded existing configuration from {config_file}")
        else:
            config = PushToTalkConfig()
            logger.info("Using default configuration")

        # Show configuration GUI (now persistent and manages the app)
        result, updated_config = show_configuration_gui(config)

        # Handle the result from the GUI
        if result == "close":
            logger.info("Application closed by user")
        else:
            logger.info("Application session ended")

    except Exception as e:
        logger.error(f"Application error: {e}")

        # Show error message in GUI if possible
        try:
            root = tk.Tk()
            root.withdraw()

            error_message = f"""An error occurred while running the application:

{str(e)}

Common solutions:
• Make sure your OpenAI API key is valid
• Check that you have microphone permissions
• Run as Administrator for hotkey detection
• Ensure internet connectivity for OpenAI API

Check push_to_talk.log for detailed error information."""

            messagebox.showerror("PushToTalk - Error", error_message, parent=root)
            root.destroy()
        except Exception:
            # Fallback to console if GUI fails
            print(f"Fatal error: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
