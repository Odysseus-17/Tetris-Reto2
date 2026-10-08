"""
Síntesis de audio procedural: los sonidos se CALCULAN muestra por muestra
con fórmulas, en vez de cargarlos desde archivos .wav o .mp3.

Un sonido digital es una lista de números entre -1 y 1 (muestras). Se toman
TASA muestras por segundo; con 22050 por segundo, 1 segundo = 22050 números.
"""
import io
import math
import sys
import wave
from array import array

TASA = 22050   # muestras por segundo (calidad suficiente para un juego retro)


def midi_a_frecuencia(nota):
    """Nota MIDI -> Hz. La 69 es el La de 440 Hz y cada semitono multiplica
    la frecuencia por 2^(1/12); 12 semitonos = una octava = el doble."""
    return 440.0 * 2 ** ((nota - 69) / 12)


# ---------------- Formas de onda ----------------
# Cada función recibe la fase (0 a 1 dentro de un ciclo) y devuelve -1..1.

def seno(fase):
    return math.sin(2 * math.pi * fase)


def cuadrada(fase, ciclo=0.5):
    """Sonido "chiptune" de consolas de 8 bits. 'ciclo' es la fracción del
    período en que la onda está arriba; 0.25 suena más nasal que 0.5."""
    return 1.0 if fase < ciclo else -1.0


def triangular(fase):
    """Más suave que la cuadrada; la usaba la NES para los bajos."""
    return 4 * fase - 1 if fase < 0.5 else 3 - 4 * fase


ONDAS = {"seno": seno, "cuadrada": cuadrada, "triangular": triangular}


def tono(frecuencia, duracion, onda="cuadrada", volumen=0.3,
         ataque=0.005, liberacion=0.03, frecuencia_final=None, ciclo=0.5):
    """Genera un tono. Si se da frecuencia_final, la frecuencia se desliza
    linealmente (barrido), como el "piu" de los efectos retro.

    La envolvente sube el volumen durante 'ataque' segundos y lo baja durante
    'liberacion' segundos; sin ella, cortar la onda de golpe produce un "clic"."""
    n = int(duracion * TASA)
    funcion = ONDAS[onda]
    f_final = frecuencia if frecuencia_final is None else frecuencia_final
    n_ataque = max(1, int(ataque * TASA))
    n_liberacion = max(1, int(liberacion * TASA))
    muestras = [0.0] * n
    fase = 0.0
    for i in range(n):
        f = frecuencia + (f_final - frecuencia) * i / n
        fase = (fase + f / TASA) % 1.0          # la fase acumula ciclos
        if onda == "cuadrada":
            valor = cuadrada(fase, ciclo)
        else:
            valor = funcion(fase)
        env = min(1.0, i / n_ataque, (n - i) / n_liberacion)
        muestras[i] = valor * env * volumen
    return muestras


def ruido(duracion, motor, volumen=0.2, liberacion=None):
    """Ruido blanco (el "chhh" de un golpe). Sin librerías aleatorias:
    las muestras salen de uno de los motores del juego."""
    n = int(duracion * TASA)
    liberacion = n if liberacion is None else int(liberacion * TASA)
    salida = []
    for i in range(n):
        valor = motor.rango(2001) / 1000 - 1         # -1 .. 1
        env = min(1.0, (n - i) / liberacion)
        salida.append(valor * env * volumen)
    return salida


def silencio(duracion):
    return [0.0] * int(duracion * TASA)


def concatenar(*partes):
    salida = []
    for parte in partes:
        salida.extend(parte)
    return salida


def mezclar(*pistas):
    """Suma varias pistas muestra a muestra (sonidos al mismo tiempo)."""
    largo = max(len(p) for p in pistas)
    salida = [0.0] * largo
    for pista in pistas:
        for i, v in enumerate(pista):
            salida[i] += v
    return salida


def secuencia(eventos, duracion_total):
    """eventos: lista de (inicio_seg, muestras). Coloca cada sonido en su
    instante dentro de una pista de duracion_total segundos."""
    pista = [0.0] * int(duracion_total * TASA)
    for inicio, muestras in eventos:
        desde = int(inicio * TASA)
        for i, v in enumerate(muestras):
            if desde + i < len(pista):
                pista[desde + i] += v
    return pista


# ---------------- Conversión a bytes ----------------

def a_pcm16(muestras):
    """Lista de -1..1 -> bytes en formato PCM de 16 bits con signo,
    little-endian, que es lo que esperan aplay, paplay y pw-play."""
    datos = array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in muestras))
    if sys.byteorder != "little":
        datos.byteswap()
    return datos.tobytes()


def guardar_wav(ruta, muestras):
    """Solo para la demostración: guarda un sonido como archivo .wav."""
    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(TASA)
        archivo.writeframes(a_pcm16(muestras))