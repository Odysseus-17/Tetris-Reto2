"""
Puente entre la interfaz web (JavaScript) y la lógica del juego (Python).

Cumple el mismo papel que interfaz/pantalla.py en la versión de terminal:
no contiene reglas, solo traduce. JavaScript llama a estas funciones y
recibe el estado como JSON para dibujarlo en el canvas.
"""
import json

from motores import MOTORES, CuadradoMedio
from juego.config import VIDAS_INICIALES, METAS_NIVEL
from juego.partida import Partida
from juego.piezas import FORMAS

partida = None


def motores():
    return json.dumps([{"clave": c, "nombre": M.nombre} for c, M in MOTORES.items()])


def nueva(clave):
    global partida
    partida = Partida(clave)


def gravedad():
    partida.paso_gravedad()


def accion(nombre):
    """Las mismas acciones que el teclado de la versión de terminal."""
    if partida.terminada:
        return
    if nombre == "izquierda":
        partida.mover(-1)
    elif nombre == "derecha":
        partida.mover(1)
    elif nombre == "rotar":
        partida.rotar()
    elif nombre == "bajar":
        partida.bajar()
    elif nombre == "soltar":
        partida.caida_dura()
    elif nombre == "hardcore":
        partida.alternar_hardcore()
    elif nombre in MOTORES:
        partida.cambiar_motor(nombre)


def estado():
    p, m = partida, partida.motor
    evento, p.evento = p.evento, None
    sonidos, p.sonidos = p.sonidos, []
    actual = fantasma = []
    if not p.terminada:
        actual = list(p.actual.celdas())
        fantasma = list(p.actual.celdas(fila=p.fila_fantasma()))
    return json.dumps({
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
            "semilla": m.semilla_inicial,
            "historial": list(m.historial)[-5:],
            "resiembras": m.resiembras if isinstance(m, CuadradoMedio) else None,
            "sorteo_pieza": p.ultimo_sorteo.get("pieza", [None])[0],
            "sorteo_columna": p.ultimo_sorteo.get("columna", [None])[0],
        },
        "nivel": p.nivel,
        "niveles": len(METAS_NIVEL),
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
    })
