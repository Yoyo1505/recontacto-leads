  // ------------------------------------------------------------------ arranque de la pagina
  function iniciar() {
    armar();
    recalcular();
    refrescar();
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(() => refrescar());
    window.addEventListener("resize", () => { clearTimeout(E.temporizadorRedibujo); E.temporizadorRedibujo = setTimeout(refrescar, 200); });
    window.__recontacto = { E, M, recalcular };
  }
