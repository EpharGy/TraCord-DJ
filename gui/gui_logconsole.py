import tkinter as tk
from tkinter import ttk, scrolledtext

class LogConsolePanel(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Bot Output Log", padding="8", *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.output_text = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            width=60,
            height=15,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#404040"
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")
