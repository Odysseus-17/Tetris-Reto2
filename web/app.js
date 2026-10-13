// Interfaz gráfica del Tetris.
//
// Este archivo hace lo mismo que interfaz/pantalla.py en la versión de
// terminal: dibuja, lee el teclado y reproduce sonidos. Las reglas del juego
// y los motores aleatorios NO están aquí: se ejecutan en Python (Pyodide),
// usando exactamente los mismos archivos de juego/ y motores/.

const params = new URLSearchParams(location.search);
const PYODIDE_URL = new URL(params.get("pyodide") || PYODIDE_CDN, location.href).href;
const RAIZ = new URL("../", location.href).href;   // carpeta raíz del proyecto

const COLORES = {
  I: "#2ee6f0", O: "#f5d63d", T: "#b45cf0", S: "#4fdc6b",
  Z: "#f0525b", J: "#3f7cf5", L: "#f59a3a",
};
const DURACION_AVISO = 1500;

const $ = (id) => document.getElementById(id);

let puente = null;           // módulo web/puente.py
let estado = null;           // último estado recibido de Python
let fase = "carga";          // carga | menu | juego | versus-config | versus
let claveInicial = "3";
let pausado = false;
let ultimoPaso = 0;
let avisoHasta = 0;
let listaMotores = [];

// ====================================================================
// Audio: el hilo de audio genera las muestras con Python y aquí solo se
// reproducen con la Web Audio API del navegador (igual en todo sistema).
// ====================================================================

const audio = {
  ctx: null, maestro: null, worker: null, listo: false,
  tasa: 22050, muestras: {}, buffers: {}, voces: {},
  silenciado: false, clave: null, pedido: 0, pendiente: null,
  fuente: null, descripcion: "",

  iniciar() {
    this.worker = new Worker("audio_worker.js");
    this.worker.onmessage = (e) => this.mensaje(e.data);
    this.worker.postMessage({ tipo: "iniciar", pyodideUrl: PYODIDE_URL, raiz: RAIZ });
  },

  // Los navegadores solo permiten sonido después de una acción del usuario
  desbloquear() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.maestro = this.ctx.createGain();
      this.maestro.connect(this.ctx.destination);
      this.maestro.gain.value = this.silenciado ? 0 : 1;
    }
    if (this.ctx.state === "suspended" && !pausado) this.ctx.resume();
  },

  mensaje(m) {
    if (m.tipo === "listo") {
      this.listo = true;
      this.tasa = m.tasa;
      this.muestras = m.efectos;
      if (this.pendiente) this.worker.postMessage(this.pendiente);
      actualizarSonido();
    } else if (m.tipo === "musica" && m.id === this.pedido) {
      this.descripcion = m.descripcion;
      this.tocarMusica(m.muestras);
      actualizarSonido();
    } else if (m.tipo === "error") {
      console.error("Audio:", m.mensaje);
      this.descripcion = "no disponible";
      actualizarSonido();
    }
  },

  buffer(muestras) {
    const b = this.ctx.createBuffer(1, muestras.length, this.tasa);
    b.copyToChannel(muestras, 0);
    return b;
  },

  efecto(nombre) {
    if (!this.ctx || !this.muestras[nombre]) return;
    this.buffers[nombre] ??= this.buffer(this.muestras[nombre]);
    // Si el mismo efecto ya suena (mover muy rápido), se reinicia
    try { this.voces[nombre]?.stop(); } catch (_) {}
    const voz = this.ctx.createBufferSource();
    voz.buffer = this.buffers[nombre];
    voz.connect(this.maestro);
    voz.start();
    this.voces[nombre] = voz;
  },

  musica(clave, semilla, nivel) {
    const id = `${clave}-${semilla}-${nivel}`;
    if (id === this.clave) return;
    this.clave = id;
    this.pedido += 1;
    this.descripcion = "componiendo…";
    const pedido = { tipo: "componer", id: this.pedido, clave, semilla, nivel };
    if (this.listo) this.worker.postMessage(pedido);
    else this.pendiente = pedido;
    actualizarSonido();
  },

  tocarMusica(muestras) {
    this.detenerFuente();
    if (!this.ctx) return;
    this.fuente = this.ctx.createBufferSource();
    this.fuente.buffer = this.buffer(muestras);
    this.fuente.loop = true;
    this.fuente.connect(this.maestro);
    this.fuente.start();
  },

  detenerFuente() {
    try { this.fuente?.stop(); } catch (_) {}
    this.fuente = null;
  },

  detenerMusica() {
    this.detenerFuente();
    this.clave = null;
    this.pedido += 1;            // descarta una composición en curso
    this.descripcion = "";
  },

  pausar(valor) {
    if (!this.ctx) return;
    valor ? this.ctx.suspend() : this.ctx.resume();
  },

  alternarSilencio() {
    this.silenciado = !this.silenciado;
    if (this.maestro) this.maestro.gain.value = this.silenciado ? 0 : 1;
  },
};

