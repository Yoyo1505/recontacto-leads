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
  const poner = (id, t) => { const e = document.getElementById(id); if (e) e.innerHTML = "<b>Cómo leerlo:</b> " + t; };

