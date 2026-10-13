// Hilo de audio: un segundo intérprete de Python que solo genera sonido.
// Recibe pedidos de la página y devuelve las muestras ya calculadas.

let py = null;
let puente = null;

async function iniciar({ pyodideUrl, raiz }) {
  importScripts(pyodideUrl + "pyodide.js", "comun.js");
  py = await loadPyodide({ indexURL: pyodideUrl });
  await cargarArchivos(py, raiz, ARCHIVOS_AUDIO);
  puente = py.pyimport("puente_audio");

  const efectos = {};
  const transferibles = [];
  for (const nombre of puente.nombres_efectos().toJs()) {
    const muestras = aFloat32(puente.efecto(nombre));
    efectos[nombre] = muestras;
    transferibles.push(muestras.buffer);
  }
  postMessage({ tipo: "listo", tasa: puente.tasa(), efectos }, transferibles);
}

function aFloat32(bytesPython) {
  const u8 = bytesPython.toJs();          // Uint8Array
  bytesPython.destroy();
  const copia = u8.slice();               // buffer propio, alineado
  return new Float32Array(copia.buffer);
}

onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.tipo === "iniciar") {
      await iniciar(m);
    } else if (m.tipo === "componer") {
      const muestras = aFloat32(puente.componer(m.clave, m.semilla, m.nivel));
      const descripcion = puente.ultima_descripcion();
      postMessage({ tipo: "musica", id: m.id, muestras, descripcion }, [muestras.buffer]);
    }
  } catch (error) {
    postMessage({ tipo: "error", mensaje: String(error) });
  }
};
