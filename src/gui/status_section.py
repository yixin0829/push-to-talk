"""Status display section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk
from src.push_to_talk import PushToTalkConfig


class StatusSection:
    """Manages the application status display section."""

    def __init__(self, parent: ttk.Widget):
        """
        Initialize the status section.

        Args:
            parent: Parent widget to attach this section to
        """
        self.frame = ttk.LabelFrame(parent, text="Application Status", padding=15)
        self.frame.pack(fill="x", pady=(0, 15))

        # Status widgets
        self.status_indicator = None
        self.status_label = None
        self.settings_frame = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the status section widgets."""
        # Status indicator frame
        status_frame = ttk.Frame(self.frame)
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

        # Active settings display (shown when running)
        self.settings_frame = ttk.Frame(self.frame)

        # Update initial status
        self.update_display(is_running=False, config=None)

    def update_display(self, is_running: bool, config: PushToTalkConfig | None):
        """
        Update the status indicator and text.

        Args:
            is_running: Whether the application is currently running
            config: Current configuration (used to show active settings)
        """
        if not self.status_indicator or not self.status_label:
            return

        self.status_indicator.delete("all")

        if is_running:
            # Green circle for running
            self.status_indicator.create_oval(
                2, 2, 18, 18, fill="green", outline="darkgreen"
            )
            self.status_label.config(
                text="Running - Use your configured hotkeys", foreground="green"
            )

            # Show active settings
            self._show_active_settings(config)
        else:
            # Gray circle for stopped
            self.status_indicator.create_oval(
                2, 2, 18, 18, fill="gray", outline="darkgray"
            )
            self.status_label.config(text="Ready to start", foreground="black")

            # Hide active settings
            self._hide_active_settings()

    def _show_active_settings(self, config: PushToTalkConfig | None):
        """
        Show the current active settings when running.

        Args:
            config: Current configuration
        """
        if not self.settings_frame or not config:
            return

        # Clear existing content
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        self.settings_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(
            self.settings_frame,
            text="Active Settings:",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(anchor="w")

        settings_text = f"""• Push-to-Talk: {config.hotkey}
• Toggle Recording: {config.toggle_hotkey}
• Text Refinement: {"Enabled" if config.enable_text_refinement else "Disabled"}
• Audio Feedback: {"Enabled" if config.enable_audio_feedback else "Disabled"}"""

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
