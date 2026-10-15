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

# Modo hardcore (tecla T): probabilidad (%) de que la pieza tiemble
# una columna en cada paso de gravedad, según el nivel.
PROBABILIDAD_TEMBLOR = (10, 15, 20, 25, 30)
# Modo 2 jugadores: gana quien llegue primero a esta cantidad de puntos
# (o el que siga en pie si el otro pierde todas sus vidas).
META_VERSUS = 1000

# Tabla de puntuaciones (solo modo 1 jugador)
RANKING_MAXIMO = 10         # cuántas partidas guarda la tabla
LARGO_NOMBRE = 16           # caracteres máximos del nombre del jugador

# Modo tablero hardcore (se elige al empezar, solo 1 jugador): "puntos muertos",
# casillas grises que flotan en el tablero y se comportan como un bloque más.
PUNTOS_MUERTOS = (3, 3, 3, 4, 5)   # cantidad por nivel
FILAS_SIN_MUERTOS = 5              # las primeras filas quedan libres para que
                                   # ninguna pieza aparezca encima de uno
