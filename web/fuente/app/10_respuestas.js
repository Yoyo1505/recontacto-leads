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

