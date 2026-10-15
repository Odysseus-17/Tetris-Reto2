"""
Todo el dibujo y la lectura de teclado con curses.
La lógica del juego está en juego/partida.py; aquí solo se muestra.
"""
import curses
import datetime
import time
from pathlib import Path

from motores import MOTORES, CuadradoMedio
from juego.config import VIDAS_INICIALES, METAS_NIVEL, LARGO_NOMBRE
from juego.partida import Partida
from juego.ranking import cargar_archivo, guardar_archivo, limpiar_nombre
from juego.piezas import FORMAS, ORDEN
from juego.tablero import MUERTO
from audio.reproductor import Audio

FILAS_MIN, COLUMNAS_MIN = 24, 64
TICK_MS = 30
DURACION_AVISO = 1.5     # segundos que se muestra "¡Nivel 2!" o "Perdiste una vida"
ANCHO_BARRA = 20
# La tabla de puntuaciones de la versión de terminal vive en datos/ranking.json
RUTA_RANKING = Path(__file__).resolve().parent.parent / "datos" / "ranking.json"

COLORES = {
    "I": curses.COLOR_CYAN, "O": curses.COLOR_YELLOW, "T": curses.COLOR_MAGENTA,
    "S": curses.COLOR_GREEN, "Z": curses.COLOR_RED, "J": curses.COLOR_BLUE,
    "L": curses.COLOR_WHITE,
}
PAR_FANTASMA, PAR_LIMITE, PAR_VIDA, PAR_MUERTO = 20, 21, 22, 23
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
    # Punto muerto: gris (color 244 con 256 colores; si no, blanco atenuado)
    gris = 244 if curses.COLORS >= 256 else curses.COLOR_WHITE
    curses.init_pair(PAR_MUERTO, curses.COLOR_BLACK, gris)

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
            if tipo == MUERTO:
                escribir(win, y0 + r, x0 + 1 + c * 2, "><", curses.color_pair(PAR_MUERTO))
            elif tipo:
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
    if partida.tablero_hardcore:
        n = partida.muertos_en_tablero
        escribir(win, y0 + 17, x0 + 20, "><", curses.color_pair(PAR_MUERTO))
        escribir(win, y0 + 17, x0 + 23, f"{n} punto{'s' if n != 1 else ''} muerto{'s' if n != 1 else ''}")
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
    escribir(win, y0 + 20, x0, "1-4 motor  t hardcore  p pausa  q salir", curses.A_DIM)

    if pausado:
        escribir(win, y0 + 17, x0, " PAUSA ", curses.A_REVERSE | negrita)


def dibujar_aviso(win, texto, y0, x0):
    escribir(win, y0 + 9, x0 + 2, f" {texto:^16} ", curses.A_REVERSE | curses.A_BOLD)


def dibujar_fin(win, partida, nombre, resultado, y0, x0):
    titulo = "¡GANASTE!" if partida.ganada else "FIN DEL JUEGO"
    puesto = resultado["puesto"]
    if resultado["error"]:
        texto_puesto = "No se guardó"
    else:
        texto_puesto = f"Puesto {puesto}" if puesto else "Fuera del top"
    lineas = [f"{titulo:^16}", f"{nombre[:16]:^16}", f"Puntos: {partida.puntos:<8}",
              f"Nivel:  {partida.nivel:<8}", f"{texto_puesto:^16}",
              "r: reiniciar    ", "q: menú         "]
    for i, texto in enumerate(lineas):
        escribir(win, y0 + 6 + i, x0 + 2, f" {texto} ", curses.A_REVERSE | curses.A_BOLD)


