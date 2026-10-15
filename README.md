# Tetris CLI — Reto 2

Tetris para la terminal escrito en Python, donde **todo lo aleatorio lo deciden generadores de números pseudoaleatorios implementados a mano**, sin usar `random`, `secrets`, `numpy` ni ninguna otra librería de aleatoriedad.

El jugador puede cambiar de motor en plena partida y ver en un panel los números que se están generando, para comparar cómo se comporta cada método.

Tiene **dos interfaces que comparten exactamente la misma lógica en Python**:

| Versión | Cómo se juega | Sonido |
|---|---|---|
| **Web** | En el navegador, en cualquier sistema operativo o celular. Publicada en GitHub Pages. | Siempre funciona (lo reproduce el navegador) |
| **Terminal** | `python3 main.py`, con curses | Linux con `paplay`, `aplay` o `pw-play` |

**▶ Jugar en línea:** https://odysseus-17.github.io/Tetris-Reto2/

```
  │ · · · · · · · · · ·│   MOTOR [3] PCG32
  │ · · · · · · · · · ·│   Semilla: 4180726106
  │ · · · · · · · · · ·│   Últimos números:
  │ · · · · · · · · · ·│     3774991495
  │ · · · · · · · · · ·│     473553775
  │ · · · · · · · · · ·│   Próxima pieza: rango(7) -> Z
  │ · · · · · · · · · ·│   Columna:       rango(n) -> 5
  │ · · · · · · · · · ·│
  │ · · · · · · · · · ·│   NIVEL 1/5     Vidas ♥♥♥♥♥
  │ · · · · · ·     · ·│   Puntos del nivel: 0 / 1000
  │ · · · · ·     · · ·│   ░░░░░░░░░░░░░░░░░░░░   0%
  │ · · · · · · · · · ·│   Total: 0   Líneas: 0
  │ · · · · · · · · · ·│   Velocidad: x1.00   Zona: 20x10
  │ · · · · · · · · · ·│   HARDCORE 10%
  │ · · · · · · · · · ·│   Siguiente:
  │ · · · · · ·[][] · ·│   ♪ Do mayor · 100 bpm   (m silenciar)
  │ · · · · ·[][] · · ·│   ←→ mover  ↑ rotar  ↓ bajar  espacio soltar
  └────────────────────┘   1-4 motor  t hardcore  p pausa  q salir
```

---

## Contenido

