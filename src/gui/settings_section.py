"""Miscellaneous settings sections for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk


class FeatureFlagsSection:
    """Manages the feature flags configuration section."""

    def __init__(self, parent: ttk.Widget):
        """
        Initialize the feature flags section.

        Args:
            parent: Parent widget to attach this section to
        """
        self.frame = ttk.LabelFrame(parent, text="Feature Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variables
        self.enable_text_refinement_var = tk.BooleanVar()
        self.enable_logging_var = tk.BooleanVar()
        self.enable_audio_feedback_var = tk.BooleanVar()
        self.debug_mode_var = tk.BooleanVar()

        self._create_widgets()

    def _create_widgets(self):
        """Create the feature flags section widgets."""
        # Text Refinement
        ttk.Checkbutton(
            self.frame,
            text="Enable Text Refinement (additional processing for better text quality)",
            variable=self.enable_text_refinement_var,
        ).grid(row=0, column=0, sticky="w", pady=2)

        # Logging
        ttk.Checkbutton(
            self.frame,
            text="Enable Logging (creates push_to_talk.log file)",
            variable=self.enable_logging_var,
        ).grid(row=1, column=0, sticky="w", pady=2)

        # Audio Feedback
        ttk.Checkbutton(
            self.frame,
            text="Enable Audio Feedback (plays sounds when recording starts/stops)",
            variable=self.enable_audio_feedback_var,
        ).grid(row=2, column=0, sticky="w", pady=2)

        # Debug Mode
        ttk.Checkbutton(
            self.frame,
            text="Debug Mode (saves recorded audio files to debug directories)",
            variable=self.debug_mode_var,
        ).grid(row=3, column=0, sticky="w", pady=2)

    def get_values(self) -> dict[str, bool]:
        """
        Get the current feature flag values.

        Returns:
            Dictionary with feature flag values
        """
        return {
            "enable_text_refinement": self.enable_text_refinement_var.get(),
            "enable_logging": self.enable_logging_var.get(),
            "enable_audio_feedback": self.enable_audio_feedback_var.get(),
            "debug_mode": self.debug_mode_var.get(),
        }

    def set_values(
        self,
        enable_text_refinement: bool,
        enable_logging: bool,
        enable_audio_feedback: bool,
        debug_mode: bool,
    ):
        """
        Set the feature flag values.

        Args:
            enable_text_refinement: Enable text refinement flag
            enable_logging: Enable logging flag
            enable_audio_feedback: Enable audio feedback flag
            debug_mode: Debug mode flag
        """
        self.enable_text_refinement_var.set(enable_text_refinement)
        self.enable_logging_var.set(enable_logging)
        self.enable_audio_feedback_var.set(enable_audio_feedback)
        self.debug_mode_var.set(debug_mode)
