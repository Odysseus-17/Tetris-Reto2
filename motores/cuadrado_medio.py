"""
Método del cuadrado medio (John von Neumann, 1946).

Idea: tomar un número de d dígitos, elevarlo al cuadrado (queda de 2d dígitos)
y quedarse con los d dígitos del centro. Ese es el siguiente número.

    x = 5735  ->  x² = 32890225  ->  centro: 8902

Problema conocido: la secuencia se degenera. Tarde o temprano cae en 0
(y 0² = 0 para siempre) o entra en un ciclo corto. Por eso este motor
detecta cuándo un valor se repite y se re-siembra.
"""
from .base import MotorAleatorio, semilla_por_reloj


class CuadradoMedio(MotorAleatorio):
    nombre = "Cuadrado medio"

    def __init__(self, semilla=None, digitos=8, resembrar=True):
        if digitos % 2 != 0:
            raise ValueError("La cantidad de dígitos debe ser par")
        self.digitos = digitos
        self.MAXIMO = 10 ** digitos
        self.resembrar_activo = resembrar
        self.resiembras = 0

        if semilla is None:
            semilla = semilla_por_reloj()
        semilla = self._normalizar(semilla)
        super().__init__(semilla)

        self.x = semilla
        self.vistos = {semilla}

    def _normalizar(self, valor):
        """Lleva la semilla a d dígitos y evita que empiece en cero."""
        valor %= self.MAXIMO
        if valor < self.MAXIMO // 10:          # muy pocos dígitos significativos
            valor += self.MAXIMO // 10
        return valor

    def _extraer_centro(self, x):
        cuadrado = x * x                        # hasta 2d dígitos
        # Quitar d/2 dígitos de la derecha y quedarse con d dígitos:
        return (cuadrado // 10 ** (self.digitos // 2)) % self.MAXIMO

    def _resembrar(self):
        """Nueva semilla derivada de la original y del conteo, para que la
        secuencia siga siendo reproducible con la misma semilla inicial."""
        self.resiembras += 1
        nueva = self.semilla_inicial + self.resiembras * 104729 + self.generados * 7919
        self.x = self._normalizar(nueva)
        self.vistos = {self.x}

    def _generar(self):
        self.x = self._extraer_centro(self.x)
        if self.resembrar_activo and (self.x == 0 or self.x in self.vistos):
            self._resembrar()
        self.vistos.add(self.x)
        return self.x