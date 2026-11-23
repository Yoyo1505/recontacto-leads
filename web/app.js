/*
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

  // ------------------------------------------------------------------ estado
  const base = M.desdeFilas(DATOS.columnas, DATOS.filas);
  const ultimoRegistro = Math.max(...base.map((l) => l.fecha));
  const fechaInicial = Math.floor(ultimoRegistro / M.DIA) * M.DIA + M.DIA + 8 * M.HORA;
  const E = {
    base,
    actual: base,
    historial: [],
    bajas: new Set(),
    reglas: { ...M.REGLAS, dias: [...M.REGLAS.dias] },
    ahora: fechaInicial,
    lista: null,
    pendiente: null,
    prep: null,
    sub: "lista",
    filtro: { canales: null, nuevos: false },
    orden: { col: "prioridad", asc: true },
    pagina: 0,
    seleccion: null,
    dimension: "franja_hora",
    comparar: true,
    chat: { lead: null, texto: "", resultado: null, hechos: [] },
  };
  try {
    (JSON.parse(localStorage.getItem("recontacto_bajas") || "[]") || []).forEach((c) => E.bajas.add(c));
  } catch (e) {}

  function validarReglas(r) {
    if (!(r.horaInicio < r.horaFin)) throw new Error("El horario de inicio debe ser menor que el de fin");
    if (!r.dias.length) throw new Error("Elige al menos un día");
    return true;
  }
  function recalcular() {
    try {
      validarReglas(E.reglas);
    } catch (e) {
      $("#aviso-reglas").textContent = e.message;
      return false;
    }
    $("#aviso-reglas").textContent = "";
    E.enriquecidos = M.enriquecer(E.actual, E.bajas);
    E.lista = M.generarLista(E.enriquecidos, MODELO, E.ahora, E.reglas, { compararVariantes: E.comparar });
    E.prep = null;
    E.pagina = 0;
    return true;
  }

  // ------------------------------------------------------------------ graficas
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  function colores() {
    return { fg: css("--fg"), muted: css("--muted"), line: css("--line"), accent: css("--accent"), steel: css("--steel"), ok: css("--ok"), warn: css("--warn"), panel: css("--panel"), soft: css("--steel-soft") };
  }
  function baseLayout(extra) {
    const c = colores();
    const eje = { gridcolor: c.line, zerolinecolor: c.line, linecolor: c.line, automargin: true };
    const out = { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { family: "Inter, system-ui, sans-serif", color: c.fg, size: 12 }, margin: { l: 56, r: 16, t: 16, b: 48 }, xaxis: { ...eje }, yaxis: { ...eje }, legend: { orientation: "h", y: -0.28 }, hoverlabel: { font: { family: "Inter, system-ui, sans-serif" } } };
    for (const [k, v] of Object.entries(extra || {})) out[k] = typeof v === "object" && !Array.isArray(v) && out[k] ? { ...out[k], ...v } : v;
    return out;
  }
  const CONFIG = { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] };
  function graficar(id, trazas, layout) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!window.Plotly) {
      el.innerHTML = '<p class="nota">No se pudo cargar la librería de gráficas. Revisa tu conexión y recarga la página.</p>';
      return;
    }
    window.Plotly.react(el, trazas, baseLayout(layout), CONFIG);
  }
  const kpi = (t, v, s) => `<div class="kpi"><div class="t">${esc(t)}</div><div class="v">${esc(v)}</div>${s ? `<div class="s">${esc(s)}</div>` : ""}</div>`;
  const ayuda = (t) => `<p class="ayuda">${t}</p>`;

  // ------------------------------------------------------------------ armado de la herramienta
  const SUBPESTANAS = [
    ["lista", "Lista del día"],
    ["mensajes", "Mensajes"],
    ["respuestas", "Respuestas"],
    ["evidencia", "Evidencia"],
    ["simulacion", "Simulación"],
    ["ab", "Prueba A/B"],
    ["datos", "Datos"],
    ["limites", "Límites"],
  ];

  function armar() {
    const r = E.reglas;
    const dias = M.DIAS.map((d, i) => `<label><input type="checkbox" data-dia="${i}" ${r.dias.includes(i) ? "checked" : ""}>${d.slice(0, 3)}</label>`).join("");
    const fechaIso = M.fmtDia(E.ahora);
    $("#vista-herramienta").innerHTML = `
      <div class="hero">
        <div>
          <h2>Recupera la conversación, <span style="opacity:.85">con respeto.</span></h2>
          <p>Cada mañana, a quién volver a buscar, cuándo y con qué mensaje. Cuatro de cada diez personas que pidieron información no contestan cuando un asesor las busca. Funciona dentro de tu navegador: no instala nada y nada sale de tu computadora.</p>
          <button class="pildora blanca" id="hero-cta" type="button">Ver la lista del día →</button>
        </div>
        <div class="hero-datos" aria-label="Cifras clave">
          <div><b>40.3%</b><span>no contesta</span></div>
          <div><b>346</b><span>personas hoy</span></div>
          <div><b>3</b><span>intentos máximo</span></div>
        </div>
      </div>
      <p class="nota-hero">Datos ficticios (1,811 registros del 28 de septiembre al 8 de noviembre de 2026). Cambia las reglas de la izquierda y todo se recalcula.</p>
      <div class="herramienta">
        <aside class="lateral" aria-label="Reglas de trato">
          <h3>Reglas de trato</h3>
          <label for="r-fecha">Fecha de la lista</label>
          <input id="r-fecha" type="date" value="${fechaIso}">
          <label for="r-ini">Hora de inicio <output id="o-ini">${r.horaInicio}:00</output></label>
          <input id="r-ini" type="range" min="6" max="21" step="1" value="${r.horaInicio}">
          <label for="r-fin">Hora de fin <output id="o-fin">${r.horaFin}:00</output></label>
          <input id="r-fin" type="range" min="7" max="22" step="1" value="${r.horaFin}">
          <label>Días permitidos</label>
          <div class="dias" id="r-dias">${dias}</div>
          <label for="r-max">Máximo de intentos <output id="o-max">${r.maxIntentos}</output></label>
          <input id="r-max" type="range" min="1" max="5" step="1" value="${r.maxIntentos}">
          <label for="r-entre">Horas entre intentos <output id="o-entre">${r.horasEntre}</output></label>
          <input id="r-entre" type="range" min="0" max="72" step="6" value="${r.horasEntre}">
          <label for="r-vent">Ventana de recuperación (días) <output id="o-vent">${r.ventanaDias}</output></label>
          <input id="r-vent" type="range" min="7" max="60" step="1" value="${r.ventanaDias}">
          <label for="r-cap">Contactos por hora <output id="o-cap">${r.capacidad}</output></label>
          <input id="r-cap" type="range" min="1" max="40" step="1" value="${r.capacidad}">
          <div class="aviso-reglas" id="aviso-reglas" role="alert"></div>
          <p class="nota">Los valores son supuestos, no datos. Los datos son ficticios.</p>
          <button class="boton claro" id="r-reset" type="button">Valores por defecto</button>
        </aside>
        <div>
          <div class="subpestanas" role="tablist">${SUBPESTANAS.map(([id, t]) => `<button role="tab" data-sub="${id}" aria-selected="${id === E.sub}">${t}</button>`).join("")}</div>
          ${SUBPESTANAS.map(([id]) => `<div class="subvista" id="sub-${id}" ${id === E.sub ? "" : "hidden"}></div>`).join("")}
        </div>
      </div>`;
    $$(".subpestanas button").forEach((b) => b.addEventListener("click", () => mostrarSub(b.dataset.sub)));
    $("#hero-cta").addEventListener("click", () => { mostrarSub("lista"); $(".herramienta").scrollIntoView({ behavior: "smooth", block: "start" }); });
    const leer = () => {
      const g = (id) => +$("#" + id).value;
      E.reglas = { horaInicio: g("r-ini"), horaFin: g("r-fin"), dias: $$("#r-dias input:checked").map((i) => +i.dataset.dia), maxIntentos: g("r-max"), horasEntre: g("r-entre"), ventanaDias: g("r-vent"), capacidad: g("r-cap"), horizonteDias: 3 };
      $("#o-ini").textContent = E.reglas.horaInicio + ":00";
      $("#o-fin").textContent = E.reglas.horaFin + ":00";
      $("#o-max").textContent = E.reglas.maxIntentos;
      $("#o-entre").textContent = E.reglas.horasEntre;
      $("#o-vent").textContent = E.reglas.ventanaDias;
      $("#o-cap").textContent = E.reglas.capacidad;
      const f = $("#r-fecha").value;
      if (f) E.ahora = M.parseFecha(f + " 08:00");
      if (recalcular()) refrescar();
    };
    let t = null;
    $$(".lateral input").forEach((el) => el.addEventListener("input", () => { clearTimeout(t); t = setTimeout(leer, 90); }));
    $("#r-reset").addEventListener("click", () => {
      E.reglas = { ...M.REGLAS, dias: [...M.REGLAS.dias] };
      E.ahora = fechaInicial;
      armar();
      recalcular();
      mostrarSub(E.sub);
    });
    for (const [id] of SUBPESTANAS) $("#sub-" + id).dataset.listo = "";
  }

  function mostrarSub(id) {
    E.sub = id;
    $$(".subpestanas button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.sub === id)));
    $$(".subvista").forEach((s) => (s.hidden = s.id !== "sub-" + id));
    refrescar();
  }
  function refrescar() {
    ({ lista: vistaLista, mensajes: vistaMensajes, respuestas: vistaRespuestas, evidencia: vistaEvidencia, simulacion: vistaSimulacion, ab: vistaAB, datos: vistaDatos, limites: vistaLimites })[E.sub]();
  }

  // ------------------------------------------------------------------ lista del dia
  function vistaLista() {
    const cont = $("#sub-lista");
    const L = E.lista;
    const canales = [...new Set(L.filas.map((f) => f.canal))].sort();
    if (!E.filtro.canales) E.filtro.canales = new Set(canales);
    const asignados = L.filas.filter((f) => f.accion === "contactar").length;
    const nuevos = L.filas.filter((f) => f.nunca).length;
    if (!cont.dataset.listo) {
      cont.innerHTML = `
        <div class="pila">
          <div class="kpis" id="l-kpis"></div>
          <div class="tarjeta">
            <div class="barra" id="l-filtros"></div>
            <div class="scroll"><table id="l-tabla"></table></div>
            <div class="paginacion" id="l-pag"></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>Carga por día y hora</h3>${ayuda("Cuántos contactos caen en cada hora. El límite por hora evita saturar al equipo.")}<div id="l-mapa" class="grafica"></div></div>
            <div class="tarjeta" id="l-detalle"></div>
          </div>
          <div class="tarjeta" id="l-excl"></div>
        </div>`;
      cont.dataset.listo = "1";
    }
    $("#l-kpis").innerHTML = kpi("Personas por recontactar", num(L.filas.length), "Con las reglas de la izquierda") + kpi("Nunca contactadas", num(nuevos), "Salen primero y el mismo día") + kpi("Con horario asignado", num(asignados)) + kpi("En cola", num(L.filas.length - asignados), "Se reprograman, no se descartan");
    $("#l-filtros").innerHTML = canales.map((c) => `<label><input type="checkbox" data-canal="${esc(c)}" ${E.filtro.canales.has(c) ? "checked" : ""}>${esc(c)}</label>`).join("") + `<label><input type="checkbox" id="l-nuevos" ${E.filtro.nuevos ? "checked" : ""}>Solo nunca contactadas</label>`;
    $$("#l-filtros input[data-canal]").forEach((i) => i.addEventListener("change", () => { i.checked ? E.filtro.canales.add(i.dataset.canal) : E.filtro.canales.delete(i.dataset.canal); E.pagina = 0; vistaLista(); }));
    $("#l-nuevos").addEventListener("change", (e) => { E.filtro.nuevos = e.target.checked; E.pagina = 0; vistaLista(); });

    let filas = L.filas.filter((f) => E.filtro.canales.has(f.canal) && (!E.filtro.nuevos || f.nunca));
    const col = E.orden.col;
    const valor = (f) => (col === "horario" ? f.horario || Infinity : f[col] === undefined || f[col] === null ? "" : f[col]);
    filas = filas.slice().sort((a, b) => (valor(a) < valor(b) ? -1 : valor(a) > valor(b) ? 1 : 0) * (E.orden.asc ? 1 : -1));
    const porPagina = 12;
    const paginas = Math.max(1, Math.ceil(filas.length / porPagina));
    E.pagina = Math.min(E.pagina, paginas - 1);
    const visibles = filas.slice(E.pagina * porPagina, (E.pagina + 1) * porPagina);
    const cols = [["prioridad", "Prioridad"], ["lead_id", "Lead"], ["canal", "Canal"], ["accion", "Acción"], ["intento", "Intento"], ["horario", "Horario asignado"], ["prob", "Prob. de contestar"], ["asesor", "Asesor"]];
    $("#l-tabla").innerHTML = `<thead><tr>${cols.map(([c, t]) => `<th class="ord" data-col="${c}">${t}${E.orden.col === c ? (E.orden.asc ? " ▲" : " ▼") : ""}</th>`).join("")}</tr></thead><tbody>${
      visibles.map((f) => `<tr class="fila ${E.seleccion === f.lead_id ? "sel" : ""}" data-id="${esc(f.lead_id)}"><td class="num">${f.prioridad}</td><td>${esc(f.lead_id)}</td><td>${esc(f.canal)}</td><td class="${f.accion === "en_cola" ? "cola" : ""}">${f.accion === "contactar" ? "contactar" : "en cola"}</td><td class="num">${f.intento}</td><td class="num">${f.horario ? `${DIAS_CORTOS[M.diaSemana(f.horario)]} ${M.fmt(f.horario).slice(8, 10)}/${M.fmt(f.horario).slice(5, 7)} ${M.fmt(f.horario).slice(11)}` : "sin horario"}</td><td class="num">${f.prob === null ? "" : pct(f.prob)}</td><td>${esc(f.asesor)}</td></tr>`).join("") || `<tr><td colspan="8">Sin personas con estos filtros.</td></tr>`
    }</tbody>`;
    $$("#l-tabla th.ord").forEach((th) => th.addEventListener("click", () => { E.orden = { col: th.dataset.col, asc: E.orden.col === th.dataset.col ? !E.orden.asc : true }; vistaLista(); }));
    $$("#l-tabla tr.fila").forEach((tr) => tr.addEventListener("click", () => { E.seleccion = tr.dataset.id; vistaLista(); }));
    $("#l-pag").innerHTML = `<button class="boton claro" id="p-ant" ${E.pagina === 0 ? "disabled" : ""}>Anterior</button><span>Página ${E.pagina + 1} de ${paginas} · ${num(filas.length)} personas</span><button class="boton claro" id="p-sig" ${E.pagina >= paginas - 1 ? "disabled" : ""}>Siguiente</button>`;
    $("#p-ant").addEventListener("click", () => { E.pagina--; vistaLista(); });
    $("#p-sig").addEventListener("click", () => { E.pagina++; vistaLista(); });

    const sel = L.filas.find((f) => f.lead_id === E.seleccion);
    if (!sel) $("#l-detalle").innerHTML = `<h3>Detalle de la persona</h3>${ayuda("Elige una fila de la tabla para ver el motivo y el mensaje sugerido.")}`;
    else {
      const v = sel.mensaje ? M.validarMensaje(sel.mensaje) : null;
      $("#l-detalle").innerHTML = `<h3>${esc(sel.lead_id)} · ${esc(sel.canal)}</h3><p class="nota">Intento ${sel.intento}${sel.nunca ? " · nunca contactada" : ""}${sel.asesor ? " · " + esc(sel.asesor) : ""}${sel.variante ? ` · variante ${esc(sel.variante)}` : ""}</p><div class="etiqueta-campo">Por qué</div><p>${esc(sel.motivo)}</p>${
        sel.mensaje ? `<div class="etiqueta-campo">Mensaje sugerido</div><div class="msg" id="l-msg">${esc(sel.mensaje)}</div><div class="fila-accion"><button class="boton claro" id="l-copiar" type="button">Copiar mensaje</button><span class="insignia ${v.valido ? "ok" : "mal"}">${v.valido ? "Validado: sin salud, sin presión, con opción de baja" : "No pasa la validación: " + esc(v.problemas.join(", "))}</span></div>` : ""
      }`;
      const b = $("#l-copiar");
      if (b) b.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(sel.mensaje); b.textContent = "Copiado"; }
        catch (e) { const r = document.createRange(); r.selectNodeContents($("#l-msg")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = "Seleccionado: copia con Ctrl+C"; }
      });
    }

    const dias = [...new Set(L.filas.filter((f) => f.horario).map((f) => M.fmtDia(f.horario)))].sort();
    const horas = [...new Set(L.filas.filter((f) => f.horario).map((f) => M.horaDe(f.horario)))].sort((a, b) => a - b);
    const z = dias.map((d) => horas.map((h) => L.filas.filter((f) => f.horario && M.fmtDia(f.horario) === d && M.horaDe(f.horario) === h).length));
    const c = colores();
    graficar("l-mapa", [{ type: "heatmap", z, x: horas.map((h) => `${String(h).padStart(2, "0")}:00`), y: dias.map((d) => `${DIAS_CORTOS[M.diaSemana(M.parseFecha(d))]} ${d.slice(8)}/${d.slice(5, 7)}`), colorscale: [[0, c.panel], [1, c.steel]], hovertemplate: "%{y} a las %{x}: %{z} contactos<extra></extra>", colorbar: { title: "Contactos" } }], { yaxis: { autorange: "reversed" }, height: 300 });
    const filasExcl = Object.entries(L.conteoExcluidos).sort((a, b) => b[1] - a[1]);
    $("#l-excl").innerHTML = `<h3>Quién no recibe mensajes hoy y por qué</h3>${ayuda("Cada registro cuenta en el primer motivo que le aplica.")}<div class="scroll"><table><thead><tr><th>Motivo</th><th>Registros</th></tr></thead><tbody>${filasExcl.map(([k, n]) => `<tr><td>${esc(M.MOTIVOS[k])}</td><td class="num">${num(n)}</td></tr>`).join("") || '<tr><td colspan="2">Nadie excluido.</td></tr>'}</tbody></table></div>`;
  }

  // ------------------------------------------------------------------ evidencia
  const ORDEN = { franja_hora: EVID.confusion.franjas, rango_espera: EVID.confusion.esperas, dia_semana: M.DIAS };
  const NOMBRES_DIM = { franja_hora: "Hora del contacto", rango_espera: "Espera desde el registro", canal: "Canal", dia_semana: "Día de la semana" };
  const NOMBRES_ABL = { solo_canal: "Solo canal", horario_y_canal: "Horario y canal", solo_espera: "Solo espera", solo_horario: "Solo horario", espera_y_horario: "Espera y horario", perfil: "Perfil (objetivo, edad, plan)", todo: "Todas las variables" };

  function graficaTasas() {
    const dim = E.dimension;
    let filas = EVID.tasas[dim].slice();
    if (ORDEN[dim]) filas = ORDEN[dim].map((c) => filas.find((f) => f.categoria === c)).filter(Boolean);
    else filas.sort((a, b) => a.tasa - b.tasa);
    const c = colores();
    const media = 1 - EVID.tasa_contesta;
    graficar("e-tasas", [{ type: "bar", x: filas.map((f) => f.categoria), y: filas.map((f) => f.tasa * 100), marker: { color: c.steel }, error_y: { type: "data", symmetric: false, array: filas.map((f) => (f.alto - f.tasa) * 100), arrayminus: filas.map((f) => (f.tasa - f.bajo) * 100), color: c.muted }, customdata: filas.map((f) => [f.n, f.bajo * 100, f.alto * 100]), hovertemplate: "%{x}: %{y:.1f}%<br>n = %{customdata[0]}<br>Intervalo 95%: %{customdata[1]:.0f}% a %{customdata[2]:.0f}%<extra></extra>" }], { xaxis: { type: "category" }, yaxis: { title: "% que no contesta", range: [0, 85] }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: media * 100, y1: media * 100, line: { color: c.accent, dash: "dash" } }], annotations: [{ xref: "paper", x: 0, y: media * 100, text: `Promedio ${pct(media)}`, showarrow: false, yshift: 10, xanchor: "left", font: { color: c.accent } }], height: 340 });
  }

  function vistaEvidencia() {
    const cont = $("#sub-evidencia");
    const m = EVID.metricas;
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      cont.innerHTML = `
        <div class="pila">
          <div class="kpis">${kpi("AUC del modelo", m.logistica.auc.toFixed(2), `Intervalo 95%: ${m.logistica.auc_ic95[0].toFixed(2)} a ${m.logistica.auc_ic95[1].toFixed(2)}`)}${kpi("Azar", m.constante.auc.toFixed(2), "AUC de la tasa constante")}${kpi("Precisión en el 10% más alto", pct(m.logistica.precision_top_decil), `Base: ${pct(m.logistica.tasa_base)}`)}${kpi("Periodo de prueba", `desde ${m.corte.slice(8)}/${m.corte.slice(5, 7)}`, `${m.n_prueba} contactos`)}</div>
          <div class="tarjeta"><h3>Dónde se pierde la respuesta</h3>${ayuda("Elige una variable. Las barras de error son intervalos de confianza al 95%: si dos barras se traslapan, la diferencia puede ser azar.")}<select id="e-dim" class="entrada" style="max-width:320px;margin-bottom:10px">${Object.entries(NOMBRES_DIM).map(([k, t]) => `<option value="${k}">${t}</option>`).join("")}</select><div id="e-tasas" class="grafica"></div></div>
          <div class="dos">
            <div class="tarjeta"><h3>La hora y la espera van juntas</h3>${ayuda("Los contactos de la tarde casi siempre fueron rápidos. Por eso no se puede separar el efecto de la hora del de la rapidez.")}<div id="e-conf" class="grafica"></div></div>
            <div class="tarjeta"><h3>Qué variables aportan</h3>${ayuda("El canal explica casi toda la señal; el perfil de la persona no aporta.")}<div id="e-abl" class="grafica"></div></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>Calibración</h3>${ayuda("Con puntos sobre la diagonal, la probabilidad predicha coincide con lo observado. Aquí el modelo subestima en los grupos bajos.")}<div id="e-cal" class="grafica"></div></div>
            <div class="tarjeta"><h3>Control estadístico por día</h3>${ayuda("Carta p: un día fuera de los límites sería una señal de algo distinto al azar.")}<div id="e-carta" class="grafica"></div></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>¿Algún asesor se aleja del promedio?</h3>${ayuda("Gráfico de embudo: un punto dentro de los límites no se distingue del azar.")}<div id="e-emb" class="grafica"></div></div>
            <div class="tarjeta"><h3>Del interés a la compra</h3>${ayuda("Cuántas personas llegan a cada etapa (datos originales).")}<div id="e-fun" class="grafica"></div></div>
          </div>
          <p class="nota">La evidencia se calculó con los datos originales (1,811 registros). El modelo no se vuelve a entrenar en el navegador. Evaluación hacia adelante en el tiempo: entrenamiento antes del ${m.corte.slice(8)}/${m.corte.slice(5, 7)}.</p>
        </div>`;
      $("#e-dim").addEventListener("change", (e) => { E.dimension = e.target.value; graficaTasas(); });
    }
    const c = colores();
    graficaTasas();
    const cf = EVID.confusion;
    graficar("e-conf", [{ type: "heatmap", z: cf.z, x: cf.esperas, y: cf.franjas, text: cf.n.map((f) => f.map((n) => (n ? `n=${n}` : ""))), texttemplate: "%{text}", zmin: 20, zmax: 70, colorscale: [[0, c.panel], [1, c.steel]], hovertemplate: "Hora %{y}, espera %{x}<br>No contesta: %{z:.0f}%<br>%{text}<extra></extra>", colorbar: { title: "% no contesta" } }], { xaxis: { type: "category", title: "Espera desde el registro" }, yaxis: { type: "category", autorange: "reversed", title: "Hora del contacto" }, height: 340 });
    const ab = Object.entries(EVID.ablacion).sort((a, b) => a[1] - b[1]);
    graficar("e-abl", [{ type: "bar", orientation: "h", x: ab.map((a) => a[1]), y: ab.map((a) => NOMBRES_ABL[a[0]] || a[0]), marker: { color: ab.map((a) => (["solo_canal", "horario_y_canal"].includes(a[0]) ? c.ok : c.steel)) }, hovertemplate: "%{y}: AUC %{x:.3f}<extra></extra>" }], { xaxis: { title: "AUC en el periodo de prueba", range: [0.45, 0.65] }, shapes: [{ type: "line", yref: "paper", y0: 0, y1: 1, x0: 0.5, x1: 0.5, line: { color: c.accent, dash: "dash" } }], height: 340, margin: { l: 170, r: 16, t: 16, b: 48 } });
    const cal = EVID.calibracion;
    graficar("e-cal", [{ type: "scatter", mode: "lines", x: [0.3, 0.9], y: [0.3, 0.9], line: { dash: "dash", color: c.muted }, name: "Calibración perfecta" }, { type: "scatter", mode: "lines+markers", x: cal.map((f) => f.predicha), y: cal.map((f) => f.observada), line: { color: c.accent }, name: "Modelo", customdata: cal.map((f) => f.n), hovertemplate: "Predicha %{x:.0%}<br>Observada %{y:.0%}<br>n = %{customdata}<extra></extra>" }], { xaxis: { title: "Probabilidad predicha de contestar", tickformat: ".0%", range: [0.3, 0.9] }, yaxis: { title: "Proporción observada", tickformat: ".0%", range: [0.3, 0.9] }, height: 340 });
    const cp = EVID.carta_p;
    graficar("e-carta", [{ type: "scatter", mode: "lines", x: cp.map((r) => r.fecha), y: cp.map((r) => r.alto * 100), line: { color: c.warn, dash: "dot" }, name: "Límite superior (3σ)" }, { type: "scatter", mode: "lines", x: cp.map((r) => r.fecha), y: cp.map((r) => r.bajo * 100), line: { color: c.warn, dash: "dot" }, name: "Límite inferior (3σ)" }, { type: "scatter", mode: "lines", x: cp.map((r) => r.fecha), y: cp.map((r) => r.centro * 100), line: { color: c.muted }, name: "Promedio" }, { type: "scatter", mode: "lines+markers", x: cp.map((r) => r.fecha), y: cp.map((r) => r.tasa * 100), line: { color: c.steel }, name: "% que no contesta", customdata: cp.map((r) => r.n), hovertemplate: "%{x}: %{y:.0f}%<br>n = %{customdata}<extra></extra>" }, { type: "scatter", mode: "markers", x: cp.filter((r) => r.fuera).map((r) => r.fecha), y: cp.filter((r) => r.fuera).map((r) => r.tasa * 100), marker: { size: 12, color: c.accent, symbol: "diamond" }, name: "Fuera de control" }], { yaxis: { title: "% que no contesta", range: [0, 100] }, height: 340 });
    const ea = EVID.embudo_asesores;
    const lim = ea.limites;
    const trazasEmb = [];
    [["99.8%", c.warn], ["95%", c.ok]].forEach(([n, col], i) => ["alto", "bajo"].forEach((lado, j) => trazasEmb.push({ type: "scatter", mode: "lines", x: lim.n, y: lim[`${lado}_${n}`].map((v) => v * 100), line: { color: col, dash: "dot" }, name: `Límite ${n}`, showlegend: j === 0, hoverinfo: "skip" })));
    trazasEmb.push({ type: "scatter", mode: "markers+text", x: ea.asesores.map((a) => a.n), y: ea.asesores.map((a) => a.tasa * 100), text: ea.asesores.map((a) => a.asesor), textposition: "top center", marker: { size: 12, color: ea.asesores.map((a) => (a.fuera_de_control ? c.accent : c.steel)) }, name: "Asesores", hovertemplate: "%{text}: %{y:.1f}%<br>contactos = %{x}<extra></extra>" });
    graficar("e-emb", trazasEmb, { xaxis: { title: "Contactos realizados" }, yaxis: { title: "% que no contesta", range: [20, 60] }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: ea.centro * 100, y1: ea.centro * 100, line: { color: c.muted } }], height: 340 });
    graficar("e-fun", [{ type: "funnel", y: EVID.embudo.etapas, x: EVID.embudo.valores, textinfo: "value+percent previous", marker: { color: [css("--kpi-b"), c.steel, c.ok, c.accent] }, hovertemplate: "%{y}: %{x}<extra></extra>" }], { margin: { l: 170, r: 16, t: 16, b: 24 }, height: 340 });
  }

  // ------------------------------------------------------------------ simulacion
  function preparacion() {
    if (!E.prep) E.prep = M.prepararSimulacion(E.lista, E.ahora, MODELO, E.reglas);
    return E.prep;
  }
  function vistaSimulacion() {
    const cont = $("#sub-simulacion");
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      cont.innerHTML = `
        <div class="pila">
          <div class="tarjeta">
            <div class="formulario">
              <div><label for="s-alfa">Parte de la ventaja del horario que es causal (alpha): <output id="o-alfa">0.50</output></label><input id="s-alfa" type="range" min="0" max="1" step="0.05" value="0.5" style="width:100%"></div>
              <div><label for="s-n">Número de simulaciones: <output id="o-n">2000</output></label><input id="s-n" type="range" min="500" max="5000" step="500" value="2000" style="width:100%"></div>
            </div>
            ${ayuda("alpha = 0 significa que el horario no importa; alpha = 1, que toda la ventaja observada es causal. En los datos, el horario y la rapidez del contacto están mezclados, así que no se sabe cuál es el valor real. Cada corrida elige un modelo entre 100 remuestras y sortea quién contesta.")}
          </div>
          <div class="kpis" id="s-kpis"></div>
          <div class="tarjeta"><p id="s-texto" style="font-weight:500;margin:0"></p></div>
          <div class="dos">
            <div class="tarjeta"><h3>Distribución de la mejora</h3><div id="s-hist" class="grafica"></div></div>
            <div class="tarjeta"><h3>Sensibilidad al supuesto</h3><div id="s-sens" class="grafica"></div></div>
          </div>
          <div class="tarjeta"><h3>Tasa de respuesta simulada por brazo</h3><div id="s-caja" class="grafica"></div></div>
        </div>`;
      let t = null;
      ["s-alfa", "s-n"].forEach((id) => $("#" + id).addEventListener("input", () => { $("#o-alfa").textContent = (+$("#s-alfa").value).toFixed(2); $("#o-n").textContent = $("#s-n").value; clearTimeout(t); t = setTimeout(vistaSimulacion, 120); }));
    }
    const alfa = +$("#s-alfa").value;
    const nSim = +$("#s-n").value;
    const prep = preparacion();
    if (!prep.n) { $("#s-kpis").innerHTML = ""; $("#s-texto").textContent = "No hay personas con horario asignado con estas reglas."; return; }
    const corridas = M.simular(prep, alfa, nSim);
    const r = M.resumenSimulacion(corridas);
    $("#s-kpis").innerHTML = kpi("Mejora media", (r.media >= 0 ? "+" : "") + r.media.toFixed(1), "Personas adicionales que contestan") + kpi("Intervalo 95%", `${Math.round(r.icBajo)} a ${Math.round(r.icAlto)}`, "Incertidumbre total") + kpi("Probabilidad de mejora", pct(r.probMejora), "Corridas en que gana el modelo") + kpi("Ventas extra esperadas", (r.ventasExtra >= 0 ? "+" : "") + r.ventasExtra.toFixed(2), "Según la conversión histórica por canal");
    const cruza = r.icBajo <= 0 && 0 <= r.icAlto;
    $("#s-texto").textContent = `Con alpha = ${alfa.toFixed(2)}, el horario del modelo hace que contesten en promedio ${r.media.toFixed(1)} personas más de ${prep.n} (intervalo 95%: ${Math.round(r.icBajo)} a ${Math.round(r.icAlto)}). En ${pct(r.probMejora)} de las corridas el modelo supera al horario sin optimizar. ` + (cruza ? "El intervalo incluye el cero: con un solo día de lista no se puede distinguir la mejora del azar." : "El intervalo no incluye el cero: bajo este supuesto la mejora es distinguible del azar.");
    const c = colores();
    graficar("s-hist", [{ type: "histogram", x: corridas.diferencias, nbinsx: 40, marker: { color: c.steel }, opacity: 0.85, hovertemplate: "Diferencia %{x}: %{y} corridas<extra></extra>" }], { xaxis: { title: "Personas adicionales que contestan" }, yaxis: { title: "Corridas" }, shapes: [{ type: "rect", xref: "x", yref: "paper", x0: r.icBajo, x1: r.icAlto, y0: 0, y1: 1, fillcolor: c.ok, opacity: 0.12, line: { width: 0 } }, { type: "line", xref: "x", yref: "paper", x0: 0, x1: 0, y0: 0, y1: 1, line: { color: c.accent, dash: "dash" } }, { type: "line", xref: "x", yref: "paper", x0: r.media, x1: r.media, y0: 0, y1: 1, line: { color: c.fg } }], annotations: [{ x: 0, xref: "x", yref: "paper", y: 1, text: "Sin mejora", showarrow: false, xanchor: "right", font: { color: c.accent } }, { x: r.media, xref: "x", yref: "paper", y: 1, text: `Media ${r.media.toFixed(1)}`, showarrow: false, xanchor: "left" }], height: 340, showlegend: false });
    const alfas = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1];
    const sens = alfas.map((a) => ({ a, ...M.resumenSimulacion(M.simular(prep, a, 500)) }));
    graficar("s-sens", [{ type: "scatter", x: sens.map((s) => s.a), y: sens.map((s) => s.icAlto), mode: "lines", line: { width: 0 }, hoverinfo: "skip", showlegend: false }, { type: "scatter", x: sens.map((s) => s.a), y: sens.map((s) => s.icBajo), mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(120,160,190,0.25)", name: "IC 95%", hoverinfo: "skip" }, { type: "scatter", x: sens.map((s) => s.a), y: sens.map((s) => s.media), mode: "lines+markers", line: { color: c.steel }, name: "Mejora media", customdata: sens.map((s) => s.probMejora), hovertemplate: "alpha %{x:.1f}<br>Mejora media %{y:.1f}<br>Prob. de mejora %{customdata:.0%}<extra></extra>" }], { xaxis: { title: "Parte causal del horario (alpha)", range: [0, 1] }, yaxis: { title: "Personas adicionales que contestan" }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0, y1: 0, line: { color: c.accent, dash: "dash" } }, { type: "line", yref: "paper", x0: alfa, x1: alfa, y0: 0, y1: 1, line: { color: c.fg, dash: "dot" } }], height: 340 });
    graficar("s-caja", [{ type: "box", y: corridas.tasaBase.map((v) => v * 100), name: "Horario sin optimizar", marker: { color: c.muted }, boxmean: true }, { type: "box", y: corridas.tasaPol.map((v) => v * 100), name: "Horario del modelo", marker: { color: c.steel }, boxmean: true }], { yaxis: { title: "% que contesta en la lista" }, showlegend: false, height: 320 });
  }

  // ------------------------------------------------------------------ prueba A/B
  function vistaAB() {
    const cont = $("#sub-ab");
    const p0 = EVID.tasa_contesta;
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      cont.innerHTML = `
        <div class="pila">
          <div class="tarjeta">
            <div class="formulario">
              <div><label for="a-ef">Efecto a detectar (puntos): <output id="o-ef">3</output></label><input id="a-ef" type="range" min="1" max="12" step="1" value="3" style="width:100%"></div>
              <div><label for="a-alfa">Nivel de significancia</label><select id="a-alfa" class="entrada"><option value="0.05">5%</option><option value="0.01">1%</option></select></div>
              <div><label for="a-pot">Potencia</label><select id="a-pot" class="entrada"><option value="0.8">80%</option><option value="0.9">90%</option></select></div>
              <div><label for="a-flujo">Leads nuevos por día</label><input id="a-flujo" class="entrada" type="number" min="1" max="1000" value="${Math.round(EVID.leads_por_dia)}"></div>
            </div>
            ${ayuda(`Tasa base de respuesta usada: ${pct(p0)} (la observada en los datos). Prueba z de dos proporciones, de dos colas.`)}
          </div>
          <div class="kpis" id="a-kpis"></div>
          <div class="dos">
            <div class="tarjeta"><h3>Potencia según el tamaño de la prueba</h3><div id="a-pot-g" class="grafica"></div></div>
            <div class="tarjeta"><h3>Tamaños de muestra por efecto</h3>${ayuda("Entre paréntesis, los días que tomaría con el flujo indicado.")}<div id="a-tabla" class="scroll"></div></div>
          </div>
        </div>`;
      $$("#sub-ab input,#sub-ab select").forEach((e) => e.addEventListener("input", () => { $("#o-ef").textContent = $("#a-ef").value; vistaAB(); }));
    }
    const delta = +$("#a-ef").value / 100;
    const alfa = +$("#a-alfa").value;
    const pot = +$("#a-pot").value;
    const flujo = Math.max(1, +$("#a-flujo").value || 1);
    const n = M.tamanoMuestra(p0, delta, pot, alfa);
    $("#a-kpis").innerHTML = kpi("Personas por grupo", num(n)) + kpi("Personas en total", num(2 * n), "Dos grupos") + kpi("Duración estimada", `${num((2 * n) / flujo)} días`, "Con el flujo indicado");
    const c = colores();
    const efectos = [0.02, 0.03, 0.05, 0.08, 0.1];
    const colEf = [c.steel, c.ok, c.accent, c.muted, "#C9A227"];
    const ns = []; for (let k = 0; k <= 80; k++) ns.push(Math.round(50 * Math.pow(12000 / 50, k / 80)));
    graficar("a-pot-g", efectos.map((d, i) => ({ type: "scatter", mode: "lines", x: ns, y: ns.map((x) => M.potenciaAnalitica(p0, d, x, alfa)), name: `+${Math.round(d * 100)} puntos`, line: { color: colEf[i] }, hovertemplate: "n = %{x} por grupo<br>Potencia %{y:.0%}<extra></extra>" })), { xaxis: { type: "log", title: "Personas por grupo" }, yaxis: { title: "Potencia", tickformat: ".0%", range: [0, 1.02] }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0.8, y1: 0.8, line: { color: c.muted, dash: "dash" } }, { type: "line", yref: "paper", x0: n, x1: n, y0: 0, y1: 1, line: { color: c.fg, dash: "dot" } }], height: 360 });
    $("#a-tabla").innerHTML = `<table><thead><tr><th>Efecto</th><th>Potencia 80%</th><th>Potencia 90%</th></tr></thead><tbody>${efectos.map((d) => `<tr><td>+${Math.round(d * 100)} puntos</td>${[0.8, 0.9].map((q) => { const nn = M.tamanoMuestra(p0, d, q, alfa); return `<td class="num">${num(nn)} (${num((2 * nn) / flujo)} días)</td>`; }).join("")}</tr>`).join("")}</tbody></table>`;
  }

  // ------------------------------------------------------------------ datos
  const GUARDA_BAJAS = () => { try { localStorage.setItem("recontacto_bajas", JSON.stringify([...E.bajas])); } catch (e) {} };

  function decisionesPara(informe) {
    const enr = M.enriquecer(informe.fusionado, E.bajas);
    const L = M.generarLista(enr, MODELO, E.ahora, E.reglas);
    const ids = [...informe.agregados, ...Object.keys(informe.actualizados)];
    return ids.map((id) => {
      const f = L.filas.find((x) => x.lead_id === id);
      if (f) return { id, decision: f.accion === "contactar" ? "contactar" : "en cola", horario: f.horario, motivo: f.motivo, mensaje: f.mensaje };
      const e = L.excluidos.find((x) => x.lead_id === id);
      return { id, decision: "no contactar", horario: null, motivo: e ? M.MOTIVOS[e.motivo] : "No requiere recontacto", mensaje: "" };
    });
  }
  const tablaDecisiones = (d) => (d.length ? `<div class="scroll"><table><thead><tr><th>Lead</th><th>Decisión</th><th>Horario</th><th>Motivo</th><th>Mensaje</th></tr></thead><tbody>${d.map((x) => `<tr><td>${esc(x.id)}</td><td>${esc(x.decision)}</td><td class="num">${x.horario ? `${DIAS_CORTOS[M.diaSemana(x.horario)]} ${M.fmt(x.horario).slice(8, 10)}/${M.fmt(x.horario).slice(5, 7)} ${M.fmt(x.horario).slice(11)}` : ""}</td><td>${esc(x.motivo)}</td><td>${esc(x.mensaje)}</td></tr>`).join("")}</tbody></table></div>` : '<p class="ayuda">No hay personas nuevas ni actualizadas que mostrar.</p>');

  function mostrarInforme(informe, titulo) {
    const hijos = [`<pre>${esc(M.textoInforme(informe))}</pre>`];
    if (informe.rechazados.length) hijos.push(`<h4>Filas rechazadas (no se guardan)</h4><div class="scroll"><table><thead><tr><th>Lead</th><th>Motivo</th></tr></thead><tbody>${informe.rechazados.slice(0, 10).map((r) => `<tr><td>${esc(r.lead_id)}</td><td>${esc(r.motivo)}</td></tr>`).join("")}</tbody></table></div>`);
    if (informe.hayCambios && informe.agregados.length + Object.keys(informe.actualizados).length <= 200) hijos.push(`<h4 style="margin-top:14px">Qué haría la herramienta con estas personas</h4>${tablaDecisiones(decisionesPara(informe))}`);
    $("#d-informe").innerHTML = hijos.join("");
    $("#d-aplicar").disabled = !informe.hayCambios;
    $("#d-msg").textContent = "";
  }

  async function leerArchivo(archivo) {
    if (archivo.size > 20 * 1024 * 1024) throw new Error("El archivo supera 20 MB");
    const nombre = archivo.name.toLowerCase();
    if (nombre.endsWith(".parquet")) throw new Error("Parquet no se lee en el navegador. Usa CSV, JSON o Excel aquí, o los archivos .bat de la versión completa.");
    if (/\.(xlsx|xls|xlsm)$/.test(nombre)) {
      if (!window.XLSX) throw new Error("No se pudo cargar el lector de Excel. Revisa tu conexión.");
      const libro = window.XLSX.read(await archivo.arrayBuffer(), { type: "array", cellDates: true });
      return window.XLSX.utils.sheet_to_json(libro.Sheets[libro.SheetNames[0]], { defval: "", raw: false, dateNF: "yyyy-mm-dd hh:mm" });
    }
    const texto = await archivo.text();
    if (nombre.endsWith(".jsonl") || nombre.endsWith(".ndjson")) return texto.split(/\r?\n/).filter((l) => l.trim()).map((l) => JSON.parse(l));
    if (nombre.endsWith(".json")) {
      let o = JSON.parse(texto);
      if (!Array.isArray(o) && o && typeof o === "object") o = Object.values(o).find(Array.isArray);
      if (!Array.isArray(o)) throw new Error("El JSON debe ser una lista de registros o un objeto que contenga una lista");
      return o;
    }
    if (nombre.endsWith(".csv") || nombre.endsWith(".txt") || nombre.endsWith(".tsv")) {
      if (!window.Papa) throw new Error("No se pudo cargar el lector de CSV. Revisa tu conexión.");
      return window.Papa.parse(texto.replace(/^﻿/, ""), { header: true, skipEmptyLines: true }).data;
    }
    throw new Error("Formato no soportado. Usa csv, json, jsonl o xlsx.");
  }

  function procesarFilas(filas, origen) {
    try {
      E.pendiente = M.procesarIngesta(filas, E.actual, origen);
      mostrarInforme(E.pendiente);
    } catch (e) {
      E.pendiente = null;
      $("#d-informe").innerHTML = `<pre class="error">Error: ${esc(e.message)}</pre>`;
      $("#d-aplicar").disabled = true;
    }
  }

  function resumenDatos() {
    const fechas = E.actual.map((l) => l.fecha);
    $("#d-kpis").innerHTML = kpi("Leads en la base", num(E.actual.length)) + kpi("Periodo", `${M.fmtDia(Math.min(...fechas)).slice(5)} a ${M.fmtDia(Math.max(...fechas))}`) + kpi("Bajas registradas", num(E.bajas.size), "Nunca se les escribe") + kpi("Versiones guardadas", num(E.historial.length), "Para volver atrás");
    $("#d-version").innerHTML = E.historial.map((h, i) => `<option value="${i}">Versión ${i + 1}: ${num(h.datos.length)} leads (${esc(h.hora)})</option>`).reverse().join("");
  }

  function vistaDatos() {
    const cont = $("#sub-datos");
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      const ayerIso = M.fmtDia(E.ahora - M.DIA);
      cont.innerHTML = `
        <div class="pila">
          <div class="kpis" id="d-kpis"></div>
          <div class="tarjeta">
            <h3>1. Subir información</h3>
            <label class="zona" id="d-zona" for="d-archivo">Arrastra un archivo o elige uno (CSV, JSON, Excel)</label>
            <input id="d-archivo" type="file" accept=".csv,.json,.jsonl,.xlsx,.xls,.txt" hidden>
            ${ayuda("Se aceptan sinónimos de columnas (por ejemplo celular o whatsapp en lugar de telefono). Obligatorias: lead_id, fecha_registro, canal, telefono y resultado. Nada sale de tu computadora.")}
            <div class="fila-accion"><button class="boton claro" id="d-ejemplo" type="button">Cargar el ejemplo de dos personas nuevas</button></div>
          </div>
          <div class="tarjeta">
            <h3>2. O agrega una persona</h3>
            <div class="formulario">
              <div><label for="f-canal">Canal</label><select id="f-canal" class="entrada"><option>Agente IA</option><option>Meta</option><option>Google</option><option>TikTok</option><option>Referido</option><option>Organico</option></select></div>
              <div><label for="f-obj">Objetivo</label><select id="f-obj" class="entrada"><option>control de peso</option><option>diabetes tipo 2</option></select></div>
              <div><label for="f-plan">Plan de interés</label><select id="f-plan" class="entrada"><option>1299</option><option selected>1599</option><option>2499</option></select></div>
              <div><label for="f-edad">Edad</label><input id="f-edad" class="entrada" type="number" min="18" max="100" value="38"></div>
              <div><label for="f-tel">Teléfono</label><input id="f-tel" class="entrada" type="text" placeholder="55-12345678"></div>
              <div><label for="f-ent">Entidad</label><input id="f-ent" class="entrada" type="text" value="CDMX"></div>
              <div><label for="f-fecha">Fecha y hora de registro</label><input id="f-fecha" class="entrada" type="text" value="${ayerIso} 20:00"></div>
              <div><label for="f-res">¿Ya se intentó contactar?</label><select id="f-res" class="entrada"><option value="sin_contactar">No, nunca</option><option value="no_contesta">Sí, no contestó</option></select></div>
              <div><label for="f-con">Fecha y hora del intento</label><input id="f-con" class="entrada" type="text" placeholder="AAAA-MM-DD HH:MM"></div>
            </div>
            <button class="boton claro" id="f-revisar" type="button">Revisar persona</button>
          </div>
          <div class="tarjeta">
            <h3>Informe y confirmación</h3>
            <div id="d-informe"><p class="ayuda">Aquí aparecerá el informe. Nada se guarda hasta que confirmes.</p></div>
            <div class="fila-accion"><button class="boton" id="d-aplicar" type="button" disabled>Aplicar cambios</button><span id="d-msg"></span></div>
          </div>
          <div class="tarjeta">
            <h3>3. Respetar a quien pide no recibir mensajes</h3>
            ${ayuda("Se guarda en este navegador y se aplica a toda la base, incluso si el mismo teléfono llega otra vez en un archivo.")}
            <div class="fila-accion"><input id="b-tel" class="entrada" style="max-width:340px" type="text" placeholder="Teléfono de quien pidió no recibir mensajes"><button class="boton" id="b-boton" type="button">Registrar baja</button><span id="b-msg"></span></div>
          </div>
          <div class="tarjeta">
            <h3>4. Volver atrás</h3>
            ${ayuda("Cada cambio guarda la versión anterior. Los cambios viven solo en tu navegador: al cerrar la página se pierden, salvo las bajas.")}
            <div class="fila-accion"><select id="d-version" class="entrada" style="max-width:360px"></select><button class="boton claro" id="d-restaurar" type="button">Restaurar versión</button><button class="boton claro" id="d-original" type="button">Volver a la base original</button><span id="d-vmsg"></span></div>
          </div>
          <p class="nota">El modelo no se vuelve a entrenar en el navegador: las probabilidades siguen usando el modelo entrenado con los datos originales. La versión completa (Python) sí reentrena y lee CSV, JSON, Excel, Parquet, bases de datos y nube.</p>
        </div>`;
      const zona = $("#d-zona");
      ["dragenter", "dragover"].forEach((ev) => zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
      ["dragleave", "drop"].forEach((ev) => zona.addEventListener(ev, (e) => { e.preventDefault(); zona.classList.remove("encima"); }));
      const subir = async (archivo) => { try { procesarFilas(await leerArchivo(archivo), archivo.name); } catch (e) { E.pendiente = null; $("#d-informe").innerHTML = `<pre class="error">Error: ${esc(e.message)}</pre>`; $("#d-aplicar").disabled = true; } };
      zona.addEventListener("drop", (e) => e.dataTransfer.files[0] && subir(e.dataTransfer.files[0]));
      $("#d-archivo").addEventListener("change", (e) => e.target.files[0] && subir(e.target.files[0]));
      $("#d-ejemplo").addEventListener("click", () => procesarFilas(EJEMPLO_DOS, "ejemplo de dos personas"));
      $("#f-revisar").addEventListener("click", () => {
        const g = (id) => $("#" + id).value;
        const ids = E.actual.map((l) => /^L(\d+)$/.exec(l.lead_id)).filter(Boolean).map((m) => +m[1]);
        const id = "L" + String(Math.max(0, ...ids) + 1).padStart(5, "0");
        procesarFilas([{ lead_id: id, fecha_registro: g("f-fecha"), canal: g("f-canal"), anuncio: "", estado: g("f-ent"), edad: g("f-edad"), objetivo: g("f-obj"), plan_de_interes: g("f-plan"), telefono: g("f-tel"), asesor: "", primer_contacto: g("f-con"), resultado: g("f-res"), monto_venta: "" }], "formulario");
      });
      $("#d-aplicar").addEventListener("click", () => {
        const p = E.pendiente;
        if (!p || !p.hayCambios) return;
        E.historial.push({ datos: E.actual, hora: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }) });
        if (E.historial.length > 20) E.historial.shift();
        E.actual = p.fusionado;
        E.pendiente = null;
        recalcular();
        const dec = decisionesPara({ agregados: p.agregados, actualizados: p.actualizados, fusionado: E.actual });
        $("#d-informe").innerHTML = `<p class="exito">Listo: ${p.agregados.length} nuevas, ${Object.keys(p.actualizados).length} actualizadas. La lista ya las incluye.</p>${tablaDecisiones(dec)}`;
        $("#d-aplicar").disabled = true;
        resumenDatos();
      });
      $("#b-boton").addEventListener("click", () => {
        const tel = $("#b-tel").value;
        const clave = M.claveTelefono(tel);
        const msg = $("#b-msg");
        if (clave.length < 8) { msg.className = "error"; msg.textContent = "Teléfono no válido: debe tener al menos 8 dígitos"; return; }
        if (E.bajas.has(clave)) { msg.className = ""; msg.textContent = "Ese teléfono ya estaba en la lista de bajas."; return; }
        E.bajas.add(clave);
        GUARDA_BAJAS();
        recalcular();
        msg.className = "exito";
        msg.textContent = "Baja registrada: no se le volverá a escribir.";
        resumenDatos();
      });
      $("#d-restaurar").addEventListener("click", () => {
        const i = $("#d-version").value;
        const m = $("#d-vmsg");
        if (i === "") { m.className = "error"; m.textContent = "Elige una versión."; return; }
        E.historial.push({ datos: E.actual, hora: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }) });
        E.actual = E.historial[+i].datos;
        recalcular();
        m.className = "exito";
        m.textContent = `Base restaurada a la versión ${+i + 1}.`;
        resumenDatos();
      });
      $("#d-original").addEventListener("click", () => {
        E.historial.push({ datos: E.actual, hora: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }) });
        E.actual = E.base;
        recalcular();
        const m = $("#d-vmsg");
        m.className = "exito";
        m.textContent = "Base original restaurada.";
        resumenDatos();
      });
    }
    resumenDatos();
  }

  // ------------------------------------------------------------------ mensajes
  const NOMBRES_ETAPA = { primer_contacto: "Primer contacto", retoma: "Retomar", cierre: "Cierre" };
  const A_QUIEN = { primer_contacto: "A quien nunca recibió un contacto", retoma: "A quien no contestó el primer intento", cierre: "Al último intento permitido" };

  function vistaMensajes() {
    const cont = $("#sub-mensajes");
    const L = E.lista;
    const conteo = {};
    L.filas.filter((f) => f.etapa).forEach((f) => {
      conteo[f.etapa] = conteo[f.etapa] || {};
      conteo[f.etapa][f.variante] = (conteo[f.etapa][f.variante] || 0) + 1;
    });
    const p0 = EVID.tasa_contesta;
    const filas = [];
    for (const etapa of Object.keys(M.BIBLIOTECA)) {
      for (const letra of Object.keys(M.BIBLIOTECA[etapa]).sort()) {
        const contexto = { nunca: etapa === "primer_contacto", ultimo: etapa === "cierre", variante: letra, franja: "hoy por la tarde", asesor: "Asesor B" };
        const texto = M.plantilla(contexto);
        const v = M.validarMensaje(texto, contexto);
        filas.push(`<tr><td>${NOMBRES_ETAPA[etapa]}<div class="nota">${A_QUIEN[etapa]}</div></td><td><b>${letra}</b><div class="nota">${esc(M.ESTRATEGIAS[etapa][letra])}</div></td><td>${esc(texto)}</td><td class="num">${(conteo[etapa] || {})[letra] || 0}</td><td><span class="insignia ${v.valido ? "ok" : "mal"}">${v.valido ? "Válido" : "Revisar"}</span></td></tr>`);
      }
    }
    cont.innerHTML = `
      <div class="pila">
        <div class="tarjeta">
          <h3>Qué mensaje recibe cada persona</h3>
          ${ayuda("La conversación se recupera en hasta tres pasos, y cada paso tiene varias redacciones con una estrategia distinta. A cada persona le toca siempre la misma variante (se asigna por su número de lead), para poder comparar después cuál recupera más conversaciones.")}
          <label class="barra" style="margin:0 0 10px"><input type="checkbox" id="m-comparar" ${E.comparar ? "checked" : ""}> Comparar variantes (si se desmarca, todos reciben la variante A)</label>
          <div class="scroll"><table><thead><tr><th>Situación</th><th>Variante</th><th>Mensaje de ejemplo</th><th>Personas hoy</th><th>Reglas</th></tr></thead><tbody>${filas.join("")}</tbody></table></div>
        </div>
        <div class="dos">
          <div class="tarjeta">
            <h3>Reglas que todo mensaje cumple</h3>
            <ul>
              <li>No menciona la condición de salud, no promete resultados, no mete urgencia ni enlaces.</li>
              <li>Menciona la marca y trae la forma de pedir que no se le escriba más.</li>
              <li>Hasta 480 caracteres, en tono de tú, y siempre habla de la solicitud de información.</li>
              <li>Cambia según el canal (si llegó por un asistente de IA, lo dice) y si pasaron varios días desde la solicitud.</li>
              <li>El tercer mensaje avisa que no se insistirá más.</li>
            </ul>
          </div>
          <div class="tarjeta">
            <h3>Cómo se sabrá cuál variante recupera más</h3>
            ${ayuda("Hoy los datos no dicen qué mensaje se envió, así que esto es una hipótesis por probar, no un resultado.")}
            <ul>
              <li>Se guarda la variante enviada junto con el resultado (columna <code>variante</code> al subir datos).</li>
              <li>Se compara el porcentaje que contesta de cada variante contra la A, con intervalos y una prueba de dos proporciones.</li>
              <li>Para detectar una diferencia de 5 puntos entre dos variantes hacen falta unas <b>${num(M.tamanoMuestra(p0, 0.05))}</b> personas por variante; para 8 puntos, unas <b>${num(M.tamanoMuestra(p0, 0.08))}</b>.</li>
            </ul>
          </div>
        </div>
      </div>`;
    $("#m-comparar").addEventListener("change", (e) => { E.comparar = e.target.checked; recalcular(); vistaMensajes(); });
  }

  // ------------------------------------------------------------------ respuestas
  const EJEMPLOS_RESPUESTA = ["NO", "Sí, llámame mañana a las 4", "¿Cuánto cuesta?", "Ahorita no puedo", "Me siento mal desde ayer", "No gracias, ya no me interesa", "Mejor el lunes por la mañana", "Hola"];
  const NOMBRES_INTENCION = { baja: "Pide no recibir más mensajes", no_interesado: "No le interesa", interes: "Quiere seguir", agenda: "Propone un día u hora", posponer: "Pide otro momento", pregunta: "Hace una pregunta", seguridad: "Menciona un malestar o emergencia", ambigua: "No se entiende" };

  function aplicarRespuesta(lead, c) {
    const hechos = [];
    if (c.baja) {
      const clave = M.claveTelefono(lead.telefono);
      if (E.bajas.has(clave)) hechos.push("el teléfono ya estaba en la lista de bajas");
      else { E.bajas.add(clave); GUARDA_BAJAS(); hechos.push("baja registrada: no se le volverá a escribir"); }
    }
    if (c.estadoNuevo) {
      E.historial.push({ datos: E.actual, hora: new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }) });
      E.actual = E.actual.map((x) => (x.lead_id === lead.lead_id ? { ...x, resultado: c.estadoNuevo } : x));
      hechos.push(`estado cambiado a ${c.estadoNuevo}: sale de la lista de recontacto`);
    }
    if (!hechos.length) hechos.push(c.intencion === "posponer" ? "se reprograma el siguiente intento (no cambia el estado)" : "sin cambios en los datos: la conversación pasa a un asesor");
    recalcular();
    return hechos;
  }

  function vistaRespuestas() {
    const cont = $("#sub-respuestas");
    const L = E.lista;
    const candidatos = L.filas.filter((f) => f.mensaje).slice(0, 80);
    if (!E.chat.lead || !L.filas.some((f) => f.lead_id === E.chat.lead)) E.chat = { lead: candidatos.length ? candidatos[0].lead_id : null, texto: "", resultado: null, hechos: [] };
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      cont.innerHTML = `
        <div class="pila">
          <div class="tarjeta">
            <h3>Probar una conversación</h3>
            ${ayuda("Elige a una persona de la lista, escribe lo que contesta y mira qué entiende la herramienta y qué haría. Es un clasificador por reglas, sin modelo: cada decisión se puede leer. Ante la duda, pasa la conversación a un asesor.")}
            <div class="formulario">
              <div><label for="c-lead">Persona de la lista</label><select id="c-lead" class="entrada"></select></div>
              <div style="grid-column: span 2"><label for="c-texto">Lo que contesta la persona</label><input id="c-texto" class="entrada" type="text" placeholder="Escribe una respuesta, por ejemplo: sí, llámame mañana a las 4"></div>
            </div>
            <div class="fila-accion" id="c-ejemplos"></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>Conversación</h3><div id="c-chat" class="chat"></div></div>
            <div class="tarjeta"><h3>Qué entendió y qué hace</h3><div id="c-resultado"></div></div>
          </div>
          <p class="nota">Lo que no hace: enviar mensajes ni leer respuestas reales de WhatsApp (no hay conexión con ningún canal). Esto muestra la lógica que se conectaría. Las respuestas sugeridas las envía el asesor; solo la confirmación de una baja y el agradecimiento son textos fijos.</p>
        </div>`;
      $("#c-ejemplos").innerHTML = EJEMPLOS_RESPUESTA.map((t) => `<button class="boton claro" type="button" data-ej="${esc(t)}">${esc(t)}</button>`).join("");
      $$("#c-ejemplos button").forEach((b) => b.addEventListener("click", () => { $("#c-texto").value = b.dataset.ej; interpretar(); }));
      $("#c-texto").addEventListener("keydown", (e) => { if (e.key === "Enter") interpretar(); });
      $("#c-lead").addEventListener("change", () => { E.chat.lead = $("#c-lead").value; E.chat.resultado = null; E.chat.hechos = []; pintarChat(); });
      $("#c-texto").addEventListener("input", () => { E.chat.texto = $("#c-texto").value; });
    }
    $("#c-lead").innerHTML = candidatos.map((f) => `<option value="${esc(f.lead_id)}" ${f.lead_id === E.chat.lead ? "selected" : ""}>${esc(f.lead_id)} · ${esc(f.canal)} · ${f.nunca ? "nunca contactada" : "intento " + f.intento}</option>`).join("");
    pintarChat();
  }

  function interpretar() {
    const texto = $("#c-texto").value.trim();
    if (!texto) return;
    E.chat.texto = texto;
    E.chat.resultado = M.clasificarRespuesta(texto);
    E.chat.hechos = [];
    pintarChat();
  }

  function pintarChat() {
    const fila = E.lista.filas.find((f) => f.lead_id === E.chat.lead);
    const c = E.chat.resultado;
    const burbujas = [];
    if (fila) burbujas.push(`<div class="burbuja asesor"><div class="quien">${esc(fila.asesor || "Asesor")} · variante ${esc(fila.variante || "A")}</div>${esc(fila.mensaje)}</div>`);
    else burbujas.push('<p class="ayuda">No hay personas con mensaje en la lista con estas reglas.</p>');
    if (c) {
      burbujas.push(`<div class="burbuja persona"><div class="quien">La persona</div>${esc(E.chat.texto)}</div>`);
      if (c.respuestaSugerida) burbujas.push(`<div class="burbuja asesor sugerida"><div class="quien">Respuesta sugerida (la envía el asesor)</div>${esc(c.respuestaSugerida)}</div>`);
      else if (c.requiereHumano) burbujas.push('<div class="burbuja sistema">Pasa a un asesor: la herramienta no responde sola.</div>');
    }
    $("#c-chat").innerHTML = burbujas.join("");
    if (!c) {
      $("#c-resultado").innerHTML = '<p class="ayuda">Escribe una respuesta o elige un ejemplo.</p>';
      return;
    }
    const clase = c.intencion === "baja" || c.intencion === "seguridad" ? "mal" : c.intencion === "ambigua" || c.intencion === "pregunta" ? "" : "ok";
    const propuesta = [c.dia, c.hora >= 0 ? `a las ${c.hora}:00` : "", c.franja].filter(Boolean).join(" ");
    $("#c-resultado").innerHTML = `
      <p><span class="insignia ${clase}">${esc(NOMBRES_INTENCION[c.intencion])}</span> <span class="nota">confianza ${esc(c.confianza)}</span></p>
      <div class="etiqueta-campo">Por qué</div><p>${esc(c.motivo)}</p>
      <div class="etiqueta-campo">Qué hace la herramienta</div><p>${esc(c.accion)}</p>
      ${propuesta ? `<div class="etiqueta-campo">Lo que propone la persona</div><p>${esc(propuesta)}</p>` : ""}
      <div class="etiqueta-campo">¿Lo atiende un asesor?</div><p>${c.requiereHumano ? "Sí" : "No"}</p>
      <div class="fila-accion"><button class="boton" id="c-aplicar" type="button">Aplicar a los datos</button></div>
      <div id="c-hechos">${E.chat.hechos.map((h) => `<p class="exito">${esc(h)}</p>`).join("")}</div>`;
    $("#c-aplicar").addEventListener("click", () => {
      const lead = E.actual.find((l) => l.lead_id === E.chat.lead);
      if (!lead) return;
      E.chat.hechos = aplicarRespuesta(lead, c);
      $("#c-hechos").innerHTML = E.chat.hechos.map((h) => `<p class="exito">${esc(h)}</p>`).join("");
      $("#c-lead").innerHTML = E.lista.filas.filter((f) => f.mensaje).slice(0, 80).map((f) => `<option value="${esc(f.lead_id)}" ${f.lead_id === E.chat.lead ? "selected" : ""}>${esc(f.lead_id)} · ${esc(f.canal)} · ${f.nunca ? "nunca contactada" : "intento " + f.intento}</option>`).join("");
      const sigue = E.lista.filas.some((f) => f.lead_id === E.chat.lead);
      $("#c-hechos").insertAdjacentHTML("beforeend", `<p class="nota">${sigue ? "Esta persona sigue en la lista." : "Esta persona ya no aparece en la lista de recontacto."}</p>`);
    });
  }

  // ------------------------------------------------------------------ limites
  function vistaLimites() {
    const cont = $("#sub-limites");
    if (cont.dataset.listo) return;
    cont.dataset.listo = "1";
    const lista = (t, xs, clase) => `<div class="tarjeta ${clase || ""}"><h3>${t}</h3><ul>${xs.map((x) => `<li>${x}</li>`).join("")}</ul></div>`;
    cont.innerHTML = `<div class="pila">
      <div class="dos">
        ${lista("Lo que no se puede afirmar", ["Que un mensaje convenza más que otro: hay un solo intento de contacto por lead y no se registró el mensaje usado.", "Que el horario, por sí mismo, haga contestar más: en los datos, la hora del contacto y la rapidez del contacto van juntas.", "Que un asesor sea mejor o peor: las diferencias entre asesores caben dentro del azar.", "Que la ventaja del modelo sea detectable en un solo día: la simulación muestra un intervalo que incluye el cero."], "no")}
        ${lista("Supuestos que no son datos", ["Ventana de recuperación de 21 días, máximo de 3 intentos, 24 h entre intentos y 15 contactos por hora.", "Horario de 9:00 a 20:00 de lunes a sábado.", "La parte causal de la ventaja del horario (alpha) se explora de 0 a 1; no se conoce.", "La conversión a venta de quien contesta es la histórica por canal, suavizada hacia el promedio global."])}
      </div>
      ${lista("Datos que harían falta", ["Segundos intentos y su resultado.", "Texto del mensaje enviado y hora de apertura.", "Motivo cuando alguien dice que no le interesa.", "Origen del lead cuando llega por un agente de inteligencia artificial."])}
      ${lista("Qué hace esta versión web y qué no", ["Hace: la lista del día con reglas ajustables, la evidencia, la simulación, la calculadora de prueba A/B y la carga de datos (CSV, JSON, Excel).", "No hace: enviar mensajes, leer respuestas ni reentrenar el modelo con datos nuevos.", "No lee Parquet, bases de datos ni la nube: eso lo hace la versión completa (Python, con archivos .bat)."])}
    </div>`;
  }

  // ------------------------------------------------------------------ rutas
  const VISTAS = ["herramienta", "memo", "bitacora", "video"];
  function ruta() {
    const h = (location.hash || "#herramienta").slice(1);
    const v = VISTAS.includes(h) ? h : "herramienta";
    VISTAS.forEach((x) => { $("#vista-" + x).hidden = x !== v; });
    $$("nav.piezas a").forEach((a) => (a.getAttribute("href") === "#" + v ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    if (v === "herramienta" && E.lista) refrescar();
  }

  function iniciar() {
    armar();
    recalcular();
    ruta();
    window.addEventListener("hashchange", ruta);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(() => { if (!$("#vista-herramienta").hidden) refrescar(); });
    window.__recontacto = { E, M, recalcular };
  }
  iniciar();
})();
