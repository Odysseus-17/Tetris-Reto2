"""
PCG32 — Permuted Congruential Generator (Melissa O'Neill, 2014), variante XSH-RR.

Dos etapas:
  1. Un LCG de 64 bits avanza el estado interno (igual al motor congruencial,
     pero con m = 2^64).
  2. El estado NO se entrega directamente: se "permuta" (xorshift + rotación)
     para producir una salida de 32 bits de mucha mejor calidad.

Python usa enteros de precisión infinita, así que el "mod 2^64" se hace a mano
con una máscara: x & 0xFFFFFFFFFFFFFFFF.
"""
from .base import MotorAleatorio, semilla_por_reloj

MASCARA_64 = (1 << 64) - 1
MASCARA_32 = (1 << 32) - 1


class PCG32(MotorAleatorio):
    nombre = "PCG32"
    MULTIPLICADOR = 6364136223846793005   # constante recomendada por O'Neill

    def __init__(self, semilla=None, secuencia=54):
        if semilla is None:
            semilla = semilla_por_reloj()
        super().__init__(semilla)
        # El incremento debe ser impar (Hull-Dobell con m = 2^64).
        # 'secuencia' permite tener flujos distintos con la misma semilla.
        self.incremento = ((secuencia << 1) | 1) & MASCARA_64
        # Inicialización oficial (pcg32_srandom_r):
        self.estado = 0
        self._avanzar()
        self.estado = (self.estado + semilla) & MASCARA_64
        self._avanzar()

    def _avanzar(self):
        """Etapa 1: paso congruencial de 64 bits."""
        self.estado = (self.estado * self.MULTIPLICADOR + self.incremento) & MASCARA_64

    def _generar(self):
        viejo = self.estado
        self._avanzar()
        # Etapa 2a (XSH): mezclar bits altos con bajos y quedarse con 32 bits.
        xorshifted = (((viejo >> 18) ^ viejo) >> 27) & MASCARA_32
        # Etapa 2b (RR): los 5 bits más altos dicen cuánto rotar (0 a 31).
        rot = viejo >> 59
        # Rotación a la derecha de 32 bits.
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & MASCARA_32