// Modo 2 jugadores en pantalla dividida.
//
// Igual que app.js, este archivo solo dibuja, lee el teclado y reproduce
// sonidos. Las dos partidas y la regla de quién gana están en Python
// (juego/versus.py). Usa las funciones de dibujo de app.js.

const META_TEXTO = "1000";
const CUENTA_REGRESIVA = 3000;     // ms antes de empezar
const RETARDO_REPETICION = 170;    // ms que hay que mantener una tecla antes de que se repita
const INTERVALO_REPETICION = 50;   // ms entre repeticiones

// Teclas de cada jugador. Los motores se cambian con 1–4 (jugador 1)
// y con 7, 8, 9, 0 (jugador 2).
const CONTROLES = [
  {
    nombre: "Jugador 1", insignia: "J1", ayuda: "W A S D · Espacio · 1–4",
    acciones: { a: "izquierda", d: "derecha", w: "rotar", s: "bajar", " ": "soltar" },
    motores: ["1", "2", "3", "4"],
  },
  {
    nombre: "Jugador 2", insignia: "J2", ayuda: "← ↑ → ↓ · Enter · 7–0",
    acciones: { ArrowLeft: "izquierda", ArrowRight: "derecha", ArrowUp: "rotar",
                ArrowDown: "bajar", Enter: "soltar" },
    motores: ["7", "8", "9", "0"],
  },
];
const REPETIBLES = new Set(["izquierda", "derecha", "bajar"]);

