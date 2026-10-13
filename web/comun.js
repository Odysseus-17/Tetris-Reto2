// Utilidades compartidas por la página y el hilo de audio.

// Pyodide: Python compilado a WebAssembly. Se puede cambiar con ?pyodide=<url>
// (por ejemplo, para servir una copia local y jugar sin internet).
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

// Archivos Python del proyecto que se copian al sistema de archivos virtual
// de Pyodide. Son los MISMOS que usa la versión de terminal.
const ARCHIVOS_JUEGO = [
  "motores/__init__.py", "motores/base.py", "motores/cuadrado_medio.py",
  "motores/congruencial.py", "motores/pcg.py",
  "juego/__init__.py", "juego/config.py", "juego/piezas.py",
  "juego/tablero.py", "juego/partida.py",
  "web/puente.py",
];
const ARCHIVOS_AUDIO = [
  "motores/__init__.py", "motores/base.py", "motores/cuadrado_medio.py",
  "motores/congruencial.py", "motores/pcg.py",
  "audio/__init__.py", "audio/sintetizador.py", "audio/efectos.py",
  "audio/musica.py",
  "web/puente_audio.py",
];

async function cargarArchivos(py, raiz, archivos) {
  const textos = await Promise.all(archivos.map(async (a) => {
    const r = await fetch(raiz + a);
    if (!r.ok) throw new Error(`No se pudo cargar ${a} (${r.status})`);
    return r.text();
  }));
  archivos.forEach((a, i) => {
    const carpeta = "/tetris/" + a.split("/").slice(0, -1).join("/");
    py.FS.mkdirTree(carpeta);
    py.FS.writeFile("/tetris/" + a, textos[i]);
  });
  py.runPython("import sys; sys.path.insert(0, '/tetris'); sys.path.insert(0, '/tetris/web')");
}
