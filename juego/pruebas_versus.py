"""
Pruebas del modo 2 jugadores, sin interfaz.
Ejecutar desde la raíz:  python3 juego/pruebas_versus.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego.versus import Versus
from juego.config import META_VERSUS

ok = lambda cond, msg: print(("  OK   " if cond else "  FALLA") + "  " + msg)


def completar_lineas(partida, cantidad):
    """Llena 'cantidad' filas dejando un hueco bajo la pieza actual y la suelta
    vertical para completarlas, como haría un jugador."""
    col = partida.actual.columna
    for fila in range(20 - cantidad, 20):
        for c in range(10):
            partida.tablero.celdas[fila][c] = None if c == col else "I"
    partida.actual.forma = [[1]] * cantidad
    partida.caida_dura()


print("Partidas independientes")
v = Versus("1", "4", semilla_1=10, semilla_2=10)
a, b = v.jugadores
ok(a.motor.nombre == "Cuadrado medio" and b.motor.nombre == "Xoshiro256**", "cada jugador tiene su propio motor")
a.caida_dura()
ok(a.piezas_colocadas == 1 and b.piezas_colocadas == 0, "lo que hace un jugador no afecta al otro")
a.cambiar_motor("2")
ok(b.motor.nombre == "Xoshiro256**", "cambiar el motor de uno no cambia el del otro")
ok(v.meta == META_VERSUS == 1000, "la meta es 1000 puntos")

print("Gana el primero en llegar a la meta")
v = Versus("3", "3", semilla_1=1, semilla_2=2)
a, b = v.jugadores
for _ in range(2):
    completar_lineas(b, 4)             # 800 puntos para el jugador 2
v.revisar()
ok(not v.terminada and abs(v.progreso(1) - 0.8) < 1e-9, "con 800 puntos todavía no gana (80%)")
b.tablero.celdas[10][0] = "T"          # un bloque de la torre que no está en las filas completas
completar_lineas(b, 2)                 # 1000
v.revisar()
ok(v.ganador == 1 and v.motivo == "meta", "al llegar a 1000 gana el jugador 2")
ok(a.terminada and b.terminada, "ambos tableros se detienen")
ok("victoria" in b.sonidos and "fin" in a.sonidos, "suena victoria para uno y fin para el otro")
ok(b.nivel == 1, "el ganador no sube de nivel")
ok(b.tablero.celdas[12][0] == "T", "la torre del ganador queda a la vista (no se limpia el tablero)")

print("Gana el otro si uno pierde todas sus vidas")
v = Versus("2", "2", semilla_1=5, semilla_2=6)
a, b = v.jugadores
for _ in range(400):
    if a.terminada:
        break
    a.caida_dura()
v.revisar()
ok(a.vidas == 0 and v.ganador == 1 and v.motivo == "vidas", "jugador 1 sin vidas: gana el jugador 2")

print("Las vidas y la línea azul funcionan igual que en 1 jugador")
v = Versus("3", "3", semilla_1=7, semilla_2=8)
a, b = v.jugadores
while a.vidas == 5:
    a.caida_dura()
v.revisar()
ok(a.vidas == 4 and a.filas_efectivas == 18 and b.filas_efectivas == 20,
   "solo el jugador que perdió la vida ve bajar su línea")
ok(not v.terminada, "perder una vida no termina el duelo")
