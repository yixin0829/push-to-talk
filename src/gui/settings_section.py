"""Miscellaneous settings sections for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk


class TextInsertionSection:
    """Manages the text insertion configuration section."""

    def __init__(self, parent: ttk.Widget):
        """
        Initialize the text insertion section.

        Args:
            parent: Parent widget to attach this section to
        """
        self.frame = ttk.LabelFrame(parent, text="Text Insertion Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variable
        self.insertion_delay_var = tk.DoubleVar()

        self._create_widgets()

    def _create_widgets(self):
        """Create the text insertion section widgets."""
        # Insertion Delay
        ttk.Label(self.frame, text="Insertion Delay (seconds):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        delay_spinbox = tk.Spinbox(
            self.frame,
            textvariable=self.insertion_delay_var,
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
            self.frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def get_value(self) -> float:
        """
        Get the current insertion delay value.

        Returns:
            Insertion delay in seconds
        """
        return self.insertion_delay_var.get()

    def set_value(self, insertion_delay: float):
        """
        Set the insertion delay value.

        Args:
            insertion_delay: Insertion delay in seconds
        """
        self.insertion_delay_var.set(insertion_delay)


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
            text="Enable Text Refinement (uses GPT for better text quality)",
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
