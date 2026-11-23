/*
 * Compara el motor en JavaScript con los resultados de la version en Python (web/referencia.json).
 * Uso: node web/prueba_motor.js
 */
const fs = require("fs");
const path = require("path");
const Motor = require("./motor.js");

const leer = (n) => JSON.parse(fs.readFileSync(path.join(__dirname, n), "utf-8"));
const datos = leer("datos.json");
const modelo = leer("modelo.json");
const ref = leer("referencia.json");

let fallos = 0;
const comprobar = (condicion, mensaje) => {
  if (!condicion) {
    fallos += 1;
    console.log("FALLA:", mensaje);
  }
};
const cerca = (a, b, tol) => Math.abs(a - b) <= tol;

const leads = Motor.enriquecer(Motor.desdeFilas(datos.columnas, datos.filas), []);
comprobar(leads.length === 1811, `leads ${leads.length}`);
comprobar(leads.filter((l) => l.esDuplicado).length === 70, "duplicados");

const ahora = Motor.parseFecha(ref.ahora);
const resultado = Motor.generarLista(leads, modelo, ahora, Motor.REGLAS);
const py = ref.lista;
comprobar(resultado.filas.length === py.length, `largo de la lista ${resultado.filas.length} contra ${py.length}`);

let difAccion = 0, difHorario = 0, difProb = 0, difMotivo = 0, difMensaje = 0, difOrden = 0, difVariante = 0, maxDifProb = 0;
py.forEach((p, i) => {
  const j = resultado.filas[i];
  if (!j) return;
  if (j.lead_id !== p.lead_id) difOrden += 1;
  if (j.accion !== p.accion) difAccion += 1;
  if ((j.horario === null ? null : Motor.fmt(j.horario)) !== p.horario) difHorario += 1;
  if (p.prob !== null && j.prob !== null) {
    maxDifProb = Math.max(maxDifProb, Math.abs(j.prob - p.prob));
    if (!cerca(j.prob, p.prob, 1e-9)) difProb += 1;
  }
  if (j.motivo !== p.motivo) difMotivo += 1;
  if (j.mensaje !== p.mensaje) difMensaje += 1;
  if (j.variante !== p.variante || j.etapa !== p.etapa) difVariante += 1;
});
comprobar(difVariante === 0, `etapa o variante distinta en ${difVariante} leads`);
comprobar(difOrden === 0, `orden distinto en ${difOrden} leads`);
comprobar(difAccion === 0, `accion distinta en ${difAccion}`);
comprobar(difHorario === 0, `horario distinto en ${difHorario}`);
comprobar(difProb === 0, `probabilidad distinta en ${difProb} (max ${maxDifProb})`);
comprobar(difMotivo === 0, `motivo distinto en ${difMotivo}`);
comprobar(difMensaje === 0, `mensaje distinto en ${difMensaje}`);
for (const [k, v] of Object.entries(ref.excluidos)) comprobar(resultado.conteoExcluidos[k] === v, `excluidos ${k}: ${resultado.conteoExcluidos[k]} contra ${v}`);

comprobar(Motor.tamanoMuestra(ref.ab.p0, 0.03) === ref.ab.n_3pts, `n 3 puntos ${Motor.tamanoMuestra(ref.ab.p0, 0.03)} contra ${ref.ab.n_3pts}`);
comprobar(Motor.tamanoMuestra(ref.ab.p0, 0.08) === ref.ab.n_8pts, "n 8 puntos");
comprobar(cerca(Motor.potenciaAnalitica(ref.ab.p0, 0.03, 1000), ref.ab.potencia_3pts_1000, 1e-4), "potencia analitica");

const prep = Motor.prepararSimulacion(resultado, ahora, modelo, Motor.REGLAS);
comprobar(prep.n === ref.simulacion.n_leads, `leads de simulacion ${prep.n} contra ${ref.simulacion.n_leads}`);
const media = (m) => m.reduce((a, f) => a + f.reduce((x, y) => x + y, 0), 0) / (m.length * m[0].length);
comprobar(cerca(media(prep.pPol), ref.simulacion.p_politica_media, 1e-6), `p politica ${media(prep.pPol)} contra ${ref.simulacion.p_politica_media}`);
comprobar(cerca(media(prep.pBase), ref.simulacion.p_base_media, 1e-6), "p base");
for (const alfa of [0, 0.5, 1]) {
  const r = Motor.resumenSimulacion(Motor.simular(prep, alfa, 4000));
  const e = ref.simulacion.resumen[Number.isInteger(alfa) ? alfa.toFixed(1) : String(alfa)];
  comprobar(cerca(r.media, e.media, 1.2), `simulacion alfa ${alfa}: media ${r.media.toFixed(2)} contra ${e.media.toFixed(2)}`);
  comprobar(cerca(r.probMejora, e.prob_mejora, 0.05), `simulacion alfa ${alfa}: prob ${r.probMejora.toFixed(2)} contra ${e.prob_mejora.toFixed(2)}`);
}

