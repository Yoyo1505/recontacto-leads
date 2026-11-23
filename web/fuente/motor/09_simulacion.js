  // ------------------------------------------------------------------ simulacion
  function prepararSimulacion(lista, ahora, modelo, r) {
    const asignados = lista.elegibles.filter((l) => l.horario !== null);
    const esperaRef = modelo.espera_referencia_h;
    const modelos = modelo.bootstrap;
    const pPol = [];
    const pBase = [];
    modelos.forEach((m) => {
      const a = new Float64Array(asignados.length);
      const b = new Float64Array(asignados.length);
      asignados.forEach((l, i) => {
        const base = parteLead(m, l);
        a[i] = probabilidad(m, base, l.horario, esperaRef);
        let suma = 0;
        for (const s of l.slots) suma += probabilidad(m, base, s, esperaRef);
        b[i] = suma / l.slots.length;
      });
      pPol.push(a);
      pBase.push(b);
    });
    const pesos = asignados.map((l) => (modelo.conversion[l.canal] !== undefined ? modelo.conversion[l.canal] : promedio(Object.values(modelo.conversion))));
    return { pPol, pBase, pesos, n: asignados.length };
  }
  const promedio = (v) => v.reduce((a, b) => a + b, 0) / v.length;

  function simular(prep, alfa, nSim, semilla = 7) {
    const aleatorio = generador(semilla);
    const diferencias = new Array(nSim);
    const tasaPol = new Array(nSim);
    const tasaBase = new Array(nSim);
    const ventas = new Array(nSim);
    const nModelos = prep.pPol.length;
    for (let s = 0; s < nSim; s++) {
      const m = Math.floor(aleatorio() * nModelos);
      const pol = prep.pPol[m];
      const base = prep.pBase[m];
      let cPol = 0;
      let cBase = 0;
      let extra = 0;
      for (let i = 0; i < prep.n; i++) {
        const efectiva = Math.min(1, Math.max(0, base[i] + alfa * (pol[i] - base[i])));
        const a = aleatorio() < efectiva ? 1 : 0;
        const b = aleatorio() < base[i] ? 1 : 0;
        cPol += a;
        cBase += b;
        extra += (a - b) * prep.pesos[i];
      }
      diferencias[s] = cPol - cBase;
      tasaPol[s] = prep.n ? cPol / prep.n : 0;
      tasaBase[s] = prep.n ? cBase / prep.n : 0;
      ventas[s] = extra;
    }
    return { diferencias, tasaPol, tasaBase, ventas };
  }
  function resumenSimulacion(corridas) {
    const d = corridas.diferencias;
    if (!d.length) return { media: 0, icBajo: 0, icAlto: 0, probMejora: 0, ventasExtra: 0 };
    return { media: promedio(d), icBajo: percentil(d, 2.5), icAlto: percentil(d, 97.5), probMejora: d.filter((x) => x > 0).length / d.length, ventasExtra: promedio(corridas.ventas) };
  }

