"""
Generador congruencial lineal (LCG), D. H. Lehmer, 1949.

    X(n+1) = (a * X(n) + c) mod m

a = multiplicador, c = incremento, m = módulo, X(0) = semilla.

Con m = 2^32 y los parámetros de Numerical Recipes (a = 1664525,
c = 1013904223) el período es completo: recorre los 2^32 valores antes de
repetir. Eso lo garantiza el teorema de Hull-Dobell (ver cumple_hull_dobell).
"""
from .base import MotorAleatorio, semilla_por_reloj


def _factores_primos(n):
    factores, d = set(), 2
    while d * d <= n:
        while n % d == 0:
            factores.add(d)
            n //= d
        d += 1
    if n > 1:
        factores.add(n)
    return factores


def _mcd(a, b):
    while b:
        a, b = b, a % b
    return a


def cumple_hull_dobell(a, c, m):
    """Condiciones para que el LCG tenga período completo m:
    1. c y m son coprimos.
    2. a - 1 es divisible por todos los factores primos de m.
    3. Si m es múltiplo de 4, a - 1 también lo es."""
    if _mcd(c, m) != 1:
        return False
    if any((a - 1) % p != 0 for p in _factores_primos(m)):
        return False
    if m % 4 == 0 and (a - 1) % 4 != 0:
        return False
    return True


class CongruencialLineal(MotorAleatorio):
    nombre = "Congruencial lineal"

    def __init__(self, semilla=None, a=1664525, c=1013904223, m=2 ** 32):
        self.a, self.c, self.m = a, c, m
        self.MAXIMO = m
        if semilla is None:
            semilla = semilla_por_reloj()
        super().__init__(semilla % m)
        self.x = semilla % m

    def _generar(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x