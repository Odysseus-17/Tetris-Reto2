"""
Tabla de puntuaciones del modo de 1 jugador.

Aquí solo está la lógica (ordenar, insertar, recortar al top). Dónde se
guarda depende de la interfaz, y ambas usan el mismo formato JSON:
  - Terminal: el archivo datos/ranking.json  (cargar_archivo / guardar_archivo)
  - Web:      el almacenamiento del navegador (localStorage), desde JavaScript

Cada fila es una partida terminada:
  {"nombre": "Alfonso", "puntos": 3400, "nivel": 3,
   "motor": "PCG32", "fecha": "2026-10-15"}

Orden: más puntos primero; si empatan, el que llegó a un nivel mayor; si
también empatan, el que lo logró antes conserva el puesto.
"""
import json
import os

from .config import RANKING_MAXIMO, LARGO_NOMBRE


def limpiar_nombre(nombre):
    """Quita espacios sobrantes y caracteres de control, y recorta el largo."""
    nombre = "".join(c for c in str(nombre) if c.isprintable())
    nombre = " ".join(nombre.split())[:LARGO_NOMBRE].strip()
    return nombre or "Anónimo"


def _clave_orden(fila):
    return (-fila["puntos"], -fila["nivel"])


class Ranking:
    def __init__(self, filas=None, maximo=RANKING_MAXIMO):
        self.maximo = maximo
        self.filas = []
        for f in filas or []:
            try:
                self.filas.append({
                    "nombre": limpiar_nombre(f["nombre"]),
                    "puntos": int(f["puntos"]),
                    "nivel": int(f["nivel"]),
                    "motor": str(f.get("motor", "")),
                    "fecha": str(f.get("fecha", "")),
                })
            except (KeyError, TypeError, ValueError):
                continue                      # fila dañada: se ignora
        self.filas.sort(key=_clave_orden)     # sort es estable: respeta el orden previo
        del self.filas[maximo:]

    # ---------- Formato JSON compartido ----------

    @classmethod
    def desde_json(cls, texto):
        """Tolera texto vacío o dañado: en ese caso la tabla empieza vacía."""
        try:
            datos = json.loads(texto) if texto and texto.strip() else []
        except json.JSONDecodeError:
            datos = []
        return cls(datos if isinstance(datos, list) else [])

    def a_json(self):
        return json.dumps(self.filas, ensure_ascii=False, indent=2)

    # ---------- Operaciones ----------

    def agregar(self, nombre, puntos, nivel, motor="", fecha=""):
        """Registra una partida. Devuelve su puesto (1, 2, ...) o None si no
        alcanzó a entrar en la tabla."""
        fila = {"nombre": limpiar_nombre(nombre), "puntos": int(puntos),
                "nivel": int(nivel), "motor": motor, "fecha": fecha}
        # Se inserta DESPUÉS de las filas con igual o mejor resultado:
        # en un empate, quien lo logró antes conserva su puesto.
        i = 0
        while i < len(self.filas) and _clave_orden(self.filas[i]) <= _clave_orden(fila):
            i += 1
        if i >= self.maximo:
            return None
        self.filas.insert(i, fila)
        del self.filas[self.maximo:]
        return i + 1


# ---------- Persistencia en archivo (versión de terminal) ----------

def cargar_archivo(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return Ranking.desde_json(f.read())
    except FileNotFoundError:
        return Ranking()


def guardar_archivo(ruta, ranking):
    ruta = os.fspath(ruta)          # acepta texto o pathlib.Path
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        f.write(ranking.a_json())
    os.replace(temporal, ruta)     # reemplazo atómico: no deja el archivo a medias
