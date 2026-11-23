/*
 * Motor de recontacto en JavaScript: la misma logica que la version en Python, para que la herramienta
 * abra en el navegador sin instalar nada.
 *
 * Modulos (en este orden): fechas, datos, reglas de trato, probabilidad y asignacion, mensajes,
 * simulacion y estadistica, ingesta (leer, validar y fusionar).
 *
 * Todo son funciones puras. Las fechas son milisegundos UTC "ingenuos": la hora que se ve es la hora
 * local de los datos, sin zonas horarias.
 *
 * Donde cambiar cosas
 *   - Reglas por defecto: REGLAS.
 *   - Textos de los mensajes: plantilla().
 *   - Sinonimos de columnas y reglas de validacion: SINONIMOS y validarFilas().
 * La comparacion con Python esta en web/prueba_motor.js (node web/prueba_motor.js).
 */
(function (raiz, fabrica) {
  const Motor = fabrica();
  if (typeof module === "object" && module.exports) module.exports = Motor;
  else raiz.Motor = Motor;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const MARCA = "Clivi";
  const DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"];
  const RESULTADOS = ["no_contesta", "sin_contactar", "en_seguimiento", "no_interesado", "venta"];
  const HORA = 3600000;
  const DIA = 86400000;
  const REGLAS = { horaInicio: 9, horaFin: 20, dias: [0, 1, 2, 3, 4, 5], maxIntentos: 3, horasEntre: 24, ventanaDias: 21, capacidad: 15, horizonteDias: 3 };
  const MOTIVOS = {
    baja: "Pidió no recibir más mensajes",
    duplicado: "Registro repetido de otro lead con el mismo teléfono",
    cliente: "Ya es cliente",
    rechazo: "Dijo que no le interesa",
    en_seguimiento: "Ya está en conversación con un asesor",
    fuera_ventana: "Fuera de la ventana de recuperación",
    max_intentos: "Alcanzó el máximo de intentos",
  };

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

  // ------------------------------------------------------------------ datos
  const claveTelefono = (v) => String(v === null || v === undefined ? "" : v).replace(/\D/g, "").slice(-10);

  function desdeFilas(columnas, filas) {
    const i = Object.fromEntries(columnas.map((c, k) => [c, k]));
    return filas.map((f) => ({
      lead_id: f[i.lead_id],
      fecha: parseFecha(f[i.fecha_registro]),
      canal: f[i.canal],
      anuncio: f[i.anuncio],
      entidad: f[i.estado],
      edad: f[i.edad],
      objetivo: f[i.objetivo],
      plan: f[i.plan_de_interes],
      telefono: f[i.telefono],
      asesor: f[i.asesor],
      contacto: f[i.primer_contacto] ? parseFecha(f[i.primer_contacto]) : null,
      resultado: f[i.resultado],
      monto: f[i.monto_venta],
    }));
  }

  const comparar = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

  function enriquecer(leads, bajas) {
    const orden = leads.map((l) => ({ ...l })).sort((a, b) => a.fecha - b.fecha || comparar(a.lead_id, b.lead_id));
    const claves = bajas instanceof Set ? bajas : new Set((bajas || []).map(claveTelefono));
    const grupos = new Map();
    orden.forEach((l) => {
      l.clave = claveTelefono(l.telefono);
      if (!grupos.has(l.clave)) grupos.set(l.clave, { cliente: false, rechazo: false, seguimiento: false, baja: false, intentos: 0, ultimo: null });
      const g = grupos.get(l.clave);
      g.cliente = g.cliente || l.resultado === "venta";
      g.rechazo = g.rechazo || l.resultado === "no_interesado";
      g.seguimiento = g.seguimiento || l.resultado === "en_seguimiento";
      g.baja = g.baja || claves.has(l.clave) || l.baja === true;
      if (l.contacto !== null && l.contacto !== undefined) {
        g.intentos += 1;
        g.ultimo = g.ultimo === null ? l.contacto : Math.max(g.ultimo, l.contacto);
      }
    });
    const vistos = new Set();
    orden.forEach((l) => {
      const g = grupos.get(l.clave);
      l.esDuplicado = vistos.has(l.clave);
      vistos.add(l.clave);
      l.cliente = g.cliente;
      l.rechazo = g.rechazo;
      l.seguimiento = g.seguimiento;
      l.enBaja = g.baja;
      l.intentosPrevios = g.intentos;
      l.ultimoContacto = g.ultimo;
    });
    return orden;
  }

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

  // ------------------------------------------------------------------ respuestas
  const ACCIONES_RESPUESTA = {
    seguridad: ["Pasar de inmediato a un asesor", "", false, true, "Gracias por escribir. Si es una emergencia médica, llama al 911. Un asesor te contactará en cuanto pueda."],
    baja: ["Registrar la baja y confirmar", "", true, false, "Entendido, no te volveremos a escribir. Gracias por tu tiempo."],
    no_interesado: ["Marcar como no interesado y agradecer", "no_interesado", false, false, "Gracias por avisarnos. Si más adelante cambias de opinión, aquí estaremos."],
    agenda: ["Pasar a seguimiento y agendar la hora", "en_seguimiento", false, false, ""],
    interes: ["Pasar a seguimiento: la conversación sigue con el asesor", "en_seguimiento", false, false, ""],
    posponer: ["Reprogramar el siguiente intento", "", false, false, ""],
    pregunta: ["Pasar a un asesor: la herramienta no responde preguntas", "", false, true, ""],
    ambigua: ["Pasar a un asesor para revisar", "", false, true, ""],
  };
  const PR = {
    seguridad: /\b(emergencia|urgencia medica|me siento mal|dolor fuerte|ayuda urgente|no me siento bien|suicid\w*|mareo\w*|desmay\w*)\b/,
    baja: /^(no|n o|stop|baja|cancelar|cancela)$|\b(no (me )?(escriban|escribas|escriba|contacten|contactes|manden|molesten)|dejen de|deja de|no quiero (mas )?(mensajes|que me escriban|que me contacten)|ya no (me )?(escriban|escribas|contacten)|quiten mi numero|borren mi numero|no mas mensajes)\b/,
    noInteresado: /\b(no me interesa|ya no me interesa|no estoy interesad\w*|no gracias|ya no necesito|no lo necesito|no por ahora gracias)\b/,
    posponer: /\b(ahorita no|ahora no|mas tarde|otro dia|despues|luego|en otro momento|ahora no puedo|no puedo ahora|estoy ocupad\w*)\b/,
    negacionTiempo: /\b(no puedo|no podre|no voy a poder|no puedes|ahorita no|ahora no)\b/,
    interes: /^(si|sii+|claro|ok|okay|dale|adelante|por favor|va|sale|perfecto|de acuerdo)\b|\b(me interesa|quiero (mas )?informacion|llamame|llamenme|marcame|marquenme|escribeme|mandame (la )?informacion|si quiero|me gustaria)\b/,
    pregunta: /\?|\b(cuanto|cuanta|cuales|cual|que incluye|precio|costo|cuesta|como funciona|tienen|incluye|medicamento|tratamiento|receta|puedo|donde)\b/,
    preguntaFuerte: /\?|\b(cuanto|cuanta|precio|costo|cuesta|incluye|medicamento|tratamiento|receta)\b/,
    horaExplicita: /\b(?:a las|a la|como a las|tipo|a eso de las|despues de las)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|h|hrs|horas)?\b/,
    horaSufijo: /\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|h|hrs|horas)\b/,
    horaDosPuntos: /\b(\d{1,2}):(\d{2})\b/,
    franja: /\b(en la manana|por la manana|de manana|en la tarde|por la tarde|en la noche|por la noche)\b/,
  };
  const DIAS_RESP = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"];
  const NOMBRES_FRANJA = { manana: "mañana", tarde: "tarde", noche: "noche" };

  function limpioRespuesta(t) {
    return String(t === null || t === undefined ? "" : t)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/\b([ap])\.\s?m\.?/g, "$1m")
      .replace(/[^a-z0-9_:?¿!¡ ]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }
  function horaYFranja(limpio) {
    const franja = PR.franja.exec(limpio);
    let hora = -1;
    let sufijo = null;
    for (const [patron, conSufijo] of [[PR.horaExplicita, true], [PR.horaSufijo, true], [PR.horaDosPuntos, false]]) {
      const m = patron.exec(limpio);
      if (m) {
        hora = parseInt(m[1], 10);
        sufijo = conSufijo ? m[3] || null : null;
        break;
      }
    }
    if (!(hora >= 0 && hora <= 23)) hora = -1;
    if (hora >= 0) {
      if (sufijo === "pm" && hora < 12) hora += 12;
      else if (sufijo === null && franja && /(tarde|noche)$/.test(franja[1]) && hora < 12) hora += 12;
      else if (sufijo === null && !franja && hora >= 1 && hora <= 7) hora += 12;
    }
    const nombre = franja ? NOMBRES_FRANJA[franja[1].split(" ").pop()] : "";
    return [hora, nombre];
  }
  function diaDeRespuesta(limpio) {
    if (/\bpasado manana\b/.test(limpio)) return "pasado mañana";
    if (/\bmanana\b/.test(limpio) && !/(en la|por la|de) manana/.test(limpio)) return "mañana";
    if (/\bhoy\b/.test(limpio)) return "hoy";
    for (const nombre of DIAS_RESP) if (new RegExp("\\b" + nombre + "\\b").test(limpio)) return { miercoles: "miércoles", sabado: "sábado" }[nombre] || nombre;
    return "";
  }
  function armarRespuesta(intencion, confianza, motivo, dia = "", hora = -1, franja = "", humanoExtra = false) {
    const [accion, estado, baja, humano0, respuesta0] = ACCIONES_RESPUESTA[intencion];
    const humano = humano0 || humanoExtra;
    let respuesta = respuesta0;
    if (intencion === "agenda") {
      const cuando = [dia, hora >= 0 ? `a las ${hora}:00` : "", franja && hora < 0 ? `por la ${franja}` : ""].filter(Boolean).join(" ");
      respuesta = humano ? "" : cuando ? `Perfecto, quedamos ${cuando}. Gracias por contestar.` : "Perfecto, gracias por contestar.";
    }
    return { intencion, accion, estadoNuevo: estado, baja, requiereHumano: humano, respuestaSugerida: respuesta, confianza, dia, hora, franja, motivo };
  }
  function clasificarRespuesta(texto) {
    const limpio = limpioRespuesta(texto);
    if (!limpio) return armarRespuesta("ambigua", "baja", "Respuesta vacía");
    if (PR.seguridad.test(limpio)) return armarRespuesta("seguridad", "alta", "Menciona malestar o una emergencia");
    if (PR.baja.test(limpio)) return armarRespuesta("baja", "alta", "Pide no recibir más mensajes");
    if (PR.noInteresado.test(limpio)) return armarRespuesta("no_interesado", "alta", "Dice que no le interesa");
    const [hora, franja] = horaYFranja(limpio);
    const dia = diaDeRespuesta(limpio);
    const pregunta = PR.pregunta.test(limpio);
    if (PR.negacionTiempo.test(limpio) && hora < 0) return armarRespuesta("posponer", "media", "Dice que no puede en este momento", dia, hora, franja);
    if (hora >= 0 || dia || franja) {
      const extra = PR.preguntaFuerte.test(limpio);
      return armarRespuesta("agenda", hora >= 0 || dia ? "alta" : "media", "Propone un día u hora" + (extra ? " y además hace una pregunta" : ""), dia, hora, franja, extra);
    }
    if (PR.posponer.test(limpio)) return armarRespuesta("posponer", "media", "Pide hablar en otro momento");
    if (PR.interes.test(limpio)) return armarRespuesta("interes", "alta", "Responde que sí o pide información", "", -1, "", pregunta);
    if (pregunta) return armarRespuesta("pregunta", "media", "Hace una pregunta");
    return armarRespuesta("ambigua", "baja", "No se entiende con claridad");
  }

  // ------------------------------------------------------------------ estadistica
  function erfc(x) {
    const z = Math.abs(x);
    const t = 1 / (1 + 0.5 * z);
    const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    return x >= 0 ? r : 2 - r;
  }
  const cdfNormal = (x) => 0.5 * erfc(-x / Math.SQRT2);
  function ppfNormal(p) {
    const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
    const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
    const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
    const bajo = 0.02425;
    if (p < bajo) {
      const q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (p > 1 - bajo) {
      const q = Math.sqrt(-2 * Math.log(1 - p));
      return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    const q = p - 0.5;
    const r = q * q;
    return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  function tamanoMuestra(p0, delta, potencia = 0.8, alfa = 0.05) {
    const p1 = p0 + delta;
    if (!(p0 > 0 && p0 < 1 && p1 > 0 && p1 < 1) || delta === 0) throw new Error("p0 y p0 + delta deben estar entre 0 y 1 y delta no puede ser 0");
    const media = (p0 + p1) / 2;
    const za = ppfNormal(1 - alfa / 2);
    const zb = ppfNormal(potencia);
    const num = (za * Math.sqrt(2 * media * (1 - media)) + zb * Math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2;
    return Math.ceil(num / delta ** 2);
  }
  function potenciaAnalitica(p0, delta, n, alfa = 0.05) {
    const p1 = p0 + delta;
    const media = (p0 + p1) / 2;
    const za = ppfNormal(1 - alfa / 2);
    return cdfNormal((Math.abs(delta) * Math.sqrt(n) - za * Math.sqrt(2 * media * (1 - media))) / Math.sqrt(p0 * (1 - p0) + p1 * (1 - p1)));
  }
  function percentil(valores, q) {
    const orden = valores.slice().sort((a, b) => a - b);
    const pos = (q / 100) * (orden.length - 1);
    const i = Math.floor(pos);
    return orden[i] + (orden[Math.min(i + 1, orden.length - 1)] - orden[i]) * (pos - i);
  }
  function generador(semilla) {
    let a = semilla >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

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

  return {
    DIAS, REGLAS, MOTIVOS, RESULTADOS, HORA, DIA,
    parseFecha, fmt, fmtDia, diaSemana, horaDe, claveTelefono,
    desdeFilas, enriquecer, motivoExclusion, horariosValidos, primerHorarioPermitido,
    franjaHora, rangoEspera, calcularAsignacion, generarLista, plantilla, validarMensaje, validarFidelidad, franjaTexto,
    BIBLIOTECA, ESTRATEGIAS, etapaDe, elegirVariante, crc32, clasificarRespuesta, limpioRespuesta,
    cdfNormal, ppfNormal, tamanoMuestra, potenciaAnalitica, percentil, generador,
    prepararSimulacion, simular, resumenSimulacion,
    normalizarColumnas, validarFilas, fusionar, procesarIngesta, textoInforme,
  };
});
