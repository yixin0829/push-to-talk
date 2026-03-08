#!/usr/bin/env python3
"""
PushToTalk GUI Application Entry Point

Run this script to start the push-to-talk speech-to-text application with GUI configuration.
"""

import sys
import os
import argparse
import platform
import ctypes
import tkinter as tk
from tkinter import messagebox
from loguru import logger

from src.push_to_talk import PushToTalkConfig
from src.gui import show_configuration_gui


def setup_logging(debug_mode: bool = False):
    """
    Configure logging based on debug mode.

    Args:
        debug_mode: If True, logs to both console and file. If False, logs to file only.
    """
    # Remove default handler
    logger.remove()

    if debug_mode:
        # Add console handler with detailed format for debugging
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )
        # Also add file handler
        logger.add("push_to_talk.log", level="DEBUG")
        logger.info("Debug mode enabled - logging to console and file")
    else:
        # Configure loguru for GUI mode - only log to file
        logger.add("push_to_talk.log", level="INFO")


def main():
    """Main entry point for the GUI application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PushToTalk - Speech to Text Application"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with console logging"
    )
    args = parser.parse_args()

    # Setup logging based on debug flag
    setup_logging(debug_mode=args.debug)

    # Enable High DPI support on Windows
    if platform.system() == "Windows":
        try:
            # Try SetProcessDpiAwareness (Windows 8.1+)
            # 0 = DPI_AWARENESS_UNAWARE
            # 1 = DPI_AWARENESS_SYSTEM_AWARE
            # 2 = DPI_AWARENESS_PER_MONITOR_AWARE
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                # Fallback to SetProcessDPIAware (Windows Vista+)
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

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
