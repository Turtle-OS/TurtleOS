"""Bloco de Notas do TurtleOS."""

import tkinter as tk
from tkinter import filedialog, messagebox

from .. import theme


class NotepadApp(tk.Toplevel):
    def __init__(self, master, initial_text="", filename=None,
                 vfs=None, vfs_path=None, on_save_vfs=None):
        super().__init__(master)
        self.title(f"📝 Bloco de Notas - {filename or 'sem titulo'}")
        self.geometry("520x420")
        self.configure(bg=theme.BG_WINDOW)

        self.disk_path = None
        self.vfs = vfs
        self.vfs_path = vfs_path

        # ---- menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Novo", command=self.novo)
        file_menu.add_command(label="Abrir do disco...", command=self.abrir_disco)
        file_menu.add_command(label="Salvar no disco...", command=self.salvar_disco)
        if self.vfs is not None:
            file_menu.add_separator()
            file_menu.add_command(label="Salvar no TurtleOS", command=self.salvar_vfs)
        file_menu.add_separator()
        file_menu.add_command(label="Fechar", command=self.destroy)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        self.config(menu=menubar)

        # ---- text area
        frame = tk.Frame(self, bg=theme.BG_WINDOW)
        frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            frame, wrap="word", undo=True,
            bg="#fdfdfd", fg="#202020", insertbackground="#202020",
            font=theme.FONT_MONO, padx=8, pady=8,
        )
        scrollbar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        if initial_text:
            self.text.insert("1.0", initial_text)

        # status bar
        self.status = tk.Label(
            self, text="Pronto", anchor="w",
            bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=("Segoe UI", 8),
        )
        self.status.pack(fill="x")

    # ------------------------------------------------------------
    def novo(self):
        if messagebox.askyesno("Novo", "Limpar o texto atual?"):
            self.text.delete("1.0", "end")
            self.disk_path = None
            self.title("📝 Bloco de Notas - sem titulo")

    def abrir_disco(self):
        path = filedialog.askopenfilename(
            title="Abrir arquivo",
            filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as exc:
            messagebox.showerror("Erro ao abrir", str(exc))
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.disk_path = path
        self.title(f"📝 Bloco de Notas - {path}")
        self.status.config(text=f"Aberto: {path}")

    def salvar_disco(self):
        path = filedialog.asksaveasfilename(
            title="Salvar arquivo",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            initialfile=self.disk_path or "documento.txt",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc))
            return
        self.disk_path = path
        self.title(f"📝 Bloco de Notas - {path}")
        self.status.config(text=f"Salvo em: {path}")

    def salvar_vfs(self):
        if self.vfs is None or not self.vfs_path:
            messagebox.showinfo("TurtleOS", "Nenhum arquivo do TurtleOS associado.")
            return
        content = self.text.get("1.0", "end-1c")
        self.vfs.write(self.vfs_path, content)
        self.status.config(text=f"Salvo no TurtleOS: {self.vfs_path}")
