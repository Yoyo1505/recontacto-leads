  // ------------------------------------------------------------------ limites
  function vistaLimites() {
    const cont = $("#sub-limites");
    if (cont.dataset.listo) return;
    cont.dataset.listo = "1";
    const lista = (t, xs, clase) => `<div class="tarjeta ${clase || ""}"><h3>${t}</h3><ul>${xs.map((x) => `<li>${x}</li>`).join("")}</ul></div>`;
    cont.innerHTML = `<div class="pila">
      <div class="dos">
        ${lista("Lo que no se puede afirmar", ["Que un mensaje convenza más que otro: hay un solo intento de contacto por lead y no se registró el mensaje usado.", "Que el horario, por sí mismo, haga contestar más: en los datos, la hora del contacto y la rapidez del contacto van juntas.", "Que un asesor sea mejor o peor: las diferencias entre asesores caben dentro del azar.", "Que la ventaja del modelo sea detectable en un solo día: la simulación muestra un intervalo que incluye el cero."], "no")}
        ${lista("Supuestos que no son datos", ["Ventana de recuperación de 21 días, máximo de 3 intentos, 24 h entre intentos y 15 contactos por hora.", "Horario de 9:00 a 20:00 de lunes a sábado.", "La parte causal de la ventaja del horario (alpha) se explora de 0 a 1; no se conoce.", "La conversión a venta de quien contesta es la histórica por canal, suavizada hacia el promedio global."])}
      </div>
      ${lista("Datos que harían falta", ["Segundos intentos y su resultado.", "Texto del mensaje enviado y hora de apertura.", "Motivo cuando alguien dice que no le interesa.", "Origen del lead cuando llega por un agente de inteligencia artificial."])}
      ${lista("Qué hace esta versión web y qué no", ["Hace: la lista del día con reglas ajustables, la evidencia, la simulación, la calculadora de prueba A/B y la carga de datos (CSV, JSON, Excel).", "No hace: enviar mensajes, leer respuestas ni reentrenar el modelo con datos nuevos.", "No lee Parquet, bases de datos ni la nube: eso lo hace la versión completa (Python, con archivos .bat)."])}
    </div>`;
  }

