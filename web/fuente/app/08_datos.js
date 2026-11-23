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

