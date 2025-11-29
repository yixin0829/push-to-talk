"""Glossary management section for PushToTalk configuration GUI."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable


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


class GlossarySection:
    """Manages the custom glossary configuration section."""

    def __init__(
        self,
        parent: ttk.Widget,
        root: tk.Tk,
        initial_terms: list[str],
        on_change: Callable[[], None] | None = None,
    ):
        """
        Initialize the glossary section.

        Args:
            parent: Parent widget to attach this section to
            root: Root window (needed for dialogs)
            initial_terms: Initial glossary terms
            on_change: Callback called when terms are modified
        """
        self.root = root
        self.on_change = on_change
        self.glossary_terms = list(initial_terms)

        # Create the frame
        self.frame = ttk.LabelFrame(parent, text="Custom Glossary", padding=10)
        self.frame.pack(fill="x", pady=(0, 10))

        # Widgets
        self.glossary_search_var = None
        self.glossary_listbox = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the glossary section widgets."""
        # Description
        description = ttk.Label(
            self.frame,
            text="Add domain-specific terms, acronyms, and technical words to help the AI\nbetter recognize and transcribe your vocabulary.",
            font=("TkDefaultFont", 9),
        )
        description.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Search bar
        search_frame = ttk.Frame(self.frame)
        search_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 5))

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        self.glossary_search_var = tk.StringVar()
        self.glossary_search_var.trace("w", self._filter_glossary_list)
        search_entry = ttk.Entry(
            search_frame, textvariable=self.glossary_search_var, width=30
        )
        search_entry.pack(side="left", fill="x", expand=True)

        # Glossary list with scrollbar
        list_frame = ttk.Frame(self.frame)
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
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(5, 0))

        ttk.Button(buttons_frame, text="Add", command=self._add_term).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(buttons_frame, text="Edit", command=self._edit_term).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(buttons_frame, text="Delete", command=self._delete_term).pack(
            side="left"
        )

        # Configure grid weights for proper resizing
        self.frame.grid_columnconfigure(0, weight=1)

        # Initialize the glossary list
        self._refresh_list()

    def _filter_glossary_list(self, *args):
        """Filter the glossary list based on search term."""
        search_term = self.glossary_search_var.get().lower()
        self.glossary_listbox.delete(0, tk.END)

        for term in self.glossary_terms:
            if search_term in term.lower():
                self.glossary_listbox.insert(tk.END, term)

    def _refresh_list(self):
        """Refresh the glossary list display."""
        if not self.glossary_listbox:
            return

        self.glossary_listbox.delete(0, tk.END)
        for term in sorted(self.glossary_terms, key=str.lower):
            self.glossary_listbox.insert(tk.END, term)

    def _add_term(self):
        """Add a new glossary term."""
        dialog = GlossaryTermDialog(self.root, "Add Glossary Term")
        term = dialog.show()

        if term and term.strip():
            term = term.strip()
            if term not in self.glossary_terms:
                self.glossary_terms.append(term)
                self._refresh_list()
                if self.on_change:
                    self.on_change()
            else:
                messagebox.showinfo(
                    "Duplicate Term", f"The term '{term}' is already in the glossary."
                )

    def _edit_term(self):
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
                    self._refresh_list()
                    if self.on_change:
                        self.on_change()
                else:
                    messagebox.showinfo(
                        "Duplicate Term",
                        f"The term '{new_term}' is already in the glossary.",
                    )

    def _delete_term(self):
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
            self._refresh_list()
            if self.on_change:
                self.on_change()

    def get_terms(self) -> list[str]:
        """
        Get the current glossary terms.

        Returns:
            List of glossary terms
        """
        return list(self.glossary_terms)

    def set_terms(self, terms: list[str]):
        """
        Set the glossary terms.

        Args:
            terms: New list of glossary terms
        """
        self.glossary_terms = list(terms)
        self._refresh_list()
