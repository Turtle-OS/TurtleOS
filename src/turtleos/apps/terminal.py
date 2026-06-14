"""Terminal do TurtleOS - um CLI de verdade rodando dentro do simulador."""

import getpass
import shlex
import socket
import subprocess
import time

import tkinter as tk
from tkinter import messagebox

from .. import theme
from ..filesystem import VFSError

TURTLE_ART = r"""
        __
   ____/ o\___
  /  _/   |   \____
 |  |  TurtleOS    \
  \_/\___/\___/\___/
"""

HELP_TEXT = """\
Comandos disponiveis:
  ls [pasta]            lista arquivos e pastas
  cd [pasta]            muda de diretorio (".." volta um nivel)
  pwd                    mostra o diretorio atual
  mkdir <nome>           cria uma pasta
  touch <nome>           cria um arquivo vazio
  rm [-r] <nome>         remove arquivo ou pasta (-r para nao vazia)
  cat <arquivo>          mostra o conteudo de um arquivo
  echo <texto>           imprime texto (use > ou >> para salvar em arquivo)
  tree [pasta]           mostra a arvore de arquivos
  edit <arquivo>         abre o arquivo no Bloco de Notas
  open <app>             abre um aplicativo (notepad, paint, velha, snake,
                         calc, terminal, sobre)
  calc <expressao>       calculadora rapida (ex: calc 2*(3+4))
  sh <comando>           executa um comando real do sistema
  py <expressao>         avalia uma expressao Python
  clear                  limpa a tela
  whoami / date / turtlefetch
  history                mostra o historico de comandos
  save                    salva o sistema de arquivos virtual em disco
  exit                    fecha este terminal
"""


