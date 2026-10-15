"""
Pruebas de la tabla de puntuaciones, sin interfaz.
Ejecutar desde la raíz:  python3 juego/pruebas_ranking.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego.ranking import Ranking, limpiar_nombre, cargar_archivo, guardar_archivo
from juego.config import RANKING_MAXIMO

ok = lambda cond, msg: print(("  OK   " if cond else "  FALLA") + "  " + msg)

print("Nombres")
ok(limpiar_nombre("  Alfonso   Pérez ") == "Alfonso Pérez", "quita espacios sobrantes y respeta tildes")
ok(limpiar_nombre("") == "Anónimo" and limpiar_nombre("   ") == "Anónimo", "nombre vacío -> Anónimo")
ok(len(limpiar_nombre("x" * 50)) == 16, "recorta a 16 caracteres")
ok(limpiar_nombre("Ana\x07\n") == "Ana", "elimina caracteres de control")

print("Orden")
r = Ranking()
r.agregar("Ana", 1200, 2)
r.agregar("Beto", 3400, 3)
puesto = r.agregar("Caro", 1200, 3)
ok([f["nombre"] for f in r.filas] == ["Beto", "Caro", "Ana"], "más puntos primero; con empate, mayor nivel")
ok(puesto == 2, "agregar devuelve el puesto obtenido")
puesto = r.agregar("Dani", 1200, 2)
ok(puesto == 4 and r.filas[2]["nombre"] == "Ana", "empate total: quien lo logró antes conserva el puesto")
ok(r.agregar("Ana", 0, 1) == 5, "el mismo nombre puede aparecer varias veces (una fila por partida)")

print("Top")
r = Ranking()
for i in range(RANKING_MAXIMO):
    r.agregar(f"J{i}", 1000 + i * 100, 1)
ok(len(r.filas) == RANKING_MAXIMO, f"guarda como máximo {RANKING_MAXIMO} partidas")
ok(r.agregar("Bajo", 500, 1) is None and len(r.filas) == RANKING_MAXIMO, "un puntaje que no alcanza no entra")
ok(r.agregar("Alto", 5000, 4) == 1 and r.filas[-1]["nombre"] == "J1", "uno que entra desplaza al último")

print("Tablero hardcore")
r2 = Ranking()
r2.agregar("Eva", 900, 2, tablero_hardcore=True)
ok(r2.filas[0]["tablero_hardcore"] is True, "guarda si la partida se jugó con puntos muertos")
ok(Ranking([{"nombre": "Vieja", "puntos": 5, "nivel": 1}]).filas[0]["tablero_hardcore"] is False,
   "las filas guardadas antes de este modo se leen como partidas normales")

print("JSON y persistencia")
copia = Ranking.desde_json(r.a_json())
ok(copia.filas == r.filas, "ida y vuelta por JSON sin pérdidas")
ok(Ranking.desde_json("").filas == [] and Ranking.desde_json("{basura").filas == [], "archivo vacío o dañado -> tabla vacía")
ok(len(Ranking([{"nombre": "x"}, {"nombre": "Ok", "puntos": 5, "nivel": 1}]).filas) == 1, "ignora filas incompletas")
with tempfile.TemporaryDirectory() as d:
    ruta = os.path.join(d, "datos", "ranking.json")
    ok(cargar_archivo(ruta).filas == [], "si el archivo no existe, la tabla empieza vacía")
    guardar_archivo(ruta, r)
    ok(cargar_archivo(ruta).filas == r.filas, "lo guardado se recupera en la siguiente partida")
    from pathlib import Path
    guardar_archivo(Path(ruta), r)
    ok(cargar_archivo(Path(ruta)).filas == r.filas, "también acepta la ruta como pathlib.Path (así la usa la terminal)")
    ok("Pérez" in (guardar_archivo(ruta, Ranking([{"nombre": "Pérez", "puntos": 1, "nivel": 1}])) or open(ruta, encoding="utf-8").read()),
       "el archivo guarda las tildes legibles")