- [Inicio rápido](#inicio-rápido)
- [Versión web](#versión-web)
- [Requisitos del sistema](#requisitos-del-sistema)
- [Controles](#controles)
- [Motores de números aleatorios](#motores-de-números-aleatorios)
- [Qué controla el azar en el juego](#qué-controla-el-azar-en-el-juego)
- [Reglas del juego](#reglas-del-juego)
- [Modo tablero hardcore](#modo-tablero-hardcore)
- [Tabla de puntuaciones](#tabla-de-puntuaciones)
- [Sonido procedural](#sonido-procedural)
- [Pruebas](#pruebas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Solución de problemas](#solución-de-problemas)

---

## Inicio rápido

**Linux**

```bash
git clone https://github.com/Odysseus-17/Tetris-Reto2.git
cd Tetris-Reto2
python3 main.py
```

**Windows** (PowerShell o Windows Terminal)

```powershell
git clone https://github.com/Odysseus-17/Tetris-Reto2.git
cd Tetris-Reto2
py -m pip install windows-curses
py main.py
```

> Todos los comandos se ejecutan desde la carpeta raíz del proyecto (donde está `main.py`), porque el juego importa sus módulos con rutas relativas a esa carpeta.

---

## Versión web

La interfaz gráfica ejecuta **los mismos archivos Python** de `motores/`, `juego/` y `audio/` dentro del navegador, gracias a [Pyodide](https://pyodide.org) (el intérprete de Python compilado a WebAssembly). No hay servidor que ejecute el juego: todo corre en el equipo del jugador.

```
┌──────────────────────── Navegador ────────────────────────┐
│  app.js  (dibujo en canvas, teclado, Web Audio)           │
│     │ JSON                                                │
│  web/puente.py ──► juego/partida.py ──► motores/*.py      │   hilo principal
├───────────────────────────────────────────────────────────┤
│  audio_worker.js                                          │
│  web/puente_audio.py ──► audio/musica.py, efectos.py      │   hilo de audio
└───────────────────────────────────────────────────────────┘
```

- `web/puente.py` cumple el mismo papel que `interfaz/pantalla.py`: traduce, no tiene reglas. Ninguna regla del juego se reescribió en JavaScript.
- Componer la música tarda alrededor de un segundo en el navegador, así que el audio corre en un **Web Worker** (un hilo aparte) para que el juego no se congele, igual que el mezclador de la versión de terminal.
- El sonido lo reproduce la Web Audio API del navegador, por eso funciona igual en Linux, Windows, macOS y celulares.

### Modo 2 jugadores

En el menú, la tecla **V** abre el modo de pantalla dividida para dos personas en el mismo teclado. Cada jugador elige su propio motor de números aleatorios y construye su torre; en el centro, dos torres de progreso muestran quién va más cerca de la meta.

| | Jugador 1 | Jugador 2 |
|---|---|---|
| Mover | `A` `D` | `←` `→` |
| Rotar | `W` | `↑` |
| Bajar | `S` | `↓` |
| Soltar | `Espacio` | `Enter` |
| Cambiar motor | `1` `2` `3` `4` | `7` `8` `9` `0` |

`T` activa el modo hardcore para los dos a la vez, `P` pausa, `M` silencia y `Esc` vuelve al menú.

**Reglas:** gana quien llegue primero a **1000 puntos** (`META_VERSUS` en `juego/config.py`). Cada jugador conserva sus 5 vidas y su línea azul; si uno pierde todas sus vidas, gana el otro. La partida empieza con una cuenta regresiva de 3 segundos y al terminar se puede pedir la revancha con `R`.

Las reglas están en `juego/versus.py`, que crea dos `Partida` normales y solo decide quién gana. Como el navegador solo repite la última tecla mantenida, la repetición de teclas de cada jugador se maneja en `web/versus.js`, para que los dos puedan mantener teclas al mismo tiempo.

### Jugar localmente

El navegador no permite cargar los archivos `.py` abriendo `index.html` con doble clic (`file://`), así que se necesita un servidor local. Python ya trae uno:

```bash
python3 -m http.server 8000      # en Windows: py -m http.server 8000
```

Y abrir **http://localhost:8000/web/**. La primera carga descarga Pyodide (unos 10 MB) desde el CDN de jsDelivr y requiere internet; después queda en la caché del navegador.

### Publicar en GitHub Pages

1. Subir el repositorio completo, incluidos `index.html` y `.nojekyll` en la raíz.
2. En GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, rama `main`, carpeta `/ (root)`, **Save**.
3. En uno o dos minutos el juego queda en `https://<usuario>.github.io/<repositorio>/`.

El archivo `.nojekyll` es necesario: sin él, GitHub Pages ignora los archivos que empiezan con guion bajo, como `__init__.py`, y el juego no carga. El `index.html` de la raíz solo redirige a `web/`.

### Publicar en Render

El repositorio incluye `render.yaml`, así que Render lee la configuración solo. Se publica como **sitio estático**: es gratis y, a diferencia de los servicios web del plan gratuito, no se suspende por inactividad.

1. Crear una cuenta en [render.com](https://render.com) e iniciar sesión con GitHub.
2. **New → Blueprint**, elegir este repositorio y confirmar con **Apply**.
3. Al terminar, el juego queda en `https://tetris-reto2.onrender.com` (si el nombre está ocupado, Render agrega un sufijo).

Cada `git push` a `main` vuelve a publicar el sitio automáticamente.

Si se prefiere configurarlo a mano: **New → Static Site**, elegir el repositorio y llenar:

| Campo | Valor |
|---|---|
| Branch | `main` |
| Build Command | `mkdir -p public && cp -r web motores juego audio public/` |
| Publish Directory | `public` |

y en **Redirects/Rewrites** agregar una regla *Redirect* de `/` a `/web/`.

El comando de compilación copia a `public/` solo lo que usa la versión web (la interfaz y los `.py` del juego), así no se publican las pruebas ni los audios de demostración.

### Requisitos

Un navegador actual (Chrome, Edge, Firefox o Safari) con JavaScript y WebAssembly. Funciona con teclado en el computador y con botones táctiles en el celular.

---

## Requisitos del sistema (versión de terminal)

### Comunes

| Requisito | Detalle |
|---|---|
| Python | 3.8 o superior |
| Terminal | Al menos **64 columnas × 24 filas**. Si es más pequeña, el juego lo avisa en vez de romperse. |
| Codificación | UTF-8, para dibujar `│ ━ ♥ █ ░ ♪` |
| Colores | 256 colores recomendados (la barra de avance usa un degradado). Con 8 colores también funciona. |
| Librerías externas | Ninguna en Linux. Solo `windows-curses` en Windows. |

### Linux

La interfaz usa `curses`, que ya viene incluido en Python.

Para el sonido se necesita **uno** de estos reproductores, que el juego busca en este orden:

| Reproductor | Paquete | Instalación |
|---|---|---|
| `paplay` | PulseAudio / PipeWire-Pulse | Debian/Ubuntu: `sudo apt install pulseaudio-utils`<br>Fedora: `sudo dnf install pulseaudio-utils`<br>Arch: `sudo pacman -S libpulse` |
| `aplay` | ALSA | Debian/Ubuntu: `sudo apt install alsa-utils`<br>Fedora: `sudo dnf install alsa-utils`<br>Arch: `sudo pacman -S alsa-utils` |
| `pw-play` | PipeWire | Viene con PipeWire en la mayoría de distribuciones actuales |

Para saber cuáles tienen instalados:

```bash
which paplay aplay pw-play
```

Si no hay ninguno, el juego funciona igual y el panel muestra "Sonido: no disponible".

Sirve cualquier emulador de terminal moderno con UTF-8 (GNOME Terminal, Konsole, Kitty, Alacritty, el de VS Code).

### Windows

1. Instalar [Python 3](https://www.python.org/downloads/) y marcar **"Add Python to PATH"** durante la instalación.
2. Instalar el soporte de `curses`, que en Windows no viene incluido:
   ```powershell
   py -m pip install windows-curses
   ```
3. Ejecutar el juego en **Windows Terminal** (viene en Windows 11 y se instala gratis desde la Microsoft Store en Windows 10). La consola clásica `cmd.exe` puede dibujar mal los caracteres especiales y los colores.

**Sonido en Windows:** el juego reproduce el audio enviándolo a `paplay`, `aplay` o `pw-play`, que no existen en Windows nativo. Allí el juego funciona completo pero **sin sonido**. Para tener sonido en Windows, la opción recomendada es WSL (abajo).

### Windows con WSL (recomendado para tener sonido)

En Windows 11 y Windows 10 actualizado, WSL incluye WSLg, que redirige el audio de Linux a los parlantes de Windows.

```powershell
wsl --install            # solo la primera vez; reinicia el equipo
```

Luego, dentro de la terminal de Ubuntu:

```bash
sudo apt update && sudo apt install python3 git pulseaudio-utils
git clone https://github.com/Odysseus-17/Tetris-Reto2.git
cd Tetris-Reto2
python3 main.py
```

---

## Controles

| Tecla | Acción |
|---|---|
| `←` `→` | Mover la pieza |
| `↑` | Rotar |
| `↓` | Bajar más rápido |
| `Espacio` | Soltar la pieza de golpe |
| `1` `2` `3` `4` | Cambiar el motor de números aleatorios en plena partida |
| `T` | Activar o desactivar el modo hardcore |
| `M` | Silenciar o activar el sonido |
| `P` | Pausa |
| `R` | Reiniciar (en la pantalla de fin del juego) |
| `L` | Ver la tabla de puntuaciones (en el menú) |
| `Q` | Salir |

El dispositivo de entrada es el **teclado**.

---

## Motores de números aleatorios

Los cuatro motores comparten la misma interfaz (`motores/base.py`): el juego solo llama a `motor.rango(n)`, que devuelve un entero entre `0` y `n − 1`. Por eso cambiar de motor no cambia nada más del código.

`rango(n)` escala el número (`x · n // MÁXIMO`) en vez de usar `x % n`, para que el resultado dependa de los bits altos, que en los generadores congruenciales son los de mejor calidad.

La semilla sale del reloj del sistema en nanosegundos (`time.time_ns()`), que no es una librería de aleatoriedad.

| Tecla | Motor | Fórmula | Período | Observaciones |
|---|---|---|---|---|
| `1` | **Cuadrado medio** (von Neumann, 1946) | Elevar al cuadrado un número de 8 dígitos y tomar los 8 del centro | Corto y variable | Se degenera (cae en 0 o en ciclos). El motor lo detecta y se **re-siembra**; el panel muestra cuántas veces. |
| `2` | **Congruencial lineal** (Lehmer, 1949) | `X(n+1) = (a·X(n) + c) mod m`<br>a = 1 664 525, c = 1 013 904 223, m = 2³² | 2³² (completo, por el teorema de Hull-Dobell) | Sus bits bajos son predecibles: el último bit alterna 0, 1, 0, 1… |
| `3` | **PCG32 XSH-RR** (O'Neill, 2014) | LCG de 64 bits + permutación de la salida (xorshift y rotación variable) | 2⁶⁴ | Corrige el defecto del LCG. Verificado contra la implementación de referencia en C. |
| `4` | **Xoshiro256\*\*** (Blackman y Vigna, 2018) | Estado de 4 × 64 bits mezclado solo con XOR, desplazamientos y rotaciones; salida `rotl(s1·5, 7)·9` | 2²⁵⁶ − 1 | Otra familia: sin multiplicación congruencial. El estado se siembra con SplitMix64. Entrega 64 bits por número. Verificado contra los vectores de referencia. |

---

## Qué controla el azar en el juego

| Aspecto | Llamada al motor |
|---|---|
| Qué pieza aparece (I, O, T, S, Z, J, L) | `rango(7)` |
| En qué columna aparece | `rango(10 − ancho_de_la_pieza + 1)` |
| Si la pieza tiembla en el aire (modo hardcore) | `rango(100) < probabilidad del nivel` |
| Hacia dónde tiembla | `rango(2)` |
| Las notas de la música | Un motor propio de la misma clase (ver [Sonido procedural](#sonido-procedural)) |
| El ruido del golpe al fijar una pieza | El motor congruencial con semilla fija |

Con la misma semilla y el mismo motor, la secuencia de piezas y columnas es siempre idéntica.

---

## Reglas del juego

Todos los valores están en `juego/config.py`, así que se pueden cambiar en un solo lugar.

| Regla | Valor |
|---|---|
| Puntos por línea completada | 100 |
| Niveles | 5 |
| Meta de cada nivel | 1000 · 2000 · 3000 · 4000 · 5000 puntos |
| Vidas | 5 |
| Velocidad de caída | Aumenta 5 % por nivel: ×1.00, ×1.05, ×1.10, ×1.15, ×1.20 |
| Probabilidad de temblor (hardcore) | 10 % · 15 % · 20 % · 25 % · 30 % según el nivel |

**Niveles.** Cada nivel pide sus propios puntos empezando desde 0; los puntos que sobren al completarlo se descartan. Al subir de nivel el tablero se limpia. La barra de avance muestra `puntos del nivel / meta del nivel` y va del azul al rojo. Al completar el nivel 5 se gana la partida.

**Vidas y línea limitadora.** Cada vida perdida baja una línea azul dos filas, reduciendo el espacio jugable:

| Vidas | Zona jugable |
|---|---|
| 5 | 20 × 10 (sin línea) |
| 4 | 18 × 10 |
| 3 | 16 × 10 |
| 2 | 14 × 10 |
| 1 | 12 × 10 |

Se pierde una vida cuando una pieza queda fija con algún bloque por encima de la línea (o, con 5 vidas, cuando una pieza nueva ya no cabe arriba). La revisión se hace después de limpiar las líneas completadas. Al perder una vida el tablero se limpia, pero se conservan el nivel y los puntos. Al perder la última vida termina la partida, y con `R` se empieza otra desde el nivel 1.

**Modo hardcore (`T`).** En cada paso de gravedad, el motor decide si la pieza se corre una columna a la izquierda o a la derecha, al estilo de *Tricky Towers*. Si choca con una pared o con otra pieza, no se mueve.

---

## Modo tablero hardcore

Opcional y solo en el modo de 1 jugador. Después de escribir el nombre, el juego pregunta **¿Activar modo tablero hardcore?** (`S` / `N`). Al activarlo aparecen **puntos muertos**: casillas grises que flotan en el tablero.

| Nivel | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Puntos muertos | 3 | 3 | 3 | 4 | 5 |

- **Las piezas se apoyan en ellos y se quedan ahí**, flotando. Apoyarse en un punto muerto no cuesta una vida.
- **Su ubicación la decide el motor de números aleatorios** activo: se sortea una casilla con `motor.rango(casillas_posibles)` por cada punto muerto, sin repetir. Es otro uso visible de los generadores: con la misma semilla y el mismo motor, aparecen en las mismas casillas.
- **Nunca aparecen en las primeras 5 filas**, para que ninguna pieza nueva caiga encima de uno, **ni por encima de la línea azul**, porque eso sería perder una vida sin jugar.
- **Cambian de lugar al perder una vida y al subir de nivel**: el tablero se limpia y se sortean de nuevo, evitando las casillas que tenían antes.
- **Cuentan como casilla llena para completar una fila.** Si no contaran, una fila con un punto muerto nunca podría completarse. Al completarla, el punto muerto desaparece con ella; si se limpian filas debajo de él, baja junto con su fila, como cualquier bloque.

La tabla de puntuaciones marca las partidas jugadas en este modo (☠ en la web, `*` en la terminal), porque no son comparables con las normales. La revancha con `R` repite el nombre y el modo.

Los valores están en `juego/config.py` (`PUNTOS_MUERTOS` y `FILAS_SIN_MUERTOS`) y la lógica en `juego/partida.py`. Para el tablero, un punto muerto es simplemente una casilla ocupada (`MUERTO = "X"` en `juego/tablero.py`), así que las colisiones y la limpieza de filas no necesitaron cambios.

## Tabla de puntuaciones

Solo en el modo de 1 jugador; el modo 2 jugadores no la usa.

1. Después de elegir el motor, el juego pregunta el nombre del jugador (hasta 16 caracteres). La revancha con `R` usa el mismo nombre.
2. Al terminar la partida, por perder todas las vidas o por ganar, se registra una fila con **nombre, nivel alcanzado y puntos acumulados** de la partida, además del motor usado y la fecha.
3. La pantalla final muestra la tabla con la partida recién jugada resaltada y el puesto obtenido. Desde el menú, la tecla `L` la muestra en cualquier momento.

La tabla guarda las **10 mejores partidas**, ordenadas por puntos; si empatan, gana el que llegó a un nivel mayor, y si también empatan, quien lo logró primero conserva el puesto. Un mismo nombre puede aparecer varias veces, una por partida. Salir con `Q` a mitad de una partida no la registra.

La lógica está en `juego/ranking.py` y es la misma para las dos interfaces; solo cambia dónde se guarda:

| Versión | Dónde se guarda | Alcance |
|---|---|---|
| Terminal | `datos/ranking.json` | En ese computador, para cualquiera que juegue desde esa carpeta |
| Web | Almacenamiento del navegador (`localStorage`) | En ese navegador y computador. Se pierde si se borran los datos del sitio |

La versión web no tiene servidor, así que cada navegador tiene su propia tabla. Una tabla compartida entre todos los jugadores del enlace necesitaría un servidor con base de datos.

## Sonido procedural

Ningún sonido viene de un archivo: todos se **calculan** muestra por muestra (22 050 por segundo) con ondas senoidales, cuadradas y triangulares, usando solo `math`, `array` y `wave` de la librería estándar.

**Efectos:** mover, rotar, fijar la pieza, completar líneas (el arpegio crece con la cantidad de líneas), temblor, subir de nivel, perder una vida, fin del juego y victoria.

**Música:** la melodía la compone el motor de números aleatorios activo, con cuatro reglas que evitan la disonancia:

1. **Escala pentatónica.** El motor elige posiciones dentro de 5 notas (Do, Re, Mi, Sol, La) que no forman semitonos entre sí, nunca frecuencias libres.
2. **Movimiento por pasos.** El motor decide cuánto se mueve la melodía (repetir, subir o bajar uno o dos), no a qué nota salta.
3. **Acordes con anclaje.** Un bajo toca Do – La menor – Fa – Sol, y el primer tiempo de cada compás cae siempre en una nota del acorde.
4. **Ritmo cerrado.** Cada tiempo es una negra o dos corcheas, así los compases siempre quedan completos.

Cada motor compone una melodía distinta y cada nivel sube la tonalidad un tono y el tempo 10 bpm (de Do mayor a 100 bpm hasta Sol# mayor a 140 bpm). La música usa su propia instancia del motor, así que no altera la secuencia de piezas.

El audio se mezcla en un hilo aparte y se envía a un único proceso del sistema, por lo que el juego nunca se congela esperando al sonido.

---

## Pruebas

Las pruebas no usan librerías externas ni necesitan abrir la interfaz.

```bash
python3 pruebas_motores.py   # los cuatro generadores
python3 juego/pruebas_juego.py   # lógica del Tetris, niveles, vidas, hardcore
python3 juego/pruebas_versus.py  # modo 2 jugadores
python3 juego/pruebas_ranking.py # tabla de puntuaciones
python3 juego/pruebas_muertos.py # modo tablero hardcore
python3 pruebas_audio.py     # sintetizador, música y mezclador (no necesita parlantes)
```

En Windows, reemplazar `python3` por `py`.

| Archivo | Qué verifica |
|---|---|
| `pruebas_motores.py` | PCG32, Xoshiro256** y SplitMix64 contra sus referencias; teorema de Hull-Dobell; degeneración del cuadrado medio; defecto de los bits bajos del LCG; distribución de 70 000 piezas por motor con prueba de **chi-cuadrado** |
| `juego/pruebas_muertos.py` | Cantidad por nivel, filas permitidas, que los decida el motor, cambio de lugar al perder una vida y al subir de nivel, piezas apoyadas, filas completadas con puntos muertos |
| `juego/pruebas_ranking.py` | Limpieza de nombres, orden y desempates, límite de 10 partidas, archivo vacío o dañado, persistencia en disco |
| `juego/pruebas_versus.py` | Partidas independientes, motor propio por jugador, victoria por meta y por vidas, que la torre del ganador no se borre |
| `juego/pruebas_juego.py` | Rotación, colisiones, limpieza de líneas, aparición controlada por el motor, cambio de motor, puntaje, niveles, vidas, línea limitadora, velocidad y frecuencia del temblor |
| `pruebas_audio.py` | Afinación del sintetizador; 18 215 notas generadas con los 4 motores, 5 niveles y 20 semillas, todas dentro de la escala y ancladas a los acordes; ritmo del mezclador |

**Demostración del sonido** sin abrir el juego:

```bash
python3 demo_audio.py              # guarda todos los sonidos como .wav en sonidos_demo/
python3 demo_audio.py --escuchar   # además los reproduce
```

---

## Estructura del proyecto

```
Tetris-Reto2/
├── main.py                  # punto de entrada
├── motores/                 # generadores de números aleatorios
│   ├── base.py              #   interfaz común: siguiente() y rango(n)
│   ├── cuadrado_medio.py
│   ├── congruencial.py
│   ├── pcg.py
│   └── xoshiro.py
├── juego/                   # reglas del juego, sin nada de interfaz
│   ├── config.py            #   todos los valores ajustables
│   ├── piezas.py
│   ├── tablero.py
│   ├── partida.py
│   ├── versus.py            #   modo 2 jugadores: decide quién gana
│   ├── ranking.py           #   tabla de puntuaciones (1 jugador)
│   ├── pruebas_muertos.py
│   ├── pruebas_juego.py
│   └── pruebas_versus.py
├── interfaz/
│   └── pantalla.py          # dibujo y teclado con curses
├── audio/                   # sonido procedural
│   ├── sintetizador.py      #   formas de onda y envolventes
│   ├── efectos.py
│   ├── musica.py            #   composición con el motor
│   └── reproductor.py       #   mezclador en tiempo real (solo terminal)
├── web/                     # interfaz gráfica para el navegador
│   ├── index.html
│   ├── estilos.css
│   ├── app.js               #   dibujo, teclado y Web Audio
│   ├── versus.js            #   pantalla dividida para 2 jugadores
│   ├── comun.js             #   carga de Pyodide y de los archivos .py
│   ├── audio_worker.js      #   hilo de audio
│   ├── puente.py            #   JavaScript ⇄ juego/partida.py
│   └── puente_audio.py      #   JavaScript ⇄ audio/
├── datos/
│   └── ranking.json         # tabla de puntuaciones de la versión de terminal
├── index.html               # redirige a web/ (GitHub Pages)
├── .nojekyll                # para que GitHub Pages publique los __init__.py
├── render.yaml              # despliegue en Render (sitio estático)
├── pruebas_motores.py
├── pruebas_audio.py
└── demo_audio.py
```

La lógica (`juego/`) no depende de la interfaz ni del audio: la partida solo anota eventos y la interfaz decide cómo mostrarlos y qué sonido reproducir. Eso permite probar todo sin abrir ninguna ventana, y es lo que hizo posible agregar la versión web sin modificar una sola línea de `juego/` ni de `motores/`.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named '_curses'` (Windows) | `py -m pip install windows-curses` |
| `ModuleNotFoundError: No module named 'motores'` | Ejecutar el juego desde la carpeta raíz del proyecto, no desde una subcarpeta. |
| "Agranda la terminal" | Maximizar la ventana o reducir el tamaño de la fuente. Mínimo 64 × 24. |
| Aparecen símbolos raros en vez de `│ ♥ █` | Usar una terminal con UTF-8 (en Windows, Windows Terminal). En Linux, revisar que `echo $LANG` termine en `UTF-8`. |
| "Sonido: no disponible" | Instalar `pulseaudio-utils` o `alsa-utils` (Linux), o usar WSL (Windows). |
| No suena aunque el panel muestra la música | Revisar que no esté silenciado con `M` y el volumen del sistema. Para forzar un reproductor: `TETRIS_AUDIO="aplay -q -t raw -f S16_LE -r 22050 -c 1" python3 main.py` |
| Las flechas tardan en responder | Usar una terminal moderna; algunas terminales antiguas envían las flechas con retraso. |
| La terminal queda desordenada tras un cierre forzado | Ejecutar `reset` (Linux). |
| **Web:** "No se pudo cargar" al abrir `index.html` con doble clic | Usar un servidor local: `python3 -m http.server 8000` y abrir `http://localhost:8000/web/`. |
| **Web:** se queda en "Descargando Python…" | Revisar la conexión a internet; la primera carga descarga Pyodide desde jsDelivr. |
| **Web:** el juego carga en GitHub Pages pero falla al iniciar | Verificar que el archivo `.nojekyll` esté en la raíz del repositorio. |
| **Web:** después de actualizar el juego no aparecen los cambios (por ejemplo, la tecla V no abre el modo 2 jugadores) | El navegador está usando archivos viejos guardados en caché. Recargar forzando con `Ctrl + Shift + R` (en Mac `Cmd + Shift + R`) o abrir el enlace en una ventana de incógnito. |
| **Web:** no suena | Los navegadores solo permiten sonido después de pulsar una tecla o hacer clic; elegir el motor ya lo activa. Revisar también que no esté silenciado con `M`. |

---

## Créditos

Proyecto académico de Ingeniería de Sistemas — Reto 2: videojuego con generadores de números pseudoaleatorios propios.

Referencias de los algoritmos:

- J. von Neumann, *Various techniques used in connection with random digits*, 1951.
- D. H. Lehmer, *Mathematical methods in large-scale computing units*, 1949.
- T. E. Hull y A. R. Dobell, *Random Number Generators*, SIAM Review, 1962.
- M. E. O'Neill, *PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation*, 2014.
