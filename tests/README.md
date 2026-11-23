# `tests/` · pruebas

```
python -m pytest                      todo (unos 4 minutos)
python -m pytest tests/test_ingesta.py
node web/prueba_motor.js              JavaScript contra Python
```

| Archivo | Qué cubre |
|---|---|
| `test_data.py` | Limpieza de datos |
| `test_policy.py`, `test_reglas.py` | Reglas de trato y reglas ajustables |
| `test_model_pipeline.py` | Modelo, evaluación sin mezclar entrenamiento y prueba, lista y horarios |
| `test_mensajes.py` | Plantillas, validadores, variantes y respaldo del modelo de lenguaje |
| `test_respuestas.py` | Lectura de respuestas y sus acciones |
| `test_ingesta.py` | Todos los formatos, bases SQL, URLs, secretos, validación, fusión, versiones y bajas |
| `test_simulacion.py` | Monte Carlo, potencia, intervalos y control |
| `test_visibilidad.py` | Panel de visibilidad en IA |
| `test_app.py` | Cada sección de Dash, cada callback y el flujo completo de datos |
| `test_web.py` | JavaScript contra Python, las cinco páginas armadas y archivos ensamblados al día |
| `conftest.py` | `entorno`: aísla las rutas de datos en una carpeta temporal |
