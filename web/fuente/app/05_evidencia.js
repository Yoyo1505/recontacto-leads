  // ------------------------------------------------------------------ evidencia
  const ORDEN = { franja_hora: EVID.confusion.franjas, rango_espera: EVID.confusion.esperas, dia_semana: M.DIAS };
  const NOMBRES_DIM = { franja_hora: "Hora del contacto", rango_espera: "Espera desde el registro", canal: "Canal", dia_semana: "Día de la semana" };
  const NOMBRES_ABL = { solo_canal: "Solo canal", horario_y_canal: "Horario y canal", solo_espera: "Solo espera", solo_horario: "Solo horario", espera_y_horario: "Espera y horario", perfil: "Perfil (objetivo, edad, plan)", todo: "Todas las variables" };

  function graficaTasasBase() {
    const dim = E.dimension;
    let filas = EVID.tasas[dim].slice();
    if (ORDEN[dim]) filas = ORDEN[dim].map((c) => filas.find((f) => f.categoria === c)).filter(Boolean);
    else filas.sort((a, b) => a.tasa - b.tasa);
    const c = colores();
    const media = 1 - EVID.tasa_contesta;
    graficar("e-tasas", [{ type: "bar", x: filas.map((f) => f.categoria), y: filas.map((f) => f.tasa * 100), marker: { color: c.steel }, error_y: { type: "data", symmetric: false, array: filas.map((f) => (f.alto - f.tasa) * 100), arrayminus: filas.map((f) => (f.tasa - f.bajo) * 100), color: c.muted }, customdata: filas.map((f) => [f.n, f.bajo * 100, f.alto * 100]), hovertemplate: "%{x}: %{y:.1f}%<br>n = %{customdata[0]}<br>Intervalo 95%: %{customdata[1]:.0f}% a %{customdata[2]:.0f}%<extra></extra>" }], { xaxis: { type: "category" }, yaxis: { title: "% que no contesta", range: [0, 85] }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: media * 100, y1: media * 100, line: { color: c.accent, dash: "dash" } }], annotations: [{ xref: "paper", x: 0, y: media * 100, text: `Promedio ${pct(media)}`, showarrow: false, yshift: 10, xanchor: "left", font: { color: c.accent } }], height: 340 });
  }

  function graficaTasas() {
    graficaTasasBase();
    const filas = EVID.tasas[E.dimension].slice().sort((a, b) => a.tasa - b.tasa);
    const peor = filas[filas.length - 1];
    const mejor = filas[0];
    poner("e-tasas-txt", `en "${NOMBRES_DIM[E.dimension]}", donde más gente no contesta es ${peor.categoria} (${pct(peor.tasa)}) y donde menos, ${mejor.categoria} (${pct(mejor.tasa)}). Las líneas pequeñas de cada barra son el margen de error: si las de dos barras se traslapan, la diferencia puede ser azar. La línea punteada es el promedio.`);
  }

  function vistaEvidencia() {
    const cont = $("#sub-evidencia");
    const m = EVID.metricas;
    if (!cont.dataset.listo) {
      cont.dataset.listo = "1";
      cont.innerHTML = `
        <div class="pila">
          <div class="kpis">${kpi("AUC del modelo", m.logistica.auc.toFixed(2), `Intervalo 95%: ${m.logistica.auc_ic95[0].toFixed(2)} a ${m.logistica.auc_ic95[1].toFixed(2)}`)}${kpi("Azar", m.constante.auc.toFixed(2), "AUC de la tasa constante")}${kpi("Precisión en el 10% más alto", pct(m.logistica.precision_top_decil), `Base: ${pct(m.logistica.tasa_base)}`)}${kpi("Periodo de prueba", `desde ${m.corte.slice(8)}/${m.corte.slice(5, 7)}`, `${m.n_prueba} contactos`)}</div>
          <div class="tarjeta resumen"><h3>En resumen, en palabras sencillas</h3><ul id="e-resumen"></ul></div>
          <div class="dos">
            <div class="tarjeta"><h3>1 · El canal importa</h3>${ayuda("Porcentaje de personas que no contestan, según cómo llegaron.")}<div id="e-canal" class="grafica"></div><p class="lectura-caja" id="e-canal-txt"></p></div>
            <div class="tarjeta"><h3>2 · La rapidez importa</h3>${ayuda("Porcentaje que no contesta, según cuánto tardó el primer contacto desde que pidieron información.")}<div id="e-rapidez" class="grafica"></div><p class="lectura-caja" id="e-rapidez-txt"></p></div>
          </div>
          <div class="tarjeta"><h3>Explora otra variable</h3>${ayuda("Elige una variable. Las barras de error son intervalos de confianza al 95%: si dos barras se traslapan, la diferencia puede ser azar.")}<select id="e-dim" class="entrada" style="max-width:320px;margin-bottom:10px">${Object.entries(NOMBRES_DIM).map(([k, t]) => `<option value="${k}">${t}</option>`).join("")}</select><div id="e-tasas" class="grafica"></div><p class="lectura-caja" id="e-tasas-txt"></p></div>
          <div class="dos">
            <div class="tarjeta"><h3>La hora y la espera van juntas</h3>${ayuda("Los contactos de la tarde casi siempre fueron rápidos. Por eso no se puede separar el efecto de la hora del de la rapidez.")}<div id="e-conf" class="grafica"></div><p class="lectura-caja" id="e-conf-txt"></p></div>
            <div class="tarjeta"><h3>Qué variables aportan</h3>${ayuda("El canal explica casi toda la señal; el perfil de la persona no aporta.")}<div id="e-abl" class="grafica"></div><p class="lectura-caja" id="e-abl-txt"></p></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>Calibración</h3>${ayuda("Con puntos sobre la diagonal, la probabilidad predicha coincide con lo observado. Aquí el modelo subestima en los grupos bajos.")}<div id="e-cal" class="grafica"></div><p class="lectura-caja" id="e-cal-txt"></p></div>
            <div class="tarjeta"><h3>Control estadístico por día</h3>${ayuda("Carta p: un día fuera de los límites sería una señal de algo distinto al azar.")}<div id="e-carta" class="grafica"></div><p class="lectura-caja" id="e-carta-txt"></p></div>
          </div>
          <div class="dos">
            <div class="tarjeta"><h3>¿Algún asesor se aleja del promedio?</h3>${ayuda("Gráfico de embudo: un punto dentro de los límites no se distingue del azar.")}<div id="e-emb" class="grafica"></div><p class="lectura-caja" id="e-emb-txt"></p></div>
            <div class="tarjeta"><h3>Del interés a la compra</h3>${ayuda("Cuántas personas llegan a cada etapa (datos originales).")}<div id="e-fun" class="grafica"></div><p class="lectura-caja" id="e-fun-txt"></p></div>
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

    const media = 1 - EVID.tasa_contesta;
    const porTasa = EVID.tasas.canal.slice().sort((a, b) => a.tasa - b.tasa);
    const canalPeor = porTasa[porTasa.length - 1];
    const canalMejor = porTasa[0];
    const espera = Object.fromEntries(EVID.tasas.rango_espera.map((f) => [f.categoria, f]));
    const colorear = (f) => (f.tasa > media + 0.03 ? c.warn : f.tasa < media - 0.03 ? c.ok : c.steel);
    const barras = (id, filas) => graficar(id, [{ type: "bar", x: filas.map((f) => f.categoria), y: filas.map((f) => f.tasa * 100), text: filas.map((f) => `${(f.tasa * 100).toFixed(0)}%`), textposition: "outside", marker: { color: filas.map(colorear) }, customdata: filas.map((f) => f.n), hovertemplate: "%{x}: %{y:.1f}% no contesta<br>n = %{customdata} contactos<extra></extra>" }], { xaxis: { type: "category" }, yaxis: { title: "% que no contesta", range: [0, 70] }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: media * 100, y1: media * 100, line: { color: c.accent, dash: "dash" } }], annotations: [{ xref: "paper", x: 1, y: media * 100, text: `Promedio ${pct(media)}`, showarrow: false, yshift: 10, xanchor: "right", font: { color: c.accent } }], height: 300 });
    barras("e-canal", porTasa);
    barras("e-rapidez", ORDEN.rango_espera.map((k) => espera[k]).filter(Boolean));
    poner("e-canal-txt", `cada barra es un canal. Rojo = no contesta más que el promedio, verde = menos. ${canalPeor.categoria} es el peor (${pct(canalPeor.tasa)}) y ${canalMejor.categoria} el mejor (${pct(canalMejor.tasa)}).`);
    poner("e-rapidez-txt", `de izquierda a derecha, más tiempo entre la solicitud y el primer contacto. Con menos de 30 minutos no contesta el ${pct(espera["<30min"].tasa)}; entre 12 y 24 horas, el ${pct(espera["12-24h"].tasa)}. Ojo: la hora del día y la rapidez van juntas en los datos, así que no se puede separar cuál de las dos pesa.`);
    const fuera = EVID.carta_p.filter((r) => r.fuera).length;
    const asesFuera = EVID.embudo_asesores.asesores.filter((a) => a.fuera_de_control).length;
    $("#e-resumen").innerHTML = [
      `De cada 10 personas contactadas, ${Math.round(media * 10)} no contestan: ${pct(media, 1)} sin contar los 70 registros con teléfono repetido (con ellos, 40.3% de 1,694).`,
      `El canal es lo que más pesa: no contesta el ${pct(canalPeor.tasa)} de quienes llegaron por ${canalPeor.categoria} y el ${pct(canalMejor.tasa)} de quienes llegaron por ${canalMejor.categoria}.`,
      `La rapidez también: si se contacta en menos de 30 minutos no contesta el ${pct(espera["<30min"].tasa)}; si pasan de 12 a 24 horas, el ${pct(espera["12-24h"].tasa)}.`,
      `El modelo acierta un poco mejor que tirar una moneda (AUC ${m.logistica.auc.toFixed(2)} contra 0.50). Sirve para ordenar y elegir horarios, no para prometer resultados.`,
      asesFuera === 0 ? "Ningún asesor se aleja del promedio más de lo que se esperaría por azar: no hay asesores mejores o peores en estos datos." : `${asesFuera} asesor(es) se aleja(n) del promedio más de lo esperado por azar.`,
      `${fuera} de ${EVID.carta_p.length} días se salieron de los límites esperados por azar.`,
    ].map((t) => `<li>${t}</li>`).join("");
    poner("e-conf-txt", "cada casilla combina la hora del contacto (filas) con la espera desde el registro (columnas). Más oscuro = no contesta más; el número es cuántos contactos hay. Las casillas de la tarde casi no tienen contactos, por eso no se puede saber si pesa la hora o la rapidez.");
    poner("e-abl-txt", `cada barra es qué tan bien predice un modelo con esas variables; 0.50 es el azar (la línea punteada). El canal aporta casi todo (${EVID.ablacion.solo_canal.toFixed(2)}); el perfil de la persona no mejora nada (${EVID.ablacion.perfil.toFixed(2)}).`);
    poner("e-cal-txt", "si los puntos siguen la diagonal, cuando el modelo dice 60% de probabilidad de contestar, contesta cerca del 60%. Aquí los grupos con probabilidad baja contestan algo más de lo que el modelo dice: es prudente.");
    poner("e-carta-txt", `cada punto es el porcentaje que no contesta ese día; las líneas punteadas son los límites esperados por azar. ${fuera === 0 ? "Ningún día se sale." : `${fuera} de ${EVID.carta_p.length} días (rombo) se salió; con tantos días, uno o dos fuera es normal.`}`);
    poner("e-emb-txt", `cada punto es un asesor: más a la derecha, más contactos. ${asesFuera === 0 ? "Todos caen dentro de los límites, así que sus diferencias caben en el azar." : "Los que caen fuera de los límites se alejan del promedio más de lo esperado."}`);
    const v = EVID.embudo.valores;
    poner("e-fun-txt", `de ${num(v[0])} personas que pidieron información, ${num(v[2])} contestaron (${pct(v[2] / v[0])}) y ${num(v[3])} compraron (${pct(v[3] / v[0], 1)}).`);
  }

