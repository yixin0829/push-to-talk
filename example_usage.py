#!/usr/bin/env python3
"""
PushNTalk - Example Usage

This script demonstrates different ways to use the PushNTalk application.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src import PushNTalkApp, PushNTalkConfig

def example_basic_usage():
    """Example: Basic usage with default settings."""
    print("=== Basic Usage Example ===")
    
    # Create app with default settings
    app = PushNTalkApp()
    
    print("Press Ctrl+Shift+Space to test recording...")
    print("Press Ctrl+C to stop")
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")

def example_custom_config():
    """Example: Custom configuration."""
    print("=== Custom Configuration Example ===")
    
    # Create custom configuration
    config = PushNTalkConfig()
    config.hotkey = "ctrl+shift+space"
    config.enable_text_refinement = False  # Skip GPT refinement for speed
    config.insertion_method = "sendkeys"  # Use keystroke simulation
    
    # Create app with custom config
    app = PushNTalkApp(config)
    
    print("Press Ctrl+Shift+Space to test recording (no text refinement)...")
    print("Press Ctrl+C to stop")
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")

def example_programmatic_control():
    """Example: Programmatic control without running main loop."""
    print("=== Programmatic Control Example ===")
    
    # Create app
    app = PushNTalkApp()
    
    # Start the service
    app.start()
    
    print("Service started. You can now test the hotkey.")
    print("Application status:")
    status = app.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    try:
        # Keep running for 30 seconds
        for i in range(30):
            print(f"Running... {30-i} seconds remaining", end='\r')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Stop the service
        app.stop()
        print("\nService stopped")

def example_hotkey_change():
    """Example: Changing hotkey during runtime."""
    print("=== Runtime Hotkey Change Example ===")
    
    app = PushNTalkApp()
    app.start()
    
    print("Starting with default hotkey: Ctrl+Shift+Space")
    print("Testing for 10 seconds...")
    
    time.sleep(10)
    
    # Change hotkey
    if app.change_hotkey("alt+space"):
        print("Hotkey changed to: Alt+Space")
        print("Testing new hotkey for 10 seconds...")
        time.sleep(10)
    else:
        print("Failed to change hotkey")
    
    app.stop()

def main():
    """Main function to demonstrate different examples."""
    examples = {
        "1": ("Basic Usage", example_basic_usage),
        "2": ("Custom Configuration", example_custom_config),
        "3": ("Programmatic Control", example_programmatic_control),
        "4": ("Runtime Hotkey Change", example_hotkey_change),
    }
    
    print("PushNTalk - Example Usage")
    print("=" * 40)
    print("Choose an example to run:")
    print()
    
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")
    
    print()
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}")
        print("-" * 40)
        func()
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set!")
        print("Please set it before running examples:")
        print("  set OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    main() 