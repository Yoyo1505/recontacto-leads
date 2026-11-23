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
            <div class="tarjeta"><h3>Distribución de la mejora</h3><div id="s-hist" class="grafica"></div><p class="lectura-caja"><b>Cómo leerlo:</b> cada barra cuenta cuántas de las simulaciones dieron esa mejora (cuántas personas más contestan). La zona verde es el intervalo de 95%: si incluye el 0, con un solo día de lista no se distingue la mejora del azar.</p></div>
            <div class="tarjeta"><h3>Sensibilidad al supuesto</h3><div id="s-sens" class="grafica"></div><p class="lectura-caja" id="s-sens-txt"></p></div>
          </div>
          <div class="tarjeta"><h3>Tasa de respuesta simulada por brazo</h3><div id="s-caja" class="grafica"></div><p class="lectura-caja"><b>Cómo leerlo:</b> cada caja es el porcentaje que contesta en una lista con ese horario; la línea del centro es la mediana y el rombo el promedio. Si las cajas se traslapan casi por completo, la diferencia es pequeña frente al azar.</p></div>
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
    const todasCruzan = sens.every((s) => s.icBajo <= 0 && 0 <= s.icAlto);
    poner("s-sens-txt", `muestra el resultado si el horario explicara más o menos de la ventaja (alpha, de 0 a 1). La banda es el intervalo de 95%. ${todasCruzan ? "La banda incluye el 0 con cualquier valor de alpha: con este supuesto o con otro, no hay evidencia de mejora con un solo día de lista." : "Con algunos valores de alpha la banda queda por encima de 0."}`);
    graficar("s-caja", [{ type: "box", y: corridas.tasaBase.map((v) => v * 100), name: "Horario sin optimizar", marker: { color: c.muted }, boxmean: true }, { type: "box", y: corridas.tasaPol.map((v) => v * 100), name: "Horario del modelo", marker: { color: c.steel }, boxmean: true }], { yaxis: { title: "% que contesta en la lista" }, showlegend: false, height: 320 });
  }

