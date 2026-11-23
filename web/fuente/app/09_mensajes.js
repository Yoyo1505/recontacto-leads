  // ------------------------------------------------------------------ mensajes
  const NOMBRES_ETAPA = { primer_contacto: "Primer contacto", retoma: "Retomar", cierre: "Cierre" };
  const A_QUIEN = { primer_contacto: "A quien nunca recibió un contacto", retoma: "A quien no contestó el primer intento", cierre: "Al último intento permitido" };

  function vistaMensajes() {
    const cont = $("#sub-mensajes");
    const L = E.lista;
    const conteo = {};
    L.filas.filter((f) => f.etapa).forEach((f) => {
      conteo[f.etapa] = conteo[f.etapa] || {};
      conteo[f.etapa][f.variante] = (conteo[f.etapa][f.variante] || 0) + 1;
    });
    const p0 = EVID.tasa_contesta;
    const filas = [];
    for (const etapa of Object.keys(M.BIBLIOTECA)) {
      for (const letra of Object.keys(M.BIBLIOTECA[etapa]).sort()) {
        const contexto = { nunca: etapa === "primer_contacto", ultimo: etapa === "cierre", variante: letra, franja: "hoy por la tarde", asesor: "Asesor B" };
        const texto = M.plantilla(contexto);
        const v = M.validarMensaje(texto, contexto);
        filas.push(`<tr><td>${NOMBRES_ETAPA[etapa]}<div class="nota">${A_QUIEN[etapa]}</div></td><td><b>${letra}</b><div class="nota">${esc(M.ESTRATEGIAS[etapa][letra])}</div></td><td>${esc(texto)}</td><td class="num">${(conteo[etapa] || {})[letra] || 0}</td><td><span class="insignia ${v.valido ? "ok" : "mal"}">${v.valido ? "Válido" : "Revisar"}</span></td></tr>`);
      }
    }
    cont.innerHTML = `
      <div class="pila">
        <div class="tarjeta">
          <h3>Qué mensaje recibe cada persona</h3>
          ${ayuda("La conversación se recupera en hasta tres pasos, y cada paso tiene varias redacciones con una estrategia distinta. A cada persona le toca siempre la misma variante (se asigna por su número de lead), para poder comparar después cuál recupera más conversaciones.")}
          <label class="barra" style="margin:0 0 10px"><input type="checkbox" id="m-comparar" ${E.comparar ? "checked" : ""}> Comparar variantes (si se desmarca, todos reciben la variante A)</label>
          <div class="scroll"><table><thead><tr><th>Situación</th><th>Variante</th><th>Mensaje de ejemplo</th><th>Personas hoy</th><th>Reglas</th></tr></thead><tbody>${filas.join("")}</tbody></table></div>
        </div>
        <div class="dos">
          <div class="tarjeta">
            <h3>Reglas que todo mensaje cumple</h3>
            <ul>
              <li>No menciona la condición de salud, no promete resultados, no mete urgencia ni enlaces.</li>
              <li>Menciona la marca y trae la forma de pedir que no se le escriba más.</li>
              <li>Hasta 480 caracteres, en tono de tú, y siempre habla de la solicitud de información.</li>
              <li>Cambia según el canal (si llegó por un asistente de IA, lo dice) y si pasaron varios días desde la solicitud.</li>
              <li>El tercer mensaje avisa que no se insistirá más.</li>
            </ul>
          </div>
          <div class="tarjeta">
            <h3>Cómo se sabrá cuál variante recupera más</h3>
            ${ayuda("Hoy los datos no dicen qué mensaje se envió, así que esto es una hipótesis por probar, no un resultado.")}
            <ul>
              <li>Se guarda la variante enviada junto con el resultado (columna <code>variante</code> al subir datos).</li>
              <li>Se compara el porcentaje que contesta de cada variante contra la A, con intervalos y una prueba de dos proporciones.</li>
              <li>Para detectar una diferencia de 5 puntos entre dos variantes hacen falta unas <b>${num(M.tamanoMuestra(p0, 0.05))}</b> personas por variante; para 8 puntos, unas <b>${num(M.tamanoMuestra(p0, 0.08))}</b>.</li>
            </ul>
          </div>
        </div>
      </div>`;
    $("#m-comparar").addEventListener("change", (e) => { E.comparar = e.target.checked; recalcular(); vistaMensajes(); });
  }

