#!/usr/bin/env python3
"""
PushToTalk GUI Application Entry Point

Run this script to start the push-to-talk speech-to-text application with GUI configuration.

Requirements:
- Set OPENAI_API_KEY environment variable or configure in GUI
- Ensure microphone permissions are granted
- Run with administrator privileges on Windows for hotkey detection

Usage:
    python main_gui.py
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.push_to_talk import PushToTalkApp, PushToTalkConfig
from src.config_gui import show_configuration_gui

# Configure logging for GUI mode
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("push_to_talk.log")],  # Only log to file in GUI mode
)

logger = logging.getLogger(__name__)


def show_startup_message():
    """Show a startup message window."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Configure icon if available
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except Exception:
        pass

    message = """Welcome to PushToTalk - AI Speech-to-Text

This application provides push-to-talk speech-to-text functionality with AI refinement.

Before starting, you'll need to configure:
• OpenAI API key (required for speech recognition)
• Audio settings (sample rate, etc.)
• Hotkey combinations
• Other preferences

Click OK to open the configuration window."""

    messagebox.showinfo("PushToTalk - Welcome", message, parent=root)
    root.destroy()


def main_gui():
    """Main entry point for the GUI application."""
    try:
        # Show welcome message
        show_startup_message()

        # Load existing config if it exists
        config_file = "push_to_talk_config.json"
        if os.path.exists(config_file):
            config = PushToTalkConfig.load_from_file(config_file)
            logger.info(f"Loaded existing configuration from {config_file}")
        else:
            config = PushToTalkConfig()
            logger.info("Using default configuration")

        # Show configuration GUI
        result, updated_config = show_configuration_gui(config)

        if result == "cancel":
            logger.info("User cancelled configuration")
            return

        # Validate configuration
        if not updated_config.openai_api_key.strip():
            # Check environment variable as fallback
            env_api_key = os.getenv("OPENAI_API_KEY")
            if env_api_key:
                updated_config.openai_api_key = env_api_key
            else:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "Configuration Error",
                    "OpenAI API key is required to run the application!\n\n"
                    "Please either:\n"
                    "1. Set the OPENAI_API_KEY environment variable, or\n"
                    "2. Configure it in the settings window",
                )
                root.destroy()
                return

        # Save configuration
        updated_config.save_to_file(config_file)
        logger.info(f"Configuration saved to {config_file}")

        # Show final startup message
        root = tk.Tk()
        root.withdraw()

        try:
            if os.path.exists("icon.ico"):
                root.iconbitmap("icon.ico")
        except Exception:
            pass

        startup_info = f"""Configuration saved successfully!

Starting PushToTalk with the following settings:
• Push-to-Talk Hotkey: {updated_config.hotkey}
• Toggle Recording Hotkey: {updated_config.toggle_hotkey}
• Text Refinement: {"Enabled" if updated_config.enable_text_refinement else "Disabled"}
• Audio Feedback: {"Enabled" if updated_config.enable_audio_feedback else "Disabled"}

The application will run in the background.
Use your configured hotkeys to record and transcribe speech.

Click OK to start the application."""

        messagebox.showinfo("PushToTalk - Starting", startup_info, parent=root)
        root.destroy()

        # Create and run application
        logger.info("Starting PushToTalk application")
        app = PushToTalkApp(updated_config)

        # Set up configuration update callback
        def on_config_changed(new_config: PushToTalkConfig):
            """Callback for when configuration is changed during runtime."""
            app.update_configuration(new_config)

        logger.info("Application started successfully")
        logger.info(f"Push-to-talk hotkey: {updated_config.hotkey}")
        logger.info(f"Toggle recording hotkey: {updated_config.toggle_hotkey}")
        logger.info("Press Ctrl+C to exit")

        # Run the application
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")

        # Show error message in GUI
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

        sys.exit(1)


if __name__ == "__main__":
    main_gui()
