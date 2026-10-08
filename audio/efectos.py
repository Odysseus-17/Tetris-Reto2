"""
Efectos de sonido del juego, todos calculados con el sintetizador.
Se generan una sola vez al iniciar (tardan milisegundos) y quedan en memoria.
"""
from motores import CongruencialLineal
from .sintetizador import (tono, ruido, concatenar, mezclar, silencio,
                           midi_a_frecuencia as hz)


def _arpegio(notas, duracion_nota, onda="cuadrada", volumen=0.22, ciclo=0.5):
    """Notas MIDI tocadas una tras otra."""
    return concatenar(*(tono(hz(n), duracion_nota, onda, volumen, ciclo=ciclo,
                             liberacion=duracion_nota * 0.4) for n in notas))


def crear_efectos():
    # El ruido usa el LCG con semilla fija: el sonido es siempre el mismo
    motor_ruido = CongruencialLineal(semilla=2024)
    efectos = {
        # Movimiento lateral: un "tic" muy corto y agudo
        "mover": tono(880, 0.03, "cuadrada", 0.10, ciclo=0.25, liberacion=0.02),

        # Rotación: barrido corto hacia arriba
        "rotar": tono(500, 0.07, "cuadrada", 0.12, frecuencia_final=900,
                      ciclo=0.25, liberacion=0.03),

        # Temblor del modo hardcore: un "bwip" grave que tiembla
        "temblor": tono(220, 0.08, "triangular", 0.25, frecuencia_final=150),

        # La pieza toca fondo: golpe (ruido) + tono grave
        "fijar": mezclar(ruido(0.06, motor_ruido, 0.10, liberacion=0.05),
                         tono(110, 0.10, "seno", 0.35, frecuencia_final=70)),

        # Subir de nivel: arpegio largo ascendente
        "nivel": _arpegio([72, 76, 79, 84, 88, 91, 96], 0.07, volumen=0.2),

        # Perder una vida: barrido largo hacia abajo
        "vida": tono(600, 0.45, "cuadrada", 0.15, frecuencia_final=120, ciclo=0.25,
                     liberacion=0.1),

        # Fin del juego: tres notas que bajan y la última larga
        "fin": concatenar(_arpegio([67, 64, 60], 0.18, "triangular", 0.35),
                          tono(hz(48), 0.6, "triangular", 0.35, liberacion=0.4)),

        # Victoria: fanfarria
        "victoria": concatenar(_arpegio([72, 72, 72], 0.09), silencio(0.04),
                               _arpegio([76, 79], 0.12),
                               tono(hz(84), 0.6, "cuadrada", 0.22, liberacion=0.4)),
    }
    # Líneas completadas: Do-Mi-Sol, una nota más por cada línea extra.
    # 4 líneas a la vez (un "tetris") llega hasta el Do de arriba con brillo.
    escala = [72, 76, 79, 84, 88]
    for n in range(1, 5):
        efectos[f"linea{n}"] = _arpegio(escala[: n + 1], 0.06, volumen=0.2, ciclo=0.25)
    return efectos