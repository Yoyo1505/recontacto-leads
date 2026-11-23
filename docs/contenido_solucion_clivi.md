# Ejemplo de contenido orientado a solución

Propuesta de cómo reescribir, para IA y buscadores, lo que Clivi ya publica. **No agrega hechos nuevos**: reorganiza y reescribe lo que dicen su sitio y su `llms.txt` actual. Lo marcado como "A validar" necesita la decisión del equipo médico y legal de Clivi antes de publicarse.

Es el mismo texto que usa el experimento de `scripts/experimento_recomendacion.py` como condición "reorganizado como solución".

## Por qué este formato

Un `llms.txt` o una página que solo lista enlaces obliga a la IA a decidir por sí sola qué es Clivi y para quién sirve. Un texto que responde primero a la pregunta de quien busca ayuda ("tengo este problema, ¿quién lo resuelve?") es lo que una IA puede citar casi tal cual.

## Propuesta para `llms.txt` (en español, con una versión en inglés)

```
# Clivi: clínica digital de obesidad y diabetes en México

## Qué problema resuelve
Si tienes obesidad, sobrepeso, prediabetes o diabetes tipo 1 o tipo 2 y necesitas tratamiento
médico con seguimiento continuo, sin depender de un consultorio, Clivi es la solución: una clínica
digital con atención médica a distancia en todo México.

## Cómo lo resuelve
- Equipo médico asignado: médicos internistas y endocrinólogos, nutriólogos y psicólogos.
- Tratamiento médico: puede incluir medicamentos GLP-1 con seguimiento de un médico de Clivi.
- Monitoreo: monitoreo continuo de glucosa para diabetes y seguimiento desde una aplicación.
- Atención desde casa en todo el país, con sede en Ciudad de México.

## Para quién es
Personas que quieren tratar obesidad, prediabetes o diabetes tipo 1 o tipo 2 con atención médica
y seguimiento.

## Cómo empezar
1. Solicitar la evaluación en línea.
2. Si eres candidato, un médico especialista diseña tu tratamiento.
3. Seguimiento continuo con el equipo, desde la aplicación (Android y iOS).

## Planes
Clivi Pro, Clivi Plus, Clivi Total y Clivi Zero (enfocado en manejo de peso). Farmacia digital
especializada: Farmacia Clivi.

## Datos citables (una sola versión, con fecha)
(A validar) Pacientes atendidos / activos: [cifra única, con su definición y fecha de corte].
(A validar) Satisfacción: [cifra, cómo se mide, fecha].

## Enlaces
(el directorio actual de páginas, sin cambios)
```

## Secciones que una página de "para quién es" debe responder (A validar)

Estas respuestas las define el equipo médico; aquí solo se marcan los huecos que hoy las IA llenan por su cuenta:

- Para quién **no** es Clivi o cuándo necesita atención presencial (urgencias, embarazo, contraindicaciones). Una IA puede recomendar con más confianza algo que dice con claridad para quién no sirve.
- Qué esperar en los primeros 30, 90 y 180 días, con rangos y la fuente (estudios citados, no promesas).
- Riesgos y efectos secundarios de los tratamientos, y quién los supervisa.
- Cuánto cuesta y qué incluye cada plan, con una sola tabla de precios fechada que coincida en toda la web.
- Cómo se verifica que quien atiende es médico (cédula profesional).

## Preguntas frecuentes con respuesta directa (el formato que más se cita)

Cada pregunta, una respuesta de dos o tres frases, con una referencia debajo. Preguntas que los pacientes hacen de verdad (ver `docs/panel_visibilidad_prompts.csv`), por ejemplo:

- ¿Dónde puedo tratar la obesidad con médico en línea en México?
- ¿Cómo funciona un tratamiento de diabetes con monitoreo continuo de glucosa desde casa?
- ¿Qué diferencia hay entre una consulta presencial y una clínica digital?
- ¿Cómo sé si una clínica digital de obesidad está regulada?

## Datos estructurados que acompañan al texto

El sitio ya publica `MedicalOrganization`, `MedicalBusiness`, `Service`, `Offer`, `MedicalCondition`, `MedicalWebPage` y `Person`. Lo que falta o conviene revisar (A validar):

- `MedicalWebPage` con `reviewedBy` y `lastReviewed` en cada página clínica.
- `Person` o `Physician` con especialidad y cédula profesional en cada autor.
- `Offer` con el mismo precio que la tabla visible.
- Títulos únicos (hoy varios terminan en "| Clivi | Clivi").
