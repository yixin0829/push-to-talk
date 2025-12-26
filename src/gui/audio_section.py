"""Audio configuration section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk


class AudioSection:
    """Manages the audio configuration section."""

    def __init__(self, parent: ttk.Widget):
        """
        Initialize the audio section.

        Args:
            parent: Parent widget to attach this section to
        """
        self.frame = ttk.LabelFrame(parent, text="Audio Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variables
        self.sample_rate_var = tk.IntVar()
        self.chunk_size_var = tk.IntVar()
        self.channels_var = tk.IntVar()

        self._create_widgets()

    def _create_widgets(self):
        """Create the audio section widgets."""
        # Sample Rate
        ttk.Label(self.frame, text="Sample Rate (Hz):").grid(
            row=0, column=0, sticky="w", pady=2
        )
        sample_rate_combo = ttk.Combobox(
            self.frame,
            textvariable=self.sample_rate_var,
            values=[8000, 16000, 22050, 44100],
            state="readonly",
            width=15,
        )
        sample_rate_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Chunk Size
        ttk.Label(self.frame, text="Chunk Size:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        chunk_size_combo = ttk.Combobox(
            self.frame,
            textvariable=self.chunk_size_var,
            values=[512, 1024, 2048, 4096],
            state="readonly",
            width=15,
        )
        chunk_size_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Channels
        ttk.Label(self.frame, text="Channels:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        channels_combo = ttk.Combobox(
            self.frame,
            textvariable=self.channels_var,
            values=[1, 2],
            state="readonly",
            width=15,
        )
        channels_combo.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        ttk.Label(
            self.frame,
            text="Recommended: 16000 Hz, 1024 chunk, 1 channel",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def get_values(self) -> dict[str, int]:
        """
        Get the current audio configuration values.

        Returns:
            Dictionary with keys: sample_rate, chunk_size, channels
        """
        return {
            "sample_rate": self.sample_rate_var.get(),
            "chunk_size": self.chunk_size_var.get(),
            "channels": self.channels_var.get(),
        }

    def set_values(self, sample_rate: int, chunk_size: int, channels: int):
        """
        Set the audio configuration values.

        Args:
            sample_rate: Sample rate in Hz
            chunk_size: Chunk size
            channels: Number of channels
        """
        self.sample_rate_var.set(sample_rate)
        self.chunk_size_var.set(chunk_size)
        self.channels_var.set(channels)
