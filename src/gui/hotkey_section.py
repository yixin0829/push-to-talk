"""Hotkey configuration section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk


class HotkeySection:
    """Manages the hotkey configuration section."""

    def __init__(self, parent: ttk.Widget):
        """
        Initialize the hotkey section.

        Args:
            parent: Parent widget to attach this section to
        """
        self.frame = ttk.LabelFrame(parent, text="Hotkey Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variables
        self.hotkey_var = tk.StringVar()
        self.toggle_hotkey_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        """Create the hotkey section widgets."""
        # Push-to-talk hotkey
        ttk.Label(self.frame, text="Push-to-Talk Hotkey:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        hotkey_entry = ttk.Entry(self.frame, textvariable=self.hotkey_var, width=25)
        hotkey_entry.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        # Toggle hotkey
        ttk.Label(self.frame, text="Toggle Recording Hotkey:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        toggle_hotkey_entry = ttk.Entry(
            self.frame, textvariable=self.toggle_hotkey_var, width=25
        )
        toggle_hotkey_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Add helpful text
        help_text = "Examples: ctrl+shift+space, alt+space, f12, ctrl+alt+r"
        ttk.Label(
            self.frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def get_values(self) -> dict[str, str]:
        """
        Get the current hotkey configuration values.

        Returns:
            Dictionary with keys: hotkey, toggle_hotkey
        """
        return {
            "hotkey": self.hotkey_var.get().strip(),
            "toggle_hotkey": self.toggle_hotkey_var.get().strip(),
        }

    def set_values(self, hotkey: str, toggle_hotkey: str):
        """
        Set the hotkey configuration values.

        Args:
            hotkey: Push-to-talk hotkey
            toggle_hotkey: Toggle recording hotkey
        """
        self.hotkey_var.set(hotkey)
        self.toggle_hotkey_var.set(toggle_hotkey)
