"""Clientes de modelos de lenguaje para redactar mensajes.

Todos tienen la misma interfaz: `generar(sistema, usuario)` devuelve el texto o None si algo falla,
y `disponible` dice si se puede usar. El texto que devuelvan siempre pasa por el validador de
`mensajes.py`; si no lo pasa, se usa la plantilla.

    ClienteAnthropic   API de Anthropic (variable ANTHROPIC_API_KEY)
    ClienteOllama      modelo local con Ollama, sin enviar nada fuera de la computadora

Donde cambiar cosas
    - Modelo por defecto: config.MODELO_LLM (Anthropic) o el parametro `modelo` (Ollama).
    - Temperatura y tiempo de espera: parametros de cada cliente.
"""

import json
import os
import urllib.error
import urllib.request

from . import config

URL_API = "https://api.anthropic.com/v1/messages"
URL_OLLAMA = "http://127.0.0.1:11434"


class ClienteAnthropic:
    def __init__(self, api_key=None, modelo=None, timeout=20):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.modelo = modelo or config.MODELO_LLM
        self.timeout = timeout

    @property
    def disponible(self):
        return bool(self.api_key)

    def generar(self, sistema, usuario):
        if not self.disponible:
            return None
        cuerpo = json.dumps(
            {
                "model": self.modelo,
                "max_tokens": 300,
                "system": sistema,
                "messages": [{"role": "user", "content": usuario}],
            }
        ).encode("utf-8")
        solicitud = urllib.request.Request(
            URL_API,
            data=cuerpo,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(solicitud, timeout=self.timeout) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
            return datos["content"][0]["text"]
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
            return None


class ClienteOllama:
    def __init__(self, modelo="llama3.1:8b", url=URL_OLLAMA, timeout=180, temperatura=0.4, semilla=None):
        self.modelo = modelo
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.temperatura = temperatura
        self.semilla = semilla

    @property
    def disponible(self):
        try:
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=3) as respuesta:
                modelos = json.loads(respuesta.read().decode("utf-8")).get("models", [])
            return any(m.get("name") == self.modelo or m.get("model") == self.modelo for m in modelos)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            return False

    def generar(self, sistema, usuario):
        cuerpo = json.dumps(
            {
                "model": self.modelo,
                "stream": False,
                "options": {"temperature": self.temperatura, **({"seed": self.semilla} if self.semilla is not None else {})},
                "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
            }
        ).encode("utf-8")
        solicitud = urllib.request.Request(
            f"{self.url}/api/chat", data=cuerpo, headers={"content-type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(solicitud, timeout=self.timeout) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
            return datos["message"]["content"]
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError):
            return None
