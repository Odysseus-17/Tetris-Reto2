"""
Las 7 piezas del Tetris representadas como matrices de 0 y 1.
Cada matriz es el rectángulo mínimo que encierra la pieza.
"""

FORMAS = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1],
          [1, 1]],
    "T": [[0, 1, 0],
          [1, 1, 1]],
    "S": [[0, 1, 1],
          [1, 1, 0]],
    "Z": [[1, 1, 0],
          [0, 1, 1]],
    "J": [[1, 0, 0],
          [1, 1, 1]],
    "L": [[0, 0, 1],
          [1, 1, 1]],
}

# El índice que devuelve motor.rango(7) se traduce con este orden.
ORDEN = "IOTSZJL"


def rotar(forma):
    """Rotación de 90° en sentido horario: invertir filas y transponer."""
    return [list(fila) for fila in zip(*forma[::-1])]


class Pieza:
    def __init__(self, tipo, fila, columna):
        self.tipo = tipo
        self.forma = [fila_[:] for fila_ in FORMAS[tipo]]
        self.fila = fila
        self.columna = columna

    @property
    def ancho(self):
        return len(self.forma[0])

    @property
    def alto(self):
        return len(self.forma)

    def celdas(self, forma=None, fila=None, columna=None):
        """Posiciones absolutas (fila, columna) que ocupa la pieza en el tablero.
        Los parámetros permiten preguntar por una posición hipotética."""
        forma = self.forma if forma is None else forma
        fila = self.fila if fila is None else fila
        columna = self.columna if columna is None else columna
        for r, fila_forma in enumerate(forma):
            for c, ocupada in enumerate(fila_forma):
                if ocupada:
                    yield fila + r, columna + c