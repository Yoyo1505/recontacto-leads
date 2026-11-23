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

