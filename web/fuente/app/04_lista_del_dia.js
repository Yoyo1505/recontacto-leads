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

