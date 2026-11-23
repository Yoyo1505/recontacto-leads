/*
 * Edicion: este archivo y los demas de web/fuente/app/ son las secciones; web/app.js se genera con
 * python scripts/ensamblar_web.py y no se edita a mano.
 *
 * Interfaz de la herramienta (pieza 1 de la entrega). Usa el motor de motor.js y las graficas de Plotly.
 *
 * Estructura
 *   estado E            datos vigentes, reglas, bajas e historial de versiones
 *   recalcular()        vuelve a generar la lista cuando cambian reglas o datos
 *   vistaLista/Evidencia/Simulacion/PruebaAB/Datos   una funcion por subpestana
 *   Todo se dibuja a demanda al abrir cada subpestana.
 *
 * Donde cambiar cosas
 *   - Textos de las subpestanas: constante SUBPESTANAS y cada vista*.
 *   - Estilo de las graficas: baseLayout().
 *   - Ejemplo de dos personas: EJEMPLO_DOS.
 */
(function () {
  "use strict";
  const M = window.Motor;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (t) => String(t == null ? "" : t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const leerJson = (id) => JSON.parse(document.getElementById(id).textContent);
  const DATOS = leerJson("datos-json");
  const MODELO = leerJson("modelo-json");
  const EVID = leerJson("evidencia-json");
  const num = (n, d = 0) => Number(n).toLocaleString("es-MX", { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (p, d = 0) => `${(p * 100).toFixed(d)}%`;
  const DIAS_CORTOS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];

  const EJEMPLO_DOS = [
    { lead_id: "L90001", fecha_registro: "2026-11-08 21:40", canal: "Agente IA", anuncio: "", estado: "CDMX", edad: "38", objetivo: "control de peso", plan_de_interes: "1599", telefono: "55-02000001", asesor: "", primer_contacto: "", resultado: "sin_contactar", monto_venta: "" },
    { lead_id: "L90002", fecha_registro: "2026-11-07 15:00", canal: "Meta", anuncio: "Video testimonio 01", estado: "Jalisco", edad: "45", objetivo: "diabetes tipo 2", plan_de_interes: "1299", telefono: "55-02000002", asesor: "Asesor B", primer_contacto: "2026-11-08 10:20", resultado: "no_contesta", monto_venta: "" },
  ];