// ====================================================================
// Carga de Python y del juego
// ====================================================================

function cargarScript(url) {
  return new Promise((ok, falla) => {
    const s = document.createElement("script");
    s.src = url;
    s.onload = ok;
    s.onerror = () => falla(new Error("No se pudo descargar " + url));
    document.head.appendChild(s);
  });
}

async function iniciar() {
  prepararCanvas();
  dibujar();
  try {
    $("texto-carga").textContent = "Descargando Python…";
    await cargarScript(PYODIDE_URL + "pyodide.js");
    const py = await loadPyodide({ indexURL: PYODIDE_URL });
    $("texto-carga").textContent = "Cargando el juego…";
    await cargarArchivos(py, RAIZ, ARCHIVOS_JUEGO);
    puente = py.pyimport("puente");
    // Si el navegador mezcló archivos de dos versiones distintas, avisar en
    // vez de fallar en silencio más adelante.
    const faltan = ["nueva", "estado", "nuevo_versus", "estado_versus"]
      .filter((f) => typeof puente[f] !== "function");
    if (faltan.length) {
      throw new Error("El navegador cargó archivos de una versión anterior del juego. " +
        "Recarga con Ctrl + Shift + R (en Mac Cmd + Shift + R).");
    }
    listaMotores = JSON.parse(puente.motores());
    audio.iniciar();
    construirMenus();
    mostrarMenu();
    requestAnimationFrame(bucle);
  } catch (error) {
    console.error(error);
    $("texto-error").textContent = error.message +
      (location.protocol === "file:" ? " — abre la página con un servidor (ver README)." : "");
    mostrarCapa("capa-error");
  }
}

// ====================================================================
// Flujo: menú → partida → fin
// ====================================================================

function mostrarCapa(id) {
  for (const capa of document.querySelectorAll(".capa")) {
    capa.classList.toggle("visible", capa.id === id);
  }
}

function construirMenus() {
  const menu = $("opciones-menu");
  const rango = `1–${listaMotores.length}`;
  $("ayuda-menu").textContent = `Teclas ${rango} · o haz clic`;
  $("tecla-motores").textContent = rango;
  const pestanas = $("pestanas-motor");
  for (const m of listaMotores) {
    const b = document.createElement("button");
    b.tabIndex = -1;
    b.innerHTML = `<kbd>${m.clave}</kbd>${m.nombre}`;
    b.onclick = () => { audio.desbloquear(); empezar(m.clave); };
    menu.appendChild(b);

    const p = document.createElement("button");
    p.tabIndex = -1;
    p.dataset.clave = m.clave;
    p.innerHTML = `<kbd>${m.clave}</kbd>${m.nombre}`;
    p.onclick = () => {
      audio.desbloquear();
      if (fase === "juego") ejecutar(m.clave);
      else if (fase === "menu") empezar(m.clave);
    };
    pestanas.appendChild(p);
  }
  $("boton-versus").onclick = () => { audio.desbloquear(); versus.configurar(); };
  versus.construir();
  $("boton-reiniciar").onclick = () => empezar(claveInicial);
  $("boton-menu").onclick = mostrarMenu;
  $("boton-hardcore").onclick = () => fase === "juego" && ejecutar("hardcore");
  $("boton-sonido").onclick = () => { audio.desbloquear(); audio.alternarSilencio(); actualizarSonido(); };
  for (const b of document.querySelectorAll(".tactil button")) {
    b.onclick = () => {
      audio.desbloquear();
      if (fase !== "juego" || estado.terminada) return;
      const accion = b.dataset.accion;
      if (accion === "pausa") return alternarPausa();
      if (pausado) return;
      ejecutar(accion);
      if (accion === "bajar" || accion === "soltar") ultimoPaso = performance.now();
    };
  }
  // Que los botones no se queden con el foco (Espacio los volvería a pulsar)
  for (const b of document.querySelectorAll("button")) {
    b.addEventListener("mousedown", (e) => e.preventDefault());
  }
}

