  // ------------------------------------------------------------------ reglas de trato
  function motivoExclusion(l, ahora, r) {
    const dias = (ahora - l.fecha) / DIA;
    if (l.enBaja) return "baja";
    if (l.esDuplicado) return "duplicado";
    if (l.cliente) return "cliente";
    if (l.rechazo) return "rechazo";
    if (l.seguimiento) return "en_seguimiento";
    if (dias > r.ventanaDias) return "fuera_ventana";
    if (l.intentosPrevios >= r.maxIntentos) return "max_intentos";
    return null;
  }

  function horariosValidos(ahora, r) {
    const inicio = Math.floor(ahora / DIA) * DIA;
    const salida = [];
    for (let d = 0; d <= r.horizonteDias; d++) {
      for (let h = r.horaInicio; h < r.horaFin; h++) {
        const m = inicio + d * DIA + h * HORA;
        if (m > ahora && r.dias.includes(diaSemana(m))) salida.push(m);
      }
    }
    return salida;
  }

  const primerHorarioPermitido = (ultimo, ahora, r) => (ultimo === null || ultimo === undefined ? ahora : Math.max(ahora, ultimo + r.horasEntre * HORA));

