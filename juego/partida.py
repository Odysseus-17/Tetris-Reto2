"""
Lógica de una partida, sin nada de dibujo. Aquí es donde el motor de
números aleatorios decide:
  1. Qué pieza aparece          -> motor.rango(7)
  2. En qué columna aparece     -> motor.rango(ancho_tablero - ancho_pieza + 1)
  3. Si la pieza tiembla         -> motor.rango(100) < probabilidad   (modo hardcore)
     y hacia dónde               -> motor.rango(2)

También maneja niveles, vidas, la línea limitadora y la velocidad.
"""
from motores import MOTORES, semilla_por_reloj
from .config import (PUNTOS_POR_LINEA, METAS_NIVEL, VIDAS_INICIALES,
                     FILAS_POR_VIDA, INTERVALO_BASE, INCREMENTO_VELOCIDAD,
                     PROBABILIDAD_TEMBLOR)
from .piezas import Pieza, ORDEN, rotar
from .tablero import Tablero

# Desplazamientos que se intentan si una rotación choca con una pared o pieza
DESPLAZAMIENTOS_ROTACION = (0, -1, 1, -2, 2)


class Partida:
    def __init__(self, clave_motor="3", semilla=None, ancho=10, alto=20):
        self.tablero = Tablero(ancho, alto)
        self.lineas = 0
        self.piezas_colocadas = 0
        self.puntos = 0            # total de la partida
        self.puntos_nivel = 0      # avance dentro del nivel actual
        self.nivel = 1
        self.vidas = VIDAS_INICIALES
        self.terminada = False
        self.ganada = False
        self.hardcore = False
        self.temblores = 0
        self.ultimo_temblor = None  # (dirección, tirada, si se pudo mover)
        self.evento = None         # "vida" o "nivel": la interfaz lo muestra y lo limpia
        self.sonidos = []          # efectos pendientes; la interfaz los reproduce y vacía
        self.ultimo_sorteo = {}    # para mostrar en el panel
        self.cambiar_motor(clave_motor, semilla)

        self.siguiente_tipo = self._sortear_tipo()
        self.actual = None
        self._aparecer()

    # ---------- Valores derivados ----------

    @property
    def fila_limite(self):
        """Primera fila jugable. Las filas por encima están prohibidas.
        5 vidas -> 0 (20 filas), 4 -> 2 (18), 3 -> 4 (16), 2 -> 6 (14), 1 -> 8 (12)."""
        return (VIDAS_INICIALES - self.vidas) * FILAS_POR_VIDA

    @property
    def filas_efectivas(self):
        return self.tablero.alto - self.fila_limite

    @property
    def meta_actual(self):
        return METAS_NIVEL[self.nivel - 1]

    @property
    def progreso(self):
        """Fracción entre 0 y 1 del nivel actual, para la barra de avance."""
        return min(self.puntos_nivel / self.meta_actual, 1.0)

    @property
    def multiplicador_velocidad(self):
        return 1 + INCREMENTO_VELOCIDAD * (self.nivel - 1)

    @property
    def probabilidad_temblor(self):
        return PROBABILIDAD_TEMBLOR[self.nivel - 1]

    @property
    def intervalo_caida(self):
        # Más velocidad = menos tiempo entre cada paso de gravedad
        return INTERVALO_BASE / self.multiplicador_velocidad

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

    # ---------- Modo hardcore: temblor en vuelo ----------

    def alternar_hardcore(self):
        self.hardcore = not self.hardcore

    def _temblar(self):
        tirada = self.motor.rango(100)              # 0..99
        if tirada >= self.probabilidad_temblor:
            return
        direccion = -1 if self.motor.rango(2) == 0 else 1
        se_movio = self.mover(direccion, sonido=False)  # si choca, no se mueve
        if se_movio:
            self.sonidos.append("temblor")
        self.temblores += 1
        self.ultimo_temblor = (direccion, tirada, se_movio)

    def paso_gravedad(self):
        """Lo que pasa en cada tic del reloj: primero el posible temblor,
        después la pieza baja una fila."""
        if self.hardcore:
            self._temblar()
        self.bajar()

    # ---------- Ciclo de vida de las piezas ----------

    def _aparecer(self):
        tipo = self.siguiente_tipo
        self.siguiente_tipo = self._sortear_tipo()
        pieza = Pieza(tipo, 0, 0)
        pieza.columna = self._sortear_columna(pieza.ancho)
        self.actual = pieza
        if not self.tablero.cabe(pieza):
            # Solo puede pasar con 5 vidas (sin línea): el tablero llegó al techo
            self._perder_vida()

    def _fijar(self):
        self.tablero.fijar(self.actual)
        self.piezas_colocadas += 1
        eliminadas = self.tablero.limpiar_lineas()
        self.sonidos.append(f"linea{min(eliminadas, 4)}" if eliminadas else "fijar")
        self._sumar_lineas(eliminadas)
        if self.terminada:            # ganó con esta pieza
            return
        if self._sobrepasa_limite():
            self._perder_vida()
        else:
            self._aparecer()

    def _sobrepasa_limite(self):
        return any(any(celda is not None for celda in self.tablero.celdas[r])
                   for r in range(self.fila_limite))

    # ---------- Puntos, niveles y vidas ----------

    def _sumar_lineas(self, cantidad):
        if cantidad == 0:
            return
        ganados = cantidad * PUNTOS_POR_LINEA
        self.lineas += cantidad
        self.puntos += ganados
        self.puntos_nivel += ganados
        if self.puntos_nivel >= self.meta_actual:
            if self.nivel == len(METAS_NIVEL):
                self.ganada = True
                self.terminada = True
                self.sonidos.append("victoria")
            else:
                self.puntos_nivel = 0   # cada nivel empieza de cero; el sobrante se descarta
                self.tablero = Tablero(self.tablero.ancho, self.tablero.alto)  # tablero limpio
                self.nivel += 1
                self.evento = "nivel"
                self.sonidos.append("nivel")

    def _perder_vida(self):
        self.vidas -= 1
        if self.vidas == 0:
            self.terminada = True
            self.sonidos.append("fin")
            return
        # La línea bajó: se limpia el tablero para empezar en la zona más pequeña.
        # Los puntos y el nivel se conservan.
        self.tablero = Tablero(self.tablero.ancho, self.tablero.alto)
        self.evento = "vida"
        self.sonidos.append("vida")
        self._aparecer()

    # ---------- Acciones del jugador ----------

    def mover(self, dc, sonido=True):
        p = self.actual
        if self.tablero.cabe(p, columna=p.columna + dc):
            p.columna += dc
            if sonido:
                self.sonidos.append("mover")
            return True
        return False

    def rotar(self):
        p = self.actual
        nueva = rotar(p.forma)
        for dc in DESPLAZAMIENTOS_ROTACION:
            if self.tablero.cabe(p, forma=nueva, columna=p.columna + dc):
                p.forma = nueva
                p.columna += dc
                self.sonidos.append("rotar")
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
        while not self.terminada and self.bajar():
            pass

    def fila_fantasma(self):
        """Fila donde caería la pieza si se suelta (para dibujar la sombra)."""
        p = self.actual
        fila = p.fila
        while self.tablero.cabe(p, fila=fila + 1):
            fila += 1
        return fila