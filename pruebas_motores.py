"""
Pruebas de los tres motores, independientes del juego.
Ejecutar:  python3 pruebas_motores.py
"""
from motores import CuadradoMedio, CongruencialLineal, PCG32, cumple_hull_dobell

PIEZAS = "IOTSZJL"
SEMILLA = 12345
N = 70_000


def chi_cuadrado(conteos, esperado):
    return sum((o - esperado) ** 2 / esperado for o in conteos)


def histograma(motor, k, etiquetas):
    conteos = [0] * k
    for _ in range(N):
        conteos[motor.rango(k)] += 1
    esperado = N / k
    for etq, c in zip(etiquetas, conteos):
        barra = "█" * round(c / esperado * 20)
        print(f"   {etq:>2} {c:6d} {barra}")
    return chi_cuadrado(conteos, esperado)


def seccion(titulo):
    print("\n" + "=" * 60 + f"\n{titulo}\n" + "=" * 60)


seccion("1. Verificación de PCG32 contra la implementación de referencia")
pcg = PCG32(semilla=42, secuencia=54)
obtenidos = [pcg.siguiente() for _ in range(6)]
referencia = [0xa15c02b7, 0x7b47f409, 0xba1d3330, 0x83d2f293, 0xbfa4784b, 0xcbed606e]
print("   obtenidos :", " ".join(f"{v:08x}" for v in obtenidos))
print("   referencia:", " ".join(f"{v:08x}" for v in referencia))
print("   ¿Coinciden?", obtenidos == referencia)

seccion("2. Hull-Dobell para el LCG")
print("   a=1664525, c=1013904223, m=2^32 ->", cumple_hull_dobell(1664525, 1013904223, 2**32))
print("   a=1664525, c=1013904224, m=2^32 ->", cumple_hull_dobell(1664525, 1013904224, 2**32),
      "(c par: falla)")

seccion("3. Degeneración del cuadrado medio SIN re-siembra (4 dígitos)")
cm = CuadradoMedio(semilla=1234, digitos=4, resembrar=False)
secuencia = [cm.siguiente() for _ in range(60)]
print("  ", secuencia)

seccion("4. Defecto del LCG: el bit más bajo alterna 0,1,0,1...")
lcg = CongruencialLineal(semilla=SEMILLA)
print("   x % 2 ->", [lcg.siguiente() % 2 for _ in range(20)])
print("   Por eso rango() escala con los bits altos en vez de usar x % n.")

for Motor, kwargs in [(CuadradoMedio, {}), (CongruencialLineal, {}), (PCG32, {})]:
    seccion(f"Distribución de piezas: {Motor.nombre} (semilla {SEMILLA})")
    motor = Motor(semilla=SEMILLA, **kwargs)
    chi = histograma(motor, 7, PIEZAS)
    print(f"   chi² = {chi:.2f}  (con 6 grados de libertad, < 12.59 es aceptable al 95%)")
    if isinstance(motor, CuadradoMedio):
        print(f"   re-siembras necesarias: {motor.resiembras}")

seccion("Columna de aparición (tablero de 10, pieza de ancho 3 -> 8 columnas)")
motor = PCG32(semilla=SEMILLA)
chi = histograma(motor, 8, [str(i) for i in range(8)])
print(f"   chi² = {chi:.2f}  (con 7 grados de libertad, < 14.07 es aceptable al 95%)")
