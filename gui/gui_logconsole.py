import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

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
        # Configure text tags for colored output
        self.output_text.tag_configure("info", foreground="#ffffff")
        self.output_text.tag_configure("success", foreground="#4CAF50")
        self.output_text.tag_configure("warning", foreground="#FF9800")
        self.output_text.tag_configure("error", foreground="#f44336")
        self.output_text.tag_configure("timestamp", foreground="#888888")

    def add_log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.output_text.insert(tk.END, f"{message}\n", level)
        self.output_text.see(tk.END)
        # Limit log size (keep last 1000 lines)
        lines = self.output_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            lines_to_delete = len(lines) - 1000
            self.output_text.delete("1.0", f"{lines_to_delete}.0")

    def clear_log(self):
        self.output_text.delete("1.0", tk.END)
        self.add_log("Log cleared", "info")
