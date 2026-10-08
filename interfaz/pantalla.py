"""
Todo el dibujo y la lectura de teclado con curses.
La lógica del juego está en juego/partida.py; aquí solo se muestra.
"""
import curses
import time

from motores import MOTORES, CuadradoMedio
from juego.partida import Partida
from juego.piezas import FORMAS, ORDEN

FILAS_MIN, COLUMNAS_MIN = 24, 64
TICK_MS = 30

COLORES = {
    "I": curses.COLOR_CYAN, "O": curses.COLOR_YELLOW, "T": curses.COLOR_MAGENTA,
    "S": curses.COLOR_GREEN, "Z": curses.COLOR_RED, "J": curses.COLOR_BLUE,
    "L": curses.COLOR_WHITE,
}
PAR_FANTASMA = 20


def iniciar_colores():
    curses.start_color()
    curses.use_default_colors()
    for i, tipo in enumerate(ORDEN, start=1):
        curses.init_pair(i, curses.COLOR_BLACK, COLORES[tipo])
    curses.init_pair(PAR_FANTASMA, curses.COLOR_WHITE, -1)


def par(tipo):
    return curses.color_pair(ORDEN.index(tipo) + 1)


def escribir(win, y, x, texto, attr=0):
    """addstr que no revienta si el texto se sale de la ventana."""
    alto, ancho = win.getmaxyx()
    if 0 <= y < alto and x < ancho:
        try:
            win.addstr(y, x, texto[: ancho - x - 1], attr)
        except curses.error:
            pass


# ---------------- Dibujo ----------------

def dibujar_tablero(win, partida, y0, x0):
    t = partida.tablero
    for r in range(t.alto):
        escribir(win, y0 + r, x0, "│")
        escribir(win, y0 + r, x0 + 1 + t.ancho * 2, "│")
        for c in range(t.ancho):
            tipo = t.celdas[r][c]
            if tipo:
                escribir(win, y0 + r, x0 + 1 + c * 2, "  ", par(tipo))
            else:
                escribir(win, y0 + r, x0 + 1 + c * 2, " ·", curses.A_DIM)
    escribir(win, y0 + t.alto, x0, "└" + "──" * t.ancho + "┘")

    if partida.terminada:
        return
    p = partida.actual
    # Sombra: dónde caería la pieza
    for r, c in p.celdas(fila=partida.fila_fantasma()):
        escribir(win, y0 + r, x0 + 1 + c * 2, "[]", curses.color_pair(PAR_FANTASMA) | curses.A_DIM)
    for r, c in p.celdas():
        escribir(win, y0 + r, x0 + 1 + c * 2, "  ", par(p.tipo))


def dibujar_mini_pieza(win, tipo, y0, x0):
    for r, fila in enumerate(FORMAS[tipo]):
        for c, ocupada in enumerate(fila):
            if ocupada:
                escribir(win, y0 + r, x0 + c * 2, "  ", par(tipo))


def dibujar_panel(win, partida, y0, x0, pausado):
    m = partida.motor
    negrita = curses.A_BOLD
    escribir(win, y0, x0, "MOTOR ALEATORIO", negrita)
    escribir(win, y0 + 1, x0, f"[{partida.clave_motor}] {m.nombre}", curses.A_REVERSE)
    escribir(win, y0 + 2, x0, f"Semilla: {m.semilla_inicial}")
    if isinstance(m, CuadradoMedio):
        escribir(win, y0 + 3, x0, f"Re-siembras: {m.resiembras}")

    escribir(win, y0 + 5, x0, "Últimos números:", negrita)
    for i, valor in enumerate(list(m.historial)[-5:][::-1]):
        escribir(win, y0 + 6 + i, x0, f"  {valor}", 0 if i else negrita)

    pieza = partida.ultimo_sorteo.get("pieza")
    columna = partida.ultimo_sorteo.get("columna")
    if pieza:
        escribir(win, y0 + 12, x0, f"Próxima pieza: rango(7) -> {pieza[0]}")
    if columna:
        escribir(win, y0 + 13, x0, f"Columna:       rango(n) -> {columna[0]}")

    escribir(win, y0 + 15, x0, "Siguiente:", negrita)
    dibujar_mini_pieza(win, partida.siguiente_tipo, y0 + 16, x0 + 12)

    escribir(win, y0 + 19, x0, f"Líneas: {partida.lineas}   Piezas: {partida.piezas_colocadas}")
    escribir(win, y0 + 21, x0, "←→ mover  ↑ rotar  ↓ bajar  espacio soltar", curses.A_DIM)
    escribir(win, y0 + 22, x0, "1/2/3 cambiar motor   p pausa   q salir", curses.A_DIM)

    if pausado:
        escribir(win, y0 + 17, x0 + 22, " PAUSA ", curses.A_REVERSE | negrita)


