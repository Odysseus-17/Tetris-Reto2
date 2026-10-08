"""
Pruebas de la lógica del juego, sin abrir la interfaz.
Ejecutar:  python3 pruebas_juego.py
"""
from juego.partida import Partida
from juego.piezas import Pieza, rotar, FORMAS

ok = lambda cond, msg: print(("  OK   " if cond else "  FALLA") + "  " + msg)

print("Rotación")
t = FORMAS["T"]
ok(rotar(rotar(rotar(rotar(t)))) == t, "4 rotaciones devuelven la forma original")
ok(rotar(FORMAS["I"]) == [[1], [1], [1], [1]], "la I acostada queda vertical")

print("Limpieza de líneas")
p = Partida("3", semilla=1)
for c in range(10):
    p.tablero.celdas[19][c] = "I"
p.tablero.celdas[18][0] = "O"
eliminadas = p.tablero.limpiar_lineas()
ok(eliminadas == 1, "se elimina la fila completa")
ok(p.tablero.celdas[19][0] == "O", "la fila de arriba baja")

print("Aparición controlada por el motor")
a, b = Partida("2", semilla=99), Partida("2", semilla=99)
ok((a.actual.tipo, a.actual.columna) == (b.actual.tipo, b.actual.columna),
   "misma semilla y motor -> misma pieza y columna")
ok(0 <= a.actual.columna <= 10 - a.actual.ancho, "la columna sorteada deja la pieza dentro del tablero")

print("Cambio de motor")
p = Partida("1", semilla=5)
p.cambiar_motor("3", semilla=5)
ok(p.motor.nombre == "PCG32", "el motor activo cambia a PCG32")
p.caida_dura()
ok(p.motor.generados >= 2, "las piezas nuevas usan el motor nuevo")

print("Fin del juego")
p = Partida("3", semilla=7)
for _ in range(200):
    if p.terminada:
        break
    p.caida_dura()
ok(p.terminada, "soltando piezas sin moverlas el tablero se llena y termina")

print("Paredes")
p = Partida("3", semilla=3)
for _ in range(15):
    p.mover(-1)
ok(p.actual.columna == 0, "no atraviesa la pared izquierda")
