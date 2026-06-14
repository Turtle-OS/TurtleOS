"""TurtleOS - area de trabalho, menu iniciar e barra de tarefas."""

import os
import time

import tkinter as tk
from tkinter import messagebox

from . import theme
from .filesystem import VirtualFileSystem
from .apps.terminal import TerminalApp
from .apps.notepad import NotepadApp
from .apps.paint import PaintApp
from .apps.games import TicTacToeApp, SnakeApp
from .apps.calculator import CalculatorApp


ICONS = [
    ("🐢", "Terminal", "launch_terminal"),
    ("📝", "Bloco de Notas", "launch_notepad"),
    ("🎨", "Turtle Paint", "launch_paint"),
    ("⭕", "Jogo da Velha", "launch_tictactoe"),
    ("🐍", "Snake", "launch_snake"),
    ("🧮", "Calculadora", "launch_calculator"),
    ("ℹ️", "Sobre", "launch_about"),
]


class Desktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TurtleOS")
        self.geometry("1024x680")
        self.configure(bg=theme.BG_DESKTOP)
        self.minsize(800, 560)

        data_dir = os.path.join(os.path.expanduser("~"), ".turtleos")
        os.makedirs(data_dir, exist_ok=True)
        self.vfs = VirtualFileSystem(save_path=os.path.join(data_dir, "filesystem.json"))

        self.start_menu = None
        self.taskbar_buttons = {}

        self._build_desktop()
        self._build_taskbar()

        self.protocol("WM_DELETE_WINDOW", self.shutdown)

    # ------------------------------------------------------------ layout
    def _build_desktop(self):
        self.desktop_area = tk.Frame(self, bg=theme.BG_DESKTOP)
        self.desktop_area.pack(side="top", fill="both", expand=True)

        icon_frame = tk.Frame(self.desktop_area, bg=theme.BG_DESKTOP)
        icon_frame.place(x=16, y=16)

        for emoji, label, action in ICONS:
            self._make_icon(icon_frame, emoji, label, action)

        # logo/marca d'agua no centro
        tk.Label(
            self.desktop_area, text="🐢 TurtleOS",
            font=("Segoe UI", 38, "bold"),
            bg=theme.BG_DESKTOP, fg="#145c3f",
        ).place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(
            self.desktop_area, text="simulador de sistema operacional",
            font=theme.FONT_UI,
            bg=theme.BG_DESKTOP, fg="#1d6f4e",
        ).place(relx=0.5, rely=0.52, anchor="center")

    def _make_icon(self, parent, emoji, label, action):
        cell = tk.Frame(parent, bg=theme.BG_DESKTOP, width=88, height=88)
        cell.pack(pady=4)
        icon = tk.Label(cell, text=emoji, font=theme.FONT_ICON,
                         bg=theme.BG_DESKTOP, fg=theme.FG_TEXT)
        icon.pack()
        text = tk.Label(cell, text=label, font=("Segoe UI", 9),
                         bg=theme.BG_DESKTOP, fg=theme.FG_TEXT, wraplength=86,
                         justify="center")
        text.pack()

        def open_app(_event=None):
            getattr(self, action)()

        for widget in (cell, icon, text):
            widget.bind("<Double-Button-1>", open_app)

    def _build_taskbar(self):
        self.taskbar = tk.Frame(self, bg=theme.BG_PANEL, height=42)
        self.taskbar.pack(side="bottom", fill="x")

        self.start_btn = tk.Button(
            self.taskbar, text="🐢 Iniciar", font=theme.FONT_UI_BOLD,
            bg=theme.ACCENT, fg="#063a26", activebackground=theme.ACCENT_DARK,
            relief="flat", command=self._toggle_start_menu,
        )
        self.start_btn.pack(side="left", padx=8, pady=6)

        self.running_frame = tk.Frame(self.taskbar, bg=theme.BG_PANEL)
        self.running_frame.pack(side="left", fill="x", expand=True, padx=8)

        self.clock_label = tk.Label(
            self.taskbar, font=theme.FONT_UI, bg=theme.BG_PANEL, fg=theme.FG_TEXT,
        )
        self.clock_label.pack(side="right", padx=12)
        self._update_clock()

    def _update_clock(self):
        self.clock_label.config(text=time.strftime("%H:%M:%S  %d/%m/%Y"))
        self.after(1000, self._update_clock)

    # ------------------------------------------------------------ start menu
    def _toggle_start_menu(self):
        if self.start_menu is not None and self.start_menu.winfo_exists():
            self.start_menu.destroy()
            self.start_menu = None
            return

        menu = tk.Toplevel(self)
        menu.overrideredirect(True)
        menu.configure(bg=theme.BG_PANEL, highlightthickness=1,
                        highlightbackground=theme.ACCENT)
        x = self.winfo_rootx() + 8
        y = self.winfo_rooty() + self.winfo_height() - self.taskbar.winfo_height() - 4
        menu.geometry(f"+{x}+{max(y, 0) - 230}")

        tk.Label(menu, text="🐢 TurtleOS", font=theme.FONT_TITLE,
                 bg=theme.BG_PANEL, fg=theme.ACCENT).pack(fill="x", padx=12, pady=(10, 4))

        for emoji, label, action in ICONS:
            self._menu_item(menu, f"{emoji}  {label}", getattr(self, action))

        tk.Frame(menu, bg=theme.ACCENT, height=1).pack(fill="x", padx=8, pady=4)
        self._menu_item(menu, "🔄  Reiniciar", self.reboot)
        self._menu_item(menu, "⏻  Desligar", self.shutdown)

        menu.bind("<FocusOut>", lambda e: menu.destroy())
        menu.focus_force()
        self.start_menu = menu

    def _menu_item(self, parent, text, command):
        def run():
            if self.start_menu is not None:
                self.start_menu.destroy()
                self.start_menu = None
            command()

        tk.Button(
            parent, text=text, font=theme.FONT_UI, anchor="w",
            bg=theme.BG_PANEL, fg=theme.FG_TEXT, activebackground=theme.ACCENT_DARK,
            relief="flat", command=run,
        ).pack(fill="x", padx=8, pady=2)

    # ------------------------------------------------------------ window/taskbar tracking
    def _register_window(self, win, title):
        btn = tk.Button(
            self.running_frame, text=title, font=theme.FONT_UI,
            bg=theme.BG_WINDOW, fg=theme.FG_TEXT, relief="flat",
            activebackground=theme.ACCENT_DARK,
            command=lambda: self._raise_window(win),
        )
        btn.pack(side="left", padx=3)
        self.taskbar_buttons[win] = btn

        def on_destroy(event):
            if event.widget is win:
                b = self.taskbar_buttons.pop(win, None)
                if b is not None:
                    b.destroy()

        win.bind("<Destroy>", on_destroy)

    def _raise_window(self, win):
        if not win.winfo_exists():
            return
        if win.state() == "iconic":
            win.deiconify()
        win.lift()
        win.focus_force()

    # ------------------------------------------------------------ app launchers
    def launch_terminal(self):
        win = TerminalApp(self, self.vfs, desktop=self)
        self._register_window(win, "🐢 Terminal")
        return win

    def launch_notepad(self, initial_text="", filename=None, vfs=None, vfs_path=None):
        win = NotepadApp(self, initial_text=initial_text, filename=filename,
                          vfs=vfs, vfs_path=vfs_path)
        self._register_window(win, "📝 Bloco de Notas")
        return win

    def launch_paint(self):
        win = PaintApp(self)
        self._register_window(win, "🎨 Turtle Paint")
        return win

    def launch_tictactoe(self):
        win = TicTacToeApp(self)
        self._register_window(win, "⭕ Jogo da Velha")
        return win

    def launch_snake(self):
        win = SnakeApp(self)
        self._register_window(win, "🐍 Snake")
        return win

    def launch_calculator(self):
        win = CalculatorApp(self)
        self._register_window(win, "🧮 Calculadora")
        return win

    def launch_about(self):
        win = tk.Toplevel(self)
        win.title("ℹ️ Sobre o TurtleOS")
        win.geometry("360x260")
        win.resizable(False, False)
        win.configure(bg=theme.BG_WINDOW)
        tk.Label(win, text="🐢", font=("Segoe UI Emoji", 48),
                 bg=theme.BG_WINDOW, fg=theme.ACCENT).pack(pady=(16, 0))
        tk.Label(win, text=f"TurtleOS {theme.VERSION}", font=theme.FONT_TITLE,
                 bg=theme.BG_WINDOW, fg=theme.FG_TEXT).pack()
        tk.Label(
            win,
            text=(
                "Um simulador de sistema operacional\n"
                "feito em Python com Tkinter.\n\n"
                "Inclui terminal com sistema de arquivos\n"
                "virtual, bloco de notas, jogos e um\n"
                "editor de desenhos Turtle/Logo."
            ),
            font=theme.FONT_UI, bg=theme.BG_WINDOW, fg=theme.FG_TEXT, justify="center",
        ).pack(pady=10)
        self._register_window(win, "ℹ️ Sobre")
        return win

    # ------------------------------------------------------------ power
    def reboot(self):
        for win in list(self.taskbar_buttons.keys()):
            if win.winfo_exists():
                win.destroy()
        self.vfs.save()
        overlay = tk.Toplevel(self)
        overlay.overrideredirect(True)
        overlay.configure(bg="black")
        overlay.geometry(f"{self.winfo_width()}x{self.winfo_height()}"
                          f"+{self.winfo_rootx()}+{self.winfo_rooty()}")
        tk.Label(overlay, text="🐢 Reiniciando o TurtleOS...", fg=theme.ACCENT,
                 bg="black", font=theme.FONT_TITLE).place(relx=0.5, rely=0.5, anchor="center")
        self.after(1200, overlay.destroy)

    def shutdown(self):
        if messagebox.askyesno("TurtleOS", "Deseja realmente encerrar o TurtleOS?"):
            self.vfs.save()
            self.destroy()