function mostrarMenu() {
  if (fase.startsWith("versus")) versus.salir();
  fase = "menu";
  estado = null;
  pausado = false;
  audio.detenerMusica();
  audio.pausar(false);
  mostrarCapa("capa-menu");
  actualizarSonido();
}

function empezar(clave) {
  claveInicial = clave;
  puente.nueva(clave);
  fase = "juego";
  pausado = false;
  audio.pausar(false);
  ultimoPaso = performance.now();
  mostrarCapa(null);
  refrescar();
}

function ejecutar(accion) {
  puente.accion(accion);
  refrescar();
}

function alternarPausa(valor = !pausado) {
  if (fase !== "juego" || estado?.terminada) return;
  pausado = valor;
  audio.pausar(pausado);
  mostrarCapa(pausado ? "capa-pausa" : null);
  if (!pausado) ultimoPaso = performance.now();
}

// Lee el estado de Python y reacciona: sonidos, avisos, música, panel.
function refrescar() {
  estado = JSON.parse(puente.estado());

  for (const nombre of estado.sonidos) audio.efecto(nombre);

  if (estado.evento) {
    const aviso = $("aviso");
    aviso.textContent = estado.evento === "nivel" ? `¡NIVEL ${estado.nivel}!` : "¡Perdiste una vida!";
    aviso.classList.toggle("malo", estado.evento === "vida");
    avisoHasta = performance.now() + DURACION_AVISO;
  }

  if (estado.terminada) {
    audio.detenerMusica();
    $("titulo-fin").textContent = estado.ganada ? "¡GANASTE!" : "FIN DEL JUEGO";
    $("fin-puntos").textContent = estado.puntos;
    $("fin-nivel").textContent = estado.nivel;
    mostrarCapa("capa-fin");
  } else {
    audio.musica(estado.motor.clave, estado.motor.semilla, estado.nivel);
  }
  actualizarPanel();
}

// ====================================================================
// Bucle principal: la gravedad se mide con el reloj del navegador
// ====================================================================

function bucle(ahora) {
  if (fase === "juego" && estado && !pausado && !estado.terminada &&
      ahora - ultimoPaso >= estado.intervalo * 1000) {
    puente.gravedad();
    ultimoPaso = ahora;
    refrescar();
  }
  if (fase.startsWith("versus")) {
    versus.tick(ahora);
    versus.dibujar(ahora);
  } else {
    $("aviso").classList.toggle("visible",
      fase === "juego" && !estado?.terminada && ahora < avisoHasta);
    dibujar();
  }
  requestAnimationFrame(bucle);
}

// ====================================================================
// Teclado: las mismas teclas que la versión de terminal
// ====================================================================

const ACCIONES = {
  ArrowLeft: "izquierda", ArrowRight: "derecha", ArrowUp: "rotar",
  ArrowDown: "bajar", " ": "soltar", t: "hardcore",
};

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const tecla = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", " "].includes(tecla)) e.preventDefault();
  if (e.repeat && fase.startsWith("versus")) { e.preventDefault(); return; }
  if (fase === "carga") return;
  audio.desbloquear();

  if (tecla === "m") {
    audio.alternarSilencio();
    actualizarSonido();
    return;
  }

  if (fase.startsWith("versus")) return versus.teclado(e, tecla);

  if (fase === "menu") {
    if (listaMotores.some((m) => m.clave === tecla)) empezar(tecla);
    else if (tecla === "v") versus.configurar();
    return;
  }

  if (tecla === "q" || tecla === "Escape") return mostrarMenu();
  if (estado.terminada) {
    if (tecla === "r") empezar(claveInicial);
    return;
  }
  if (tecla === "p") return alternarPausa();
  if (pausado) return;

  const esMotor = listaMotores.some((m) => m.clave === tecla);
  const accion = esMotor ? tecla : ACCIONES[tecla];
  if (!accion) return;
  ejecutar(accion);
  if (accion === "bajar" || accion === "soltar") ultimoPaso = performance.now();
});

