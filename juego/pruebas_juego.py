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

print("Puntaje")
p = Partida("3", semilla=11)
for fila in (18, 19):
    for c in range(10):
        p.tablero.celdas[fila][c] = "I"
    p.tablero.celdas[fila][p.actual.columna] = None  # dejar un hueco bajo la pieza
p.actual.forma = [[1], [1]]                          # pieza vertical de 2 que tapa los huecos
p.caida_dura()
ok(p.lineas == 2 and p.puntos == 200, "2 líneas completas dan 200 puntos")

print("Vidas y línea limitadora")
p = Partida("3", semilla=21)
ok(p.vidas == 5 and p.filas_efectivas == 20, "empieza con 5 vidas y 20x10")
for r in range(20):                       # llenar sin completar filas
    for c in range(10):
        if c != r % 10:
            p.tablero.celdas[r][c] = "I"
p._aparecer()                             # la pieza ya no cabe arriba
ok(p.vidas == 4 and p.filas_efectivas == 18, "al llegar al techo pierde una vida y queda 18x10")
ok(all(c is None for fila in p.tablero.celdas for c in fila), "el tablero se limpia")

columnas = {c for _, c in p.actual.celdas()}
hueco = next(c for c in range(10) if c not in columnas)
for c in range(10):
    if c != hueco:
        p.tablero.celdas[2][c] = "O"      # piso justo debajo de la línea (fila límite = 2)
p.caida_dura()
ok(p.vidas == 3 and p.fila_limite == 4, "fijar una pieza por encima de la línea quita otra vida")

p.vidas = 1
p._perder_vida()
ok(p.terminada and not p.ganada, "sin vidas termina la partida")

print("Niveles y velocidad")
p = Partida("3", semilla=4)
ok(p.multiplicador_velocidad == 1.0, "nivel 1 a velocidad básica")
p.puntos_nivel = 900
p._sumar_lineas(2)
ok(p.nivel == 2 and p.puntos_nivel == 0, "1100/1000: sube a nivel 2 y el sobrante se descarta")
ok(p.puntos == 200 and p.progreso == 0, "el total conserva lo ganado; la barra del nivel 2 arranca en 0%")
p.nivel, p.puntos_nivel = 5, 4900
ok(abs(p.multiplicador_velocidad - 1.2) < 1e-9, "nivel 5 a x1.20")
p._sumar_lineas(1)
ok(p.terminada and p.ganada, "completar el nivel 5 gana la partida")

print("Perder vida conserva el avance")
p = Partida("3", semilla=8)
p.nivel, p.puntos_nivel, p.puntos = 3, 1200, 4200
p._perder_vida()
ok((p.nivel, p.puntos_nivel, p.puntos, p.vidas) == (3, 1200, 4200, 4), "nivel y puntos intactos, una vida menos")
print("Reinicio tras game over")
ok(Partida("3").nivel == 1 and Partida("3").vidas == 5, "una partida nueva arranca en nivel 1 con 5 vidas")