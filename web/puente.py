"""
Puente entre la interfaz web (JavaScript) y la lógica del juego (Python).

Cumple el mismo papel que interfaz/pantalla.py en la versión de terminal:
no contiene reglas, solo traduce. JavaScript llama a estas funciones y
recibe el estado como JSON para dibujarlo en el canvas.

Modo 1 jugador: nueva(), gravedad(), accion(), estado().
Modo 2 jugadores: nuevo_versus() y las mismas funciones con el número de
jugador (0 o 1); las reglas de quién gana están en juego/versus.py.
"""
import json

from motores import MOTORES, CuadradoMedio
from juego.config import VIDAS_INICIALES
from juego.partida import Partida
from juego.versus import Versus
from juego.piezas import FORMAS

partida = None      # modo 1 jugador
versus = None       # modo 2 jugadores


def motores():
    return json.dumps([{"clave": c, "nombre": M.nombre} for c, M in MOTORES.items()])


def nueva(clave):
    global partida
    partida = Partida(clave)


def gravedad():
    partida.paso_gravedad()


def _aplicar(p, nombre):
    """Las mismas acciones que el teclado de la versión de terminal."""
    if p.terminada:
        return
    if nombre == "izquierda":
        p.mover(-1)
    elif nombre == "derecha":
        p.mover(1)
    elif nombre == "rotar":
        p.rotar()
    elif nombre == "bajar":
        p.bajar()
    elif nombre == "soltar":
        p.caida_dura()
    elif nombre == "hardcore":
        p.alternar_hardcore()
    elif nombre in MOTORES:
        p.cambiar_motor(nombre)


def accion(nombre):
    _aplicar(partida, nombre)


def estado():
    return json.dumps(_estado(partida))


# ---------------- Modo 2 jugadores ----------------

def nuevo_versus(motor_1, motor_2):
    global versus
    versus = Versus(motor_1, motor_2)


def gravedad_jugador(i):
    versus.jugadores[i].paso_gravedad()
    versus.revisar()


def accion_jugador(i, nombre):
    _aplicar(versus.jugadores[i], nombre)
    versus.revisar()


def estado_versus():
    return json.dumps({
        "meta": versus.meta,
        "ganador": versus.ganador,
        "motivo": versus.motivo,
        "jugadores": [_estado(p) for p in versus.jugadores],
    })


def _estado(p):
    m = p.motor
    evento, p.evento = p.evento, None
    sonidos, p.sonidos = p.sonidos, []
    actual = fantasma = []
    if not p.terminada:
        actual = list(p.actual.celdas())
        fantasma = list(p.actual.celdas(fila=p.fila_fantasma()))
    return {
        "tablero": p.tablero.celdas,
        "ancho": p.tablero.ancho,
        "alto": p.tablero.alto,
        "pieza": {"tipo": p.actual.tipo, "celdas": actual},
        "fantasma": fantasma,
        "fila_limite": p.fila_limite,
        "siguiente": {"tipo": p.siguiente_tipo, "forma": FORMAS[p.siguiente_tipo]},
        "motor": {
            "clave": p.clave_motor,
            "nombre": m.nombre,
            "clase": type(m).__name__,
            # Como texto: Xoshiro256** entrega 64 bits y JavaScript solo
            # representa enteros exactos hasta 2^53; así se ven sin redondeo.
            "historial": [str(v) for v in list(m.historial)[-5:]],
            "semilla": str(m.semilla_inicial),
            "resiembras": m.resiembras if isinstance(m, CuadradoMedio) else None,
            "sorteo_pieza": p.ultimo_sorteo.get("pieza", [None])[0],
            "sorteo_columna": p.ultimo_sorteo.get("columna", [None])[0],
        },
        "nivel": p.nivel,
        "niveles": len(p.metas),
        "vidas": p.vidas,
        "vidas_max": VIDAS_INICIALES,
        "puntos": p.puntos,
        "puntos_nivel": p.puntos_nivel,
        "meta": p.meta_actual,
        "progreso": p.progreso,
        "lineas": p.lineas,
        "velocidad": p.multiplicador_velocidad,
        "intervalo": p.intervalo_caida,
        "zona": f"{p.filas_efectivas}x{p.tablero.ancho}",
        "hardcore": p.hardcore,
        "probabilidad_temblor": p.probabilidad_temblor,
        "ultimo_temblor": p.ultimo_temblor,
        "terminada": p.terminada,
        "ganada": p.ganada,
        "evento": evento,
        "sonidos": sonidos,
    }
