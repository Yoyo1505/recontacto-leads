/*
 * Edicion: este archivo y los demas de web/fuente/motor/ son las secciones; web/motor.js se genera con
 * python scripts/ensamblar_web.py y no se edita a mano.
 *
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

