"""Turtle Paint - editor de desenhos estilo Logo, o coracao do TurtleOS."""

import tkinter as tk
from tkinter import colorchooser, messagebox
from turtle import RawTurtle, TurtleScreen

from .. import theme

HELP_TEXT = """\
Comandos (separe varios por ';' ou uma por linha):
  fd <n> / bk <n>      anda para frente / para tras
  rt <graus> / lt <graus>  vira a direita / esquerda
  pu / pd              levanta / abaixa a caneta
  color <nome|#hex>    muda a cor da caneta
  width <n>            espessura da linha
  circle <raio>        desenha um circulo
  goto <x> <y>         vai para uma posicao
  home                 volta ao centro
  speed <0-10>         velocidade do desenho
  clear                limpa o desenho (mantem posicao)
  reset                limpa tudo e volta ao centro
"""


class PaintApp(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("🎨 Turtle Paint - TurtleOS")
        self.geometry("760x560")
        self.configure(bg=theme.BG_WINDOW)
        self.resizable(False, False)

        # ---- canvas + turtle
        canvas = tk.Canvas(self, width=560, height=480, bg="white",
                            highlightthickness=1, highlightbackground=theme.ACCENT)
        canvas.place(x=10, y=10)

        self.screen = TurtleScreen(canvas)
        self.screen.bgcolor("white")
        self.turtle = RawTurtle(self.screen)
        self.turtle.shape("turtle")
        self.turtle.speed(6)

        # ---- side panel
        panel = tk.Frame(self, bg=theme.BG_WINDOW)
        panel.place(x=580, y=10, width=170, height=540)

        tk.Label(panel, text="Controles", bg=theme.BG_WINDOW, fg=theme.ACCENT,
                 font=theme.FONT_TITLE).pack(pady=(0, 8))

        self.step = tk.StringVar(value="50")
        self.angle = tk.StringVar(value="90")

        tk.Label(panel, text="Passo", bg=theme.BG_WINDOW, fg=theme.FG_TEXT).pack(anchor="w")
        tk.Entry(panel, textvariable=self.step).pack(fill="x", pady=(0, 4))
        tk.Label(panel, text="Angulo", bg=theme.BG_WINDOW, fg=theme.FG_TEXT).pack(anchor="w")
        tk.Entry(panel, textvariable=self.angle).pack(fill="x", pady=(0, 8))

        grid = tk.Frame(panel, bg=theme.BG_WINDOW)
        grid.pack(pady=4)
        self._btn(grid, "↑ Frente", lambda: self._move(1), 0, 1)
        self._btn(grid, "↓ Tras", lambda: self._move(-1), 2, 1)
        self._btn(grid, "↺ Esquerda", lambda: self.turtle.left(self._f(self.angle)), 1, 0)
        self._btn(grid, "↻ Direita", lambda: self.turtle.right(self._f(self.angle)), 1, 2)

        self._btn(panel, "Levantar caneta", self.turtle.penup)
        self._btn(panel, "Abaixar caneta", self.turtle.pendown)
        self._btn(panel, "Escolher cor...", self._choose_color)
        self._btn(panel, "Limpar (manter pos.)", lambda: self.turtle.clear())
        self._btn(panel, "Reiniciar tudo", self._reset)
        self._btn(panel, "Ajuda", self._help)

        tk.Label(panel, text="Comandos (Logo):", bg=theme.BG_WINDOW, fg=theme.FG_TEXT)\
            .pack(anchor="w", pady=(10, 0))
        self.cmd_box = tk.Text(panel, height=6, font=theme.FONT_MONO,
                                bg="#0b0f0c", fg=theme.ACCENT, insertbackground=theme.ACCENT)
        self.cmd_box.pack(fill="x")
        self.cmd_box.insert("1.0", "fd 100; rt 90\nfd 100; rt 90")
        self._btn(panel, "Executar", self._run_commands)

    # ------------------------------------------------------------ helpers
    def _btn(self, parent, text, command, row=None, col=None):
        b = tk.Button(parent, text=text, command=command, bg=theme.ACCENT_DARK,
                       fg="white", activebackground=theme.ACCENT, relief="flat")
        if row is None:
            b.pack(fill="x", pady=2)
        else:
            b.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        return b

    def _f(self, var, default=0.0):
        try:
            return float(var.get())
        except ValueError:
            return default

    def _move(self, direction):
        self.turtle.forward(direction * self._f(self.step))

    def _choose_color(self):
        color = colorchooser.askcolor(title="Cor da caneta")
        if color and color[1]:
            self.turtle.pencolor(color[1])

    def _reset(self):
        self.turtle.reset()
        self.turtle.shape("turtle")
        self.turtle.speed(6)

    def _help(self):
        messagebox.showinfo("Turtle Paint - ajuda", HELP_TEXT)

    # ------------------------------------------------------------ command interpreter
    def _run_commands(self):
        raw = self.cmd_box.get("1.0", "end").strip()
        for chunk in raw.replace(";", "\n").splitlines():
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split()
            cmd, args = parts[0].lower(), parts[1:]
            try:
                self._exec(cmd, args)
            except Exception as exc:
                messagebox.showerror("Turtle Paint", f"Erro em '{chunk}': {exc}")
                return

    def _exec(self, cmd, args):
        t = self.turtle
        if cmd in ("fd", "forward"):
            t.forward(float(args[0]))
        elif cmd in ("bk", "back", "backward"):
            t.backward(float(args[0]))
        elif cmd in ("rt", "right"):
            t.right(float(args[0]))
        elif cmd in ("lt", "left"):
            t.left(float(args[0]))
        elif cmd in ("pu", "penup", "up"):
            t.penup()
        elif cmd in ("pd", "pendown", "down"):
            t.pendown()
        elif cmd == "color":
            t.pencolor(args[0])
        elif cmd == "bgcolor":
            self.screen.bgcolor(args[0])
        elif cmd in ("width", "pensize"):
            t.pensize(float(args[0]))
        elif cmd == "circle":
            t.circle(float(args[0]))
        elif cmd == "goto":
            t.goto(float(args[0]), float(args[1]))
        elif cmd == "home":
            t.home()
        elif cmd == "speed":
            t.speed(int(args[0]))
        elif cmd == "clear":
            t.clear()
        elif cmd == "reset":
            self._reset()
        else:
            raise ValueError(f"comando desconhecido '{cmd}'")
