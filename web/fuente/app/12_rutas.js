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
