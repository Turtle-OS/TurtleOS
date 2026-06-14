"""Jogos do TurtleOS: Jogo da Velha e Snake."""

import random

import tkinter as tk

from .. import theme


# =================================================================== Jogo da Velha
class TicTacToeApp(tk.Toplevel):
    WINS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]

    def __init__(self, master):
        super().__init__(master)
        self.title("⭕ Jogo da Velha - TurtleOS")
        self.resizable(False, False)
        self.configure(bg=theme.BG_WINDOW)

        self.board = [""] * 9
        self.turn = "X"
        self.buttons = []

        self.status = tk.Label(self, text="Vez de: X", bg=theme.BG_WINDOW,
                                fg=theme.ACCENT, font=theme.FONT_TITLE)
        self.status.grid(row=0, column=0, columnspan=3, pady=8)

        grid = tk.Frame(self, bg=theme.BG_WINDOW)
        grid.grid(row=1, column=0, columnspan=3)
        for i in range(9):
            b = tk.Button(
                grid, text="", width=6, height=3, font=("Segoe UI", 18, "bold"),
                bg="#222222", fg=theme.ACCENT, activebackground="#333333",
                command=lambda i=i: self._click(i),
            )
            b.grid(row=i // 3, column=i % 3, padx=2, pady=2)
            self.buttons.append(b)

        tk.Button(self, text="Recomecar", command=self._restart,
                  bg=theme.ACCENT_DARK, fg="white", relief="flat")\
            .grid(row=2, column=0, columnspan=3, pady=8, sticky="ew", padx=8)

    def _click(self, i):
        if self.board[i] or self._winner():
            return
        self.board[i] = self.turn
        self.buttons[i].config(text=self.turn)
        winner = self._winner()
        if winner:
            self.status.config(text=f"{winner} venceu! 🎉")
            return
        if "" not in self.board:
            self.status.config(text="Empate!")
            return
        self.turn = "O" if self.turn == "X" else "X"
        self.status.config(text=f"Vez de: {self.turn}")

    def _winner(self):
        for a, b, c in self.WINS:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def _restart(self):
        self.board = [""] * 9
        self.turn = "X"
        for b in self.buttons:
            b.config(text="")
        self.status.config(text="Vez de: X")


# =================================================================== Snake
class SnakeApp(tk.Toplevel):
    CELL = 20
    COLS = 24
    ROWS = 18

    def __init__(self, master):
        super().__init__(master)
        self.title("🐍 Snake - TurtleOS")
        self.resizable(False, False)
        self.configure(bg=theme.BG_WINDOW)

        w, h = self.COLS * self.CELL, self.ROWS * self.CELL
        self.canvas = tk.Canvas(self, width=w, height=h, bg="#0b0f0c",
                                 highlightthickness=0)
        self.canvas.pack(padx=8, pady=(8, 0))

        self.info = tk.Label(self, text="Pontos: 0  |  use as setas do teclado",
                              bg=theme.BG_WINDOW, fg=theme.FG_TEXT)
        self.info.pack(pady=6)

        self.bind("<Key>", self._on_key)
        self.after(100, self._claim_focus)

        self._start()

    def _claim_focus(self):
        self.focus_force()

    def _start(self):
        self.snake = [(5, 5), (4, 5), (3, 5)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self._new_food()
        self.score = 0
        self.running = True
        self.info.config(text="Pontos: 0  |  use as setas do teclado")
        self._tick()

    def _new_food(self):
        while True:
            pos = (random.randint(0, self.COLS - 1), random.randint(0, self.ROWS - 1))
            if pos not in self.snake:
                return pos

    def _on_key(self, event):
        key = event.keysym
        mapping = {
            "Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0),
            "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
        }
        if key in mapping:
            dx, dy = mapping[key]
            cx, cy = self.direction
            # impede virar 180 graus diretamente
            if (dx, dy) != (-cx, -cy):
                self.next_direction = (dx, dy)
        elif key == "space" and not self.running:
            self._start()

    def _tick(self):
        if not self.running:
            return
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.COLS, (head_y + dy) % self.ROWS)

        if new_head in self.snake:
            self._game_over()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.food = self._new_food()
        else:
            self.snake.pop()

        self._draw()
        self.after(110, self._tick)

    def _draw(self):
        c = self.canvas
        c.delete("all")
        fx, fy = self.food
        c.create_rectangle(fx * self.CELL, fy * self.CELL,
                            (fx + 1) * self.CELL, (fy + 1) * self.CELL,
                            fill="#ff5252", outline="")
        for i, (x, y) in enumerate(self.snake):
            color = theme.ACCENT if i == 0 else theme.ACCENT_DARK
            c.create_rectangle(x * self.CELL, y * self.CELL,
                                (x + 1) * self.CELL, (y + 1) * self.CELL,
                                fill=color, outline="#0b0f0c")
        self.info.config(text=f"Pontos: {self.score}  |  use as setas do teclado")

    def _game_over(self):
        self.running = False
        self.canvas.create_text(
            self.COLS * self.CELL // 2, self.ROWS * self.CELL // 2,
            text=f"Fim de jogo! Pontos: {self.score}\nPressione ESPACO para jogar de novo",
            fill="white", font=theme.FONT_UI_BOLD, justify="center",
        )
