"""Ponto de entrada do TurtleOS.

Execute com:
    python3 main.py
"""

from turtleos.desktop import Desktop


def main():
    app = Desktop()
    app.mainloop()


if __name__ == "__main__":
    main()
  
