"""
Lógica de una partida, sin nada de dibujo. Aquí es donde el motor de
números aleatorios decide:
  1. Qué pieza aparece          -> motor.rango(7)
  2. En qué columna aparece     -> motor.rango(ancho_tablero - ancho_pieza + 1)
"""
from motores import MOTORES, semilla_por_reloj
from .piezas import Pieza, ORDEN, rotar
from .tablero import Tablero

# Desplazamientos que se intentan si una rotación choca con una pared o pieza
DESPLAZAMIENTOS_ROTACION = (0, -1, 1, -2, 2)


class Partida:
    def __init__(self, clave_motor="3", semilla=None, ancho=10, alto=20):
        self.tablero = Tablero(ancho, alto)
        self.lineas = 0
        self.piezas_colocadas = 0
        self.terminada = False
        self.intervalo_caida = 0.6           # segundos entre cada paso de gravedad
        self.ultimo_sorteo = {}              # para mostrar en el panel
        self.cambiar_motor(clave_motor, semilla)

        self.siguiente_tipo = self._sortear_tipo()
        self.actual = None
        self._aparecer()

    # ---------- Motor de números aleatorios ----------

    def cambiar_motor(self, clave, semilla=None):
        if semilla is None:
            semilla = semilla_por_reloj()
        self.clave_motor = clave
        self.motor = MOTORES[clave](semilla=semilla)

    def _sortear_tipo(self):
        indice = self.motor.rango(len(ORDEN))
        self.ultimo_sorteo["pieza"] = (ORDEN[indice], self.motor.historial[-1])
        return ORDEN[indice]

    def _sortear_columna(self, ancho_pieza):
        opciones = self.tablero.ancho - ancho_pieza + 1
        columna = self.motor.rango(opciones)
        self.ultimo_sorteo["columna"] = (columna, self.motor.historial[-1])
        return columna

    # ---------- Ciclo de vida de las piezas ----------

    def _aparecer(self):
        tipo = self.siguiente_tipo
        self.siguiente_tipo = self._sortear_tipo()
        pieza = Pieza(tipo, 0, 0)
        pieza.columna = self._sortear_columna(pieza.ancho)
        self.actual = pieza
        if not self.tablero.cabe(pieza):
            self.terminada = True

    def _fijar(self):
        self.tablero.fijar(self.actual)
        self.lineas += self.tablero.limpiar_lineas()
        self.piezas_colocadas += 1
        self._aparecer()

    # ---------- Acciones del jugador ----------

    def mover(self, dc):
        p = self.actual
        if self.tablero.cabe(p, columna=p.columna + dc):
            p.columna += dc
            return True
        return False

    def rotar(self):
        p = self.actual
        nueva = rotar(p.forma)
        for dc in DESPLAZAMIENTOS_ROTACION:
            if self.tablero.cabe(p, forma=nueva, columna=p.columna + dc):
                p.forma = nueva
                p.columna += dc
                return True
        return False

    def bajar(self):
        """Baja una fila. Si no puede, la pieza se fija. Devuelve si bajó."""
        p = self.actual
        if self.tablero.cabe(p, fila=p.fila + 1):
            p.fila += 1
            return True
        self._fijar()
        return False

    def caida_dura(self):
        while self.bajar():
            pass

    def fila_fantasma(self):
        """Fila donde caería la pieza si se suelta (para dibujar la sombra)."""
        p = self.actual
        fila = p.fila
        while self.tablero.cabe(p, fila=fila + 1):
            fila += 1
        return fila