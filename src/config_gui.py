import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
import threading
from typing import Callable, Optional
from dataclasses import asdict

from src.push_to_talk import PushToTalkConfig

logger = logging.getLogger(__name__)


class ConfigurationGUI:
    """GUI for configuring PushToTalk application settings."""

    def __init__(
        self,
        config: PushToTalkConfig,
        on_config_changed: Optional[Callable[[PushToTalkConfig], None]] = None,
    ):
        """
        Initialize the configuration GUI.

        Args:
            config: Current configuration object
            on_config_changed: Callback function called when configuration is updated
        """
        self.config = config
        self.on_config_changed = on_config_changed
        self.root = None
        self.config_vars = {}
        self.result = None  # To store user's choice (save/cancel)

        # Application state
        self.app_instance = None
        self.app_thread = None
        self.is_running = False

        # Status widgets
        self.status_label = None
        self.main_action_btn = None
        self.status_indicator = None
        self.settings_frame = None

    def create_gui(self) -> tk.Tk:
        """Create and return the main GUI window."""
        self.root = tk.Tk()
        self.root.title("PushToTalk Configuration")
        self.root.geometry("600x800")  # Increased height for status section
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
        self._create_api_section(scrollable_frame)
        self._create_audio_section(scrollable_frame)
        self._create_hotkey_section(scrollable_frame)
        self._create_text_insertion_section(scrollable_frame)
        self._create_feature_flags_section(scrollable_frame)
        self._create_status_section(scrollable_frame)
        self._create_buttons_section(scrollable_frame)

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
            "• OpenAI API key (for speech recognition)",
            "• Microphone access",
            "• Administrator privileges (for global hotkeys)",
        ]

        for req in requirements:
            ttk.Label(
                frame, text=req, font=("TkDefaultFont", 8), foreground="gray"
            ).pack(anchor="w")

    def _create_status_section(self, parent: ttk.Widget):
        """Create application status section."""
        frame = ttk.LabelFrame(parent, text="Application Status", padding=15)
        frame.pack(fill="x", pady=(0, 15))

        # Status indicator frame
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill="x")

        # Status indicator (colored circle)
        self.status_indicator = tk.Canvas(
            status_frame, width=20, height=20, highlightthickness=0
        )
        self.status_indicator.pack(side="left", padx=(0, 10))

        # Status text
        self.status_label = ttk.Label(
            status_frame, text="Ready to start", font=("TkDefaultFont", 10, "bold")
        )
        self.status_label.pack(side="left")

        # Update initial status
        self._update_status_display()

        # Active settings display (shown when running)
        self.settings_frame = ttk.Frame(frame)
        # This will be packed when the app starts

    def _update_status_display(self):
        """Update the status indicator and text."""
        if self.status_indicator and self.status_label:
            self.status_indicator.delete("all")

            if self.is_running:
                # Green circle for running
                self.status_indicator.create_oval(
                    2, 2, 18, 18, fill="green", outline="darkgreen"
                )
                self.status_label.config(
                    text="Running - Use your configured hotkeys", foreground="green"
                )

                # Show active settings
                self._show_active_settings()
            else:
                # Gray circle for stopped
                self.status_indicator.create_oval(
                    2, 2, 18, 18, fill="gray", outline="darkgray"
                )
                self.status_label.config(text="Ready to start", foreground="black")

                # Hide active settings
                self._hide_active_settings()

    def _show_active_settings(self):
        """Show the current active settings when running."""
        if not self.settings_frame:
            return

        # Clear existing content
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        if self.is_running and self.config:
            self.settings_frame.pack(fill="x", pady=(10, 0))

            ttk.Label(
                self.settings_frame,
                text="Active Settings:",
                font=("TkDefaultFont", 9, "bold"),
            ).pack(anchor="w")

            settings_text = f"""• Push-to-Talk: {self.config.hotkey}
• Toggle Recording: {self.config.toggle_hotkey}
• Text Refinement: {"Enabled" if self.config.enable_text_refinement else "Disabled"}
• Audio Feedback: {"Enabled" if self.config.enable_audio_feedback else "Disabled"}"""

            ttk.Label(
                self.settings_frame,
                text=settings_text,
                font=("TkDefaultFont", 8),
                foreground="darkgreen",
            ).pack(anchor="w")

    def _hide_active_settings(self):
        """Hide the active settings display."""
        if self.settings_frame:
            self.settings_frame.pack_forget()

    def _create_section_frame(self, parent: ttk.Widget, title: str) -> ttk.LabelFrame:
        """Create a labeled frame for a configuration section."""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def _create_api_section(self, parent: ttk.Widget):
        """Create OpenAI API configuration section."""
        frame = self._create_section_frame(parent, "OpenAI API Settings")

        # API Key
        ttk.Label(frame, text="OpenAI API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["openai_api_key"] = tk.StringVar(
            value=self.config.openai_api_key
        )
        api_key_entry = ttk.Entry(
            frame, textvariable=self.config_vars["openai_api_key"], show="*", width=50
        )
        api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        # Show/Hide API Key button
        def toggle_api_key_visibility():
            if api_key_entry["show"] == "*":
                api_key_entry["show"] = ""
                show_hide_btn["text"] = "Hide"
            else:
                api_key_entry["show"] = "*"
                show_hide_btn["text"] = "Show"

        show_hide_btn = ttk.Button(
            frame, text="Show", command=toggle_api_key_visibility, width=8
        )
        show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)

        # STT Model
        ttk.Label(frame, text="STT Model:").grid(row=1, column=0, sticky="w", pady=2)
        self.config_vars["stt_model"] = tk.StringVar(value=self.config.stt_model)
        whisper_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["stt_model"],
            values=["whisper-1", "gpt-4o-transcribe"],
            state="readonly",
            width=20,
        )
        whisper_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Refinement Model
        ttk.Label(frame, text="Refinement Model:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.config_vars["refinement_model"] = tk.StringVar(
            value=self.config.refinement_model
        )
        gpt_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["refinement_model"],
            values=["gpt-4o-mini", "gpt-4.1-nano", "gpt-4o"],
            state="readonly",
            width=20,
        )
        gpt_combo.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=2)

        frame.columnconfigure(1, weight=1)

    def _create_audio_section(self, parent: ttk.Widget):
        """Create audio configuration section."""
        frame = self._create_section_frame(parent, "Audio Settings")

        # Sample Rate
        ttk.Label(frame, text="Sample Rate (Hz):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["sample_rate"] = tk.IntVar(value=self.config.sample_rate)
        sample_rate_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["sample_rate"],
            values=[8000, 16000, 22050, 44100],
            state="readonly",
            width=15,
        )
        sample_rate_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Chunk Size
        ttk.Label(frame, text="Chunk Size:").grid(row=1, column=0, sticky="w", pady=2)
        self.config_vars["chunk_size"] = tk.IntVar(value=self.config.chunk_size)
        chunk_size_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["chunk_size"],
            values=[512, 1024, 2048, 4096],
            state="readonly",
            width=15,
        )
        chunk_size_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Channels
        ttk.Label(frame, text="Channels:").grid(row=2, column=0, sticky="w", pady=2)
        self.config_vars["channels"] = tk.IntVar(value=self.config.channels)
        channels_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["channels"],
            values=[1, 2],
            state="readonly",
            width=15,
        )
        channels_combo.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        ttk.Label(
            frame,
            text="Recommended: 16000 Hz, 1024 chunk, 1 channel",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def _create_hotkey_section(self, parent: ttk.Widget):
        """Create hotkey configuration section."""
        frame = self._create_section_frame(parent, "Hotkey Settings")

        # Push-to-talk hotkey
        ttk.Label(frame, text="Push-to-Talk Hotkey:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["hotkey"] = tk.StringVar(value=self.config.hotkey)
        hotkey_entry = ttk.Entry(
            frame, textvariable=self.config_vars["hotkey"], width=25
        )
        hotkey_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Toggle hotkey
        ttk.Label(frame, text="Toggle Recording Hotkey:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.config_vars["toggle_hotkey"] = tk.StringVar(
            value=self.config.toggle_hotkey
        )
        toggle_hotkey_entry = ttk.Entry(
            frame, textvariable=self.config_vars["toggle_hotkey"], width=25
        )
        toggle_hotkey_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        help_text = "Examples: ctrl+shift+space, alt+space, f12, ctrl+alt+r"
        ttk.Label(
            frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def _create_text_insertion_section(self, parent: ttk.Widget):
        """Create text insertion configuration section."""
        frame = self._create_section_frame(parent, "Text Insertion Settings")

        # Insertion Method
        ttk.Label(frame, text="Insertion Method:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["insertion_method"] = tk.StringVar(
            value=self.config.insertion_method
        )
        insertion_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["insertion_method"],
            values=["sendkeys", "clipboard"],
            state="readonly",
            width=15,
        )
        insertion_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Insertion Delay
        ttk.Label(frame, text="Insertion Delay (seconds):").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.config_vars["insertion_delay"] = tk.DoubleVar(
            value=self.config.insertion_delay
        )
        delay_spinbox = tk.Spinbox(
            frame,
            textvariable=self.config_vars["insertion_delay"],
            from_=0.0,
            to=1.0,
            increment=0.01,
            width=15,
            format="%.3f",
        )
        delay_spinbox.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        help_text = "sendkeys: better for special chars, clipboard: faster"
        ttk.Label(
            frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def _create_feature_flags_section(self, parent: ttk.Widget):
        """Create feature flags configuration section."""
        frame = self._create_section_frame(parent, "Feature Settings")

        # Text Refinement
        self.config_vars["enable_text_refinement"] = tk.BooleanVar(
            value=self.config.enable_text_refinement
        )
        ttk.Checkbutton(
            frame,
            text="Enable Text Refinement (uses GPT for better text quality)",
            variable=self.config_vars["enable_text_refinement"],
        ).grid(row=0, column=0, sticky="w", pady=2)

        # Logging
        self.config_vars["enable_logging"] = tk.BooleanVar(
            value=self.config.enable_logging
        )
        ttk.Checkbutton(
            frame,
            text="Enable Logging (creates push_to_talk.log file)",
            variable=self.config_vars["enable_logging"],
        ).grid(row=1, column=0, sticky="w", pady=2)

        # Audio Feedback
        self.config_vars["enable_audio_feedback"] = tk.BooleanVar(
            value=self.config.enable_audio_feedback
        )
        ttk.Checkbutton(
            frame,
            text="Enable Audio Feedback (plays sounds when recording starts/stops)",
            variable=self.config_vars["enable_audio_feedback"],
        ).grid(row=2, column=0, sticky="w", pady=2)

    def _create_buttons_section(self, parent: ttk.Widget):
        """Create buttons section."""
        frame = ttk.Frame(parent)
        # Add extra bottom padding for margin
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

    def _validate_configuration(self) -> bool:
        """Validate the current configuration."""
        # Check API key
        if not self.config_vars["openai_api_key"].get().strip():
            messagebox.showerror("Validation Error", "OpenAI API key is required!")
            return False

        # Check hotkeys are different
        if self.config_vars["hotkey"].get() == self.config_vars["toggle_hotkey"].get():
            messagebox.showerror(
                "Validation Error", "Push-to-talk and toggle hotkeys must be different!"
            )
            return False

        return True

    def _test_configuration(self):
        """Test the current configuration."""
        if not self._validate_configuration():
            return

        # Create test config
        test_config = self._get_config_from_gui()

        try:
            # Test OpenAI API key by trying to create a client
            from openai import OpenAI

            _ = OpenAI(api_key=test_config.openai_api_key)

            # Try a simple API call to validate the key
            messagebox.showinfo(
                "Test Result",
                "Configuration test successful!\n\nAPI key is valid and configuration looks good.",
            )

        except Exception as e:
            messagebox.showerror(
                "Test Failed", f"Configuration test failed:\n\n{str(e)}"
            )

    def _reset_to_defaults(self):
        """Reset configuration to defaults."""
        if messagebox.askyesno(
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
        ):
            default_config = PushToTalkConfig()
            self._update_gui_from_config(default_config)

    def _update_gui_from_config(self, config: PushToTalkConfig):
        """Update GUI fields from a configuration object."""
        self.config_vars["openai_api_key"].set(config.openai_api_key)
        self.config_vars["stt_model"].set(config.stt_model)
        self.config_vars["refinement_model"].set(config.refinement_model)
        self.config_vars["sample_rate"].set(config.sample_rate)
        self.config_vars["chunk_size"].set(config.chunk_size)
        self.config_vars["channels"].set(config.channels)
        self.config_vars["hotkey"].set(config.hotkey)
        self.config_vars["toggle_hotkey"].set(config.toggle_hotkey)
        self.config_vars["insertion_method"].set(config.insertion_method)
        self.config_vars["insertion_delay"].set(config.insertion_delay)
        self.config_vars["enable_text_refinement"].set(config.enable_text_refinement)
        self.config_vars["enable_logging"].set(config.enable_logging)
        self.config_vars["enable_audio_feedback"].set(config.enable_audio_feedback)

    def _get_config_from_gui(self) -> PushToTalkConfig:
        """Create a configuration object from current GUI values."""
        return PushToTalkConfig(
            openai_api_key=self.config_vars["openai_api_key"].get().strip(),
            stt_model=self.config_vars["stt_model"].get(),
            refinement_model=self.config_vars["refinement_model"].get(),
            sample_rate=self.config_vars["sample_rate"].get(),
            chunk_size=self.config_vars["chunk_size"].get(),
            channels=self.config_vars["channels"].get(),
            hotkey=self.config_vars["hotkey"].get().strip(),
            toggle_hotkey=self.config_vars["toggle_hotkey"].get().strip(),
            insertion_method=self.config_vars["insertion_method"].get(),
            insertion_delay=self.config_vars["insertion_delay"].get(),
            enable_text_refinement=self.config_vars["enable_text_refinement"].get(),
            enable_logging=self.config_vars["enable_logging"].get(),
            enable_audio_feedback=self.config_vars["enable_audio_feedback"].get(),
        )

    def _toggle_application(self):
        """Toggle between starting and stopping the application."""
        if not self.is_running:
            self._start_application()
        else:
            self._stop_application()

    def _start_application(self):
        """Start the push-to-talk application."""
        if not self._validate_configuration():
            return

        try:
            # Update config object
            self.config = self._get_config_from_gui()

            # Save to default file
            self.config.save_to_file("push_to_talk_config.json")
            logger.info("Configuration saved to push_to_talk_config.json")

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
            self._update_status_display()

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
            # Update UI from main thread - capture error in closure
            self.root.after(0, lambda err=error: self._handle_app_error(err))

    def _handle_app_error(self, error):
        """Handle application errors from the main thread."""
        self.is_running = False
        self.main_action_btn.config(text="Start Application", style="Accent.TButton")
        self._update_status_display()

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
            self._update_status_display()

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

    def _save_and_start(self):
        """Save configuration and start the application."""
        # This method is now replaced by _toggle_application
        # Keeping for compatibility but redirecting
        self._start_application()

    def _cancel(self):
        """Cancel configuration and exit."""
        # This method is now replaced by _close_application
        # Keeping for compatibility but redirecting
        self._close_application()

    def show_modal(self) -> str:
        """Show the configuration GUI as a modal dialog and return the result."""
        self.create_gui()
        self.root.protocol(
            "WM_DELETE_WINDOW", self._close_application
        )  # Handle window close
        self.root.mainloop()

        # Clean up if still running
        if self.is_running:
            self._stop_application()

        if self.root:
            self.root.destroy()

        return self.result or "close"


def show_configuration_gui(
    config: Optional[PushToTalkConfig] = None,
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

    gui = ConfigurationGUI(config)
    result = gui.show_modal()

    return result, gui.config


if __name__ == "__main__":
    # Test the GUI
    config = PushToTalkConfig()
    result, updated_config = show_configuration_gui(config)
    print(f"Result: {result}")
    if result == "start":
        print("Configuration:")
        for key, value in asdict(updated_config).items():
            if key == "openai_api_key" and value:
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")