def dibujar_tabla(win, filas, y0, x0, resaltar=None):
    """Tabla de puntuaciones: #, nombre, nivel y puntos."""
    escribir(win, y0, x0, "TABLA DE PUNTUACIONES", curses.A_BOLD)
    if not filas:
        escribir(win, y0 + 2, x0, "Todavía no hay partidas.", curses.A_DIM)
        return
    escribir(win, y0 + 2, x0, f" #  {'Nombre':<{LARGO_NOMBRE}}  Nv  Puntos", curses.A_DIM)
    for i, f in enumerate(filas, start=1):
        marca = "*" if f.get("tablero_hardcore") else " "
        texto = f"{i:>2} {marca}{f['nombre']:<{LARGO_NOMBRE}}  {f['nivel']:>2}  {f['puntos']:>6}"
        attr = curses.A_REVERSE | curses.A_BOLD if i == resaltar else 0
        escribir(win, y0 + 2 + i, x0, texto, attr)
    escribir(win, y0 + 4 + len(filas), x0, "* tablero hardcore", curses.A_DIM)
    escribir(win, y0 + 5 + len(filas), x0, f"Guardada en datos/{RUTA_RANKING.name}", curses.A_DIM)


def registrar_resultado(partida, nombre):
    """Agrega la partida terminada al archivo y devuelve lo que hay que mostrar."""
    resultado = {"puesto": None, "filas": [], "error": False}
    ranking = cargar_archivo(RUTA_RANKING)
    resultado["puesto"] = ranking.agregar(nombre, partida.puntos, partida.nivel,
                                          partida.motor.nombre,
                                          datetime.date.today().isoformat(),
                                          partida.tablero_hardcore)
    resultado["filas"] = ranking.filas
    try:
        guardar_archivo(RUTA_RANKING, ranking)
    except OSError:
        resultado["error"] = True       # p. ej. carpeta de solo lectura: se muestra igual
    return resultado


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
        fila = 6 + len(MOTORES) + 1
        escribir(win, fila, 4, "En la partida: 1-4 cambian el motor,", curses.A_DIM)
        escribir(win, fila + 1, 4, "t activa el modo hardcore y m silencia el sonido.", curses.A_DIM)
        escribir(win, fila + 3, 4, "l ver la tabla de puntuaciones", curses.A_DIM)
        escribir(win, fila + 4, 4, "q para salir", curses.A_DIM)
        win.refresh()
        tecla = win.getch()
        if tecla == ord("q"):
            return None
        if tecla == ord("l"):
            ver_ranking(win)
        elif tecla != -1 and chr(tecla) in MOTORES:
            return chr(tecla)


def ver_ranking(win):
    filas = cargar_archivo(RUTA_RANKING).filas
    while True:
        win.erase()
        dibujar_tabla(win, filas, 2, 4)
        escribir(win, 2 + len(filas) + 6, 4, "cualquier tecla para volver", curses.A_DIM)
        win.refresh()
        if win.getch() != -1:
            return


def pedir_nombre(win, clave_motor, anterior):
    """Pide el nombre antes de la partida. Devuelve el nombre, o None si el
    jugador presiona Esc para volver al menú. Usa get_wch para aceptar tildes."""
    texto = anterior
    while True:
        win.erase()
        escribir(win, 2, 4, "T E T R I S   —   Reto 2", curses.A_BOLD)
        escribir(win, 4, 4, f"Motor: {MOTORES[clave_motor].nombre}")
        escribir(win, 6, 4, "¿Quién juega? Tu nombre para la tabla de puntuaciones:")
        escribir(win, 8, 6, f" {texto:<{LARGO_NOMBRE}} ", curses.A_REVERSE)
        escribir(win, 8, 7 + len(texto), "_" if len(texto) < LARGO_NOMBRE else "", curses.A_REVERSE | curses.A_BLINK)
        escribir(win, 10, 4, "Enter para jugar · Esc para volver", curses.A_DIM)
        win.refresh()
        try:
            tecla = win.get_wch()
        except curses.error:            # no se presionó nada en este ciclo
            continue
        if tecla in ("\n", "\r", curses.KEY_ENTER):
            return limpiar_nombre(texto)
        if tecla == "\x1b":
            return None
        if tecla in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            texto = texto[:-1]
        elif isinstance(tecla, str) and tecla.isprintable() and len(texto) < LARGO_NOMBRE:
            texto += tecla


