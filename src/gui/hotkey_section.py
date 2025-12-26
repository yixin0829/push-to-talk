"""Hotkey configuration section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from src.gui.hotkey_recorder import HotkeyRecorder


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

        # Recording state
        self._recorder: Optional[HotkeyRecorder] = None
        self._recording_target: Optional[str] = None  # "hotkey" or "toggle_hotkey"
        self._previous_value: str = ""

        # Widget references
        self._hotkey_entry: Optional[ttk.Entry] = None
        self._toggle_entry: Optional[ttk.Entry] = None
        self._hotkey_record_btn: Optional[ttk.Button] = None
        self._toggle_record_btn: Optional[ttk.Button] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the hotkey section widgets."""
        # Push-to-talk hotkey
        ttk.Label(self.frame, text="Push-to-Talk Hotkey:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self._hotkey_entry = ttk.Entry(
            self.frame, textvariable=self.hotkey_var, width=25
        )
        self._hotkey_entry.grid(row=0, column=1, sticky="w", padx=(10, 5), pady=2)

        self._hotkey_record_btn = ttk.Button(
            self.frame,
            text="Record",
            width=10,
            command=lambda: self._start_recording("hotkey"),
        )
        self._hotkey_record_btn.grid(row=0, column=2, sticky="w", pady=2)

        # Toggle hotkey
        ttk.Label(self.frame, text="Toggle Recording Hotkey:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self._toggle_entry = ttk.Entry(
            self.frame, textvariable=self.toggle_hotkey_var, width=25
        )
        self._toggle_entry.grid(row=1, column=1, sticky="w", padx=(10, 5), pady=2)

        self._toggle_record_btn = ttk.Button(
            self.frame,
            text="Record",
            width=10,
            command=lambda: self._start_recording("toggle_hotkey"),
        )
        self._toggle_record_btn.grid(row=1, column=2, sticky="w", pady=2)

        # Add helpful text
        help_text = "Tip: Press keys one at a time. Escape to cancel."
        ttk.Label(
            self.frame, text=help_text, font=("TkDefaultFont", 8), foreground="gray"
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))

    def _start_recording(self, target: str) -> None:
        """Start recording for the specified hotkey field.

        Args:
            target: Either "hotkey" or "toggle_hotkey"
        """
        if self._recorder and self._recorder.is_recording:
            return

        self._recording_target = target

        # Get the appropriate widgets
        if target == "hotkey":
            entry = self._hotkey_entry
            var = self.hotkey_var
            record_btn = self._hotkey_record_btn
            other_btn = self._toggle_record_btn
        else:
            entry = self._toggle_entry
            var = self.toggle_hotkey_var
            record_btn = self._toggle_record_btn
            other_btn = self._hotkey_record_btn

        # Save current value for cancel
        self._previous_value = var.get()

        # Update UI state
        if record_btn:
            record_btn.configure(text="Recording...")
        if other_btn:
            other_btn.configure(state="disabled")
        if entry:
            entry.configure(state="readonly")

        # Clear and show placeholder
        var.set("Press keys...")

        # Create and start recorder
        self._recorder = HotkeyRecorder(
            on_recording_complete=self._on_recording_complete,
            on_recording_cancelled=self._on_recording_cancelled,
            on_keys_changed=self._on_keys_changed,
        )
        self._recorder.start_recording(timeout_seconds=10.0)

    def _on_recording_complete(self, hotkey_string: str) -> None:
        """Handle successful recording.

        Args:
            hotkey_string: The recorded hotkey combination
        """
        target = self._recording_target

        # Update the appropriate variable
        if target == "hotkey":
            self.hotkey_var.set(hotkey_string)
        else:
            self.toggle_hotkey_var.set(hotkey_string)

        self._reset_recording_state()

    def _on_recording_cancelled(self) -> None:
        """Handle cancelled recording."""
        target = self._recording_target

        # Restore previous value
        if target == "hotkey":
            self.hotkey_var.set(self._previous_value)
        else:
            self.toggle_hotkey_var.set(self._previous_value)

        self._reset_recording_state()

    def _on_keys_changed(self, current_keys: str) -> None:
        """Update entry field with current combination.

        Args:
            current_keys: Current key combination string
        """
        target = self._recording_target

        if target == "hotkey":
            self.hotkey_var.set(current_keys if current_keys else "Press keys...")
        else:
            self.toggle_hotkey_var.set(
                current_keys if current_keys else "Press keys..."
            )

    def _reset_recording_state(self) -> None:
        """Reset UI to non-recording state."""
        # Reset buttons
        if self._hotkey_record_btn:
            self._hotkey_record_btn.configure(text="Record", state="normal")
        if self._toggle_record_btn:
            self._toggle_record_btn.configure(text="Record", state="normal")

        # Reset entries to editable
        if self._hotkey_entry:
            self._hotkey_entry.configure(state="normal")
        if self._toggle_entry:
            self._toggle_entry.configure(state="normal")

        # Clear recording state
        self._recorder = None
        self._recording_target = None
        self._previous_value = ""

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
