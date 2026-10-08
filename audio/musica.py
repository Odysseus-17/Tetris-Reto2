"""
Música procedural: la melodía la decide el motor de números aleatorios,
pero con reglas que garantizan que nunca suene disonante.

  1. Escala pentatónica: el motor elige POSICIONES dentro de 5 notas que
     no tienen semitonos entre sí (Do Re Mi Sol La), nunca frecuencias.
  2. Movimiento por pasos: el motor elige cuánto se mueve la melodía
     (subir 1, bajar 1, saltar 2, repetir), no a qué nota salta.
  3. Acordes fijos con anclaje: debajo suena Do - Lam - Fa - Sol, y en el
     primer tiempo de cada compás la melodía cae en una nota del acorde.
  4. Ritmo cerrado: cada tiempo es una negra o dos corcheas, así los
     compases siempre quedan completos.

Cada nivel sube la tonalidad un tono y el tempo 10 bpm.
"""
from .sintetizador import tono, secuencia, midi_a_frecuencia as hz

PENTATONICA = (0, 2, 4, 7, 9)                 # semitonos sobre la tónica
NOMBRES = ("Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si")

# Progresión I - vi - IV - V: (fundamental, notas del acorde), en semitonos
PROGRESION = (
    (0, {0, 4, 7}),     # Do mayor
    (9, {9, 0, 4}),     # La menor
    (5, {5, 9, 0}),     # Fa mayor
    (7, {7, 11, 2}),    # Sol mayor
)
COMPASES = 8
TIEMPOS_POR_COMPAS = 4

# rango(10) -> paso en la escala. Pasos pequeños son más probables.
PASOS = (1, 1, 1, -1, -1, -1, 2, -2, 0, 0)    # 20 % repetir, 60 % paso, 20 % salto


def _escala(transposicion):
    """Notas MIDI de dos octavas de la pentatónica, desde Do4 (60)."""
    base = 60 + transposicion
    notas = [base + 12 * octava + s for octava in range(2) for s in PENTATONICA]
    return notas + [base + 24]                  # 11 notas: índices 0..10


def componer(motor, nivel):
    """Devuelve (melodía, bajo, descripción). Melodía y bajo son listas de
    (tiempo_inicio, duración_en_tiempos, nota_midi)."""
    transposicion = 2 * (nivel - 1)
    bpm = 100 + 10 * (nivel - 1)
    escala = _escala(transposicion)
    indice = 5                                  # empezar en el centro (Do5)
    repeticiones = 0
    melodia, bajo = [], []

    for compas in range(COMPASES):
        fundamental, acorde = PROGRESION[compas % len(PROGRESION)]
        inicio_compas = compas * TIEMPOS_POR_COMPAS

        # Bajo: fundamental en el tiempo 1 y quinta en el tiempo 3
        nota_bajo = 48 + transposicion + fundamental
        bajo.append((inicio_compas, 2, nota_bajo))
        bajo.append((inicio_compas + 2, 2, nota_bajo + 7))

        for tiempo in range(TIEMPOS_POR_COMPAS):
            # Regla 4: negra (60 %) o dos corcheas (40 %)
            duraciones = (1,) if motor.rango(10) < 6 else (0.5, 0.5)
            t = inicio_compas + tiempo
            for k, dur in enumerate(duraciones):
                if tiempo == 0 and k == 0:
                    # Regla 3: anclar a la nota del acorde más cercana
                    candidatos = [i for i, n in enumerate(escala)
                                  if (n - transposicion) % 12 in acorde]
                    indice = min(candidatos, key=lambda i: abs(i - indice))
                else:
                    # Regla 2: el motor decide el paso
                    paso = PASOS[motor.rango(len(PASOS))]
                    if paso == 0 and repeticiones >= 1:
                        paso = 1 if indice < 5 else -1   # máximo dos notas iguales seguidas
                    repeticiones = repeticiones + 1 if paso == 0 else 0
                    indice += paso
                    if indice < 0:                    # rebotar en los bordes
                        indice = -indice
                    elif indice >= len(escala):
                        indice = 2 * (len(escala) - 1) - indice
                melodia.append((t, dur, escala[indice]))
                t += dur

    descripcion = f"{NOMBRES[transposicion % 12]} mayor · {bpm} bpm"
    return melodia, bajo, descripcion, bpm


def nombre_nota(midi):
    return f"{NOMBRES[midi % 12]}{midi // 12 - 1}"


def renderizar(melodia, bajo, bpm):
    """Convierte las notas en muestras de audio."""
    seg_tiempo = 60 / bpm
    eventos = []
    for inicio, dur, nota in melodia:
        d = dur * seg_tiempo * 0.9               # 10 % de silencio entre notas
        eventos.append((inicio * seg_tiempo,
                        tono(hz(nota), d, "cuadrada", 0.07, ciclo=0.25, liberacion=0.04)))
    for inicio, dur, nota in bajo:
        d = dur * seg_tiempo * 0.95
        eventos.append((inicio * seg_tiempo,
                        tono(hz(nota), d, "triangular", 0.18, liberacion=0.06)))
    total = COMPASES * TIEMPOS_POR_COMPAS * seg_tiempo
    return secuencia(eventos, total)


def generar(clase_motor, semilla, nivel):
    """Crea un motor PROPIO para la música (con la misma semilla de la partida
    más el nivel), para no consumir números del motor que reparte las piezas."""
    motor = clase_motor(semilla=semilla + nivel * 1000003)
    melodia, bajo, descripcion, bpm = componer(motor, nivel)
    return renderizar(melodia, bajo, bpm), descripcion, melodia