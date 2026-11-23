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

