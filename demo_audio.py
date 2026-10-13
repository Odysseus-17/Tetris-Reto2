"""
Demostración del sonido procedural, sin abrir el juego.
  python3 demo_audio.py              -> guarda los sonidos en sonidos_demo/ y
                                        muestra las melodías de cada motor
  python3 demo_audio.py --escuchar   -> además los reproduce por los parlantes
"""
import os
import sys
import time

from motores import MOTORES
from audio.efectos import crear_efectos
from audio import musica
from audio.sintetizador import guardar_wav, TASA
from audio.reproductor import Audio

SEMILLA = 12345
CARPETA = "sonidos_demo"
os.makedirs(CARPETA, exist_ok=True)

print("Efectos de sonido:")
efectos = crear_efectos()
for nombre, muestras in efectos.items():
    guardar_wav(f"{CARPETA}/efecto_{nombre}.wav", muestras)
    print(f"  {nombre:<9} {len(muestras) / TASA * 1000:5.0f} ms")

print(f"\nMelodías del nivel 1 con la semilla {SEMILLA} (primeros 2 compases):")
for clave, Motor in MOTORES.items():
    inicio = time.monotonic()
    muestras, descripcion, melodia = musica.generar(Motor, SEMILLA, 1)
    guardar_wav(f"{CARPETA}/musica_{clave}_{Motor.nombre.replace(' ', '_')}.wav", muestras)
    notas = " ".join(musica.nombre_nota(n) for t, _, n in melodia if t < 8)
    print(f"  [{clave}] {Motor.nombre:<20} {descripcion}  "
          f"({time.monotonic() - inicio:.2f} s)\n      {notas}")

print("\nNivel 5 con PCG32 (más agudo y rápido):")
muestras, descripcion, _ = musica.generar(MOTORES["3"], SEMILLA, 5)
guardar_wav(f"{CARPETA}/musica_3_nivel5.wav", muestras)
print(f"  {descripcion}")
print(f"\nArchivos guardados en {CARPETA}/")

if "--escuchar" in sys.argv:
    audio = Audio()
    if not audio.disponible:
        sys.exit("No se encontró paplay, aplay ni pw-play que funcione.")
    print(f"\nReproduciendo con {audio.nombre_reproductor}...")
    for nombre in efectos:
        print("  efecto:", nombre)
        audio.efecto(nombre)
        time.sleep(len(efectos[nombre]) / TASA + 0.3)
    for clave, Motor in MOTORES.items():
        print(f"  música: {Motor.nombre} (8 segundos)")
        audio.musica_para(Motor, SEMILLA, 1)
        time.sleep(8)
    audio.cerrar()
