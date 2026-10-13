"""
Pruebas del sonido procedural, sin necesidad de parlantes.
Ejecutar:  python3 pruebas_audio.py
"""
import os
import time

from motores import MOTORES
from audio import musica
from audio.efectos import crear_efectos
from audio.sintetizador import tono, a_pcm16, TASA

ok = lambda cond, msg: print(("  OK   " if cond else "  FALLA") + "  " + msg)

print("Sintetizador")
la = tono(440, 1.0, "seno", volumen=1.0, ataque=0.0001, liberacion=0.0001)
cruces = sum(1 for a, b in zip(la, la[1:]) if a < 0 <= b)
ok(abs(cruces - 440) <= 1, f"un La de 1 s tiene 440 ciclos ({cruces})")
ok(len(a_pcm16(la)) == 2 * TASA, "1 s de audio = 44100 bytes en PCM de 16 bits")
ok(all(abs(v) <= 1 for v in crear_efectos()["fijar"]), "los efectos no saturan")

print("Música sin disonancia (3 motores x 5 niveles x 20 semillas)")
fuera_escala = anclas_mal = saltos_grandes = total = 0
for clave, Motor in MOTORES.items():
    for nivel in range(1, 6):
        for semilla in range(1, 21):
            motor = Motor(semilla=semilla * 7919)
            melodia, _, _, _ = musica.componer(motor, nivel)
            trans = 2 * (nivel - 1)
            escala = musica._escala(trans)
            for i, (t, _, nota) in enumerate(melodia):
                total += 1
                if nota not in escala:
                    fuera_escala += 1
                if t % 4 == 0:                      # primer tiempo del compás
                    _, acorde = musica.PROGRESION[int(t // 4) % 4]
                    if (nota - trans) % 12 not in acorde:
                        anclas_mal += 1
                if i and abs(escala.index(nota) - escala.index(melodia[i - 1][2])) > 2 \
                        and t % 4 != 0:
                    saltos_grandes += 1
ok(fuera_escala == 0, f"{total} notas, todas dentro de la pentatónica")
ok(anclas_mal == 0, "todo primer tiempo cae en una nota del acorde")
ok(saltos_grandes == 0, "fuera de los anclajes, nunca salta más de 2 posiciones")

m1 = musica.componer(MOTORES["1"](semilla=99), 1)[0]
m3 = musica.componer(MOTORES["3"](semilla=99), 1)[0]
ok(m1 != m3, "con la misma semilla, motores distintos componen melodías distintas")
ok(musica.componer(MOTORES["3"](semilla=99), 1)[0] == m3, "misma semilla y motor -> misma melodía")

print("Mezclador (con un reproductor falso que escribe a un archivo)")
salida = "/tmp/claude_audio_prueba.raw"
os.environ["TETRIS_AUDIO"] = f"sh -c 'cat > {salida}'"
from audio.reproductor import Audio
audio = Audio()
ok(audio.disponible, "el reproductor se abre")
audio.musica_para(MOTORES["3"], 1, 1)
audio.efecto("rotar")
time.sleep(2.0)
audio.cerrar()
time.sleep(0.2)
segundos = os.path.getsize(salida) / 2 / TASA
ok(1.8 <= segundos <= 2.4, f"envía audio al ritmo del reloj: {segundos:.2f} s en 2 s")
ok(audio.info_musica.startswith("Do mayor"), f"la música se compuso en segundo plano: {audio.info_musica}")
del os.environ["TETRIS_AUDIO"]
