"""Main configuration window for PushToTalk application."""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Callable
from loguru import logger

from src.push_to_talk import PushToTalkConfig
from src.config.constants import CONFIG_CHANGE_DEBOUNCE_DELAY_MS
from src.gui.api_section import APISection
from src.gui.audio_section import AudioSection
from src.gui.hotkey_section import HotkeySection
from src.gui.settings_section import TextInsertionSection, FeatureFlagsSection
from src.gui.glossary_section import GlossarySection
from src.gui.status_section import StatusSection
from src.gui.validators import validate_configuration
from src.gui.config_persistence import ConfigurationPersistence


class ConfigurationWindow:
    """Main GUI window for configuring PushToTalk application settings."""

    def __init__(
        self,
        config: PushToTalkConfig,
        on_config_changed: Callable[[PushToTalkConfig], None] | None = None,
        config_file_path: str = "push_to_talk_config.json",
    ):
        """
        Initialize the configuration window.

        Args:
            config: Current configuration object
            on_config_changed: Callback function called when configuration is updated
            config_file_path: Path to the configuration file for persistence
        """
        self.config = config
        self.on_config_changed = on_config_changed
        self.config_file_path = config_file_path
        self.root = None
        self.result = None  # To store user's choice

        # Application state
        self.app_instance = None
        self.app_thread = None
        self.is_running = False

        # UI sections
        self.api_section = None
        self.audio_section = None
        self.hotkey_section = None
        self.text_insertion_section = None
        self.feature_flags_section = None
        self.glossary_section = None
        self.status_section = None

        # Main action button
        self.main_action_btn = None

        # Configuration change tracking
        self._variable_traces: list[tuple[tk.Variable, str]] = []
        self._suspend_change_events = False
        self._pending_update_job: str | None = None
        self._initialization_complete = False  # Track if initial setup is done

        # Configuration persistence
        self._config_persistence = ConfigurationPersistence()

    def create_gui(self) -> tk.Tk:
        """Create and return the main GUI window."""
        self.root = tk.Tk()
        self.root.title("PushToTalk Configuration")
        self.root.geometry("600x800")
        self.root.resizable(True, True)

        # Configure icon if available
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except Exception:
            pass  # Ignore icon errors

        # Create main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Create sections
        self._create_welcome_section(scrollable_frame)
        self.api_section = APISection(
            scrollable_frame, on_change=self._on_config_changed
        )
        self.audio_section = AudioSection(scrollable_frame)
        self.hotkey_section = HotkeySection(scrollable_frame)
        self.text_insertion_section = TextInsertionSection(scrollable_frame)
        self.glossary_section = GlossarySection(
            scrollable_frame,
            self.root,
            self.config.custom_glossary,
            on_change=self._on_config_changed,
        )
        self.feature_flags_section = FeatureFlagsSection(scrollable_frame)
        self.status_section = StatusSection(scrollable_frame)
        self._create_buttons_section(scrollable_frame)

        # Set initial values
        self._update_sections_from_config(self.config)

        # Monitor configuration variables for live updates
        self._setup_variable_traces()

        # Mark initialization as complete - now changes should trigger saves
        self._initialization_complete = True

        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

        return self.root

    def _create_welcome_section(self, parent: ttk.Widget):
        """Create welcome message section at the top."""
        frame = ttk.LabelFrame(parent, text="Welcome to PushToTalk", padding=15)
        frame.pack(fill="x", pady=(0, 15))

        # Main welcome text
        welcome_text = """AI Speech-to-Text with Push-to-Talk

This application provides push-to-talk speech-to-text functionality with AI refinement.

Configure your settings below, then click "Start Application" to begin:"""

        welcome_label = ttk.Label(
            frame, text=welcome_text, font=("TkDefaultFont", 10), justify="left"
        )
        welcome_label.pack(anchor="w")

        # Requirements list
        ttk.Label(frame, text="Required:", font=("TkDefaultFont", 9, "bold")).pack(
            anchor="w", pady=(10, 2)
        )

        requirements = [
            "• OpenAI or Deepgram API key (for speech recognition)",
            "• Microphone access",
            "• Administrator privileges (for global hotkeys)",
        ]

        for req in requirements:
            ttk.Label(
                frame, text=req, font=("TkDefaultFont", 8), foreground="gray"
            ).pack(anchor="w")

    def _create_buttons_section(self, parent: ttk.Widget):
        """Create buttons section."""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(5, 20))

        button_frame = ttk.Frame(frame)
        button_frame.pack(anchor="center")

        # Main action button (Start/Terminate)
        self.main_action_btn = ttk.Button(
            button_frame,
            text="Start Application",
            command=self._toggle_application,
            style="Accent.TButton",
        )
        self.main_action_btn.pack(side="left", padx=(0, 10))

        # Test Configuration button
        test_btn = ttk.Button(
            button_frame, text="Test Configuration", command=self._test_configuration
        )
        test_btn.pack(side="left", padx=(0, 10))

        # Reset to Defaults button
        reset_btn = ttk.Button(
            button_frame, text="Reset to Defaults", command=self._reset_to_defaults
        )
        reset_btn.pack(side="left", padx=(0, 10))

        # Cancel/Close button
        cancel_btn = ttk.Button(
            button_frame, text="Close", command=self._close_application
        )
        cancel_btn.pack(side="left")

    def _setup_variable_traces(self):
        """
        Attach trace callbacks to configuration variables for live updates.

        This implements the variable tracing system that automatically detects
        when any GUI field changes and triggers real-time configuration updates.
        """
        if self._variable_traces:
            return

        self._suspend_change_events = True
        try:
            # Get all Tkinter variables from all sections
            all_vars = []
            if self.api_section:
                all_vars.extend(
                    [
                        self.api_section.stt_provider_var,
                        self.api_section.openai_api_key_var,
                        self.api_section.deepgram_api_key_var,
                        self.api_section.stt_model_var,
                        self.api_section.refinement_model_var,
                    ]
                )
            if self.audio_section:
                all_vars.extend(
                    [
                        self.audio_section.sample_rate_var,
                        self.audio_section.chunk_size_var,
                        self.audio_section.channels_var,
                    ]
                )
            if self.hotkey_section:
                all_vars.extend(
                    [
                        self.hotkey_section.hotkey_var,
                        self.hotkey_section.toggle_hotkey_var,
                    ]
                )
            if self.text_insertion_section:
                all_vars.append(self.text_insertion_section.insertion_delay_var)
            if self.feature_flags_section:
                all_vars.extend(
                    [
                        self.feature_flags_section.enable_text_refinement_var,
                        self.feature_flags_section.enable_logging_var,
                        self.feature_flags_section.enable_audio_feedback_var,
                        self.feature_flags_section.debug_mode_var,
                    ]
                )

            # Attach traces
            for var in all_vars:
                trace_id = var.trace_add("write", self._on_config_changed)
                self._variable_traces.append((var, trace_id))
        finally:
            self._suspend_change_events = False

    def _on_config_changed(self, *args):
        """
        Handle configuration variable changes from the GUI.

        Implements debouncing to prevent excessive updates during rapid user input.
        """
        if self._suspend_change_events:
            return

        if self.root and self.root.winfo_exists():
            if self._pending_update_job:
                try:
                    self.root.after_cancel(self._pending_update_job)
                except Exception:
                    pass
            self._pending_update_job = self.root.after(
                CONFIG_CHANGE_DEBOUNCE_DELAY_MS, self._apply_config_changes
            )
        else:
            self._apply_config_changes()

    def _apply_config_changes(self, force: bool = False):
        """Apply GUI-driven configuration changes."""
        self._pending_update_job = None
        self._notify_config_changed(force=force)

    def _notify_config_changed(self, *, force: bool = False):
        """
        Notify listeners and running app about configuration changes.

        Args:
            force: If True, skip the config comparison and force an update
        """
        new_config = self._get_config_from_sections()

        if not force and new_config == self.config:
            return

        self.config = new_config

        if self.on_config_changed:
            try:
                self.on_config_changed(new_config)
            except Exception as error:
                logger.error(f"Error in configuration change callback: {error}")

        if self.is_running and self.app_instance:
            try:
                self.app_instance.update_configuration(new_config)
            except Exception as error:
                logger.error(
                    f"Failed to update running application configuration: {error}"
                )

        if self.is_running:
            self.status_section.update_display(True, new_config)

        # Save configuration to JSON file for persistence
        # Only save if initialization is complete to avoid overwriting loaded config
        if self._initialization_complete:
            self._config_persistence.save_async(new_config, self.config_file_path)

    def _get_config_from_sections(self) -> PushToTalkConfig:
        """Create a configuration object from current section values."""
        api_values = self.api_section.get_values()
        audio_values = self.audio_section.get_values()
        hotkey_values = self.hotkey_section.get_values()
        feature_values = self.feature_flags_section.get_values()

        return PushToTalkConfig(
            stt_provider=api_values["stt_provider"],
            openai_api_key=api_values["openai_api_key"],
            deepgram_api_key=api_values["deepgram_api_key"],
            cerebras_api_key=api_values["cerebras_api_key"],
            stt_model=api_values["stt_model"],
            refinement_provider=api_values["refinement_provider"],
            refinement_model=api_values["refinement_model"],
            sample_rate=audio_values["sample_rate"],
            chunk_size=audio_values["chunk_size"],
            channels=audio_values["channels"],
            hotkey=hotkey_values["hotkey"],
            toggle_hotkey=hotkey_values["toggle_hotkey"],
            insertion_delay=self.text_insertion_section.get_value(),
            enable_text_refinement=feature_values["enable_text_refinement"],
            enable_logging=feature_values["enable_logging"],
            enable_audio_feedback=feature_values["enable_audio_feedback"],
            debug_mode=feature_values["debug_mode"],
            custom_glossary=self.glossary_section.get_terms(),
        )

    def _update_sections_from_config(self, config: PushToTalkConfig):
        """Update all section values from a configuration object."""
        self._suspend_change_events = True
        try:
            self.api_section.set_values(
                config.stt_provider,
                config.openai_api_key,
                config.deepgram_api_key,
                config.cerebras_api_key,
                config.stt_model,
                config.refinement_provider,
                config.refinement_model,
            )
            self.audio_section.set_values(
                config.sample_rate, config.chunk_size, config.channels
            )
            self.hotkey_section.set_values(config.hotkey, config.toggle_hotkey)
            self.text_insertion_section.set_value(config.insertion_delay)
            self.feature_flags_section.set_values(
                config.enable_text_refinement,
                config.enable_logging,
                config.enable_audio_feedback,
                config.debug_mode,
            )
            self.glossary_section.set_terms(config.custom_glossary)
        finally:
            self._suspend_change_events = False

    def _test_configuration(self):
        """Test all provider API keys and show comprehensive status."""
        status_report = self.api_section.test_api_keys()
        messagebox.showinfo("Configuration Test Results", status_report)

    def _reset_to_defaults(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno(
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
        ):
            default_config = PushToTalkConfig()
            self._update_sections_from_config(default_config)
            self._notify_config_changed(force=True)

    def _toggle_application(self):
        """Toggle between starting and stopping the application."""
        if not self.is_running:
            self._start_application()
        else:
            self._stop_application()

    def _start_application(self):
        """Start the push-to-talk application."""
        # Validate configuration
        config = self._get_config_from_sections()
        is_valid, error_msg = validate_configuration(config)
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        try:
            # Update config object
            self.config = config

            # Save to config file
            self._config_persistence.save_sync(config, self.config_file_path)

            # Import here to avoid circular imports
            from src.push_to_talk import PushToTalkApp

            # Create app instance
            self.app_instance = PushToTalkApp(self.config)

            # Start application in separate thread
            self.app_thread = threading.Thread(
                target=self._run_application_thread, daemon=True
            )
            self.app_thread.start()

            # Update UI state
            self.is_running = True
            self.main_action_btn.config(text="Stop Application", style="")
            self.status_section.update_display(True, self.config)

            logger.info("Application started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            messagebox.showerror("Error", f"Failed to start application:\n\n{str(e)}")

    def _run_application_thread(self):
        """Run the application in a separate thread."""
        try:
            if self.app_instance:
                # Start without signal handlers since we're in a thread
                self.app_instance.start(setup_signals=False)

                # Keep running until stopped
                while self.app_instance and self.app_instance.is_running:
                    import time

                    time.sleep(0.1)

        except Exception as error:
            logger.error(f"Application thread error: {error}")
            # Update UI from main thread
            self.root.after(0, lambda err=error: self._handle_app_error(err))

    def _handle_app_error(self, error):
        """Handle application errors from the main thread."""
        self.is_running = False
        self.main_action_btn.config(text="Start Application", style="Accent.TButton")
        self.status_section.update_display(False, None)

        messagebox.showerror(
            "Application Error",
            f"The application encountered an error:\n\n{str(error)}\n\nCheck push_to_talk.log for details.",
        )

    def _stop_application(self):
        """Stop the push-to-talk application."""
        try:
            if self.app_instance:
                # Stop the application
                self.app_instance.stop()
                logger.info("Application stopped by user")

            # Update UI state
            self.is_running = False
            self.main_action_btn.config(
                text="Start Application", style="Accent.TButton"
            )
            self.status_section.update_display(False, None)

            # Wait for the background thread to finish before clearing references
            if self.app_thread and self.app_thread.is_alive():
                self.app_thread.join(timeout=1)

            self.app_instance = None
            self.app_thread = None

        except Exception as e:
            logger.error(f"Error stopping application: {e}")
            messagebox.showerror("Error", f"Error stopping application:\n\n{str(e)}")

    def _close_application(self):
        """Close the configuration GUI."""
        if self.is_running:
            if messagebox.askyesno(
                "Application Running",
                "The push-to-talk application is currently running.\n\nDo you want to stop it and close the configuration window?",
            ):
                self._stop_application()
                self.result = "close"
                self.root.quit()
        else:
            self.result = "close"
            self.root.quit()

    def show_modal(self) -> str:
        """Show the configuration GUI as a modal dialog and return the result."""
        self.create_gui()
        self.root.protocol("WM_DELETE_WINDOW", self._close_application)
        self.root.mainloop()

        # Clean up if still running
        if self.is_running:
            self._stop_application()

        if self.root:
            self.root.destroy()

        return self.result or "close"


def show_configuration_gui(
    config: PushToTalkConfig | None = None,
) -> tuple[str, PushToTalkConfig]:
    """
    Show the configuration GUI and return the result.

    Args:
        config: Initial configuration, or None for defaults

    Returns:
        Tuple of (result, config) where result is "start", "close", or "cancel"
    """
    if config is None:
        config = PushToTalkConfig()

    gui = ConfigurationWindow(config)
    result = gui.show_modal()

    return result, gui.config
