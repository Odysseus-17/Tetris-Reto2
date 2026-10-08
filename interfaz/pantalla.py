"""
Todo el dibujo y la lectura de teclado con curses.
La lógica del juego está en juego/partida.py; aquí solo se muestra.
"""
import curses
import time

from motores import MOTORES, CuadradoMedio
from juego.config import VIDAS_INICIALES, METAS_NIVEL
from juego.partida import Partida
from juego.piezas import FORMAS, ORDEN
from audio.reproductor import Audio

FILAS_MIN, COLUMNAS_MIN = 24, 64
TICK_MS = 30
DURACION_AVISO = 1.5     # segundos que se muestra "¡Nivel 2!" o "Perdiste una vida"
ANCHO_BARRA = 20

COLORES = {
    "I": curses.COLOR_CYAN, "O": curses.COLOR_YELLOW, "T": curses.COLOR_MAGENTA,
    "S": curses.COLOR_GREEN, "Z": curses.COLOR_RED, "J": curses.COLOR_BLUE,
    "L": curses.COLOR_WHITE,
}
PAR_FANTASMA, PAR_LIMITE, PAR_VIDA = 20, 21, 22
PAR_BARRA_INICIO = 30    # pares 30.. para el degradado de la barra
pares_barra = []


def iniciar_colores():
    curses.start_color()
    curses.use_default_colors()
    for i, tipo in enumerate(ORDEN, start=1):
        curses.init_pair(i, curses.COLOR_BLACK, COLORES[tipo])
    curses.init_pair(PAR_FANTASMA, curses.COLOR_WHITE, -1)
    curses.init_pair(PAR_LIMITE, curses.COLOR_BLUE, -1)
    curses.init_pair(PAR_VIDA, curses.COLOR_RED, -1)

    # Degradado azul -> rojo. Con 256 colores se usa el cubo 6x6x6 de xterm:
    # índice = 16 + 36·rojo + 6·verde + azul, con cada componente de 0 a 5.
    if curses.COLORS >= 256:
        tonos = [16 + 36 * r + (5 - r) for r in range(6)]   # 21 (azul) ... 196 (rojo)
    else:
        tonos = [curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_RED]
    for i, tono in enumerate(tonos):
        curses.init_pair(PAR_BARRA_INICIO + i, tono, -1)
        pares_barra.append(curses.color_pair(PAR_BARRA_INICIO + i))


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
    limite = partida.fila_limite
    for r in range(t.alto):
        escribir(win, y0 + r, x0, "│")
        escribir(win, y0 + r, x0 + 1 + t.ancho * 2, "│")
        for c in range(t.ancho):
            tipo = t.celdas[r][c]
            if tipo:
                escribir(win, y0 + r, x0 + 1 + c * 2, "  ", par(tipo))
            elif r == limite - 1:
                # Línea limitadora azul: justo encima de la primera fila jugable
                escribir(win, y0 + r, x0 + 1 + c * 2, "━━",
                         curses.color_pair(PAR_LIMITE) | curses.A_BOLD)
            elif r < limite:
                escribir(win, y0 + r, x0 + 1 + c * 2, "  ")      # zona prohibida
            else:
                escribir(win, y0 + r, x0 + 1 + c * 2, " ·", curses.A_DIM)
    escribir(win, y0 + t.alto, x0, "└" + "──" * t.ancho + "┘")

    if partida.terminada:
        return
    p = partida.actual
    for r, c in p.celdas(fila=partida.fila_fantasma()):
        escribir(win, y0 + r, x0 + 1 + c * 2, "[]", curses.color_pair(PAR_FANTASMA) | curses.A_DIM)
    for r, c in p.celdas():
        escribir(win, y0 + r, x0 + 1 + c * 2, "  ", par(p.tipo))


def dibujar_mini_pieza(win, tipo, y0, x0):
    for r, fila in enumerate(FORMAS[tipo]):
        for c, ocupada in enumerate(fila):
            if ocupada:
                escribir(win, y0 + r, x0 + c * 2, "  ", par(tipo))


