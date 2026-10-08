"""
El tablero es una matriz de alto x ancho. Cada celda guarda None (vacía)
o la letra de la pieza que la ocupa (para saber de qué color pintarla).
"""


class Tablero:
    def __init__(self, ancho=10, alto=20):
        self.ancho = ancho
        self.alto = alto
        self.celdas = [[None] * ancho for _ in range(alto)]

    def libre(self, fila, columna):
        return (0 <= fila < self.alto
                and 0 <= columna < self.ancho
                and self.celdas[fila][columna] is None)

    def cabe(self, pieza, forma=None, fila=None, columna=None):
        return all(self.libre(r, c) for r, c in pieza.celdas(forma, fila, columna))

    def fijar(self, pieza):
        for r, c in pieza.celdas():
            self.celdas[r][c] = pieza.tipo

    def limpiar_lineas(self):
        """Elimina las filas completas y agrega filas vacías arriba.
        Devuelve cuántas filas se eliminaron."""
        restantes = [fila for fila in self.celdas if any(c is None for c in fila)]
        eliminadas = self.alto - len(restantes)
        self.celdas = [[None] * self.ancho for _ in range(eliminadas)] + restantes
        return eliminadas