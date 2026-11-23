  // ------------------------------------------------------------------ fechas
  const pad = (n) => String(n).padStart(2, "0");
  const fmt = (ms) => {
    const d = new Date(ms);
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
  };
  const fmtDia = (ms) => fmt(ms).slice(0, 10);
  const diaSemana = (ms) => (new Date(ms).getUTCDay() + 6) % 7;
  const horaDe = (ms) => new Date(ms).getUTCHours();

  function crearFecha(y, mo, d, h, mi) {
    if (mo < 1 || mo > 12 || d < 1 || d > 31 || h > 23 || mi > 59) return null;
    const ms = Date.UTC(y, mo - 1, d, h, mi);
    const comprobacion = new Date(ms);
    return comprobacion.getUTCMonth() === mo - 1 && comprobacion.getUTCDate() === d ? ms : null;
  }

  function parseFecha(texto) {
    if (texto === null || texto === undefined) return null;
    const t = String(texto).trim();
    let m = t.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::\d{2})?)?$/);
    if (m) return crearFecha(+m[1], +m[2], +m[3], +(m[4] || 0), +(m[5] || 0));
    m = t.match(/^(\d{2})\/(\d{2})\/(\d{4})(?: (\d{2}):(\d{2})(?::\d{2})?)?$/);
    if (m) return crearFecha(+m[3], +m[2], +m[1], +(m[4] || 0), +(m[5] || 0));
    return null;
  }