class TerminalApp(tk.Toplevel):
    def __init__(self, master, vfs, desktop=None):
        super().__init__(master)
        self.vfs = vfs
        self.desktop = desktop
        self.history = []
        self.history_index = 0

        self.title("🐢 Terminal - TurtleOS")
        self.geometry("640x420")
        self.configure(bg=theme.TERMINAL_BG)

        self.text = tk.Text(
            self, bg=theme.TERMINAL_BG, fg=theme.TERMINAL_FG,
            insertbackground=theme.TERMINAL_FG, font=theme.FONT_MONO,
            wrap="word", padx=8, pady=6, borderwidth=0,
        )
        self.text.pack(fill="both", expand=True)

        self.text.insert("end", "TurtleOS - Terminal\n")
        self.text.insert("end", "Digite 'help' para ver os comandos.\n\n")
        self._print_prompt()

        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        self.text.bind("<Up>", self._on_up)
        self.text.bind("<Down>", self._on_down)
        self.text.bind("<Key>", self._on_key)
        self.text.focus_set()

    # ------------------------------------------------------------ prompt
    def _prompt_str(self):
        return f"tartaruga@turtleos:{self.vfs.pwd()}$ "

    def _print_prompt(self):
        self.text.insert("end", self._prompt_str())
        self.text.mark_set("input_start", "end-1c")
        self.text.see("end")

    def _current_input(self):
        return self.text.get("input_start", "end-1c")

    # ------------------------------------------------------------ key handling
    def _on_key(self, event):
        # impede edicao antes do prompt atual
        if self.text.compare("insert", "<", "input_start"):
            self.text.mark_set("insert", "end")

    def _on_backspace(self, event):
        if self.text.compare("insert", "<=", "input_start"):
            return "break"

    def _on_up(self, event):
        if not self.history:
            return "break"
        self.history_index = max(0, self.history_index - 1)
        self._set_input(self.history[self.history_index])
        return "break"

    def _on_down(self, event):
        if not self.history:
            return "break"
        self.history_index = min(len(self.history), self.history_index + 1)
        if self.history_index == len(self.history):
            self._set_input("")
        else:
            self._set_input(self.history[self.history_index])
        return "break"

    def _set_input(self, value):
        self.text.delete("input_start", "end")
        self.text.insert("end", value)

    def _on_return(self, event):
        line = self._current_input()
        self.text.insert("end", "\n")
        line = line.strip()
        if line:
            self.history.append(line)
            self.history_index = len(self.history)
            self._run(line)
        self._print_prompt()
        return "break"

    # ------------------------------------------------------------ output helper
    def _out(self, msg=""):
        self.text.insert("end", str(msg) + "\n")

    # ------------------------------------------------------------ command dispatch
    def _run(self, line):
        try:
            args = shlex.split(line)
        except ValueError as exc:
            self._out(f"erro de sintaxe: {exc}")
            return
        if not args:
            return
        cmd, rest = args[0], args[1:]
        handler = getattr(self, f"cmd_{cmd}", None)
        if handler is None:
            self._out(f"comando nao encontrado: {cmd}  (digite 'help')")
            return
        try:
            handler(rest)
        except VFSError as exc:
            self._out(f"erro: {exc}")
        except Exception as exc:  # noqa - terminal nao deve travar
            self._out(f"erro inesperado: {exc}")

    # ------------------------------------------------------------ commands
    def cmd_help(self, args):
        self._out(HELP_TEXT)

    def cmd_ls(self, args):
        path = args[0] if args else None
        for entry in self.vfs.ls(path):
            self._out(entry)

    def cmd_cd(self, args):
        self.vfs.cd(args[0] if args else "/home/tartaruga")

    def cmd_pwd(self, args):
        self._out(self.vfs.pwd())

    def cmd_mkdir(self, args):
        if not args:
            self._out("uso: mkdir <nome>")
            return
        for name in args:
            self.vfs.mkdir(name)

    def cmd_touch(self, args):
        if not args:
            self._out("uso: touch <nome>")
            return
        for name in args:
            self.vfs.touch(name)

    def cmd_rm(self, args):
        recursive = False
        names = []
        for a in args:
            if a == "-r":
                recursive = True
            else:
                names.append(a)
        if not names:
            self._out("uso: rm [-r] <nome>")
            return
        for name in names:
            self.vfs.rm(name, recursive=recursive)

    def cmd_cat(self, args):
        if not args:
            self._out("uso: cat <arquivo>")
            return
        for name in args:
            self._out(self.vfs.read(name))

    def cmd_echo(self, args):
        if ">>" in args or ">" in args:
            append = ">>" in args
            sep = ">>" if append else ">"
            idx = args.index(sep)
            text = " ".join(args[:idx])
            target = args[idx + 1] if len(args) > idx + 1 else None
            if not target:
                self._out("uso: echo <texto> > <arquivo>")
                return
            self.vfs.write(target, text + "\n", append=append)
        else:
            self._out(" ".join(args))

    def cmd_tree(self, args):
        path = args[0] if args else None
        self._out(self.vfs.pwd() if not path else path)
        for line in self.vfs.tree(path):
            self._out(line)

    def cmd_clear(self, args):
        self.text.delete("1.0", "end")

    def cmd_whoami(self, args):
        try:
            user = getpass.getuser()
        except Exception:
            user = "tartaruga"
        self._out(f"tartaruga (usuario real: {user})")

    def cmd_date(self, args):
        self._out(time.strftime("%a %d/%m/%Y %H:%M:%S"))

    def cmd_history(self, args):
        for i, h in enumerate(self.history, 1):
            self._out(f"{i:>3}  {h}")

    def cmd_turtlefetch(self, args):
        self.cmd_neofetch(args)

    def cmd_neofetch(self, args):
        try:
            host = socket.gethostname()
        except Exception:
            host = "turtleos"
        info = [
            f"usuario@{host}",
            "----------------",
            f"SO: {theme.APP_TITLE} {theme.VERSION}",
            "Shell: turtleshell",
            f"Diretorio: {self.vfs.pwd()}",
        ]
        lines = TURTLE_ART.splitlines()
        for i in range(max(len(lines), len(info))):
            left = lines[i] if i < len(lines) else ""
            right = info[i] if i < len(info) else ""
            self._out(f"{left:<22}{right}")

    def cmd_calc(self, args):
        if not args:
            self._out("uso: calc <expressao>")
            return
        expr = " ".join(args)
        self._safe_eval(expr)

    def cmd_py(self, args):
        if not args:
            self._out("uso: py <expressao>")
            return
        expr = " ".join(args)
        self._safe_eval(expr)

    def _safe_eval(self, expr):
        allowed = {"__builtins__": {}}
        import math
        allowed.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
        allowed.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})
        try:
            result = eval(expr, allowed, {})
        except Exception as exc:
            self._out(f"erro: {exc}")
            return
        self._out(result)

    def cmd_sh(self, args):
        if not args:
            self._out("uso: sh <comando do sistema>")
            return
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=15
            )
            if result.stdout:
                self._out(result.stdout.rstrip())
            if result.stderr:
                self._out(result.stderr.rstrip())
        except FileNotFoundError:
            self._out(f"comando nao encontrado no sistema real: {args[0]}")
        except Exception as exc:
            self._out(f"erro: {exc}")

    def cmd_edit(self, args):
        self.cmd_nano(args)

    def cmd_nano(self, args):
        if not args:
            self._out("uso: edit <arquivo>")
            return
        path = args[0]
        if not self.vfs.exists(path):
            self.vfs.touch(path)
        content = self.vfs.read(path)
        if self.desktop:
            self.desktop.launch_notepad(
                initial_text=content, filename=path,
                vfs=self.vfs, vfs_path=path,
            )
        else:
            self._out("editor indisponivel")

    def cmd_open(self, args):
        if not args or self.desktop is None:
            self._out("uso: open <notepad|paint|velha|snake|calc|terminal|sobre>")
            return
        app = args[0].lower()
        mapping = {
            "notepad": self.desktop.launch_notepad,
            "bloco": self.desktop.launch_notepad,
            "paint": self.desktop.launch_paint,
            "turtle": self.desktop.launch_paint,
            "velha": self.desktop.launch_tictactoe,
            "tictactoe": self.desktop.launch_tictactoe,
            "snake": self.desktop.launch_snake,
            "calc": self.desktop.launch_calculator,
            "calculadora": self.desktop.launch_calculator,
            "terminal": self.desktop.launch_terminal,
            "sobre": self.desktop.launch_about,
        }
        fn = mapping.get(app)
        if fn is None:
            self._out(f"aplicativo desconhecido: {app}")
            return
        fn()

    def cmd_save(self, args):
        self.vfs.save()
        self._out("sistema de arquivos salvo.")

    def cmd_exit(self, args):
        self.destroy()

    def cmd_reboot(self, args):
        self._out("reiniciando o TurtleOS...")
        if self.desktop:
            self.desktop.after(500, self.desktop.reboot)

    def cmd_poweroff(self, args):
        if messagebox.askyesno("TurtleOS", "Encerrar o TurtleOS?"):
            if self.desktop:
                self.desktop.shutdown()
            else:
                self.destroy()

    def cmd_cowsay(self, args):
        self.cmd_turtlesay(args)

    def cmd_turtlesay(self, args):
        text = " ".join(args) if args else "Mooo... digo, vrrr!"
        width = max(len(text) + 2, 10)
        self._out(" " + "_" * width)
        self._out(f"< {text} >")
        self._out(" " + "-" * width)
        self._out(TURTLE_ART)
