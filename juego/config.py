"""
Reglas del juego en un solo lugar. Si el equipo cambia algún valor,
solo se toca este archivo.
"""

PUNTOS_POR_LINEA = 100

# Puntos que hay que hacer DENTRO de cada nivel para pasarlo.
# Al subir de nivel el contador del nivel vuelve a 0 y el sobrante se descarta
# (el total de la partida sí se conserva).
METAS_NIVEL = (1000, 2000, 3000, 4000, 5000)

VIDAS_INICIALES = 5
FILAS_POR_VIDA = 2          # cuánto baja la línea azul por cada vida perdida

INTERVALO_BASE = 0.6        # segundos entre pasos de gravedad en el nivel 1
INCREMENTO_VELOCIDAD = 0.05 # +5% por nivel: nivel 5 -> x1.20