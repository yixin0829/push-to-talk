"""API configuration section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from src.gui.validators import (
    validate_openai_api_key,
    validate_deepgram_api_key,
    validate_cerebras_api_key,
    validate_gemini_api_key,
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

        # API Keys section (separate from STT settings)
        self.api_keys_frame = ttk.LabelFrame(parent, text="API Keys", padding=10)
        self.api_keys_frame.pack(fill="x", pady=(0, 10))

        # Speech-to-Text Settings section
        self.frame = ttk.LabelFrame(parent, text="Speech-to-Text Settings", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Configuration variables
        self.stt_provider_var = tk.StringVar()
        self.openai_api_key_var = tk.StringVar()
        self.deepgram_api_key_var = tk.StringVar()
        self.cerebras_api_key_var = tk.StringVar()
        self.gemini_api_key_var = tk.StringVar()
        self.stt_model_var = tk.StringVar()
        self.refinement_provider_var = tk.StringVar()
        self.refinement_model_var = tk.StringVar()

        # Provider-specific widgets
        self.openai_widgets = {}
        self.deepgram_widgets = {}
        self.cerebras_widgets = {}
        self.gemini_widgets = {}
        self.stt_model_combo = None
        self.refinement_model_combo = None

        # Provider-specific model selections (to preserve when switching)
        self.openai_stt_model = "gpt-4o-mini-transcribe"
        self.deepgram_stt_model = "nova-3"

        # Provider-specific refinement model selections
        self.openai_refinement_model = "gpt-4.1-nano"
        self.cerebras_refinement_model = "llama-3.3-70b"
        self.gemini_refinement_model = "gemini-3-flash-preview"

        self._create_widgets()

    def _create_widgets(self):
        """Create the API section widgets."""
        # === API Keys Section ===
        # OpenAI API Key Frame
        self.openai_widgets["frame"] = ttk.Frame(self.api_keys_frame)
        self.openai_widgets["frame"].grid(
            row=0, column=0, columnspan=4, sticky="ew", pady=5
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
        self.deepgram_widgets["frame"] = ttk.Frame(self.api_keys_frame)
        self.deepgram_widgets["frame"].grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=5
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

        # Cerebras API Key Frame
        self.cerebras_widgets["frame"] = ttk.Frame(self.api_keys_frame)
        self.cerebras_widgets["frame"].grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.cerebras_widgets["frame"], text="Cerebras API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        cerebras_api_key_entry = ttk.Entry(
            self.cerebras_widgets["frame"],
            textvariable=self.cerebras_api_key_var,
            show="*",
            width=50,
        )
        cerebras_api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        # Cerebras Show/Hide API Key button
        def toggle_cerebras_key_visibility():
            if cerebras_api_key_entry["show"] == "*":
                cerebras_api_key_entry["show"] = ""
                cerebras_show_hide_btn["text"] = "Hide"
            else:
                cerebras_api_key_entry["show"] = "*"
                cerebras_show_hide_btn["text"] = "Show"

        cerebras_show_hide_btn = ttk.Button(
            self.cerebras_widgets["frame"],
            text="Show",
            command=toggle_cerebras_key_visibility,
            width=8,
        )
        cerebras_show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)
        self.cerebras_widgets["frame"].columnconfigure(1, weight=1)

        # Google Gemini API Key Frame
        self.gemini_widgets["frame"] = ttk.Frame(self.api_keys_frame)
        self.gemini_widgets["frame"].grid(
            row=3, column=0, columnspan=4, sticky="ew", pady=5
        )

        ttk.Label(self.gemini_widgets["frame"], text="Gemini API Key:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        gemini_api_key_entry = ttk.Entry(
            self.gemini_widgets["frame"],
            textvariable=self.gemini_api_key_var,
            show="*",
            width=50,
        )
        gemini_api_key_entry.grid(
            row=0, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=2
        )

        # Gemini Show/Hide API Key button
        def toggle_gemini_key_visibility():
            if gemini_api_key_entry["show"] == "*":
                gemini_api_key_entry["show"] = ""
                gemini_show_hide_btn["text"] = "Hide"
            else:
                gemini_api_key_entry["show"] = "*"
                gemini_show_hide_btn["text"] = "Show"

        gemini_show_hide_btn = ttk.Button(
            self.gemini_widgets["frame"],
            text="Show",
            command=toggle_gemini_key_visibility,
            width=8,
        )
        gemini_show_hide_btn.grid(row=0, column=3, padx=(5, 0), pady=2)
        self.gemini_widgets["frame"].columnconfigure(1, weight=1)

        # === Speech-to-Text Settings Section ===
        # STT Provider Selection
        ttk.Label(self.frame, text="STT Provider:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        stt_provider_combo = ttk.Combobox(
            self.frame,
            textvariable=self.stt_provider_var,
            values=["openai", "deepgram"],
            state="readonly",
            width=20,
        )
        stt_provider_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        stt_provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        # STT Model (shared between providers, but values change)
        ttk.Label(self.frame, text="STT Model:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.stt_model_combo = ttk.Combobox(
            self.frame,
            textvariable=self.stt_model_var,
            values=["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"],
            state="readonly",
            width=20,
        )
        self.stt_model_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)
        self.stt_model_combo.bind("<<ComboboxSelected>>", self._on_stt_model_changed)

        # Refinement Provider Selection
        ttk.Label(self.frame, text="Refinement Provider:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        refinement_provider_combo = ttk.Combobox(
            self.frame,
            textvariable=self.refinement_provider_var,
            values=["openai", "cerebras", "gemini"],
            state="readonly",
            width=20,
        )
        refinement_provider_combo.grid(
            row=2, column=1, sticky="w", padx=(10, 0), pady=2
        )
        refinement_provider_combo.bind(
            "<<ComboboxSelected>>", self._on_refinement_provider_changed
        )

        # Refinement Model
        ttk.Label(self.frame, text="Refinement Model:").grid(
            row=3, column=0, sticky="w", pady=2
        )
        self.refinement_model_combo = ttk.Combobox(
            self.frame,
            textvariable=self.refinement_model_var,
            values=[
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                "gpt-4o-mini",
                "gpt-4o",
            ],
            state="readonly",
            width=20,
        )
        self.refinement_model_combo.grid(
            row=3, column=1, sticky="w", padx=(10, 0), pady=2
        )
        self.refinement_model_combo.bind(
            "<<ComboboxSelected>>", self._on_refinement_model_changed
        )

        self.frame.columnconfigure(1, weight=1)

    def _on_provider_changed(self, event=None):
        """Handle STT provider changes - show/hide appropriate API key fields."""
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

    def _on_refinement_provider_changed(self, event=None):
        """Handle refinement provider changes - update model options."""
        self._update_refinement_model_options()
        if self.on_change:
            self.on_change()

    def _on_refinement_model_changed(self, event=None):
        """Handle refinement model changes - save to provider-specific variable."""
        provider_value = self.refinement_provider_var.get()
        current_model = self.refinement_model_var.get()

        # Save the model selection to the appropriate provider-specific variable
        if provider_value == "openai":
            self.openai_refinement_model = current_model
        elif provider_value == "cerebras":
            self.cerebras_refinement_model = current_model
        elif provider_value == "gemini":
            self.gemini_refinement_model = current_model

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

    def _update_refinement_model_options(self):
        """Update refinement model options based on selected provider."""
        if not self.refinement_model_combo:
            return

        provider_value = self.refinement_provider_var.get()
        current_model = self.refinement_model_var.get()

        # Define model lists
        openai_models = [
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o-mini",
            "gpt-4o",
        ]
        cerebras_models = [
            "llama-3.3-70b",
            "qwen-3-235b-a22b-instruct-2507",
            "qwen-3-32b",
            "llama3.1-8b",
        ]
        gemini_models = [
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
            "gemini-2.5-flash-preview-05-20",
            "gemini-2.5-pro-preview-06-05",
        ]

        # Save the current model to the appropriate provider-specific variable
        if current_model in openai_models:
            self.openai_refinement_model = current_model
        elif current_model in cerebras_models:
            self.cerebras_refinement_model = current_model
        elif current_model in gemini_models:
            self.gemini_refinement_model = current_model

        # Update model options and restore provider-specific selection
        if provider_value == "openai":
            models = openai_models
            # Restore the previously selected OpenAI model
            if self.openai_refinement_model in models:
                self.refinement_model_var.set(self.openai_refinement_model)
            else:
                self.refinement_model_var.set(models[0])
        elif provider_value == "cerebras":
            models = cerebras_models
            # Restore the previously selected Cerebras model
            if self.cerebras_refinement_model in models:
                self.refinement_model_var.set(self.cerebras_refinement_model)
            else:
                self.refinement_model_var.set(models[0])
        elif provider_value == "gemini":
            models = gemini_models
            # Restore the previously selected Gemini model
            if self.gemini_refinement_model in models:
                self.refinement_model_var.set(self.gemini_refinement_model)
            else:
                self.refinement_model_var.set(models[0])
        else:
            models = []

        self.refinement_model_combo["values"] = models

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
            "cerebras_api_key": self.cerebras_api_key_var.get().strip(),
            "gemini_api_key": self.gemini_api_key_var.get().strip(),
            "stt_model": self.stt_model_var.get(),
            "refinement_provider": self.refinement_provider_var.get(),
            "refinement_model": self.refinement_model_var.get(),
        }

    def set_values(
        self,
        stt_provider: str,
        openai_api_key: str,
        deepgram_api_key: str,
        cerebras_api_key: str,
        gemini_api_key: str,
        stt_model: str,
        refinement_provider: str,
        refinement_model: str,
    ):
        """
        Set the API configuration values.

        This method sets values directly from loaded config without triggering
        model update logic. The combobox values are updated to match the provider,
        then the exact model from config is set.

        Args:
            stt_provider: STT provider name
            openai_api_key: OpenAI API key
            deepgram_api_key: Deepgram API key
            cerebras_api_key: Cerebras API key
            gemini_api_key: Gemini API key
            stt_model: STT model name
            refinement_provider: Refinement provider name
            refinement_model: Refinement model name
        """
        # Set API keys
        self.openai_api_key_var.set(openai_api_key)
        self.deepgram_api_key_var.set(deepgram_api_key)
        self.cerebras_api_key_var.set(cerebras_api_key)
        self.gemini_api_key_var.set(gemini_api_key)

        # Store provider-specific models BEFORE setting providers
        # This ensures the update methods will use these values
        if stt_provider == "openai":
            self.openai_stt_model = stt_model
        elif stt_provider == "deepgram":
            self.deepgram_stt_model = stt_model

        if refinement_provider == "openai":
            self.openai_refinement_model = refinement_model
        elif refinement_provider == "cerebras":
            self.cerebras_refinement_model = refinement_model
        elif refinement_provider == "gemini":
            self.gemini_refinement_model = refinement_model

        # Set providers (this triggers combobox value list updates)
        self.stt_provider_var.set(stt_provider)
        self.refinement_provider_var.set(refinement_provider)

        # Update combobox options to match the providers
        self._update_combobox_options_only()

        # Now set the exact model values from config
        # This must happen AFTER the combobox options are updated
        self.stt_model_var.set(stt_model)
        self.refinement_model_var.set(refinement_model)

    def _update_combobox_options_only(self):
        """Update combobox dropdown options without changing selected values."""
        # Update STT model options
        if self.stt_model_combo:
            provider = self.stt_provider_var.get()
            if provider == "openai":
                models = ["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"]
            elif provider == "deepgram":
                models = ["nova-3", "nova-2", "base", "enhanced", "whisper-medium"]
            else:
                models = []
            self.stt_model_combo["values"] = models

        # Update refinement model options
        if self.refinement_model_combo:
            provider = self.refinement_provider_var.get()
            if provider == "openai":
                models = [
                    "gpt-5",
                    "gpt-5-mini",
                    "gpt-5-nano",
                    "gpt-4.1",
                    "gpt-4.1-mini",
                    "gpt-4.1-nano",
                    "gpt-4o-mini",
                    "gpt-4o",
                ]
            elif provider == "cerebras":
                models = [
                    "llama-3.3-70b",
                    "qwen-3-235b-a22b-instruct-2507",
                    "qwen-3-32b",
                    "llama3.1-8b",
                ]
            elif provider == "gemini":
                models = [
                    "gemini-3-flash-preview",
                    "gemini-3-pro-preview",
                    "gemini-2.5-flash-preview-05-20",
                    "gemini-2.5-pro-preview-06-05",
                ]
            else:
                models = []
            self.refinement_model_combo["values"] = models

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

        # Test Cerebras
        cerebras_status = "Not configured"
        cerebras_prefix = "[ ]"
        if values["cerebras_api_key"]:
            try:
                validate_cerebras_api_key(values["cerebras_api_key"])
                cerebras_status = "VALID"
                cerebras_prefix = "[OK]"
            except Exception as e:
                cerebras_status = str(e)
                cerebras_prefix = "[X]"

        selected_marker = (
            " (Selected for refinement)"
            if values["refinement_provider"] == "cerebras"
            else ""
        )
        status_lines.append(f"\n{cerebras_prefix} Cerebras{selected_marker}:")
        status_lines.append(f"  Status: {cerebras_status}")
        if values["cerebras_api_key"]:
            status_lines.append(
                f"  Key: {'*' * min(len(values['cerebras_api_key']), 20)}"
            )

        # Test Gemini
        gemini_status = "Not configured"
        gemini_prefix = "[ ]"
        if values["gemini_api_key"]:
            try:
                validate_gemini_api_key(values["gemini_api_key"])
                gemini_status = "VALID"
                gemini_prefix = "[OK]"
            except Exception as e:
                gemini_status = str(e)
                gemini_prefix = "[X]"

        selected_marker = (
            " (Selected for refinement)"
            if values["refinement_provider"] == "gemini"
            else ""
        )
        status_lines.append(f"\n{gemini_prefix} Gemini{selected_marker}:")
        status_lines.append(f"  Status: {gemini_status}")
        if values["gemini_api_key"]:
            status_lines.append(
                f"  Key: {'*' * min(len(values['gemini_api_key']), 20)}"
            )

        # Add configuration summary
        status_lines.append("\n" + "-" * 40)
        status_lines.append("\nCurrent Settings:")
        status_lines.append(f"  STT Provider: {values['stt_provider']}")
        status_lines.append(f"  STT Model: {values['stt_model']}")
        status_lines.append(f"  Refinement Provider: {values['refinement_provider']}")
        status_lines.append(f"  Refinement Model: {values['refinement_model']}")

        # Add warning if selected providers are not valid
        if values["stt_provider"] == "openai" and openai_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected STT provider (OpenAI) has an invalid API key!"
            )
        elif values["stt_provider"] == "deepgram" and deepgram_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected STT provider (Deepgram) has an invalid API key!"
            )

        if values["refinement_provider"] == "openai" and openai_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected refinement provider (OpenAI) has an invalid API key!"
            )
        elif values["refinement_provider"] == "cerebras" and cerebras_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected refinement provider (Cerebras) has an invalid API key!"
            )
        elif values["refinement_provider"] == "gemini" and gemini_prefix == "[X]":
            status_lines.append(
                "\n*** WARNING: Selected refinement provider (Gemini) has an invalid API key!"
            )

        return "\n".join(status_lines)
