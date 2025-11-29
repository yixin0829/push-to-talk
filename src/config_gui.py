import tkinter as tk
from tkinter import ttk, messagebox
import os
from loguru import logger
import threading
from typing import Callable, Optional
from dataclasses import asdict
import json

from src.push_to_talk import PushToTalkConfig
from src.config.constants import CONFIG_CHANGE_DEBOUNCE_DELAY_MS


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

        # Configuration change tracking
        self._variable_traces: list[tuple[tk.Variable, str]] = []
        self._suspend_change_events = False
        self._pending_update_job: Optional[str] = None

        # Non-blocking save functionality
        self._save_lock = threading.Lock()
        self._save_pending = False

        # Glossary state (available even before the GUI is created)
        self.glossary_terms = list(self.config.custom_glossary)

        # Provider-specific widget storage
        self.openai_widgets = {}
        self.deepgram_widgets = {}
        self.stt_model_combo = None

        # Provider-specific model selections (to preserve when switching)
        self.openai_stt_model = (
            self.config.stt_model
            if self.config.stt_provider == "openai"
            else "gpt-4o-mini-transcribe"
        )
        self.deepgram_stt_model = (
            self.config.stt_model
            if self.config.stt_provider == "deepgram"
            else "nova-3"
        )

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
        self._create_glossary_section(scrollable_frame)
        self._create_feature_flags_section(scrollable_frame)
        self._create_status_section(scrollable_frame)
        self._create_buttons_section(scrollable_frame)

        # Monitor configuration variables for live updates
        self._setup_variable_traces()

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

    def _setup_variable_traces(self):
        """
        Attach trace callbacks to configuration variables for live updates.

        This implements the variable tracing system that automatically detects
        when any GUI field changes and triggers real-time configuration updates.

        How it works:
        - Each Tkinter variable (StringVar, IntVar, BooleanVar, etc.) gets a "write" trace
        - When ANY variable changes, _on_config_var_changed() is called automatically
        - This enables event-driven updates without manual polling
        - Traces are suspended during programmatic updates to prevent infinite loops
        """
        if self._variable_traces:
            return

        self._suspend_change_events = True
        try:
            for var in self.config_vars.values():
                trace_id = var.trace_add("write", self._on_config_var_changed)
                self._variable_traces.append((var, trace_id))
        finally:
            self._suspend_change_events = False

    def _on_config_var_changed(self, *args):
        """
        Handle configuration variable changes from the GUI.

        This implements the debouncing system that prevents excessive updates
        during rapid user input (e.g., typing in a text field).

        Debouncing process:
        1. User makes a change → This method is called
        2. Cancel any pending update timer
        3. Schedule new update after debounce delay
        4. If user makes another change within delay period → Cancel and reschedule
        5. When delay period passes with no new changes → Execute the update

        Example:
        User types "ctrl+alt+space" (16 characters):
        - Without debouncing: 16 component reinitializations
        - With debouncing: 1 component reinitialization after typing stops

        Note: See the code implementation for exact debounce timing values.
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

        This is the final step in the auto-update pipeline that:
        1. Builds a new PushToTalkConfig object from current GUI state
        2. Compares with previous config to avoid unnecessary updates
        3. Updates the running application via app_instance.update_configuration()
        4. Calls optional configuration change callbacks
        5. Refreshes the status display

        Args:
            force: If True, skip the config comparison and force an update
                  (used during programmatic GUI updates)
        """
        new_config = self._get_config_from_gui()

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
            self._update_status_display()

        # Save configuration to JSON file for persistence
        self._save_config_to_file_async()

    def _save_config_to_file_async(self, filepath: str = "push_to_talk_config.json"):
        """
        Save configuration to JSON file asynchronously for persistence.

        This method provides non-blocking save functionality during runtime updates,
        ensuring configuration changes are persisted without affecting GUI responsiveness.

        Features:
        - Thread-safe with lock to prevent concurrent save operations
        - Non-blocking background save using daemon thread
        - Deduplication: skips save if another save is already in progress
        - Error handling with logging but no GUI interruption

        Args:
            filepath: Path to save the configuration JSON file
        """

        def _save_worker():
            """Background worker for saving configuration."""
            try:
                with self._save_lock:
                    if not self._save_pending:
                        return  # Another thread already completed the save

                    # Perform the actual save
                    config_data = asdict(self.config)
                    with open(filepath, "w") as f:
                        json.dump(config_data, f, indent=2)

                    logger.debug(f"Configuration auto-saved to {filepath}")
                    self._save_pending = False

            except Exception as error:
                logger.error(
                    f"Failed to auto-save configuration to {filepath}: {error}"
                )
                self._save_pending = False

        # Thread-safe check and mark save as pending
        with self._save_lock:
            if self._save_pending:
                # Save already in progress, skip this request
                return

            self._save_pending = True

        # Start background save
        save_thread = threading.Thread(target=_save_worker, daemon=True)
        save_thread.start()

    def _create_section_frame(self, parent: ttk.Widget, title: str) -> ttk.LabelFrame:
        """Create a labeled frame for a configuration section."""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def _create_api_section(self, parent: ttk.Widget):
        """Create speech-to-text API configuration section."""
        frame = self._create_section_frame(parent, "Speech-to-Text Settings")

        # STT Provider Selection
        ttk.Label(frame, text="STT Provider:").grid(row=0, column=0, sticky="w", pady=2)
        self.config_vars["stt_provider"] = tk.StringVar(value=self.config.stt_provider)
        provider_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["stt_provider"],
            values=["openai", "deepgram"],
            state="readonly",
            width=20,
        )
        provider_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        # OpenAI API Key Frame
        self.openai_widgets["frame"] = ttk.Frame(frame)
        self.openai_widgets["frame"].grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.openai_widgets["frame"], text="OpenAI API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["openai_api_key"] = tk.StringVar(
            value=self.config.openai_api_key
        )
        openai_api_key_entry = ttk.Entry(
            self.openai_widgets["frame"],
            textvariable=self.config_vars["openai_api_key"],
            show="*",
            width=50,
        )
        openai_api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        # OpenAI Show/Hide API Key button
        def toggle_openai_key_visibility():
            if openai_api_key_entry["show"] == "*":
                openai_api_key_entry["show"] = ""
                openai_show_hide_btn["text"] = "Hide"
            else:
                openai_api_key_entry["show"] = "*"
                openai_show_hide_btn["text"] = "Show"

        openai_show_hide_btn = ttk.Button(
            self.openai_widgets["frame"],
            text="Show",
            command=toggle_openai_key_visibility,
            width=8,
        )
        openai_show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)
        self.openai_widgets["frame"].columnconfigure(1, weight=1)

        # Deepgram API Key Frame
        self.deepgram_widgets["frame"] = ttk.Frame(frame)
        self.deepgram_widgets["frame"].grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.deepgram_widgets["frame"], text="Deepgram API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.config_vars["deepgram_api_key"] = tk.StringVar(
            value=self.config.deepgram_api_key
        )
        deepgram_api_key_entry = ttk.Entry(
            self.deepgram_widgets["frame"],
            textvariable=self.config_vars["deepgram_api_key"],
            show="*",
            width=50,
        )
        deepgram_api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        # Deepgram Show/Hide API Key button
        def toggle_deepgram_key_visibility():
            if deepgram_api_key_entry["show"] == "*":
                deepgram_api_key_entry["show"] = ""
                deepgram_show_hide_btn["text"] = "Hide"
            else:
                deepgram_api_key_entry["show"] = "*"
                deepgram_show_hide_btn["text"] = "Show"

        deepgram_show_hide_btn = ttk.Button(
            self.deepgram_widgets["frame"],
            text="Show",
            command=toggle_deepgram_key_visibility,
            width=8,
        )
        deepgram_show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)
        self.deepgram_widgets["frame"].columnconfigure(1, weight=1)

        # STT Model (shared between providers, but values change)
        ttk.Label(frame, text="STT Model:").grid(row=3, column=0, sticky="w", pady=2)
        self.config_vars["stt_model"] = tk.StringVar(value=self.config.stt_model)
        self.stt_model_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["stt_model"],
            values=["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"],
            state="readonly",
            width=20,
        )
        self.stt_model_combo.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=2)
        self.stt_model_combo.bind("<<ComboboxSelected>>", self._on_stt_model_changed)

        # Refinement Model (OpenAI only)
        ttk.Label(frame, text="Refinement Model:").grid(
            row=4, column=0, sticky="w", pady=2
        )
        self.config_vars["refinement_model"] = tk.StringVar(
            value=self.config.refinement_model
        )
        gpt_combo = ttk.Combobox(
            frame,
            textvariable=self.config_vars["refinement_model"],
            values=[
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
            ],
            state="readonly",
            width=20,
        )
        gpt_combo.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=2)

        frame.columnconfigure(1, weight=1)

        # Initialize visibility based on current provider
        self._update_api_key_visibility()

    def _on_provider_changed(self, event=None):
        """Handle STT provider changes - show/hide appropriate API key fields."""
        self._update_api_key_visibility()
        self._update_stt_model_options()

    def _on_stt_model_changed(self, event=None):
        """Handle STT model changes - save to provider-specific variable."""
        provider = self.config_vars.get("stt_provider")
        if not provider:
            return

        provider_value = provider.get()
        current_model = self.config_vars["stt_model"].get()

        # Save the model selection to the appropriate provider-specific variable
        if provider_value == "openai":
            self.openai_stt_model = current_model
        elif provider_value == "deepgram":
            self.deepgram_stt_model = current_model

    def _update_api_key_visibility(self):
        """Show/hide API key fields based on selected provider."""
        provider = self.config_vars.get("stt_provider")
        if not provider:
            return

        provider_value = provider.get()

        # Hide all provider-specific widgets first
        if self.openai_widgets.get("frame"):
            self.openai_widgets["frame"].grid_remove()
        if self.deepgram_widgets.get("frame"):
            self.deepgram_widgets["frame"].grid_remove()

        # Show the appropriate provider's widgets
        if provider_value == "openai" and self.openai_widgets.get("frame"):
            self.openai_widgets["frame"].grid()
        elif provider_value == "deepgram" and self.deepgram_widgets.get("frame"):
            self.deepgram_widgets["frame"].grid()

    def _update_stt_model_options(self):
        """Update STT model options based on selected provider."""
        if not self.stt_model_combo:
            return

        provider = self.config_vars.get("stt_provider")
        if not provider:
            return

        provider_value = provider.get()
        current_model = self.config_vars["stt_model"].get()

        # Define model lists
        openai_models = ["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"]
        deepgram_models = ["nova-3", "nova-2", "base", "enhanced", "whisper-medium"]

        # Save the current model to the appropriate provider-specific variable
        # This preserves the selection before we change providers
        if current_model in openai_models:
            self.openai_stt_model = current_model
        elif current_model in deepgram_models:
            self.deepgram_stt_model = current_model

        # Update model options and restore provider-specific selection
        if provider_value == "openai":
            models = openai_models
            # Restore the previously selected OpenAI model
            if self.openai_stt_model in models:
                self.config_vars["stt_model"].set(self.openai_stt_model)
            else:
                self.config_vars["stt_model"].set(models[0])
        elif provider_value == "deepgram":
            models = deepgram_models
            # Restore the previously selected Deepgram model
            if self.deepgram_stt_model in models:
                self.config_vars["stt_model"].set(self.deepgram_stt_model)
            else:
                self.config_vars["stt_model"].set(models[0])
        else:
            models = []

        self.stt_model_combo["values"] = models

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

        # Insertion Delay
        ttk.Label(frame, text="Insertion Delay (seconds):").grid(
            row=0, column=0, sticky="w", pady=2
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
        delay_spinbox.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        help_text = "Delay before pasting text via clipboard (helps ensure target window is ready)"
        ttk.Label(
            frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

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

        # Debug Mode
        self.config_vars["debug_mode"] = tk.BooleanVar(value=self.config.debug_mode)
        ttk.Checkbutton(
            frame,
            text="Debug Mode (saves recorded audio files to debug directories)",
            variable=self.config_vars["debug_mode"],
        ).grid(row=3, column=0, sticky="w", pady=2)

    def _create_glossary_section(self, parent: ttk.Widget):
        """Create custom glossary configuration section."""
        frame = self._create_section_frame(parent, "Custom Glossary")

        # Description
        description = ttk.Label(
            frame,
            text="Add domain-specific terms, acronyms, and technical words to help the AI\nbetter recognize and transcribe your vocabulary.",
            font=("TkDefaultFont", 9),
        )
        description.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Search bar
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.glossary_search_var = tk.StringVar()
        self.glossary_search_var.trace("w", self._filter_glossary_list)
        search_entry = ttk.Entry(
            search_frame, textvariable=self.glossary_search_var, width=30
        )
        search_entry.pack(side="left", fill="x", expand=True)

        # Glossary list with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)

        # Create scrollable listbox
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill="both", expand=True)

        self.glossary_listbox = tk.Listbox(
            listbox_frame, height=6, selectmode=tk.SINGLE, font=("TkDefaultFont", 9)
        )

        scrollbar_glossary = ttk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar_glossary.config(command=self.glossary_listbox.yview)
        self.glossary_listbox.config(yscrollcommand=scrollbar_glossary.set)

        self.glossary_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_glossary.pack(side="right", fill="y")

        # Buttons frame
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(5, 0))

        ttk.Button(buttons_frame, text="Add", command=self._add_glossary_term).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(buttons_frame, text="Edit", command=self._edit_glossary_term).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(
            buttons_frame, text="Delete", command=self._delete_glossary_term
        ).pack(side="left")

        # Configure grid weights for proper resizing
        frame.grid_columnconfigure(0, weight=1)

        # Initialize the glossary list
        self.glossary_terms = list(self.config.custom_glossary)
        self._refresh_glossary_list()

    def _filter_glossary_list(self, *args):
        """Filter the glossary list based on search term."""
        search_term = self.glossary_search_var.get().lower()
        self.glossary_listbox.delete(0, tk.END)

        for term in self.glossary_terms:
            if search_term in term.lower():
                self.glossary_listbox.insert(tk.END, term)

    def _refresh_glossary_list(self):
        """Refresh the glossary list display."""
        if not hasattr(self, "glossary_listbox") or self.glossary_listbox is None:
            return

        self.glossary_listbox.delete(0, tk.END)
        for term in sorted(self.glossary_terms, key=str.lower):
            self.glossary_listbox.insert(tk.END, term)

    def _add_glossary_term(self):
        """Add a new glossary term."""
        dialog = GlossaryTermDialog(self.root, "Add Glossary Term")
        term = dialog.show()

        if term and term.strip():
            term = term.strip()
            if term not in self.glossary_terms:
                self.glossary_terms.append(term)
                self._refresh_glossary_list()
                self._notify_config_changed()
            else:
                messagebox.showinfo(
                    "Duplicate Term", f"The term '{term}' is already in the glossary."
                )

    def _edit_glossary_term(self):
        """Edit the selected glossary term."""
        selection = self.glossary_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a term to edit.")
            return

        index = selection[0]
        current_term = self.glossary_listbox.get(index)

        dialog = GlossaryTermDialog(self.root, "Edit Glossary Term", current_term)
        new_term = dialog.show()

        if new_term and new_term.strip():
            new_term = new_term.strip()
            if new_term != current_term:
                if new_term not in self.glossary_terms:
                    # Find the actual index in the sorted list
                    actual_index = self.glossary_terms.index(current_term)
                    self.glossary_terms[actual_index] = new_term
                    self._refresh_glossary_list()
                    self._notify_config_changed()
                else:
                    messagebox.showinfo(
                        "Duplicate Term",
                        f"The term '{new_term}' is already in the glossary.",
                    )

    def _delete_glossary_term(self):
        """Delete the selected glossary term."""
        selection = self.glossary_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a term to delete.")
            return

        index = selection[0]
        term = self.glossary_listbox.get(index)

        if messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete '{term}'?"
        ):
            self.glossary_terms.remove(term)
            self._refresh_glossary_list()
            self._notify_config_changed()

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
        # Check API key based on selected provider
        provider = self.config_vars["stt_provider"].get()

        if provider == "openai":
            if not self.config_vars["openai_api_key"].get().strip():
                messagebox.showerror(
                    "Validation Error",
                    "OpenAI API key is required when using OpenAI provider!\n\n"
                    "Please enter your OpenAI API key or switch to Deepgram provider.",
                )
                return False
        elif provider == "deepgram":
            if not self.config_vars["deepgram_api_key"].get().strip():
                messagebox.showerror(
                    "Validation Error",
                    "Deepgram API key is required when using Deepgram provider!\n\n"
                    "Please enter your Deepgram API key or switch to OpenAI provider.",
                )
                return False
        else:
            messagebox.showerror("Validation Error", f"Unknown provider: {provider}")
            return False

        # Check hotkeys are different
        if self.config_vars["hotkey"].get() == self.config_vars["toggle_hotkey"].get():
            messagebox.showerror(
                "Validation Error", "Push-to-talk and toggle hotkeys must be different!"
            )
            return False

        return True

    def _validate_deepgram_api_key(self, api_key: str) -> bool:
        """
        Validate Deepgram API key by making a direct request to the auth endpoint.

        Args:
            api_key: Deepgram API key to validate

        Returns:
            True if valid, False otherwise

        Raises:
            Exception: With error message containing HTTP error codes (401, 404) or timeout
        """
        import urllib.request
        import urllib.error

        url = "https://api.deepgram.com/v1/auth/token"
        headers = {"Authorization": f"Token {api_key}"}

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=10):
                # If we get here, the API key is valid
                return True
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise Exception("401 - Incorrect API key")
            elif e.code == 404:
                raise Exception("404 - API endpoint not found")
            else:
                raise Exception(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"timeout - Network error: {e.reason}")

    def _test_configuration(self):
        """Test all provider API keys and show comprehensive status."""
        # Create test config (don't validate yet - we want to test all providers)
        test_config = self._get_config_from_gui()

        # Build status report
        status_lines = ["API Key Validation Status:\n"]

        # Test OpenAI
        openai_status = "Not configured"
        openai_prefix = "[ ]"
        if test_config.openai_api_key.strip():
            try:
                from openai import OpenAI

                client = OpenAI(api_key=test_config.openai_api_key)
                # Actually test the API key by listing models (lightweight operation)
                _ = client.models.list()
                openai_status = "VALID"
                openai_prefix = "[OK]"
            except Exception as e:
                error_msg = str(e)
                # Extract the most relevant error message
                if "401" in error_msg or "Incorrect API key" in error_msg:
                    openai_status = "INVALID - Incorrect API key"
                elif "404" in error_msg:
                    openai_status = "INVALID - API endpoint not found"
                elif "timeout" in error_msg.lower():
                    openai_status = "TIMEOUT - Network issue"
                else:
                    openai_status = f"ERROR\n  {error_msg[:60]}..."
                openai_prefix = "[X]"

        selected_marker = " (Selected)" if test_config.stt_provider == "openai" else ""
        status_lines.append(f"\n{openai_prefix} OpenAI{selected_marker}:")
        status_lines.append(f"  Status: {openai_status}")
        if test_config.openai_api_key.strip():
            status_lines.append(
                f"  Key: {'*' * min(len(test_config.openai_api_key), 20)}"
            )

        # Test Deepgram
        deepgram_status = "Not configured"
        deepgram_prefix = "[ ]"
        if test_config.deepgram_api_key.strip():
            try:
                # Validate API key using direct HTTP request to auth endpoint
                self._validate_deepgram_api_key(test_config.deepgram_api_key)
                deepgram_status = "VALID"
                deepgram_prefix = "[OK]"
            except Exception as e:
                error_msg = str(e)
                # Extract the most relevant error message
                if "401" in error_msg or "Incorrect API key" in error_msg:
                    deepgram_status = "INVALID - Incorrect API key"
                elif "404" in error_msg:
                    deepgram_status = "INVALID - API endpoint not found"
                elif "timeout" in error_msg.lower():
                    deepgram_status = "TIMEOUT - Network issue"
                else:
                    deepgram_status = f"ERROR\n  {error_msg[:60]}..."
                deepgram_prefix = "[X]"

        selected_marker = (
            " (Selected)" if test_config.stt_provider == "deepgram" else ""
        )
        status_lines.append(f"\n{deepgram_prefix} Deepgram{selected_marker}:")
        status_lines.append(f"  Status: {deepgram_status}")
        if test_config.deepgram_api_key.strip():
            status_lines.append(
                f"  Key: {'*' * min(len(test_config.deepgram_api_key), 20)}"
            )

        # Add configuration summary
        status_lines.append("\n" + "-" * 40)
        status_lines.append("\nCurrent Settings:")
        status_lines.append(f"  Provider: {test_config.stt_provider}")
        status_lines.append(f"  Model: {test_config.stt_model}")

        # Add warning if selected provider is not valid
        if test_config.stt_provider == "openai" and openai_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected provider (OpenAI) has an invalid API key!"
            )
        elif test_config.stt_provider == "deepgram" and deepgram_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected provider (Deepgram) has an invalid API key!"
            )

        # Show results as info dialog
        messagebox.showinfo("Configuration Test Results", "\n".join(status_lines))

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
        self._suspend_change_events = True
        try:
            self.config_vars["stt_provider"].set(config.stt_provider)
            self.config_vars["openai_api_key"].set(config.openai_api_key)
            self.config_vars["deepgram_api_key"].set(config.deepgram_api_key)
            self.config_vars["stt_model"].set(config.stt_model)
            self.config_vars["refinement_model"].set(config.refinement_model)
            self.config_vars["sample_rate"].set(config.sample_rate)
            self.config_vars["chunk_size"].set(config.chunk_size)
            self.config_vars["channels"].set(config.channels)
            self.config_vars["hotkey"].set(config.hotkey)
            self.config_vars["toggle_hotkey"].set(config.toggle_hotkey)
            self.config_vars["insertion_delay"].set(config.insertion_delay)
            self.config_vars["enable_text_refinement"].set(
                config.enable_text_refinement
            )
            self.config_vars["enable_logging"].set(config.enable_logging)
            self.config_vars["enable_audio_feedback"].set(config.enable_audio_feedback)
            self.config_vars["debug_mode"].set(config.debug_mode)
        finally:
            self._suspend_change_events = False

        self.glossary_terms = list(config.custom_glossary)
        self._refresh_glossary_list()

        self._notify_config_changed(force=True)

    def _get_config_from_gui(self) -> PushToTalkConfig:
        """Create a configuration object from current GUI values."""
        return PushToTalkConfig(
            stt_provider=self.config_vars["stt_provider"].get(),
            openai_api_key=self.config_vars["openai_api_key"].get().strip(),
            deepgram_api_key=self.config_vars["deepgram_api_key"].get().strip(),
            stt_model=self.config_vars["stt_model"].get(),
            refinement_model=self.config_vars["refinement_model"].get(),
            sample_rate=self.config_vars["sample_rate"].get(),
            chunk_size=self.config_vars["chunk_size"].get(),
            channels=self.config_vars["channels"].get(),
            hotkey=self.config_vars["hotkey"].get().strip(),
            toggle_hotkey=self.config_vars["toggle_hotkey"].get().strip(),
            insertion_delay=self.config_vars["insertion_delay"].get(),
            enable_text_refinement=self.config_vars["enable_text_refinement"].get(),
            enable_logging=self.config_vars["enable_logging"].get(),
            enable_audio_feedback=self.config_vars["enable_audio_feedback"].get(),
            debug_mode=self.config_vars["debug_mode"].get(),
            custom_glossary=list(self.glossary_terms),
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


class GlossaryTermDialog:
    """Simple dialog for adding/editing glossary terms."""

    def __init__(self, parent, title, initial_value=""):
        self.parent = parent
        self.title = title
        self.initial_value = initial_value
        self.result = None
        self.dialog = None

    def show(self):
        """Show the dialog and return the entered term."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("350x150")
        self.dialog.resizable(False, False)

        # Make it modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = (
            self.parent.winfo_x()
            + (self.parent.winfo_width() // 2)
            - (self.dialog.winfo_width() // 2)
        )
        y = (
            self.parent.winfo_y()
            + (self.parent.winfo_height() // 2)
            - (self.dialog.winfo_height() // 2)
        )
        self.dialog.geometry(f"+{x}+{y}")

        # Create widgets
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Label and entry
        ttk.Label(main_frame, text="Enter glossary term:").pack(anchor="w", pady=(0, 5))

        self.entry_var = tk.StringVar(value=self.initial_value)
        entry = ttk.Entry(main_frame, textvariable=self.entry_var, width=40)
        entry.pack(fill="x", pady=(0, 15))
        entry.focus()
        entry.select_range(0, tk.END)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="OK", command=self._ok_clicked).pack(
            side="right", padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=self._cancel_clicked).pack(
            side="right"
        )

        # Bind Enter and Escape
        self.dialog.bind("<Return>", lambda e: self._ok_clicked())
        self.dialog.bind("<Escape>", lambda e: self._cancel_clicked())

        # Wait for dialog to close
        self.dialog.wait_window()

        return self.result

    def _ok_clicked(self):
        """Handle OK button click."""
        self.result = self.entry_var.get()
        self.dialog.destroy()

    def _cancel_clicked(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()


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
