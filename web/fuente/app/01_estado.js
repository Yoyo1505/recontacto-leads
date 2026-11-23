  // ------------------------------------------------------------------ estado
  const base = M.desdeFilas(DATOS.columnas, DATOS.filas);
  const ultimoRegistro = Math.max(...base.map((l) => l.fecha));
  const fechaInicial = Math.floor(ultimoRegistro / M.DIA) * M.DIA + M.DIA + 8 * M.HORA;
  const E = {
    base,
    actual: base,
    historial: [],
    bajas: new Set(),
    reglas: { ...M.REGLAS, dias: [...M.REGLAS.dias] },
    ahora: fechaInicial,
    lista: null,
    pendiente: null,
    prep: null,
    sub: "lista",
    filtro: { canales: null, nuevos: false },
    orden: { col: "prioridad", asc: true },
    pagina: 0,
    seleccion: null,
    dimension: "franja_hora",
    comparar: true,
    chat: { lead: null, texto: "", resultado: null, hechos: [] },
  };
  try {
    (JSON.parse(localStorage.getItem("recontacto_bajas") || "[]") || []).forEach((c) => E.bajas.add(c));
  } catch (e) {}

  function validarReglas(r) {
    if (!(r.horaInicio < r.horaFin)) throw new Error("El horario de inicio debe ser menor que el de fin");
    if (!r.dias.length) throw new Error("Elige al menos un día");
    return true;
  }
  function recalcular() {
    try {
      validarReglas(E.reglas);
    } catch (e) {
      $("#aviso-reglas").textContent = e.message;
      return false;
    }
    $("#aviso-reglas").textContent = "";
    E.enriquecidos = M.enriquecer(E.actual, E.bajas);
    E.lista = M.generarLista(E.enriquecidos, MODELO, E.ahora, E.reglas, { compararVariantes: E.comparar });
    E.prep = null;
    E.pagina = 0;
    return true;
  }

