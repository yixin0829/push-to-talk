"""API configuration section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from src.gui.validators import (
    validate_openai_api_key,
    validate_deepgram_api_key,
)


class APISection:
    """Manages the speech-to-text API configuration section."""

    def __init__(self, parent: ttk.Widget, on_change: Callable[[], None] | None = None):
        """
        Initialize the API section.

        Args:
            parent: Parent widget to attach this section to
            on_change: Optional callback when configuration changes
        """
        self.on_change = on_change
        self.frame = ttk.LabelFrame(parent, text="Speech-to-Text Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variables
        self.stt_provider_var = tk.StringVar()
        self.openai_api_key_var = tk.StringVar()
        self.deepgram_api_key_var = tk.StringVar()
        self.stt_model_var = tk.StringVar()
        self.refinement_model_var = tk.StringVar()

        # Provider-specific widgets
        self.openai_widgets = {}
        self.deepgram_widgets = {}
        self.stt_model_combo = None

        # Provider-specific model selections (to preserve when switching)
        self.openai_stt_model = "gpt-4o-mini-transcribe"
        self.deepgram_stt_model = "nova-3"

        self._create_widgets()

    def _create_widgets(self):
        """Create the API section widgets."""
        # STT Provider Selection
        ttk.Label(self.frame, text="STT Provider:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        provider_combo = ttk.Combobox(
            self.frame,
            textvariable=self.stt_provider_var,
            values=["openai", "deepgram"],
            state="readonly",
            width=20,
        )
        provider_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        # OpenAI API Key Frame
        self.openai_widgets["frame"] = ttk.Frame(self.frame)
        self.openai_widgets["frame"].grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.openai_widgets["frame"], text="OpenAI API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        openai_api_key_entry = ttk.Entry(
            self.openai_widgets["frame"],
            textvariable=self.openai_api_key_var,
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
        self.deepgram_widgets["frame"] = ttk.Frame(self.frame)
        self.deepgram_widgets["frame"].grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.deepgram_widgets["frame"], text="Deepgram API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        deepgram_api_key_entry = ttk.Entry(
            self.deepgram_widgets["frame"],
            textvariable=self.deepgram_api_key_var,
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
        ttk.Label(self.frame, text="STT Model:").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.stt_model_combo = ttk.Combobox(
            self.frame,
            textvariable=self.stt_model_var,
            values=["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"],
            state="readonly",
            width=20,
        )
        self.stt_model_combo.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=2)
        self.stt_model_combo.bind("<<ComboboxSelected>>", self._on_stt_model_changed)

        # Refinement Model (OpenAI only)
        ttk.Label(self.frame, text="Refinement Model:").grid(
            row=4, column=0, sticky="w", pady=2
        )
        gpt_combo = ttk.Combobox(
            self.frame,
            textvariable=self.refinement_model_var,
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

        self.frame.columnconfigure(1, weight=1)

    def _on_provider_changed(self, event=None):
        """Handle STT provider changes - show/hide appropriate API key fields."""
        self._update_api_key_visibility()
        self._update_stt_model_options()
        if self.on_change:
            self.on_change()

    def _on_stt_model_changed(self, event=None):
        """Handle STT model changes - save to provider-specific variable."""
        provider_value = self.stt_provider_var.get()
        current_model = self.stt_model_var.get()

        # Save the model selection to the appropriate provider-specific variable
        if provider_value == "openai":
            self.openai_stt_model = current_model
        elif provider_value == "deepgram":
            self.deepgram_stt_model = current_model

    def _update_api_key_visibility(self):
        """Show/hide API key fields based on selected provider."""
        provider_value = self.stt_provider_var.get()

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

        provider_value = self.stt_provider_var.get()
        current_model = self.stt_model_var.get()

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
                self.stt_model_var.set(self.openai_stt_model)
            else:
                self.stt_model_var.set(models[0])
        elif provider_value == "deepgram":
            models = deepgram_models
            # Restore the previously selected Deepgram model
            if self.deepgram_stt_model in models:
                self.stt_model_var.set(self.deepgram_stt_model)
            else:
                self.stt_model_var.set(models[0])
        else:
            models = []

        self.stt_model_combo["values"] = models

    def get_values(self) -> dict[str, str]:
        """
        Get the current API configuration values.

        Returns:
            Dictionary with API configuration values
        """
        return {
            "stt_provider": self.stt_provider_var.get(),
            "openai_api_key": self.openai_api_key_var.get().strip(),
            "deepgram_api_key": self.deepgram_api_key_var.get().strip(),
            "stt_model": self.stt_model_var.get(),
            "refinement_model": self.refinement_model_var.get(),
        }

    def set_values(
        self,
        stt_provider: str,
        openai_api_key: str,
        deepgram_api_key: str,
        stt_model: str,
        refinement_model: str,
    ):
        """
        Set the API configuration values.

        Args:
            stt_provider: STT provider name
            openai_api_key: OpenAI API key
            deepgram_api_key: Deepgram API key
            stt_model: STT model name
            refinement_model: Refinement model name
        """
        self.stt_provider_var.set(stt_provider)
        self.openai_api_key_var.set(openai_api_key)
        self.deepgram_api_key_var.set(deepgram_api_key)
        self.stt_model_var.set(stt_model)
        self.refinement_model_var.set(refinement_model)

        # Store provider-specific models
        if stt_provider == "openai":
            self.openai_stt_model = stt_model
        elif stt_provider == "deepgram":
            self.deepgram_stt_model = stt_model

        # Update visibility based on provider
        self._update_api_key_visibility()

    def test_api_keys(self) -> str:
        """
        Test all provider API keys and return a comprehensive status report.

        Returns:
            Multi-line string with test results
        """
        values = self.get_values()
        status_lines = ["API Key Validation Status:\n"]

        # Test OpenAI
        openai_status = "Not configured"
        openai_prefix = "[ ]"
        if values["openai_api_key"]:
            try:
                validate_openai_api_key(values["openai_api_key"])
                openai_status = "VALID"
                openai_prefix = "[OK]"
            except Exception as e:
                openai_status = str(e)
                openai_prefix = "[X]"

        selected_marker = " (Selected)" if values["stt_provider"] == "openai" else ""
        status_lines.append(f"\n{openai_prefix} OpenAI{selected_marker}:")
        status_lines.append(f"  Status: {openai_status}")
        if values["openai_api_key"]:
            status_lines.append(
                f"  Key: {'*' * min(len(values['openai_api_key']), 20)}"
            )

        # Test Deepgram
        deepgram_status = "Not configured"
        deepgram_prefix = "[ ]"
        if values["deepgram_api_key"]:
            try:
                validate_deepgram_api_key(values["deepgram_api_key"])
                deepgram_status = "VALID"
                deepgram_prefix = "[OK]"
            except Exception as e:
                deepgram_status = str(e)
                deepgram_prefix = "[X]"

        selected_marker = " (Selected)" if values["stt_provider"] == "deepgram" else ""
        status_lines.append(f"\n{deepgram_prefix} Deepgram{selected_marker}:")
        status_lines.append(f"  Status: {deepgram_status}")
        if values["deepgram_api_key"]:
            status_lines.append(
                f"  Key: {'*' * min(len(values['deepgram_api_key']), 20)}"
            )

        # Add configuration summary
        status_lines.append("\n" + "-" * 40)
        status_lines.append("\nCurrent Settings:")
        status_lines.append(f"  Provider: {values['stt_provider']}")
        status_lines.append(f"  Model: {values['stt_model']}")

        # Add warning if selected provider is not valid
        if values["stt_provider"] == "openai" and openai_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected provider (OpenAI) has an invalid API key!"
            )
        elif values["stt_provider"] == "deepgram" and deepgram_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected provider (Deepgram) has an invalid API key!"
            )

        return "\n".join(status_lines)
