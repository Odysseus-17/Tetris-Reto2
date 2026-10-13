"""
Modo 2 jugadores en pantalla dividida.

No hay reglas nuevas para mover piezas: cada jugador tiene su propia Partida,
exactamente la misma del modo de 1 jugador, con su propio motor de números
aleatorios, sus vidas y su línea limitadora. Esta clase solo decide quién gana:

  1. El primero en llegar a META_VERSUS puntos.
  2. Si un jugador pierde todas sus vidas, gana el otro.

Cada Partida se crea con una sola meta (metas=(1000,)): llegar a ella es
"ganar la partida", así que el tablero no se limpia como al subir de nivel
y la torre del ganador queda a la vista.
"""
from .config import META_VERSUS
from .partida import Partida


class Versus:
    def __init__(self, motor_1="3", motor_2="3", semilla_1=None, semilla_2=None,
                 meta=META_VERSUS):
        self.meta = meta
        self.jugadores = [Partida(motor_1, semilla_1, metas=(meta,)),
                          Partida(motor_2, semilla_2, metas=(meta,))]
        self.ganador = None        # 0 o 1 cuando termina
        self.motivo = None         # "meta" o "vidas"

    @property
    def terminada(self):
        return self.ganador is not None

    def progreso(self, i):
        """Fracción de la meta alcanzada por el jugador i (0 a 1)."""
        return min(self.jugadores[i].puntos / self.meta, 1.0)

    def revisar(self):
        """Se llama después de cada acción o paso de gravedad de cualquier
        jugador. Como las acciones se procesan una por una, no hay empates."""
        if self.terminada:
            return
        for i, p in enumerate(self.jugadores):
            if p.ganada:                              # llegó a la meta
                self._terminar(i, "meta")
                return
        for i, p in enumerate(self.jugadores):
            if p.terminada and not p.ganada:          # se quedó sin vidas
                self._terminar(1 - i, "vidas")
                return

    def _terminar(self, ganador, motivo):
        self.ganador, self.motivo = ganador, motivo
        perdedor = self.jugadores[1 - ganador]
        perdedor.terminada = True                    # se detienen ambos tableros
        if "victoria" not in self.jugadores[ganador].sonidos:
            self.jugadores[ganador].sonidos.append("victoria")
        if "fin" not in perdedor.sonidos:
            perdedor.sonidos.append("fin")
