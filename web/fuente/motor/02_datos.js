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