const variantes = {};
resultado.filas.filter((f) => f.variante).forEach((f) => (variantes[f.variante] = (variantes[f.variante] || 0) + 1));
comprobar(Object.keys(variantes).length >= 2, `varias variantes en uso ${JSON.stringify(variantes)}`);

const cm = leer("casos_mensajes.json");
cm.plantillas.forEach((c) => {
  const texto = Motor.plantilla({ nunca: c.nunca, ultimo: c.ultimo, variante: c.variante, franja: c.franja, asesor: c.asesor, origenIa: c.origenIa, dias: c.dias });
  comprobar(texto === c.texto, `plantilla distinta (${c.nunca ? "primer" : c.ultimo ? "cierre" : "retoma"} ${c.variante}): ${texto}`);
  comprobar(Motor.validarMensaje(texto).valido, `plantilla invalida: ${texto}`);
});
cm.crc.forEach((c) => comprobar(Motor.elegirVariante(c.lead, c.etapa) === c.variante, `variante de ${c.lead}/${c.etapa}: ${Motor.elegirVariante(c.lead, c.etapa)} contra ${c.variante}`));
comprobar(Motor.validarMensaje("Hola, te escribimos de Clivi. ¿En qué podemos ayudarte? Si prefieres que no te escribamos, responde NO.", { nunca: false, ultimo: false, variante: "A" }).valido === false, "fidelidad: rechaza lo que no sigue la estrategia");

const cr = leer("casos_respuestas.json");
cr.forEach((c) => {
  const r = Motor.clasificarRespuesta(c.texto);
  const ok = r.intencion === c.intencion && r.accion === c.accion && r.estadoNuevo === c.estado_nuevo && r.baja === c.baja && r.requiereHumano === c.requiere_humano && r.respuestaSugerida === c.respuesta_sugerida && r.confianza === c.confianza && r.dia === c.dia && r.hora === c.hora && r.franja === c.franja;
  comprobar(ok, `respuesta ${JSON.stringify(c.texto)}: JS ${r.intencion}/${r.hora}/${r.dia} contra Python ${c.intencion}/${c.hora}/${c.dia}`);
});

const dos = Motor.procesarIngesta(
  [
    { ID: "L90001", Fecha: "2026-11-08 21:40", Fuente: "Agente IA", Celular: "5502000001", Status: "Sin contactar", edad: 38 },
    { ID: "L90002", Fecha: "2026-11-07 15:00", Fuente: "meta", Celular: "5502000002", Status: "no_contesta", "Primer contacto": "2026-11-08 10:20" },
    { ID: "", Fecha: "2026-11-07", Fuente: "Meta", Celular: "123", Status: "venta" },
  ],
  Motor.desdeFilas(datos.columnas, datos.filas),
  "prueba",
);
comprobar(dos.validos === 2 && dos.rechazados.length === 1, "ingesta: validos y rechazados");
comprobar(dos.agregados.length === 2 && dos.hayCambios, "ingesta: nuevos");
comprobar(dos.fusionado.length === 1813, "ingesta: fusion");
const conBaja = Motor.enriquecer(dos.fusionado, new Set([Motor.claveTelefono("55-02000001")]));
const lista2 = Motor.generarLista(conBaja, modelo, ahora, Motor.REGLAS);
comprobar(!lista2.filas.some((f) => f.lead_id === "L90001"), "la baja excluye a L90001");
comprobar(lista2.filas.some((f) => f.lead_id === "L90002"), "L90002 sigue en la lista");
comprobar(lista2.conteoExcluidos.baja === 1, "conteo de bajas");

comprobar(Motor.validarMensaje("Hola, te escribimos de Clivi. Tienes diabetes. Si prefieres que no te escribamos, responde NO.").valido === false, "validador: salud");
comprobar(resultado.filas.filter((f) => f.mensaje).every((f) => Motor.validarMensaje(f.mensaje).valido), "todos los mensajes son validos");

console.log(fallos === 0 ? `OK: el motor en JavaScript coincide con Python (${py.length} leads, ${cm.plantillas.length} plantillas, ${cr.length} respuestas, max dif. de probabilidad ${maxDifProb.toExponential(1)})` : `${fallos} FALLAS`);
process.exit(fallos === 0 ? 0 : 1);