// Pausa automática si se cambia de pestaña o ventana
window.addEventListener("blur", () => {
  if (fase === "versus") versus.pausar(true);
  else alternarPausa(true);
});

document.addEventListener("keyup", (e) => {
  const tecla = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  versus.soltarTecla(tecla);
});

// ====================================================================
// Panel lateral
// ====================================================================

function actualizarPanel() {
  const e = estado;
  const m = e.motor;

  for (const p of $("pestanas-motor").children) {
    p.classList.toggle("activo", p.dataset.clave === m.clave);
  }
  $("semilla").textContent = m.semilla;
  $("fila-resiembras").hidden = m.resiembras === null;
  $("resiembras").textContent = m.resiembras ?? 0;
  $("historial").innerHTML = m.historial.length
    ? [...m.historial].reverse().map((v) => `<li>${v}</li>`).join("")
    : '<li class="espera">Motor nuevo: genera al aparecer la próxima pieza</li>';
  $("sorteo-pieza").textContent = m.sorteo_pieza ?? "—";
  $("sorteo-columna").textContent = m.sorteo_columna ?? "—";

  $("nivel").textContent = e.nivel;
  $("niveles").textContent = `/${e.niveles}`;
  $("vidas").innerHTML = Array.from({ length: e.vidas_max },
    (_, i) => i < e.vidas ? "♥" : '<span class="vacia">♥</span>').join("");
  $("puntos-nivel").textContent = `${e.puntos_nivel} / ${e.meta}`;
  const pct = Math.round(e.progreso * 100);
  $("barra-vacia").style.width = `${100 - pct}%`;
  $("barra").setAttribute("aria-valuenow", pct);
  $("porcentaje").textContent = `${pct}%`;
  $("puntos").textContent = e.puntos;
  $("lineas").textContent = e.lineas;
  $("velocidad").textContent = `×${e.velocidad.toFixed(2)}`;
  $("zona").textContent = e.zona;

  $("boton-hardcore").classList.toggle("encendido", e.hardcore);
  $("estado-hardcore").textContent = e.hardcore ? `${e.probabilidad_temblor}%` : "apagado";
  let temblor = "";
  if (e.hardcore && e.ultimo_temblor) {
    const [dir, , seMovio] = e.ultimo_temblor;
    temblor = `último temblor: ${dir < 0 ? "←" : "→"}${seMovio ? "" : " (bloqueado)"}`;
  }
  $("temblor").textContent = temblor;
  actualizarSonido();
}

function actualizarSonido() {
  $("estado-sonido").textContent = audio.silenciado ? "silenciado" : "activo";
  $("boton-sonido").classList.toggle("encendido", audio.silenciado);
  let texto = "♪ —";
  if (fase === "juego" && audio.descripcion) texto = `♪ ${audio.descripcion}`;
  else if (!audio.listo && fase !== "carga") texto = "♪ preparando sonido…";
  $("musica").textContent = texto;
}

// ====================================================================
// Dibujo del tablero en el canvas. Estas funciones reciben el canvas y el
// estado como parámetros: las usa también la pantalla dividida (versus.js).
// ====================================================================

const lienzo = $("tablero");
const lienzoSig = $("siguiente");

// Ajusta la resolución interna del canvas a su tamaño en pantalla
function ajustarCanvas(c) {
  const escala = window.devicePixelRatio || 1;
  const r = c.getBoundingClientRect();
  if (!r.width) return;
  c.width = Math.round(r.width * escala);
  c.height = Math.round(r.height * escala);
  c.getContext("2d").setTransform(c.width / r.width, 0, 0, c.height / r.height, 0, 0);
}

function prepararCanvas() {
  ajustarCanvas(lienzo);
  ajustarCanvas(lienzoSig);
  versus.prepararCanvas();
}
window.addEventListener("resize", () => { prepararCanvas(); dibujar(); });