def dibujar_fin(win, partida, y0, x0):
    lineas = ["  FIN DEL JUEGO  ", f"  Líneas: {partida.lineas:<7} ",
              "  r: reiniciar   ", "  q: salir       "]
    for i, texto in enumerate(lineas):
        escribir(win, y0 + 8 + i, x0 + 2, texto, curses.A_REVERSE | curses.A_BOLD)


def pantalla_pequena(win):
    win.erase()
    alto, ancho = win.getmaxyx()
    escribir(win, 0, 0, f"Agranda la terminal: mínimo {COLUMNAS_MIN}x{FILAS_MIN} "
                        f"(actual {ancho}x{alto}). q para salir.")
    win.refresh()


# ---------------- Menú y bucle principal ----------------

def menu(win):
    """Devuelve la clave del motor elegido, o None si el jugador sale."""
    while True:
        win.erase()
        escribir(win, 2, 4, "T E T R I S   —   Reto 2", curses.A_BOLD)
        escribir(win, 4, 4, "Elige el motor de números aleatorios:")
        for i, (clave, Motor) in enumerate(MOTORES.items()):
            escribir(win, 6 + i, 6, f"[{clave}] {Motor.nombre}")
        escribir(win, 10, 4, "Se puede cambiar durante la partida con 1, 2 y 3.", curses.A_DIM)
        escribir(win, 12, 4, "q para salir", curses.A_DIM)
        win.refresh()
        tecla = win.getch()
        if tecla == ord("q"):
            return None
        if tecla != -1 and chr(tecla) in MOTORES:
            return chr(tecla)


def jugar(win, clave_motor):
    """Devuelve True si el jugador pide reiniciar, False si sale."""
    partida = Partida(clave_motor)
    ultimo_paso = time.monotonic()
    pausado = False

    while True:
        alto, ancho = win.getmaxyx()
        if alto < FILAS_MIN or ancho < COLUMNAS_MIN:
            pantalla_pequena(win)
            if win.getch() == ord("q"):
                return False
            continue

        ahora = time.monotonic()
        if not (pausado or partida.terminada) and ahora - ultimo_paso >= partida.intervalo_caida:
            partida.bajar()
            ultimo_paso = ahora

        win.erase()
        dibujar_tablero(win, partida, 1, 2)
        dibujar_panel(win, partida, 1, 2 + partida.tablero.ancho * 2 + 5, pausado)
        if partida.terminada:
            dibujar_fin(win, partida, 1, 2)
        win.refresh()

        tecla = win.getch()
        if tecla == -1:
            continue
        if tecla == ord("q"):
            return False
        if partida.terminada:
            if tecla == ord("r"):
                return True
            continue
        if tecla == ord("p"):
            pausado = not pausado
            continue
        if pausado:
            continue

        if tecla == curses.KEY_LEFT:
            partida.mover(-1)
        elif tecla == curses.KEY_RIGHT:
            partida.mover(1)
        elif tecla == curses.KEY_UP:
            partida.rotar()
        elif tecla == curses.KEY_DOWN:
            partida.bajar()
            ultimo_paso = ahora
        elif tecla == ord(" "):
            partida.caida_dura()
            ultimo_paso = ahora
        elif chr(tecla) in MOTORES:
            partida.cambiar_motor(chr(tecla))


def principal(win):
    curses.curs_set(0)
    iniciar_colores()
    win.keypad(True)
    win.timeout(TICK_MS)   # getch() espera como máximo 30 ms: el juego no se congela
    while True:
        clave = menu(win)
        if clave is None:
            return
        while jugar(win, clave):
            pass