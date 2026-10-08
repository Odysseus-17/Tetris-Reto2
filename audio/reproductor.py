"""
Reproductor y mezclador en tiempo real.

Se abre UN solo proceso de audio del sistema (paplay, aplay o pw-play) que
recibe sonido crudo por su entrada estándar. Un hilo aparte mezcla la música
con los efectos que estén sonando y le envía bloques de 20 ms. Así:
  - el juego nunca se congela esperando al audio,
  - la música y los efectos suenan al mismo tiempo,
  - no se abre un proceso nuevo por cada efecto (sería lento).
"""
import os
import shlex
import shutil
import subprocess
import threading
import time

from .sintetizador import TASA, a_pcm16
from .efectos import crear_efectos
from . import musica as modulo_musica

BLOQUE = TASA // 50                 # 20 ms por bloque
ADELANTO = 0.08                     # se escribe 80 ms por delante del reloj
MAX_VOCES = 6                       # efectos simultáneos como máximo

REPRODUCTORES = (
    ["paplay", "--raw", "--format=s16le", f"--rate={TASA}", "--channels=1",
     "--latency-msec=40"],
    ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(TASA), "-c", "1",
     "--buffer-time=60000"],
    ["pw-play", "--format", "s16", "--rate", str(TASA), "--channels", "1",
     "--latency", "40ms", "-"],
)


class Audio:
    def __init__(self):
        self.efectos = crear_efectos()
        self.silenciado = False
        self.pausado = False
        self.info_musica = ""
        self._musica = None
        self._pos_musica = 0
        self._voces = []                # [nombre, muestras, posición]
        self._candado = threading.Lock()
        self._clave_musica = None
        self._activo = True
        self.proceso = None
        self.nombre_reproductor = None
        self._abrir_reproductor()
        if self.proceso:
            threading.Thread(target=self._mezclar, daemon=True).start()

    @property
    def disponible(self):
        return self.proceso is not None

    # ---------- Proceso del sistema ----------

    def _candidatos(self):
        # TETRIS_AUDIO permite forzar otro comando, por ejemplo para pruebas
        if os.environ.get("TETRIS_AUDIO"):
            return [shlex.split(os.environ["TETRIS_AUDIO"])]
        return [cmd for cmd in REPRODUCTORES if shutil.which(cmd[0])]

    def _abrir_reproductor(self, descartar=()):
        for cmd in self._candidatos():
            if cmd[0] in descartar:
                continue
            try:
                proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL)
            except OSError:
                continue
            time.sleep(0.05)
            if proceso.poll() is None:          # sigue vivo: funciona
                self.proceso, self.nombre_reproductor = proceso, cmd[0]
                return
        self.proceso = None

    # ---------- Hilo mezclador ----------

    def _siguiente_bloque(self):
        mezcla = [0.0] * BLOQUE
        with self._candado:
            if self.silenciado or self.pausado:
                return mezcla
            if self._musica:
                m, pos = self._musica, self._pos_musica
                for i in range(BLOQUE):
                    mezcla[i] = m[(pos + i) % len(m)]   # en bucle
                self._pos_musica = (pos + BLOQUE) % len(m)
            for voz in self._voces:
                _, muestras, pos = voz
                trozo = muestras[pos:pos + BLOQUE]
                for i, v in enumerate(trozo):
                    mezcla[i] += v
                voz[2] = pos + BLOQUE
            self._voces = [v for v in self._voces if v[2] < len(v[1])]
        return mezcla

    def _mezclar(self):
        inicio = time.monotonic()
        escritas = 0
        while self._activo:
            objetivo = (time.monotonic() - inicio + ADELANTO) * TASA
            while escritas < objetivo and self._activo:
                try:
                    self.proceso.stdin.write(a_pcm16(self._siguiente_bloque()))
                    self.proceso.stdin.flush()
                except (BrokenPipeError, OSError, ValueError):
                    # El reproductor murió: probar con el siguiente
                    fallido = self.nombre_reproductor
                    self._abrir_reproductor(descartar=(fallido,))
                    if not self.proceso:
                        return
                    inicio, escritas = time.monotonic(), 0
                    break
                escritas += BLOQUE
            time.sleep(0.01)

    # ---------- API para el juego ----------

    def efecto(self, nombre):
        muestras = self.efectos.get(nombre)
        if not muestras or not self.disponible:
            return
        with self._candado:
            # Si el mismo efecto ya suena (mover muy rápido), se reinicia
            self._voces = [v for v in self._voces if v[0] != nombre]
            self._voces.append([nombre, muestras, 0])
            del self._voces[:-MAX_VOCES]

    def musica_para(self, clase_motor, semilla, nivel):
        """Genera la música en segundo plano (tarda ~1 s) y la cambia al terminar."""
        clave = (clase_motor, semilla, nivel)
        if clave == self._clave_musica or not self.disponible:
            return
        self._clave_musica = clave

        def trabajo():
            muestras, descripcion, _ = modulo_musica.generar(clase_motor, semilla, nivel)
            with self._candado:
                if self._clave_musica == clave:   # nadie pidió otra mientras tanto
                    self._musica, self._pos_musica = muestras, 0
                    self.info_musica = descripcion
        threading.Thread(target=trabajo, daemon=True).start()

    def detener_musica(self):
        with self._candado:
            self._musica, self._clave_musica, self.info_musica = None, None, ""

    def alternar_silencio(self):
        self.silenciado = not self.silenciado

    def cerrar(self):
        self._activo = False
        if self.proceso:
            try:
                self.proceso.stdin.close()
            except OSError:
                pass
            self.proceso.terminate()