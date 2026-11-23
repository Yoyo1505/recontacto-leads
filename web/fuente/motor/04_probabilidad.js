  // ------------------------------------------------------------------ probabilidad
  function franjaHora(h) {
    return h <= 8 ? "<9" : h <= 10 ? "9-10" : h <= 12 ? "11-12" : h <= 15 ? "13-15" : h <= 18 ? "16-18" : "19+";
  }
  function rangoEspera(horas) {
    return horas <= 0.5 ? "<30min" : horas <= 2 ? "30min-2h" : horas <= 6 ? "2-6h" : horas <= 12 ? "6-12h" : horas <= 24 ? "12-24h" : ">24h";
  }
  const sigmoide = (z) => 1 / (1 + Math.exp(-z));
  const nuloNumero = (v) => v === null || v === undefined || Number.isNaN(v);

  function parteLead(modelo, l) {
    const n = modelo.num;
    const edad = nuloNumero(l.edad) ? n.edad.mediana : l.edad;
    const plan = nuloNumero(l.plan) ? n.plan_de_interes.mediana : l.plan;
    return (
      modelo.intercepto +
      (modelo.cat.canal[l.canal] || 0) +
      (modelo.cat.objetivo[l.objetivo] || 0) +
      n.edad.coef * ((edad - n.edad.media) / n.edad.escala) +
      n.plan_de_interes.coef * ((plan - n.plan_de_interes.media) / n.plan_de_interes.escala)
    );
  }
  function parteHorario(modelo, ms, esperaRef) {
    return (modelo.cat.franja_hora[franjaHora(horaDe(ms))] || 0) + (modelo.cat.dia_semana[DIAS[diaSemana(ms)]] || 0) + (modelo.cat.rango_espera[rangoEspera(esperaRef)] || 0);
  }
  const probabilidad = (modelo, base, ms, esperaRef) => sigmoide(base + parteHorario(modelo, ms, esperaRef));

  function aportes(modelo, l, ms, esperaRef) {
    const salida = {};
    const valores = { canal: l.canal, objetivo: l.objetivo, franja_hora: franjaHora(horaDe(ms)), dia_semana: DIAS[diaSemana(ms)], rango_espera: rangoEspera(esperaRef) };
    for (const columna of Object.keys(valores)) {
      let suma = 0;
      for (const categoria of Object.keys(modelo.cat[columna])) {
        const x = categoria === valores[columna] ? 1 : 0;
        suma += modelo.cat[columna][categoria] * (x - modelo.media_cat[columna][categoria]);
      }
      salida[columna] = suma;
    }
    const n = modelo.num;
    const edad = nuloNumero(l.edad) ? n.edad.mediana : l.edad;
    salida.edad = n.edad.coef * ((edad - n.edad.media) / n.edad.escala - n.edad.media_x);
    return salida;
  }

