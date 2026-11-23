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

