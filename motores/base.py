"""
Interfaz común para todos los motores de números aleatorios.

Todos los motores heredan de MotorAleatorio y solo tienen que implementar
_generar(). Así el juego puede cambiar de motor sin cambiar su propio código:
siempre llama a motor.rango(n) para elegir una pieza o una columna.
"""
import time
from abc import ABC, abstractmethod
from collections import deque


def semilla_por_reloj():
    """Semilla tomada del reloj del sistema en nanosegundos.
    No es una librería de aleatoriedad: es solo la hora actual."""
    return time.time_ns() & 0xFFFFFFFF


class MotorAleatorio(ABC):
    nombre = "Motor base"
    # Cantidad de valores distintos que puede producir _generar(): [0, MAXIMO)
    MAXIMO = 2 ** 32

    def __init__(self, semilla):
        self.semilla_inicial = semilla
        self.historial = deque(maxlen=10)  # últimos valores, para el panel del juego
        self.generados = 0

    @abstractmethod
    def _generar(self):
        """Devuelve el siguiente número crudo en [0, MAXIMO)."""

    def siguiente(self):
        valor = self._generar()
        self.historial.append(valor)
        self.generados += 1
        return valor

    def rango(self, n):
        """Entero en [0, n). Escala el número en vez de usar módulo, para
        aprovechar los bits altos (los bits bajos de un LCG son malos)."""
        if n <= 0:
            raise ValueError("n debe ser positivo")
        return self.siguiente() * n // self.MAXIMO

    def __repr__(self):
        return f"{self.nombre} (semilla={self.semilla_inicial})"