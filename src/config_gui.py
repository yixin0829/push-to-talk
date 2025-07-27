import os
import tkinter as tk
from tkinter import ttk, messagebox

from .push_to_talk import PushToTalkApp, PushToTalkConfig

CONFIG_FILE = "push_to_talk_config.json"


class ConfigGUI(tk.Tk):
    """Simple configuration GUI for PushToTalk."""

    def __init__(self):
        super().__init__()
        self.title("PushToTalk Configuration")
        self.resizable(False, False)
        self.config = self._load_config()
        self._create_widgets()

    def _load_config(self) -> PushToTalkConfig:
        if os.path.exists(CONFIG_FILE):
            return PushToTalkConfig.load_from_file(CONFIG_FILE)
        cfg = PushToTalkConfig()
        cfg.save_to_file(CONFIG_FILE)
        return cfg

    def _create_widgets(self):
        row = 0
        self.entries = {}

        def add_entry(label: str, attr: str):
            nonlocal row
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.StringVar(value=str(getattr(self.config, attr)))
            ent = ttk.Entry(self, textvariable=var, width=40)
            ent.grid(row=row, column=1, padx=5, pady=2)
            self.entries[attr] = var
            row += 1

        add_entry("OpenAI API Key", "openai_api_key")
        add_entry("Whisper Model", "whisper_model")
        add_entry("GPT Model", "gpt_model")
        add_entry("Sample Rate", "sample_rate")
        add_entry("Chunk Size", "chunk_size")
        add_entry("Channels", "channels")
        add_entry("Hotkey", "hotkey")
        add_entry("Toggle Hotkey", "toggle_hotkey")
        add_entry("Insertion Method", "insertion_method")
        add_entry("Insertion Delay", "insertion_delay")

        self.var_refine = tk.BooleanVar(value=self.config.enable_text_refinement)
        ttk.Checkbutton(self, text="Enable Text Refinement", variable=self.var_refine).grid(row=row, columnspan=2, sticky="w", padx=5, pady=2)
        row += 1
        self.var_audio = tk.BooleanVar(value=self.config.enable_audio_feedback)
        ttk.Checkbutton(self, text="Enable Audio Feedback", variable=self.var_audio).grid(row=row, columnspan=2, sticky="w", padx=5, pady=2)
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Start", command=self.start).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Quit", command=self.destroy).pack(side="left", padx=5)

    def save(self):
        self._update_config_from_entries()
        self.config.save_to_file(CONFIG_FILE)
        messagebox.showinfo("PushToTalk", "Configuration saved")

    def start(self):
        self.save()
        self.destroy()
        app = PushToTalkApp(self.config)
        app.run()

    def _update_config_from_entries(self):
        for attr, var in self.entries.items():
            value = var.get()
            try:
                cast_type = type(getattr(self.config, attr))
                setattr(self.config, attr, cast_type(value))
            except Exception:
                setattr(self.config, attr, value)
        self.config.enable_text_refinement = self.var_refine.get()
        self.config.enable_audio_feedback = self.var_audio.get()


def main():
    gui = ConfigGUI()
    gui.mainloop()


if __name__ == "__main__":
    main()