function bloque(x, cx, cy, tam, color) {
  x.fillStyle = color;
  x.fillRect(cx + 1, cy + 1, tam - 2, tam - 2);
  // Relieve: brillo arriba a la izquierda y sombra abajo a la derecha
  const borde = Math.max(2, Math.round(tam / 10));
  x.fillStyle = "rgba(255,255,255,.28)";
  x.fillRect(cx + 1, cy + 1, tam - 2, borde);
  x.fillRect(cx + 1, cy + 1, borde, tam - 2);
  x.fillStyle = "rgba(0,0,0,.25)";
  x.fillRect(cx + 1, cy + tam - 1 - borde, tam - 2, borde);
  x.fillRect(cx + tam - 1 - borde, cy + 1, borde, tam - 2);
}

function dibujar() {
  dibujarTablero(lienzo, estado);
  dibujarSiguiente(lienzoSig, estado?.siguiente);
}

function dibujarTablero(canvas, est) {
  const ctx = canvas.getContext("2d");
  const ancho = est?.ancho ?? 10, alto = est?.alto ?? 20;
  const r = canvas.getBoundingClientRect();
  const t = r.width / ancho;
  ctx.clearRect(0, 0, r.width, r.height);

  // Fondo con cuadrícula
  ctx.fillStyle = "#0c1020";
  ctx.fillRect(0, 0, r.width, r.height);
  ctx.strokeStyle = "rgba(255,255,255,.045)";
  ctx.lineWidth = 1;
  for (let c = 1; c < ancho; c++) {
    ctx.beginPath(); ctx.moveTo(c * t + .5, 0); ctx.lineTo(c * t + .5, r.height); ctx.stroke();
  }
  for (let f = 1; f < alto; f++) {
    ctx.beginPath(); ctx.moveTo(0, f * t + .5); ctx.lineTo(r.width, f * t + .5); ctx.stroke();
  }
  if (!est) return;

  // Zona prohibida por encima de la línea limitadora
  const limite = est.fila_limite;
  if (limite > 0) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, r.width, limite * t);
    ctx.clip();
    ctx.fillStyle = "rgba(35, 87, 255, .07)";
    ctx.fillRect(0, 0, r.width, limite * t);
    ctx.strokeStyle = "rgba(63, 140, 255, .16)";
    for (let d = -r.width; d < r.width + limite * t; d += 12) {
      ctx.beginPath(); ctx.moveTo(d, 0); ctx.lineTo(d + limite * t, limite * t); ctx.stroke();
    }
    ctx.restore();
  }

  // Bloques fijos
  est.tablero.forEach((fila, f) => fila.forEach((tipo, c) => {
    if (tipo) bloque(ctx, c * t, f * t, t, COLORES[tipo]);
  }));

  if (!est.terminada) {
    // Sombra: dónde caería la pieza
    const color = COLORES[est.pieza.tipo];
    ctx.strokeStyle = color;
    ctx.globalAlpha = .45;
    ctx.lineWidth = 2;
    for (const [f, c] of est.fantasma) ctx.strokeRect(c * t + 3, f * t + 3, t - 6, t - 6);
    ctx.globalAlpha = 1;
    for (const [f, c] of est.pieza.celdas) bloque(ctx, c * t, f * t, t, color);
  }

  // Línea limitadora azul
  if (limite > 0) {
    ctx.save();
    ctx.shadowColor = "#3f8cff";
    ctx.shadowBlur = 12;
    ctx.fillStyle = "#3f8cff";
    ctx.fillRect(0, limite * t - 2, r.width, 4);
    ctx.restore();
  }
}

function dibujarSiguiente(canvas, sig, t = 22) {
  const ctx = canvas.getContext("2d");
  const r = canvas.getBoundingClientRect();
  ctx.clearRect(0, 0, r.width, r.height);
  if (!sig) return;
  const filas = sig.forma.length, cols = sig.forma[0].length;
  const x0 = (r.width - cols * t) / 2, y0 = (r.height - filas * t) / 2;
  sig.forma.forEach((fila, f) => fila.forEach((v, c) => {
    if (v) bloque(ctx, x0 + c * t, y0 + f * t, t, COLORES[sig.tipo]);
  }));
}

iniciar();
