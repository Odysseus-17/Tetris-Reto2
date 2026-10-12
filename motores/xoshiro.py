"""
Xoshiro256** (David Blackman y Sebastiano Vigna, 2018).

Familia distinta a la de los otros motores: no usa multiplicaciones ni
módulos para avanzar el estado, solo operaciones de bits:
  XOR, SHIFT (desplazamiento) y ROtación  ->  "xoshiro".

  - Estado: 4 números de 64 bits (256 bits en total). Período 2^256 - 1.
  - Avance: se mezclan los 4 valores entre sí con XOR, un desplazamiento
    de 17 bits y una rotación de 45 bits.
  - Salida (el "**", star-star): rotl(s1 * 5, 7) * 9. Dos multiplicaciones
    que revuelven los bits para que la salida no delate el estado.

El estado no puede ser todo ceros (se quedaría en cero para siempre) y no
conviene sembrarlo con números "pobres" como 1, 2, 3, 4. Por eso los autores
recomiendan llenarlo con SplitMix64, un generador pequeño que convierte
una sola semilla en 4 valores bien mezclados.

Python usa enteros de precisión infinita, así que el "mod 2^64" se hace a mano
con una máscara: x & 0xFFFFFFFFFFFFFFFF.
"""
from .base import MotorAleatorio, semilla_por_reloj

MASCARA_64 = (1 << 64) - 1


def rotl(x, k):
    """Rotación a la izquierda de 64 bits: los bits que salen por la
    izquierda vuelven a entrar por la derecha."""
    return ((x << k) | (x >> (64 - k))) & MASCARA_64


def splitmix64(semilla):
    """Generador auxiliar (Vigna, 2015) usado solo para sembrar Xoshiro.
    Devuelve un iterador infinito de valores de 64 bits."""
    x = semilla & MASCARA_64
    while True:
        x = (x + 0x9E3779B97F4A7C15) & MASCARA_64
        z = x
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASCARA_64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASCARA_64
        yield z ^ (z >> 31)


class Xoshiro256(MotorAleatorio):
    nombre = "Xoshiro256**"
    MAXIMO = 2 ** 64          # entrega 64 bits por número, no 32

    def __init__(self, semilla=None, estado=None):
        if semilla is None:
            semilla = semilla_por_reloj()
        super().__init__(semilla)
        if estado is not None:
            # Estado dado a mano: solo para verificar contra la referencia.
            self.s = [v & MASCARA_64 for v in estado]
        else:
            sm = splitmix64(semilla)
            self.s = [next(sm) for _ in range(4)]
        if not any(self.s):
            raise ValueError("el estado de Xoshiro no puede ser todo ceros")

    def _generar(self):
        s = self.s
        resultado = (rotl((s[1] * 5) & MASCARA_64, 7) * 9) & MASCARA_64

        t = (s[1] << 17) & MASCARA_64
        s[2] ^= s[0]
        s[3] ^= s[1]
        s[1] ^= s[2]
        s[0] ^= s[3]
        s[2] ^= t
        s[3] = rotl(s[3], 45)
        return resultado