const versus = {
  estado: null,
  motores: ["3", "3"],
  pausado: false,
  hardcore: false,
  ultimoPaso: [0, 0],
  empiezaEn: 0,
  avisoHasta: [0, 0],
  sostenidas: new Map(),           // tecla -> { j, accion, siguiente }
  el: [],                           // elementos del DOM de cada jugador

  // ---------------- Construcción de la pantalla ----------------

  construir() {
    for (const j of [0, 1]) {
      const c = CONTROLES[j];
      const sec = $(`vs-j${j}`);
      sec.innerHTML = `
        <header class="vs-cabecera">
          <span class="vs-insignia">${c.insignia}</span>
          <b>${c.nombre}</b>
          <span class="vs-teclas">${c.ayuda}</span>
        </header>
        <div class="vs-cuerpo">
          <div class="marco">
            <canvas class="vs-tablero" aria-label="Tablero del ${c.nombre}"></canvas>
            <div class="aviso"></div>
          </div>
          <div class="vs-lado">
            <div class="vs-bloque">
              <span>Motor</span>
              <b class="vs-motor"></b>
              <ol class="historial vs-historial"></ol>
            </div>
            <div class="vs-bloque">
              <span>Siguiente</span>
              <canvas class="vs-siguiente" aria-label="Siguiente pieza"></canvas>
            </div>
            <div class="vs-bloque">
              <span>Puntos</span>
              <b class="vs-puntos">0</b>
              <div class="vidas vs-vidas"></div>
            </div>
          </div>
        </div>`;
      this.el[j] = {
        tablero: sec.querySelector(".vs-tablero"),
        siguiente: sec.querySelector(".vs-siguiente"),
        aviso: sec.querySelector(".aviso"),
        motor: sec.querySelector(".vs-motor"),
        historial: sec.querySelector(".vs-historial"),
        puntos: sec.querySelector(".vs-puntos"),
        vidas: sec.querySelector(".vs-vidas"),
        torre: document.querySelector(`.vs-torre[data-j="${j}"] .vs-relleno`),
      };

      // Selector de motor de la pantalla de configuración
      const opciones = $(`vs-opciones-${j}`);
      listaMotores.forEach((m, i) => {
        const b = document.createElement("button");
        b.tabIndex = -1;
        b.dataset.clave = m.clave;
        b.innerHTML = `<kbd>${c.motores[i]}</kbd>${m.nombre}`;
        b.onclick = () => this.elegir(j, m.clave);
        b.addEventListener("mousedown", (e) => e.preventDefault());
        opciones.appendChild(b);
      });
    }
    $("vs-meta").textContent = META_TEXTO;
    $("vs-boton-empezar").onclick = () => this.empezar();
    $("vs-boton-revancha").onclick = () => this.empezar();
    $("vs-boton-menu").onclick = () => mostrarMenu();
    for (const b of document.querySelectorAll("#modo-2 button")) {
      b.addEventListener("mousedown", (e) => e.preventDefault());
    }
  },

  prepararCanvas() {
    for (const e of this.el) {
      if (!e) continue;
      ajustarCanvas(e.tablero);
      ajustarCanvas(e.siguiente);
    }
  },

  // ---------------- Flujo: configuración → cuenta → duelo → fin ----------------

  configurar() {
    fase = "versus-config";
    this.estado = null;
    this.sostenidas.clear();
    audio.detenerMusica();
    $("modo-1").hidden = true;
    $("modo-2").hidden = false;
    this.prepararCanvas();
    this.mostrarCapa("vs-capa-config");
    this.marcarSeleccion();
  },

  salir() {
    this.sostenidas.clear();
    this.pausado = false;
    $("modo-2").hidden = true;
    $("modo-1").hidden = false;
    prepararCanvas();
  },

  elegir(j, clave) {
    this.motores[j] = clave;
    this.marcarSeleccion();
  },

  marcarSeleccion() {
    for (const j of [0, 1]) {
      for (const b of $(`vs-opciones-${j}`).children) {
        b.classList.toggle("activo", b.dataset.clave === this.motores[j]);
      }
    }
  },

  empezar() {
    puente.nuevo_versus(this.motores[0], this.motores[1]);
    if (this.hardcore) {
      // El modo hardcore se mantiene en la revancha, para los dos por igual
      puente.accion_jugador(0, "hardcore");
      puente.accion_jugador(1, "hardcore");
    }
    fase = "versus";
    this.pausado = false;
    audio.pausar(false);
    this.sostenidas.clear();
    this.empiezaEn = performance.now() + CUENTA_REGRESIVA;
    this.ultimoPaso = [this.empiezaEn, this.empiezaEn];
    this.avisoHasta = [0, 0];
    this.mostrarCapa("vs-capa-cuenta");
    this.refrescar();
  },

  mostrarCapa(id) {
    for (const capa of document.querySelectorAll(".vs-capa")) {
      capa.classList.toggle("visible", capa.id === id);
    }
  },

  pausar(valor = !this.pausado) {
    if (fase !== "versus" || this.estado?.ganador != null) return;
    if (performance.now() < this.empiezaEn) return;
    this.pausado = valor;
    this.sostenidas.clear();
    audio.pausar(valor);
    this.mostrarCapa(valor ? "vs-capa-pausa" : null);
    if (!valor) {
      const ahora = performance.now();
      this.ultimoPaso = [ahora, ahora];
    }
  },

  // Lee el estado de las dos partidas y reacciona
  refrescar() {
    const e = this.estado = JSON.parse(puente.estado_versus());
    e.jugadores.forEach((jug, j) => {
      for (const nombre of jug.sonidos) audio.efecto(nombre);
      if (jug.evento === "vida") {
        this.el[j].aviso.textContent = "¡Perdió una vida!";
        this.el[j].aviso.classList.add("malo");
        this.avisoHasta[j] = performance.now() + DURACION_AVISO;
      }
    });

    if (e.ganador != null) {
      audio.detenerMusica();
      this.sostenidas.clear();
      const g = e.ganador, p = 1 - g;
      $("vs-titulo-fin").textContent = `¡Gana el ${CONTROLES[g].nombre}!`;
      $("vs-titulo-fin").style.color = g === 0 ? "var(--j1)" : "var(--j2)";
      $("vs-motivo-fin").textContent = e.motivo === "meta"
        ? `Llegó primero a ${e.meta} puntos.`
        : `El ${CONTROLES[p].nombre} se quedó sin vidas.`;
      $("vs-fin-j0").textContent = `${e.jugadores[0].puntos} pts · ${e.jugadores[0].motor.nombre}`;
      $("vs-fin-j1").textContent = `${e.jugadores[1].puntos} pts · ${e.jugadores[1].motor.nombre}`;
      this.mostrarCapa("vs-capa-fin");
    } else {
      // La música la compone el motor del jugador 1
      const m = e.jugadores[0].motor;
      audio.musica(m.clave, m.semilla, 1);
    }
    this.actualizarPaneles();
  },

  actualizarPaneles() {
    const e = this.estado;
    e.jugadores.forEach((jug, j) => {
      const el = this.el[j];
      el.motor.textContent = jug.motor.nombre;
      el.historial.innerHTML = jug.motor.historial.length
        ? [...jug.motor.historial].reverse().slice(0, 3).map((v) => `<li>${v}</li>`).join("")
        : '<li class="espera">esperando pieza…</li>';
      el.puntos.textContent = `${jug.puntos} / ${e.meta}`;
      el.vidas.innerHTML = Array.from({ length: jug.vidas_max },
        (_, i) => i < jug.vidas ? "♥" : '<span class="vacia">♥</span>').join("");
      el.torre.style.height = `${Math.min(jug.puntos / e.meta, 1) * 100}%`;
    });
    const hc = e.jugadores[0].hardcore;
    $("vs-hardcore").textContent = hc ? `HARDCORE ${e.jugadores[0].probabilidad_temblor}%` : "";
    $("vs-musica").textContent = audio.silenciado ? "♪ silenciado"
      : audio.descripcion ? `♪ ${audio.descripcion}` : "";
  },

  // ---------------- Bucle ----------------

  tick(ahora) {
    if (fase !== "versus" || !this.estado) return;
    if (ahora < this.empiezaEn) {
      $("vs-cuenta").textContent = Math.ceil((this.empiezaEn - ahora) / 1000);
      return;
    }
    if ($("vs-capa-cuenta").classList.contains("visible")) this.mostrarCapa(null);
    if (this.pausado || this.estado.ganador != null) return;

    let cambio = false;
    // Gravedad independiente para cada jugador
    for (const j of [0, 1]) {
      const jug = this.estado.jugadores[j];
      if (!jug.terminada && ahora - this.ultimoPaso[j] >= jug.intervalo * 1000) {
        puente.gravedad_jugador(j);
        this.ultimoPaso[j] = ahora;
        cambio = true;
      }
    }
    // Teclas mantenidas: el navegador solo repite la última tecla presionada,
    // así que la repetición se maneja aquí para que dos jugadores puedan
    // mantener teclas al mismo tiempo.
    for (const s of this.sostenidas.values()) {
      while (ahora >= s.siguiente) {
        puente.accion_jugador(s.j, s.accion);
        if (s.accion === "bajar") this.ultimoPaso[s.j] = ahora;
        s.siguiente += INTERVALO_REPETICION;
        cambio = true;
      }
    }
    if (cambio) this.refrescar();
  },

  dibujar(ahora) {
    for (const j of [0, 1]) {
      const jug = this.estado?.jugadores[j];
      dibujarTablero(this.el[j].tablero, jug);
      dibujarSiguiente(this.el[j].siguiente, jug?.siguiente, 18);
      this.el[j].aviso.classList.toggle("visible",
        !!jug && this.estado.ganador == null && ahora < this.avisoHasta[j]);
    }
  },

  // ---------------- Teclado ----------------

  teclado(e, tecla) {
    if (["Enter", "Tab"].includes(tecla)) e.preventDefault();
    if (e.repeat) return;               // la repetición la maneja tick()

    if (tecla === "Escape" || tecla === "q") return mostrarMenu();

    if (fase === "versus-config") {
      for (const j of [0, 1]) {
        const i = CONTROLES[j].motores.indexOf(tecla);
        if (i >= 0 && i < listaMotores.length) this.elegir(j, listaMotores[i].clave);
      }
      if (tecla === "Enter" || tecla === " ") this.empezar();
      return;
    }

    if (this.estado?.ganador != null) {
      if (tecla === "r") this.empezar();
      return;
    }
    if (performance.now() < this.empiezaEn) return;
    if (tecla === "p") return this.pausar();
    if (this.pausado) return;

    if (tecla === "t") {
      this.hardcore = !this.hardcore;
      puente.accion_jugador(0, "hardcore");
      puente.accion_jugador(1, "hardcore");
      return this.refrescar();
    }

    for (const j of [0, 1]) {
      const c = CONTROLES[j];
      const i = c.motores.indexOf(tecla);
      if (i >= 0 && i < listaMotores.length) {
        puente.accion_jugador(j, listaMotores[i].clave);
        return this.refrescar();
      }
      const accion = c.acciones[tecla];
      if (!accion) continue;
      puente.accion_jugador(j, accion);
      if (accion === "bajar" || accion === "soltar") this.ultimoPaso[j] = performance.now();
      if (REPETIBLES.has(accion)) {
        this.sostenidas.set(tecla, { j, accion, siguiente: performance.now() + RETARDO_REPETICION });
      }
      return this.refrescar();
    }
  },

  soltarTecla(tecla) {
    this.sostenidas.delete(tecla);
  },
};