def preguntar_tablero(win, nombre, anterior):
    """Después del nombre: ¿activar el modo tablero hardcore (puntos muertos)?
    Devuelve True o False, o None si el jugador presiona Esc."""
    elegido = anterior
    while True:
        win.erase()
        escribir(win, 2, 4, "T E T R I S   —   Reto 2", curses.A_BOLD)
        escribir(win, 4, 4, f"Jugador: {nombre}")
        escribir(win, 6, 4, "¿Activar modo tablero hardcore?", curses.A_BOLD)
        escribir(win, 8, 4, "Aparecen puntos muertos: casillas grises que flotan en el")
        escribir(win, 9, 4, "tablero. Las piezas se apoyan en ellos y se quedan ahí.")
        escribir(win, 10, 4, "3 en los niveles 1-3, 4 en el nivel 4 y 5 en el nivel 5;")
        escribir(win, 11, 4, "cambian de lugar al perder una vida o subir de nivel.")
        escribir(win, 13, 6, " [s] Sí, activar ", curses.A_REVERSE if elegido else 0)
        escribir(win, 14, 6, " [n] No, tablero normal ", 0 if elegido else curses.A_REVERSE)
        escribir(win, 16, 4, "s / n, o flechas y Enter · Esc para volver", curses.A_DIM)
        win.refresh()
        tecla = win.getch()
        if tecla in (ord("s"), ord("S")):
            return True
        if tecla in (ord("n"), ord("N")):
            return False
        if tecla in (curses.KEY_UP, curses.KEY_DOWN):
            elegido = not elegido
        elif tecla in (10, 13, curses.KEY_ENTER):
            return elegido
        elif tecla == 27:
            return None


def jugar(win, clave_motor, audio, nombre, tablero_hardcore=False):
    """Devuelve True si el jugador pide reiniciar, False si sale."""
    partida = Partida(clave_motor, tablero_hardcore=tablero_hardcore)
    resultado = None                    # se llena una sola vez, al terminar
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
        for sonido in partida.sonidos:
            audio.efecto(sonido)
        partida.sonidos.clear()
        if partida.terminada:
            audio.detener_musica()
            if resultado is None:
                resultado = registrar_resultado(partida, nombre)
        else:
            audio.musica_para(type(partida.motor), partida.motor.semilla_inicial, partida.nivel)

        if partida.evento:
            aviso = f"¡NIVEL {partida.nivel}!" if partida.evento == "nivel" else "¡Perdiste una vida!"
            aviso_hasta = ahora + DURACION_AVISO
            partida.evento = None

        x_panel = 2 + partida.tablero.ancho * 2 + 5
        win.erase()
        dibujar_tablero(win, partida, 1, 2)
        if partida.terminada:
            # Al terminar, el panel lateral muestra la tabla de puntuaciones
            dibujar_fin(win, partida, nombre, resultado, 1, 2)
            dibujar_tabla(win, resultado["filas"], 2, x_panel, resultado["puesto"])
        else:
            dibujar_panel(win, partida, 1, x_panel, pausado, audio)
        if not partida.terminada and aviso and ahora < aviso_hasta:
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
    nombre, tablero_hardcore = "", False
    try:
        while True:
            clave = menu(win)
            if clave is None:
                return
            nuevo = pedir_nombre(win, clave, nombre)
            if nuevo is None:           # Esc: volver al menú
                continue
            nombre = nuevo
            modo = preguntar_tablero(win, nombre, tablero_hardcore)
            if modo is None:            # Esc: volver al menú
                continue
            tablero_hardcore = modo
            # La revancha (r) repite el nombre y el modo
            while jugar(win, clave, audio, nombre, tablero_hardcore):
                pass
            audio.detener_musica()
    finally:
        audio.cerrar()