def dibujar_barra(win, y, x, progreso):
    """Barra horizontal: cada segmento toma su color según su posición,
    así la parte llena va del azul (inicio) al rojo (final)."""
    llenos = round(progreso * ANCHO_BARRA)
    for i in range(ANCHO_BARRA):
        if i < llenos:
            color = pares_barra[i * len(pares_barra) // ANCHO_BARRA]
            escribir(win, y, x + i, "█", color)
        else:
            escribir(win, y, x + i, "░", curses.A_DIM)
    escribir(win, y, x + ANCHO_BARRA + 1, f"{progreso * 100:3.0f}%")


def dibujar_panel(win, partida, y0, x0, pausado, audio):
    m = partida.motor
    negrita = curses.A_BOLD

    # --- Motor ---
    escribir(win, y0, x0, f"MOTOR [{partida.clave_motor}] {m.nombre}", curses.A_REVERSE)
    extra = f"   Re-siembras: {m.resiembras}" if isinstance(m, CuadradoMedio) else ""
    escribir(win, y0 + 1, x0, f"Semilla: {m.semilla_inicial}{extra}")
    escribir(win, y0 + 2, x0, "Últimos números:")
    for i, valor in enumerate(list(m.historial)[-3:][::-1]):
        escribir(win, y0 + 3 + i, x0 + 2, str(valor), 0 if i else negrita)
    pieza = partida.ultimo_sorteo.get("pieza")
    columna = partida.ultimo_sorteo.get("columna")
    if pieza:
        escribir(win, y0 + 6, x0, f"Próxima pieza: rango(7) -> {pieza[0]}")
    if columna:
        escribir(win, y0 + 7, x0, f"Columna:       rango(n) -> {columna[0]}")

    # --- Progreso ---
    escribir(win, y0 + 9, x0, f"NIVEL {partida.nivel}/{len(METAS_NIVEL)}", negrita)
    corazones = "♥" * partida.vidas + "♡" * (VIDAS_INICIALES - partida.vidas)
    escribir(win, y0 + 9, x0 + 14, "Vidas ")
    escribir(win, y0 + 9, x0 + 20, corazones, curses.color_pair(PAR_VIDA) | negrita)
    escribir(win, y0 + 10, x0, f"Puntos del nivel: {partida.puntos_nivel} / {partida.meta_actual}")
    dibujar_barra(win, y0 + 11, x0, partida.progreso)
    escribir(win, y0 + 12, x0, f"Total: {partida.puntos}   Líneas: {partida.lineas}")
    escribir(win, y0 + 13, x0, f"Velocidad: x{partida.multiplicador_velocidad:.2f}   "
                               f"Zona: {partida.filas_efectivas}x{partida.tablero.ancho}")

    if partida.hardcore:
        flecha = ""
        if partida.ultimo_temblor:
            d, tirada, se_movio = partida.ultimo_temblor
            flecha = f"  último: {'←' if d < 0 else '→'}{'' if se_movio else ' (bloq.)'}"
        escribir(win, y0 + 14, x0, f"HARDCORE {partida.probabilidad_temblor}%{flecha}",
                 curses.color_pair(PAR_VIDA) | negrita)
    else:
        escribir(win, y0 + 14, x0, "Hardcore: apagado (t)", curses.A_DIM)

    # --- Siguiente pieza ---
    escribir(win, y0 + 15, x0, "Siguiente:", negrita)
    dibujar_mini_pieza(win, partida.siguiente_tipo, y0 + 15, x0 + 12)

    # --- Sonido ---
    if not audio.disponible:
        texto_audio = "Sonido: no disponible"
    elif audio.silenciado:
        texto_audio = "♪ silenciado   (m activar)"
    else:
        texto_audio = f"♪ {audio.info_musica or 'componiendo...'}   (m silenciar)"
    escribir(win, y0 + 18, x0, texto_audio, curses.A_DIM if audio.silenciado else 0)

    escribir(win, y0 + 19, x0, "←→ mover  ↑ rotar  ↓ bajar  espacio soltar", curses.A_DIM)
    escribir(win, y0 + 20, x0, "1/2/3 motor  t hardcore  p pausa  q salir", curses.A_DIM)

    if pausado:
        escribir(win, y0 + 17, x0, " PAUSA ", curses.A_REVERSE | negrita)


def dibujar_aviso(win, texto, y0, x0):
    escribir(win, y0 + 9, x0 + 2, f" {texto:^16} ", curses.A_REVERSE | curses.A_BOLD)


def dibujar_fin(win, partida, y0, x0):
    titulo = "¡GANASTE!" if partida.ganada else "FIN DEL JUEGO"
    lineas = [f"{titulo:^16}", f"Puntos: {partida.puntos:<8}",
              f"Nivel:  {partida.nivel:<8}", "r: reiniciar    ", "q: salir        "]
    for i, texto in enumerate(lineas):
        escribir(win, y0 + 7 + i, x0 + 2, f" {texto} ", curses.A_REVERSE | curses.A_BOLD)


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
        escribir(win, 10, 4, "En la partida: 1, 2, 3 cambian el motor,", curses.A_DIM)
        escribir(win, 11, 4, "t activa el modo hardcore y m silencia el sonido.", curses.A_DIM)
        escribir(win, 13, 4, "q para salir", curses.A_DIM)
        win.refresh()
        tecla = win.getch()
        if tecla == ord("q"):
            return None
        if tecla != -1 and chr(tecla) in MOTORES:
            return chr(tecla)


def jugar(win, clave_motor, audio):
    """Devuelve True si el jugador pide reiniciar, False si sale."""
    partida = Partida(clave_motor)
    ultimo_paso = time.monotonic()
    pausado = False
    audio.pausado = False
    aviso, aviso_hasta = None, 0.0

    while True:
        alto, ancho = win.getmaxyx()
        if alto < FILAS_MIN or ancho < COLUMNAS_MIN:
            pantalla_pequena(win)
            if win.getch() == ord("q"):
                return False
            continue

        ahora = time.monotonic()
        if not (pausado or partida.terminada) and ahora - ultimo_paso >= partida.intervalo_caida:
            partida.paso_gravedad()
            ultimo_paso = ahora

        # Sonido: efectos pendientes y música según motor y nivel
        for nombre in partida.sonidos:
            audio.efecto(nombre)
        partida.sonidos.clear()
        if partida.terminada:
            audio.detener_musica()
        else:
            audio.musica_para(type(partida.motor), partida.motor.semilla_inicial, partida.nivel)

        if partida.evento:
            aviso = f"¡NIVEL {partida.nivel}!" if partida.evento == "nivel" else "¡Perdiste una vida!"
            aviso_hasta = ahora + DURACION_AVISO
            partida.evento = None

        x_panel = 2 + partida.tablero.ancho * 2 + 5
        win.erase()
        dibujar_tablero(win, partida, 1, 2)
        dibujar_panel(win, partida, 1, x_panel, pausado, audio)
        if partida.terminada:
            dibujar_fin(win, partida, 1, 2)
        elif aviso and ahora < aviso_hasta:
            dibujar_aviso(win, aviso, 1, 2)
        win.refresh()

        tecla = win.getch()
        if tecla == -1:
            continue
        if tecla == ord("q"):
            return False
        if tecla in (ord("m"), ord("M")):
            audio.alternar_silencio()
            continue
        if partida.terminada:
            if tecla == ord("r"):
                return True
            continue
        if tecla == ord("p"):
            pausado = not pausado
            audio.pausado = pausado
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
        elif tecla in (ord("t"), ord("T")):
            partida.alternar_hardcore()
        elif chr(tecla) in MOTORES:
            partida.cambiar_motor(chr(tecla))


def principal(win):
    curses.curs_set(0)
    iniciar_colores()
    win.keypad(True)
    win.timeout(TICK_MS)   # getch() espera como máximo 30 ms: el juego no se congela
    audio = Audio()
    try:
        while True:
            clave = menu(win)
            if clave is None:
                return
            while jugar(win, clave, audio):
                pass
            audio.detener_musica()
    finally:
        audio.cerrar()