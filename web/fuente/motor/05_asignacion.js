  // ------------------------------------------------------------------ asignacion
  function calcularAsignacion(leads, modelo, ahora, r) {
    const base = modelo.principal;
    const esperaRef = modelo.espera_referencia_h;
    const excluidos = [];
    let elegibles = [];
    leads.forEach((l) => {
      const motivo = motivoExclusion(l, ahora, r);
      if (motivo) excluidos.push({ ...l, motivo, dias: (ahora - l.fecha) / DIA });
      else elegibles.push({ ...l, dias: (ahora - l.fecha) / DIA, intento: l.intentosPrevios + 1, nunca: l.intentosPrevios === 0 });
    });
    const slots = horariosValidos(ahora, r);
    elegibles.forEach((l) => {
      const minimo = primerHorarioPermitido(l.ultimoContacto, ahora, r);
      l.slots = slots.filter((s) => s >= minimo);
      l.base = parteLead(base, l);
      l.probs = l.slots.map((s) => probabilidad(base, l.base, s, esperaRef));
      l.probMax = l.probs.length ? Math.max(...l.probs) : -Infinity;
      l.probPromedio = l.probs.length ? l.probs.reduce((a, b) => a + b, 0) / l.probs.length : NaN;
    });
    elegibles = elegibles
      .map((l, i) => ({ l, i }))
      .sort((a, b) => Number(b.l.nunca) - Number(a.l.nunca) || b.l.dias - a.l.dias || (a.l.probMax === b.l.probMax ? 0 : b.l.probMax > a.l.probMax ? 1 : -1) || a.i - b.i)
      .map((x) => x.l);
    const restante = new Map();
    elegibles.forEach((l) => {
      l.horario = null;
      l.prob = null;
      let elegido = -1;
      for (let k = 0; k < l.slots.length; k++) {
        if ((restante.has(l.slots[k]) ? restante.get(l.slots[k]) : r.capacidad) <= 0) continue;
        if (l.nunca) {
          elegido = k;
          break;
        }
        if (elegido < 0 || l.probs[k] > l.probs[elegido]) elegido = k;
      }
      if (elegido >= 0) {
        l.horario = l.slots[elegido];
        l.prob = l.probs[elegido];
        restante.set(l.horario, (restante.has(l.horario) ? restante.get(l.horario) : r.capacidad) - 1);
      }
    });
    return { elegibles, excluidos, slots };
  }

  function textoPorcentaje(p) {
    return `${Math.round(p * 100)}%`;
  }
  const ETIQUETAS = { canal: (v) => `canal ${v}`, objetivo: (v) => `perfil ${v}`, franja_hora: (v) => `horario ${v}`, dia_semana: (v) => `día ${v}`, edad: (v) => `edad ${Math.round(v)}` };
  const VISIBLES = ["canal", "objetivo", "franja_hora", "dia_semana", "edad"];

  function explicar(modelo, l) {
    if (l.nunca) return "Nunca fue contactado: se agenda en la primera hora hábil con espacio, sin esperar un mejor horario.";
    const a = aportes(modelo.principal, l, l.horario, modelo.espera_referencia_h);
    const valores = { canal: l.canal, objetivo: l.objetivo, franja_hora: franjaHora(horaDe(l.horario)), dia_semana: DIAS[diaSemana(l.horario)], edad: l.edad };
    const visibles = VISIBLES.filter((c) => !nuloNumero(valores[c]) && valores[c] !== "").map((c) => [c, a[c]]);
    const ordenados = visibles.map((v, i) => ({ v, i })).sort((x, y) => y.v[1] - x.v[1] || x.i - y.i).map((x) => x.v);
    const aFavor = ordenados.filter(([, v]) => v > 0.03).slice(0, 2).map(([c]) => c);
    const enContra = ordenados.slice().reverse().filter(([, v]) => v < -0.03).slice(0, 1).map(([c]) => c);
    const partes = [`Horario asignado: ${DIAS[diaSemana(l.horario)]} ${pad(horaDe(l.horario))}:00 (${textoPorcentaje(l.prob)} de probabilidad de contestar contra ${textoPorcentaje(l.probPromedio)} en promedio).`];
    if (aFavor.length) partes.push("A favor: " + aFavor.map((c) => ETIQUETAS[c](valores[c])).join(", ") + ".");
    if (enContra.length) partes.push("En contra: " + enContra.map((c) => ETIQUETAS[c](valores[c])).join(", ") + ".");
    return partes.join(" ");
  }

