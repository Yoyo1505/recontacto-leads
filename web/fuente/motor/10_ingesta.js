  // ------------------------------------------------------------------ ingesta
  const SINONIMOS = {
    lead_id: ["id", "id_lead", "lead", "folio", "leadid"],
    fecha_registro: ["fecha", "fecha_de_registro", "fecha_alta", "created_at", "registro"],
    canal: ["fuente", "origen", "source", "channel"],
    anuncio: ["ad", "creativo"],
    estado: ["entidad", "estado_republica", "entidad_federativa", "state"],
    edad: ["age"],
    objetivo: ["motivo_de_consulta", "goal"],
    plan_de_interes: ["plan", "plan_interes"],
    telefono: ["celular", "whatsapp", "tel", "phone", "telefono_celular"],
    asesor: ["agente", "advisor", "asignado"],
    primer_contacto: ["fecha_primer_contacto", "contacted_at", "primer_contacto_fecha"],
    resultado: ["status", "resultado_final", "etapa"],
    monto_venta: ["monto", "importe", "monto_de_venta"],
    baja: ["no_contactar", "opt_out", "unsubscribe"],
  };
  const REQUERIDAS = ["lead_id", "fecha_registro", "canal", "telefono", "resultado"];
  const CANALES = { meta: "Meta", tiktok: "TikTok", google: "Google", referido: "Referido", organico: "Organico" };
  const SINONIMOS_RESULTADO = { contesto: "en_seguimiento", nuevo: "sin_contactar" };
  const claveColumna = (n) => sinAcentos(n).trim().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");

  function textoCelda(v) {
    if (v === null || v === undefined) return "";
    if (typeof v === "number") return Number.isNaN(v) ? "" : Number.isInteger(v) ? String(v) : String(v);
    if (v instanceof Date) return fmt(v.getTime());
    return String(v).trim();
  }

  function normalizarColumnas(filas) {
    const encontradas = new Map();
    filas.slice(0, 200).forEach((f) => Object.keys(f).forEach((k) => encontradas.has(claveColumna(k)) || encontradas.set(claveColumna(k), k)));
    const mapeo = {};
    for (const canonica of Object.keys(SINONIMOS)) {
      for (const candidata of [canonica, ...SINONIMOS[canonica]]) {
        if (encontradas.has(candidata) && !(canonica in mapeo)) mapeo[canonica] = encontradas.get(candidata);
      }
    }
    const faltantes = REQUERIDAS.filter((c) => !(c in mapeo));
    if (faltantes.length) throw new Error(`Faltan columnas obligatorias: ${faltantes.join(", ")}. Columnas encontradas: ${[...encontradas.values()].join(", ")}`);
    const usadas = new Set(Object.values(mapeo));
    const ignoradas = [...encontradas.values()].filter((c) => !usadas.has(c));
    const texto = filas.map((f) => {
      const fila = {};
      for (const canonica of Object.keys(SINONIMOS)) fila[canonica] = canonica in mapeo ? textoCelda(f[mapeo[canonica]]) : "";
      return fila;
    });
    return { texto, mapeo, ignoradas, tieneBaja: "baja" in mapeo };
  }

  function numeroTexto(t) {
    if (t === "") return null;
    const n = Number(String(t).replace(/,/g, ""));
    return Number.isFinite(n) ? n : null;
  }

  function validarFilas(texto) {
    const validos = [];
    const rechazados = [];
    const avisos = [];
    const vistos = new Set();
    texto.forEach((fila) => {
      const rechazar = (motivo) => rechazados.push({ lead_id: fila.lead_id, motivo });
      const lead = fila.lead_id;
      if (lead === "") return rechazar("lead_id vacío");
      if (vistos.has(lead)) return rechazar("lead_id repetido en el archivo");
      const registro = parseFecha(fila.fecha_registro);
      if (registro === null) return rechazar(`fecha_registro no válida: "${fila.fecha_registro}"`);
      if (fila.canal === "") return rechazar("canal vacío");
      if (fila.telefono.replace(/\D/g, "").length < 8) return rechazar(`teléfono no válido: "${fila.telefono}"`);
      const clave = claveColumna(fila.resultado);
      const resultado = SINONIMOS_RESULTADO[clave] || clave;
      if (!RESULTADOS.includes(resultado)) return rechazar(`resultado desconocido: "${fila.resultado}"`);
      let contacto = null;
      if (fila.primer_contacto !== "") {
        contacto = parseFecha(fila.primer_contacto);
        if (contacto === null) return rechazar(`primer_contacto no válido: "${fila.primer_contacto}"`);
      }
      let edad = numeroTexto(fila.edad);
      if (fila.edad !== "" && (edad === null || edad < 18 || edad > 100)) {
        avisos.push([lead, `edad fuera de rango o no numérica ("${fila.edad}"); se deja vacía`]);
        edad = null;
      }
      let monto = numeroTexto(fila.monto_venta);
      if (fila.monto_venta !== "" && (monto === null || monto < 0)) {
        avisos.push([lead, `monto_venta no válido ("${fila.monto_venta}"); se deja vacío`]);
        monto = null;
      }
      if (resultado === "venta" && !monto) avisos.push([lead, "venta sin monto"]);
      if (contacto !== null && contacto < registro) avisos.push([lead, "primer_contacto anterior al registro"]);
      if (resultado === "sin_contactar" && contacto !== null) avisos.push([lead, "marcado sin_contactar pero trae primer_contacto"]);
      if (resultado === "no_contesta" && contacto === null) avisos.push([lead, "marcado no_contesta pero sin primer_contacto"]);
      const registroValido = {
        lead_id: lead,
        fecha: registro,
        canal: CANALES[claveColumna(fila.canal)] || fila.canal,
        anuncio: fila.anuncio || null,
        entidad: fila.estado,
        edad,
        objetivo: fila.objetivo,
        plan: numeroTexto(fila.plan_de_interes),
        telefono: fila.telefono,
        asesor: fila.asesor || null,
        contacto,
        resultado,
        monto,
      };
      if (fila.baja !== undefined && fila.baja !== "") registroValido.baja = ["1", "true", "si", "sí", "yes", "s", "x"].includes(fila.baja.toLowerCase());
      validos.push(registroValido);
      vistos.add(lead);
    });
    return { validos, rechazados, avisos };
  }

  const vacio = (v) => v === null || v === undefined || v === "" || Number.isNaN(v);
  const igual = (a, b) => (vacio(a) || vacio(b) ? vacio(a) && vacio(b) : a === b);
  const SEGUIMIENTO = ["resultado", "contacto", "asesor", "monto", "plan", "edad", "objetivo", "anuncio", "entidad", "canal"];

  function fusionar(actual, nuevos) {
    const resumen = { agregados: [], actualizados: {}, sinCambio: 0, conflictos: [] };
    const indice = new Map(actual.map((l, i) => [l.lead_id, i]));
    const fusionado = actual.map((l) => ({ ...l }));
    nuevos.forEach((n) => {
      if (!indice.has(n.lead_id)) {
        fusionado.push({ ...n });
        resumen.agregados.push(n.lead_id);
        return;
      }
      const previa = fusionado[indice.get(n.lead_id)];
      if (claveTelefono(previa.telefono) !== claveTelefono(n.telefono)) {
        resumen.conflictos.push(n.lead_id);
        return;
      }
      const campos = SEGUIMIENTO.filter((c) => !igual(previa[c], n[c]));
      if (campos.length) {
        campos.forEach((c) => (previa[c] = n[c]));
        resumen.actualizados[n.lead_id] = campos;
      } else resumen.sinCambio += 1;
    });
    return { fusionado, resumen };
  }

  function procesarIngesta(filasCrudas, actual, origen) {
    const { texto, mapeo, ignoradas } = normalizarColumnas(filasCrudas);
    const { validos, rechazados, avisos } = validarFilas(texto);
    const { fusionado, resumen } = fusionar(actual, validos);
    resumen.conflictos.forEach((c) => rechazados.push({ lead_id: c, motivo: "lead_id ya existe con otro teléfono" }));
    return {
      origen,
      filasLeidas: filasCrudas.length,
      mapeo: Object.fromEntries(Object.entries(mapeo).filter(([k, v]) => k !== claveColumna(v))),
      ignoradas,
      validos: validos.length,
      rechazados,
      avisos,
      agregados: resumen.agregados,
      actualizados: resumen.actualizados,
      sinCambio: resumen.sinCambio,
      conflictos: resumen.conflictos,
      fusionado,
      hayCambios: resumen.agregados.length + Object.keys(resumen.actualizados).length > 0,
    };
  }

  function textoInforme(i) {
    const lineas = [
      `Origen: ${i.origen}`,
      `Filas leídas: ${i.filasLeidas}`,
      `Válidas: ${i.validos} | Rechazadas: ${i.rechazados.length} | Avisos: ${i.avisos.length}`,
      `Nuevas: ${i.agregados.length} | Actualizadas: ${Object.keys(i.actualizados).length} | Sin cambio: ${i.sinCambio} | Conflictos: ${i.conflictos.length}`,
    ];
    if (i.ignoradas.length) lineas.push("Columnas ignoradas: " + i.ignoradas.join(", "));
    i.avisos.slice(0, 8).forEach(([lead, m]) => lineas.push(`  Aviso ${lead}: ${m}`));
    if (i.avisos.length > 8) lineas.push(`  ... y ${i.avisos.length - 8} avisos más`);
    return lineas.join("\n");
  }

