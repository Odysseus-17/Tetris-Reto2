"""
Puente del audio para la interfaz web. Se ejecuta dentro de un Web Worker
(un hilo aparte del navegador), igual que el mezclador de la versión de
terminal corre en un hilo aparte: componer la música tarda alrededor de
un segundo y así el juego no se congela.

Usa los mismos módulos audio/efectos.py y audio/musica.py; lo único que
cambia es quién reproduce las muestras: el navegador en vez de paplay/aplay.
"""
from array import array

from motores import MOTORES
from audio.efectos import crear_efectos
from audio import musica
from audio.sintetizador import TASA

_efectos = None
descripcion = ""        # tonalidad y tempo de la última música compuesta


def _a_bytes(muestras):
    """Lista de floats -> bytes de float32, que JavaScript convierte en
    Float32Array sin copiar número por número."""
    return array("f", muestras).tobytes()


def nombres_efectos():
    global _efectos
    _efectos = crear_efectos()
    return list(_efectos)


def efecto(nombre):
    return _a_bytes(_efectos[nombre])


def componer(clave, semilla, nivel):
    global descripcion
    muestras, descripcion, _ = musica.generar(MOTORES[clave], int(semilla), int(nivel))
    return _a_bytes(muestras)


def ultima_descripcion():
    return descripcion


def tasa():
    return TASA
