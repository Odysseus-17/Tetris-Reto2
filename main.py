"""
Tetris en CLI — Reto 2.
Ejecutar desde la carpeta tetris/:  python3 main.py
"""
import curses
import locale
import os

from interfaz.pantalla import principal

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")      # para que curses dibuje los caracteres Unicode
    os.environ.setdefault("ESCDELAY", "25")  # evita el retraso de 1 s en algunas teclas
    curses.wrapper(principal)                # restaura la terminal aunque haya un error