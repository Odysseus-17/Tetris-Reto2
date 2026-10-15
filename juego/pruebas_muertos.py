"""
Pruebas del modo tablero hardcore (puntos muertos), sin interfaz.
Ejecutar desde la raíz:  python3 juego/pruebas_muertos.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego.partida import Partida
from juego.versus import Versus
from juego.tablero import MUERTO
from juego.config import FILAS_SIN_MUERTOS

ok = lambda cond, msg: print(("  OK   " if cond else "  FALLA") + "  " + msg)


def posiciones(p):
    return sorted((f, c) for f, fila in enumerate(p.tablero.celdas)
                  for c, v in enumerate(fila) if v == MUERTO)


def subir_nivel(p):
    p.puntos_nivel = p.meta_actual - 100
    p._sumar_lineas(1)


print("Activación")
ok(posiciones(Partida("3", semilla=1)) == [], "sin el modo no hay puntos muertos")
ok(all(posiciones(j) == [] for j in Versus("3", "3").jugadores), "el modo 2 jugadores no tiene puntos muertos")
p = Partida("3", semilla=1, tablero_hardcore=True)
ok(len(posiciones(p)) == 3 and posiciones(p) == sorted(p.muertos), "nivel 1: 3 puntos muertos")

print("Ubicación")
ok(all(f >= FILAS_SIN_MUERTOS for f, _ in posiciones(p)), "nunca en las primeras 5 filas")
for motor in "1234":
    for semilla in range(30):
        q = Partida(motor, semilla=semilla, tablero_hardcore=True)
        if len(set(q.muertos)) != len(q.muertos) or any(f < 5 for f, _ in q.muertos):
            ok(False, f"motor {motor} semilla {semilla}: posiciones repetidas o en filas prohibidas")
            break
else:
    ok(True, "4 motores x 30 semillas: sin posiciones repetidas ni en filas prohibidas")
a = Partida("2", semilla=77, tablero_hardcore=True)
b = Partida("2", semilla=77, tablero_hardcore=True)
ok(a.muertos == b.muertos, "misma semilla y motor -> mismos puntos muertos (los decide el motor)")
antes = Partida("4", semilla=5).motor.generados
ok(Partida("4", semilla=5, tablero_hardcore=True).motor.generados == antes + 3,
   "cada punto muerto consume un número del motor")

print("Cantidad por nivel")
p = Partida("3", semilla=2, tablero_hardcore=True)
cantidades = [len(posiciones(p))]
for _ in range(4):
    subir_nivel(p)
    cantidades.append(len(posiciones(p)))
ok(cantidades == [3, 3, 3, 4, 5], f"niveles 1 a 5: {cantidades}")

print("Al subir de nivel cambian de lugar")
p = Partida("3", semilla=3, tablero_hardcore=True)
distintos = True
for _ in range(4):
    anteriores = set(p.muertos)
    subir_nivel(p)
    distintos &= not (anteriores & set(p.muertos))
ok(distintos, "ningún punto muerto repite casilla respecto al nivel anterior")

print("Al perder una vida cambian de lugar")
p = Partida("1", semilla=4, tablero_hardcore=True)
distintos, respetan_linea = True, True
while p.vidas > 1:
    anteriores = set(p.muertos)
    p._perder_vida()
    distintos &= not (anteriores & set(p.muertos))
    respetan_linea &= all(f >= max(5, p.fila_limite) for f, _ in p.muertos)
    respetan_linea &= len(posiciones(p)) == 3
ok(distintos, "con cada vida perdida se mueven a casillas nuevas")
ok(respetan_linea, "siempre debajo de la línea azul (con 1 vida, desde la fila 8)")

print("Los bloques se quedan sobre un punto muerto")
p = Partida("3", semilla=6, tablero_hardcore=True)
p.tablero = type(p.tablero)(10, 20)
p.tablero.celdas[12][4] = MUERTO
p.actual.forma, p.actual.fila, p.actual.columna = [[1, 1]], 0, 3   # pieza de 2 sobre las columnas 3 y 4
p.caida_dura()
ok(p.tablero.celdas[11][3] is not None and p.tablero.celdas[11][4] is not None,
   "la pieza queda apoyada encima del punto muerto (fila 11), flotando")
ok(p.vidas == 5, "apoyarse en un punto muerto no cuesta una vida")

print("Filas con puntos muertos")
p = Partida("3", semilla=7, tablero_hardcore=True)
p.tablero = type(p.tablero)(10, 20)
p.tablero.celdas[19] = ["I"] * 9 + [None]
p.tablero.celdas[19][2] = MUERTO               # la fila 19 tiene un punto muerto
p.tablero.celdas[15][6] = MUERTO               # otro flotando más arriba
p.actual.forma, p.actual.fila, p.actual.columna = [[1]], 0, 9
p.caida_dura()
ok(p.lineas == 1 and p.puntos == 100, "el punto muerto cuenta como casilla llena: la fila se completa")
ok(p.muertos_en_tablero == 1, "el punto muerto de la fila completada desaparece con ella")
ok(p.tablero.celdas[16][6] == MUERTO, "el que estaba más arriba baja junto con su fila")
