"""Calculadora do TurtleOS."""

import tkinter as tk

from .. import theme

ALLOWED_CHARS = set("0123456789.+-*/() %")


class CalculatorApp(tk.Toplevel):
    BUTTONS = [
        ["C", "(", ")", "/"],
        ["7", "8", "9", "*"],
        ["4", "5", "6", "-"],
        ["1", "2", "3", "+"],
        ["0", ".", "=", "%"],
    ]

    def __init__(self, master):
        super().__init__(master)
        self.title("🧮 Calculadora - TurtleOS")
        self.resizable(False, False)
        self.configure(bg=theme.BG_WINDOW)

        self.display = tk.StringVar(value="0")
        entry = tk.Entry(self, textvariable=self.display, font=("Consolas", 18),
                          justify="right", bg="#0b0f0c", fg=theme.ACCENT,
                          insertbackground=theme.ACCENT, relief="flat", bd=8)
        entry.grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=8)

        for r, row in enumerate(self.BUTTONS, start=1):
            for c, label in enumerate(row):
                tk.Button(
                    self, text=label, font=("Segoe UI", 14), width=4, height=2,
                    bg=theme.ACCENT_DARK, fg="white", activebackground=theme.ACCENT,
                    relief="flat", command=lambda l=label: self._press(l),
                ).grid(row=r, column=c, padx=2, pady=2)

        self.bind("<Return>", lambda e: self._press("="))
        self.bind("<Key>", self._on_key)

    def _on_key(self, event):
        if event.keysym == "BackSpace":
            self._press("⌫")

    def _press(self, label):
        cur = self.display.get()
        if label == "C":
            self.display.set("0")
        elif label == "⌫":
            self.display.set(cur[:-1] or "0")
        elif label == "=":
            self._evaluate()
        else:
            if cur == "0" and label not in (".", "%"):
                cur = ""
            self.display.set(cur + label)

    def _evaluate(self):
        expr = self.display.get()
        if not expr or not set(expr) <= ALLOWED_CHARS:
            self.display.set("Erro")
            return
        try:
            result = eval(expr, {"__builtins__": {}}, {})
        except Exception:
            self.display.set("Erro")
            return
        self.display.set(str(result))
