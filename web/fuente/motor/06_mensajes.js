  // ------------------------------------------------------------------ mensajes
  const BAJA = "Si prefieres que no te escribamos, responde NO.";
  function franjaTexto(ms, ahora) {
    const parte = horaDe(ms) < 12 ? "por la mañana" : "por la tarde";
    return fmtDia(ms) === fmtDia(ahora) ? `hoy ${parte}` : `el ${DIAS[diaSemana(ms)]} ${parte}`;
  }
  const BIBLIOTECA = {
    primer_contacto: {
      A: "{recibimos} y con gusto te la compartimos. ¿Te parece bien si te llamamos {franja}?",
      B: "{recibimos}. ¿Prefieres que te llamemos o que te escribamos por aquí? Dime qué te acomoda mejor.",
      C: "{recibimos}. En una llamada corta te explico cómo funciona y resuelvo tus dudas. ¿Cuándo te viene bien?",
    },
    retoma: {
      A: "Intenté comunicarme contigo por tu solicitud de información y no logramos hablar. Cuando tengas un momento, dime si prefieres que te llame o seguir por mensaje.",
      B: "Te busqué por tu solicitud de información y no pudimos hablar. ¿Te escribo con la información por aquí, o prefieres que te llame {franja}?",
      C: "Sigo con tu solicitud de información a la mano. ¿Quieres que la retomemos? Con un «sí» te busco en el horario que prefieras.",
    },
    cierre: {
      A: "Este es mi último mensaje sobre tu solicitud de información, para no insistirte. Si más adelante quieres retomarla, aquí estaremos.",
      B: "No quiero molestarte, así que este es mi último mensaje. Tu solicitud queda guardada: cuando quieras retomarla, solo respóndeme aquí.",
    },
  };
  const ESTRATEGIAS = {
    primer_contacto: { A: "propone un horario concreto", B: "deja elegir el canal", C: "explica el siguiente paso y pregunta cuándo" },
    retoma: { A: "da el control sobre cómo seguir", B: "ofrece las dos opciones con horario", C: "pide un sí sencillo" },
    cierre: { A: "libera la presión", B: "deja la solicitud guardada" },
  };
  const etapaDe = (c) => (c.nunca ? "primer_contacto" : c.ultimo ? "cierre" : "retoma");

  const TABLA_CRC = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(texto) {
    let c = 0xffffffff;
    for (const byte of new TextEncoder().encode(texto)) c = TABLA_CRC[(c ^ byte) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }
  function elegirVariante(leadId, etapa) {
    const letras = Object.keys(BIBLIOTECA[etapa]).sort();
    return letras[crc32(`${leadId}:${etapa}`) % letras.length];
  }

  function plantilla(c) {
    const etapa = etapaDe(c);
    let letra = c.variante || "A";
    if (!BIBLIOTECA[etapa][letra]) letra = "A";
    const recibimos = c.origenIa ? "Recibimos la solicitud de información que enviaste a través de un asistente de inteligencia artificial" : "Recibimos tu solicitud de información";
    const saludo = c.asesor ? `Hola, te escribe ${c.asesor} de ${MARCA}.` : `Hola, te escribimos de ${MARCA}.`;
    let cuerpo = BIBLIOTECA[etapa][letra].replace("{recibimos}", recibimos).replace("{franja}", c.franja || "hoy");
    if (etapa !== "cierre" && (c.dias || 0) >= 3) cuerpo = "Sé que pasaron unos días desde tu solicitud. " + cuerpo;
    return `${saludo} ${cuerpo} ${BAJA}`;
  }
  const PATRONES_PROHIBIDOS = {
    "menciona la condición de salud": /\b(diabet\w*|obesidad|sobrepeso|peso|kilos?|kg|glucosa|enfermedad\w*)\b/,
    "promete resultados": /\b(cura\w*|curar\w*|garantiz\w*|milagro\w*|sin esfuerzo|100%)\b/,
    "presiona con urgencia": /\b(ultima oportunidad|solo hoy|urgente|oferta|descuento|promocion)\b/,
    "incluye enlaces": /(https?:\/\/|www\.)/,
  };
  const sinAcentos = (t) => String(t).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const ESTRATEGIA_REQUERIDA = {
    "primer_contacto|A": [/llam/],
    "primer_contacto|B": [/llam/, /escrib/],
    "primer_contacto|C": [/llamada/, /cuando/],
    "retoma|A": [/llam/, /mensaje/],
    "retoma|B": [/llam/, /escrib/],
    "retoma|C": [/retom/],
    "cierre|A": [/ultimo/],
    "cierre|B": [/ultimo/],
  };
  const TRATO_DE_USTED = /\b(usted|ustedes|ayudarlo|ayudarla|apoyarlo|apoyarla|le escribimos|le podemos|le invito|necesita|desea|su solicitud)\b/;
  function validarFidelidad(texto, c) {
    const limpio = sinAcentos(texto);
    const problemas = [];
    if (!limpio.includes("solicitud")) problemas.push("no menciona la solicitud de información");
    const etapa = etapaDe(c);
    const letra = c.variante || "A";
    for (const p of ESTRATEGIA_REQUERIDA[`${etapa}|${letra}`] || []) {
      if (!p.test(limpio)) {
        problemas.push(`no sigue la estrategia de la variante ${letra} (${etapa})`);
        break;
      }
    }
    if (TRATO_DE_USTED.test(limpio)) problemas.push("mezcla el trato de usted con el de tú");
    return problemas;
  }
  function validarMensaje(texto, contexto) {
    const limpio = sinAcentos(texto);
    const problemas = [];
    if (!texto.trim()) problemas.push("está vacío");
    if (texto.length > 480) problemas.push("es demasiado largo");
    if (!limpio.includes("responde no")) problemas.push("no incluye la opción de baja");
    if (!limpio.includes(MARCA.toLowerCase())) problemas.push("no menciona la marca");
    for (const [nombre, patron] of Object.entries(PATRONES_PROHIBIDOS)) if (patron.test(limpio)) problemas.push(nombre);
    if (contexto) problemas.push(...validarFidelidad(texto, contexto));
    return { valido: problemas.length === 0, problemas };
  }

  function generarLista(leads, modelo, ahora, r, opciones) {
    const comparar = !opciones || opciones.compararVariantes !== false;
    const { elegibles, excluidos, slots } = calcularAsignacion(leads, modelo, ahora, r);
    const filas = elegibles.map((l, i) => {
      const asignado = l.horario !== null;
      return {
        prioridad: i + 1,
        lead_id: l.lead_id,
        canal: l.canal,
        accion: asignado ? "contactar" : "en_cola",
        intento: l.intento,
        nunca: l.nunca,
        dias: l.dias,
        horario: l.horario,
        prob: l.prob,
        probPromedio: l.probPromedio,
        motivo: asignado ? explicar(modelo, l) : "Sin horario libre en los próximos días: se reprograma sin descartarlo.",
        etapa: asignado ? etapaDe({ nunca: l.nunca, ultimo: l.intento >= r.maxIntentos }) : "",
        variante: asignado ? (comparar ? elegirVariante(l.lead_id, etapaDe({ nunca: l.nunca, ultimo: l.intento >= r.maxIntentos })) : "A") : "",
        mensaje: asignado
          ? plantilla({ nunca: l.nunca, ultimo: l.intento >= r.maxIntentos, franja: franjaTexto(l.horario, ahora), asesor: l.asesor || "", variante: comparar ? elegirVariante(l.lead_id, etapaDe({ nunca: l.nunca, ultimo: l.intento >= r.maxIntentos })) : "A", origenIa: String(l.canal).toLowerCase().includes("agente"), dias: Math.floor(l.dias) })
          : "",
        asesor: l.asesor || "",
        telefono: l.telefono,
        objetivo: l.objetivo,
        edad: l.edad,
        plan: l.plan,
      };
    });
    const conteo = {};
    excluidos.forEach((e) => (conteo[e.motivo] = (conteo[e.motivo] || 0) + 1));
    return { filas, excluidos, conteoExcluidos: conteo, slots, elegibles };
  }

