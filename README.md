# Tetris — Reto 2

Tetris para el navegador en el que **todo lo aleatorio lo deciden generadores de números pseudoaleatorios implementados a mano**, sin `random`, `secrets`, `numpy` ni ninguna otra librería de aleatoriedad. El jugador elige entre cuatro motores y puede cambiarlo en plena partida mientras un panel muestra los números que se van generando.

La lógica está escrita en Python y se ejecuta **dentro del navegador** con [Pyodide](https://pyodide.org) (Python compilado a WebAssembly): no hay servidor que procese el juego y el sonido funciona igual en cualquier sistema operativo.

**▶ Jugar en línea:** https://tetris-reto2-lldk.onrender.com/web/

---

## Clonar y jugar

Se necesita **Git**, **Python 3** (solo para servir los archivos localmente) y un navegador actual: Chrome, Edge, Firefox o Safari. La primera carga descarga Pyodide (unos 10 MB) y requiere internet; después queda en la caché del navegador.

**Linux / macOS**

```bash
git clone https://github.com/Odysseus-17/Tetris-Reto2.git
cd Tetris-Reto2
python3 -m http.server 8000
```

**Windows** (PowerShell o Windows Terminal)

```powershell
git clone https://github.com/Odysseus-17/Tetris-Reto2.git
cd Tetris-Reto2
py -m http.server 8000
```

Luego, abrir **http://localhost:8000/web/** en el navegador.

> El juego no funciona abriendo `index.html` con doble clic: el navegador bloquea la carga de los archivos `.py` desde `file://`, por eso se usa el servidor local que trae Python.

---

## Funcionalidades

| Modo | Descripción |
|---|---|
| **1 jugador** | Partida de 5 niveles. Antes de empezar se pide el nombre del jugador, y al terminar la partida se registra en una **tabla de puntuaciones** (top 10, guardada en el navegador) con el nivel alcanzado y los puntos acumulados. |
| **2 jugadores** | Pantalla dividida en el mismo teclado. Cada jugador elige su motor y construye su torre; gana quien llegue primero a **1000 puntos**, o el que siga en pie si el otro pierde sus 5 vidas. Dos torres en el centro muestran el avance hacia la meta. No usa tabla de puntuaciones. |
| **Hardcore** (`T`) | Durante la partida, la pieza puede **temblar** una columna a la izquierda o a la derecha mientras cae, al estilo de *Tricky Towers*. La probabilidad sube con el nivel: 10 %, 15 %, 20 %, 25 % y 30 %. En 2 jugadores se activa para los dos a la vez. |
| **Tablero hardcore** | Solo en 1 jugador; se elige después del nombre. Aparecen **puntos muertos**: casillas grises que flotan en el tablero y sobre las que las piezas se quedan apoyadas. Hay 3 en los niveles 1 a 3, 4 en el nivel 4 y 5 en el 5; nunca en las primeras 5 filas, y cambian de lugar al perder una vida o subir de nivel. Cuentan como casilla llena para completar una fila y desaparecen con ella. |

## Reglas del juego

| Regla | Valor |
|---|---|
| Puntos por línea completada | 100 |
| Meta de cada nivel | 1000 · 2000 · 3000 · 4000 · 5000 puntos (cada nivel empieza desde 0; el sobrante se descarta) |
| Velocidad de caída | +5 % por nivel: ×1.00, ×1.05, ×1.10, ×1.15, ×1.20 |
| Vidas | 5 |
| Línea limitadora | Cada vida perdida baja una línea azul dos filas: 20×10, 18×10, 16×10, 14×10 y 12×10 |
| Perder una vida | Dejar un bloque por encima de la línea azul (o, con 5 vidas, que una pieza nueva no quepa). El tablero se limpia; el nivel y los puntos se conservan. |
| Subir de nivel | El tablero se limpia. Al completar el nivel 5 se gana la partida. |

Todos los valores están en `juego/config.py`.

## Controles

**1 jugador**

| Tecla | Acción |
|---|---|
| `←` `→` | Mover |
| `↑` | Rotar |
| `↓` | Bajar más rápido |
| `Espacio` | Soltar la pieza de golpe |
| `1` `2` `3` `4` | Cambiar de motor en plena partida |
| `T` | Activar o desactivar el modo hardcore |
| `M` | Silenciar |
| `P` | Pausa |
| `R` | Revancha, con el mismo nombre y modo (en la pantalla final) |
| `Q` / `Esc` | Volver al menú |
| `L` | Ver la tabla de puntuaciones (en el menú) |
| `V` | Abrir el modo 2 jugadores (en el menú) |

En celulares aparecen botones táctiles debajo del tablero.

**2 jugadores**

| | Jugador 1 | Jugador 2 |
|---|---|---|
| Mover | `A` `D` | `←` `→` |
| Rotar | `W` | `↑` |
| Bajar | `S` | `↓` |
| Soltar | `Espacio` | `Enter` |
| Cambiar motor | `1` `2` `3` `4` | `7` `8` `9` `0` |

`T` hardcore para ambos, `M` silencio, `P` pausa, `R` revancha y `Esc` menú.

---

## Arquitectura

```
Tetris-Reto2/
├── motores/                  # Generadores de números pseudoaleatorios
│   ├── base.py               #   Interfaz común: siguiente(), rango(n), historial
│   ├── cuadrado_medio.py     #   Motor 1
│   ├── congruencial.py       #   Motor 2
│   ├── pcg.py                #   Motor 3
│   └── xoshiro.py            #   Motor 4
├── juego/                    # Reglas del juego, sin nada de interfaz
│   ├── config.py             #   Todos los valores ajustables
│   ├── piezas.py             #   Las 7 piezas y la rotación
│   ├── tablero.py            #   Colisiones y limpieza de filas
│   ├── partida.py            #   Niveles, vidas, velocidad, hardcore, puntos muertos
│   ├── versus.py             #   Modo 2 jugadores: decide quién gana
│   ├── ranking.py            #   Tabla de puntuaciones
│   └── pruebas_*.py          #   Pruebas de cada módulo
├── audio/                    # Sonido procedural
│   ├── sintetizador.py       #   Formas de onda y envolventes
│   ├── efectos.py            #   Efectos de sonido
│   └── musica.py             #   Composición de la música con el motor
├── web/                      # Interfaz gráfica
│   ├── index.html · estilos.css
│   ├── app.js                #   Dibujo en canvas, teclado, Web Audio (1 jugador)
│   ├── versus.js             #   Pantalla dividida (2 jugadores)
│   ├── comun.js              #   Carga de Pyodide y de los archivos .py
│   ├── audio_worker.js       #   Hilo aparte que compone la música
│   ├── puente.py             #   JavaScript ⇄ juego/
│   └── puente_audio.py       #   JavaScript ⇄ audio/
├── index.html                # Redirige a web/
├── render.yaml               # Despliegue en Render (sitio estático)
└── pruebas_motores.py · pruebas_audio.py
```

**Separación de responsabilidades:** `juego/` y `motores/` no saben nada de la interfaz. JavaScript solo dibuja, lee el teclado y reproduce sonido; cada acción se envía a Python a través de `web/puente.py`, que devuelve el estado como JSON. Ninguna regla del juego está escrita en JavaScript.

---

## Motores de números pseudoaleatorios

### Interfaz común

Los cuatro motores heredan de `MotorAleatorio` (`motores/base.py`) y solo implementan `_generar()`, que devuelve el siguiente número "crudo". El juego nunca usa ese número directamente; siempre llama a:

- **`rango(n)`**: un entero entre `0` y `n − 1`. Se calcula **escalando** (`x · n // MÁXIMO`) y no con módulo (`x % n`), para que el resultado dependa de los bits altos, que en los generadores congruenciales son los de mejor calidad.
- **`historial`**: los últimos números generados, que el panel muestra en pantalla.

Por eso cambiar de motor es solo reemplazar un objeto: el resto del código no cambia. La semilla sale del reloj del sistema (`time.time_ns()`), que no es una librería de aleatoriedad.

### Qué decide el motor activo

| Aspecto del juego | Llamada |
|---|---|
| Qué pieza aparece (I, O, T, S, Z, J, L) | `rango(7)` |
| En qué columna aparece | `rango(10 − ancho de la pieza + 1)`: nunca queda fuera del tablero |
| Si la pieza tiembla (hardcore) | `rango(100) < probabilidad del nivel` |
| Hacia dónde tiembla | `rango(2)`: 0 izquierda, 1 derecha |
| Dónde quedan los puntos muertos (tablero hardcore) | `rango(casillas posibles)` por cada uno, sin repetir |
| Las notas y el ritmo de la música | Una instancia propia del mismo motor (ver [Música](#música-procedural)) |

La **rotación no es aleatoria**: las piezas siempre aparecen en su orientación base y solo el jugador las rota. Con la misma semilla y el mismo motor, la secuencia de piezas, columnas y puntos muertos es siempre idéntica.

### Los cuatro motores

**1 · Cuadrado medio** (von Neumann, 1946). Se eleva al cuadrado un número de 8 dígitos y se toman los 8 dígitos del centro como el siguiente número: `x = 5735 → x² = 32890225 → 8902`. Es el más simple, pero se **degenera**: tarde o temprano cae en 0 (y 0² = 0 para siempre) o en un ciclo corto. El motor detecta cuando un valor se repite y se **re-siembra**; el panel muestra cuántas veces lo ha hecho.

**2 · Congruencial lineal** (Lehmer, 1949). `X(n+1) = (a · X(n) + c) mod m`, con a = 1 664 525, c = 1 013 904 223 y m = 2³². Estos parámetros cumplen el **teorema de Hull-Dobell**, así que recorre los 2³² valores antes de repetir (período completo). Su debilidad es que los bits bajos son predecibles: el último bit alterna 0, 1, 0, 1… Por eso `rango()` usa los bits altos.

**3 · PCG32** (O'Neill, 2014). Un congruencial lineal de 64 bits avanza el estado, pero el estado **no se entrega directamente**: se permuta con un *xorshift* y una **rotación cuyo tamaño depende del propio estado**. Eso esconde los patrones del congruencial. Período 2⁶⁴. Verificado contra la implementación de referencia en C.

**4 · Xoshiro256\*\*** (Blackman y Vigna, 2018). Otra familia: el estado son cuatro números de 64 bits que se mezclan solo con **XOR, desplazamientos y rotaciones**, sin multiplicación congruencial; la salida es `rotl(s1 · 5, 7) · 9`. Período 2²⁵⁶ − 1. El estado se siembra con **SplitMix64**, como recomiendan los autores. Verificado contra los vectores de referencia.

En Python los enteros no tienen límite de tamaño, así que el "mod 2⁶⁴" de PCG32 y Xoshiro se aplica a mano con una máscara (`x & 0xFFFFFFFFFFFFFFFF`) después de cada operación. Los cuatro motores pasan la prueba de **chi-cuadrado** con 70 000 piezas (`pruebas_motores.py`).

---

## Música procedural

No hay archivos de audio: cada sonido se **calcula** muestra por muestra (22 050 por segundo) con ondas cuadradas, triangulares y senoidales. La melodía la **compone el motor activo**, con reglas que evitan que suene disonante: el motor nunca elige frecuencias libres, solo posiciones dentro de notas que ya suenan bien juntas.

**1. Escala pentatónica mayor.** Cinco notas por octava: **Do, Re, Mi, Sol, La** (0, 2, 4, 7 y 9 semitonos sobre la tónica). No tiene semitonos entre sus notas, que son los intervalos que causan el choque, así que cualquier combinación suena bien. La melodía usa dos octavas, 11 notas desde Do4 hasta Do6, y empieza en Do5:

```
Do4  Re4  Mi4  Sol4  La4  [Do5]  Re5  Mi5  Sol5  La5  Do6
```

**2. Movimiento por pasos.** El motor no elige a qué nota saltar, sino cuánto se mueve la melodía, con `rango(10)`:

| Paso | Probabilidad |
|---|---|
| Subir o bajar 1 nota | 60 % |
| Subir o bajar 2 notas | 20 % |
| Repetir la nota | 20 % (máximo dos veces seguidas) |

**3. Acordes con anclaje.** Debajo suena un bajo con la progresión **Do – La menor – Fa – Sol** (I – vi – IV – V), que toca la fundamental en el tiempo 1 y la quinta en el tiempo 3 de cada compás. En el primer tiempo de cada compás, la melodía se lleva a la nota del acorde más cercana, así siempre "aterriza" bien.

**4. Ritmo cerrado.** Cada tiempo es una negra (60 %) o dos corcheas (40 %), así los compases de 4/4 siempre quedan completos. Se componen 8 compases que se repiten en bucle.

**Timbre:** melodía en onda cuadrada (el sonido de las consolas de 8 bits) y bajo en onda triangular. Cada nota tiene una envolvente que sube y baja el volumen suavemente para evitar "clics". La frecuencia de cada nota sale de `f = 440 · 2^((n − 69) / 12)`, donde `n` es su número MIDI.

**Cada nivel cambia la tonalidad y el tempo**, lo que refuerza la sensación de dificultad:

| Nivel | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Tonalidad | Do mayor | Re mayor | Mi mayor | Fa# mayor | Sol# mayor |
| Tempo | 100 bpm | 110 bpm | 120 bpm | 130 bpm | 140 bpm |

La música usa una **instancia propia** del motor, con la semilla de la partida más el nivel, para no consumir los números que reparten las piezas. Con la misma semilla, cada motor compone una melodía distinta pero siempre afinada. Como componerla tarda alrededor de un segundo, se genera en un **Web Worker** (un hilo aparte) para que el juego no se congele. En 2 jugadores, la compone el motor del jugador 1.

**Efectos de sonido:** mover, rotar, fijar la pieza, completar líneas (un arpegio Do-Mi-Sol que crece con la cantidad de líneas), temblor, subir de nivel, perder una vida, fin del juego y victoria. La tecla `M` silencia todo.

---

## Referencias

- J. von Neumann, *Various techniques used in connection with random digits*, 1951.
- D. H. Lehmer, *Mathematical methods in large-scale computing units*, 1949.
- T. E. Hull y A. R. Dobell, *Random Number Generators*, SIAM Review, 1962.
- M. E. O'Neill, *PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation*, 2014.
- D. Blackman y S. Vigna, *Scrambled Linear Pseudorandom Number Generators*, 2018.
