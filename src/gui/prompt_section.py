"""Custom refinement prompt section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from src.config.prompts import (
    text_refiner_prompt_w_glossary,
    text_refiner_prompt_wo_glossary,
)


class PromptSection:
    """Manages the custom refinement prompt configuration section."""

    def __init__(
        self,
        parent: ttk.Widget,
        root: tk.Tk,
        initial_prompt: str = "",
        on_change: Callable[[], None] | None = None,
    ):
        """
        Initialize the prompt section.

        Args:
            parent: Parent widget to attach this section to
            root: Root window (needed for dialogs)
            initial_prompt: Initial custom prompt value
            on_change: Callback called when prompt is modified
        """
        self.root = root
        self.on_change = on_change
        self._suspend_change_events = False

        # Create the frame
        self.frame = ttk.LabelFrame(parent, text="Custom Refinement Prompt", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Widgets
        self.prompt_text = None
        self.char_count_label = None
        self._defaults_visible = None
        self._defaults_frame = None

        self._create_widgets()

        # Set initial value
        if initial_prompt:
            self.set_prompt(initial_prompt)

    def _create_widgets(self):
        """Create the prompt section widgets."""
        # Description
        description = ttk.Label(
            self.frame,
            text="Customize the system prompt used for text refinement. Leave empty to use the default.\n"
            "Use {custom_glossary} placeholder to include your glossary terms.",
            font=("TkDefaultFont", 9),
        )
        description.pack(fill="x", pady=(0, 10))

        # Collapsible default prompts reference
        self._create_default_prompts_section()

        # Custom prompt text area with scrollbar
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill="both", expand=True, pady=(10, 5))

        self.prompt_text = tk.Text(
            text_frame,
            height=10,
            width=60,
            wrap=tk.WORD,
            font=("TkFixedFont", 9),
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.prompt_text.yview
        )
        self.prompt_text.configure(yscrollcommand=scrollbar.set)

        self.prompt_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind change events
        self.prompt_text.bind("<<Modified>>", self._on_text_modified)

        # Character count
        self.char_count_label = ttk.Label(
            self.frame,
            text="0 characters",
            font=("TkDefaultFont", 8),
            foreground="gray",
        )
        self.char_count_label.pack(anchor="w", pady=(0, 5))

        # Buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=(5, 0))

        ttk.Button(
            button_frame,
            text="Copy Default (with Glossary)",
            command=self._copy_default_with_glossary,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Copy Default (no Glossary)",
            command=self._copy_default_without_glossary,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_prompt,
        ).pack(side="left")

    def _create_default_prompts_section(self):
        """Create collapsible section showing default prompts."""
        # Toggle button for showing/hiding defaults
        self._defaults_visible = tk.BooleanVar(value=False)

        # Create a frame for the toggle button
        toggle_frame = ttk.Frame(self.frame)
        toggle_frame.pack(fill="x")

        # Use a button with arrow indicator for better UX
        self._toggle_btn = ttk.Button(
            toggle_frame,
            text="\u25b6 Show default prompts (reference)",
            command=self._toggle_defaults_visibility,
            width=35,
        )
        self._toggle_btn.pack(side="left")

        # Frame for default prompts - initially not packed
        self._defaults_frame = ttk.Frame(self.frame)

    def _toggle_defaults_visibility(self):
        """Toggle visibility of default prompts section."""
        is_visible = self._defaults_visible.get()
        self._defaults_visible.set(not is_visible)

        if self._defaults_visible.get():
            # Show defaults - update button text and show frame
            self._toggle_btn.configure(text="\u25bc Hide default prompts (reference)")
            self._defaults_frame.pack(
                fill="x", pady=(5, 0), after=self._toggle_btn.master
            )
            self._populate_defaults_frame()
        else:
            # Hide defaults - update button text and hide frame
            self._toggle_btn.configure(text="\u25b6 Show default prompts (reference)")
            self._defaults_frame.pack_forget()

    def _populate_defaults_frame(self):
        """Populate the defaults frame with read-only prompt displays."""
        # Clear existing content
        for widget in self._defaults_frame.winfo_children():
            widget.destroy()

        # With glossary prompt
        ttk.Label(
            self._defaults_frame,
            text="Default (with glossary):",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(anchor="w")

        with_glossary_text = tk.Text(
            self._defaults_frame,
            height=6,
            width=60,
            wrap=tk.WORD,
            font=("TkFixedFont", 8),
            state="disabled",
            background="#f0f0f0",
        )
        with_glossary_text.pack(fill="x", pady=(2, 10))
        with_glossary_text.configure(state="normal")
        with_glossary_text.insert("1.0", text_refiner_prompt_w_glossary)
        with_glossary_text.configure(state="disabled")

        # Without glossary prompt
        ttk.Label(
            self._defaults_frame,
            text="Default (without glossary):",
            font=("TkDefaultFont", 9, "bold"),
        ).pack(anchor="w")

        wo_glossary_text = tk.Text(
            self._defaults_frame,
            height=6,
            width=60,
            wrap=tk.WORD,
            font=("TkFixedFont", 8),
            state="disabled",
            background="#f0f0f0",
        )
        wo_glossary_text.pack(fill="x", pady=(2, 0))
        wo_glossary_text.configure(state="normal")
        wo_glossary_text.insert("1.0", text_refiner_prompt_wo_glossary)
        wo_glossary_text.configure(state="disabled")

    def _on_text_modified(self, event=None):
        """Handle text modification events."""
        if self._suspend_change_events:
            return

        # Reset the modified flag
        self.prompt_text.edit_modified(False)

        # Update character count
        content = self.prompt_text.get("1.0", "end-1c")
        self.char_count_label.configure(text=f"{len(content)} characters")

        # Notify change
        if self.on_change:
            self.on_change()

    def _copy_default_with_glossary(self):
        """Copy default prompt with glossary placeholder to editor."""
        self._suspend_change_events = True
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", text_refiner_prompt_w_glossary)
        self._suspend_change_events = False
        self._on_text_modified()

    def _copy_default_without_glossary(self):
        """Copy default prompt without glossary to editor."""
        self._suspend_change_events = True
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", text_refiner_prompt_wo_glossary)
        self._suspend_change_events = False
        self._on_text_modified()

    def _clear_prompt(self):
        """Clear the custom prompt."""
        if self.prompt_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno(
                "Clear Custom Prompt",
                "Are you sure you want to clear the custom prompt?\nThe default prompt will be used.",
            ):
                self._suspend_change_events = True
                self.prompt_text.delete("1.0", tk.END)
                self._suspend_change_events = False
                self._on_text_modified()
        else:
            # Already empty, just clear without confirmation
            self._suspend_change_events = True
            self.prompt_text.delete("1.0", tk.END)
            self._suspend_change_events = False
            self._on_text_modified()

    def get_prompt(self) -> str:
        """
        Get the current custom prompt.

        Returns:
            Custom prompt string (empty if using default)
        """
        return self.prompt_text.get("1.0", "end-1c").strip()

    def set_prompt(self, prompt: str):
        """
        Set the custom prompt.

        Args:
            prompt: Custom prompt string
        """
        self._suspend_change_events = True
        self.prompt_text.delete("1.0", tk.END)
        if prompt:
            self.prompt_text.insert("1.0", prompt)
        self._suspend_change_events = False
        # Update character count without triggering change callback
        content = self.prompt_text.get("1.0", "end-1c")
        self.char_count_label.configure(text=f"{len(content)} characters")
