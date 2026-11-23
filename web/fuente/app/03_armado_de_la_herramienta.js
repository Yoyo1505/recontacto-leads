  // ------------------------------------------------------------------ armado de la herramienta
  const SUBPESTANAS = [
    ["lista", "Lista del día", "¿A quién contacto hoy?", "La tabla de personas a las que hay que volver a escribir, con su horario, el motivo y el mensaje.", "trabajar"],
    ["mensajes", "Mensajes", "¿Qué le escribo?", "Los mensajes por situación y la estrategia de cada variante.", "trabajar"],
    ["respuestas", "Respuestas", "¿Qué hago si contesta?", "Escribe lo que contestó una persona y mira qué entiende la herramienta y qué haría.", "trabajar"],
    ["datos", "Datos", "¿Cómo subo personas o bajas?", "Sube un archivo, agrega personas nuevas o registra a quien pidió no recibir mensajes.", "trabajar"],
    ["evidencia", "Evidencia", "¿Qué dicen los datos?", "Dónde se pierde la respuesta y qué tan confiable es el modelo, con un resumen en palabras sencillas.", "entender"],
    ["simulacion", "Simulación", "¿Cuánto ayudaría?", "Cuántas personas más contestarían con el horario del modelo, con su incertidumbre.", "entender"],
    ["ab", "Prueba A/B", "¿Cómo lo compruebo?", "Cuánta gente y cuántos días hacen falta para comprobar una mejora de verdad.", "entender"],
    ["limites", "Límites", "¿Qué no se puede afirmar?", "Lo que estos datos no permiten concluir y los supuestos que usé.", "entender"],
  ];
  const GRUPOS = { trabajar: "Para trabajar cada día", entender: "Para entender si funciona" };

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
      <p class="nota-hero">Datos ficticios (1,811 registros del 28 de septiembre al 8 de noviembre de 2026). Cambia las reglas y todo se recalcula.</p>
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
          <div class="pestanas-guia">${Object.entries(GRUPOS).map(([g, titulo]) => `<div class="grupo-pestanas"><div class="grupo-titulo">${titulo}</div><div class="subpestanas" role="tablist" aria-label="${titulo}">${SUBPESTANAS.filter((p) => p[4] === g).map(([id, t, q]) => `<button role="tab" data-sub="${id}" aria-selected="${id === E.sub}"><span class="n">${SUBPESTANAS.findIndex((p) => p[0] === id) + 1}</span><span class="tx"><b>${t}</b><small>${q}</small></span></button>`).join("")}</div></div>`).join("")}</div>
          <div class="guia-actual" id="guia-actual" role="status" aria-live="polite"></div>
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
    pintarGuia();
  }

  function pintarGuia() {
    const i = SUBPESTANAS.findIndex((p) => p[0] === E.sub);
    const [, t, q, d] = SUBPESTANAS[i];
    const ant = SUBPESTANAS[i - 1];
    const sig = SUBPESTANAS[i + 1];
    $("#guia-actual").innerHTML = `<div><span class="paso">Pestaña ${i + 1} de ${SUBPESTANAS.length}</span><b>${t}</b> · ${q}<p>${d}</p></div><div class="fila-accion">${ant ? `<button class="boton claro" type="button" data-ir="${ant[0]}">← ${ant[1]}</button>` : ""}${sig ? `<button class="boton" type="button" data-ir="${sig[0]}">${sig[1]} →</button>` : ""}</div>`;
    $$("#guia-actual [data-ir]").forEach((b) => b.addEventListener("click", () => { mostrarSub(b.dataset.ir); $(".pestanas-guia").scrollIntoView({ behavior: "smooth", block: "start" }); }));
  }

  function mostrarSub(id) {
    E.sub = id;
    $$(".subpestanas button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.sub === id)));
    $$(".subvista").forEach((s) => (s.hidden = s.id !== "sub-" + id));
    pintarGuia();
    refrescar();
  }
  function refrescar() {
    ({ lista: vistaLista, mensajes: vistaMensajes, respuestas: vistaRespuestas, evidencia: vistaEvidencia, simulacion: vistaSimulacion, ab: vistaAB, datos: vistaDatos, limites: vistaLimites })[E.sub]();
  }

