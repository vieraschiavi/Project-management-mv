# © 2026 Martín Viera. Todos los derechos reservados.
"""Capa genérica de IA multi-proveedor (Claude / ChatGPT / Gemini / Grok / Copilot).

Mismo principio que el resto del producto: la IA es SIEMPRE opcional y aditiva.
Si no hay una clave configurada, o el proveedor falla, `completar()` devuelve
None y el que llama usa su texto de reglas/preestablecido. Nunca se ofrece un
proveedor sin su clave.

Qué modelo se usa lo decide `mvpm/modelos.py`: primero lo que el cliente eligió
en la pantalla de Configuración, y si no eligió nada, la variable de entorno del
proveedor. Antes el modelo de Claude estaba fijo en este archivo y el de los
demás sólo se podía cambiar exportando una variable antes de abrir el programa
— o sea que desde una instalación de escritorio no se podía cambiar, que es
justo donde más importa (el modelo es la palanca principal del gasto en tokens).

`advisor.py` tiene su propia copia especializada de esto por razones históricas;
los módulos nuevos (governance, organigrama) usan esta capa genérica.
"""

import os

from . import modelos

# Se derivan de modelos.PROVEEDORES para que no haya dos listas de proveedores
# que se puedan desincronizar: agregar uno allá lo agrega acá.
_ENV_KEYS = {nombre: cfg["env_clave"] for nombre, cfg in modelos.PROVEEDORES.items()}

ETIQUETAS = {
    "claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini",
    "grok": "Grok", "copilot": "Copilot",
}

# Único proveedor con modelo por defecto: el SDK de Anthropic es dependencia
# declarada del producto (requirements.txt) y este ID es el que se venía usando,
# así que quien no elige nada sigue teniendo exactamente el comportamiento de
# antes. Para el resto, sin modelo elegido no hay pedido: adivinar un ID ajeno
# es un error 404 con la culpa puesta en el lugar equivocado.
_MODELO_POR_DEFECTO = {"claude": "claude-opus-4-8"}

# Proveedores que hablan el dialecto de OpenAI y sólo cambian de URL base.
_BASE_URL_OPENAI = {
    "chatgpt": None,  # el que trae el SDK
    "grok": "https://api.x.ai/v1",
    "copilot": "https://models.github.ai/inference",
}


def _modelo(proveedor: str) -> str | None:
    return modelos.modelo_actual(proveedor) or _MODELO_POR_DEFECTO.get(proveedor)


def proveedores_disponibles() -> list[str]:
    """Sólo los proveedores usables ya mismo: con clave configurada y con un
    modelo resuelto (elegido en Configuración, por variable de entorno, o por
    defecto)."""
    return [nombre for nombre in modelos.PROVEEDORES
            if os.environ.get(_ENV_KEYS[nombre]) and _modelo(nombre)]


def _claude(system: str, user: str, max_tokens: int) -> str | None:
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=_modelo("claude"),
            max_tokens=max_tokens,
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None


def _compatible_openai(proveedor: str, system: str, user: str,
                       max_tokens: int) -> str | None:
    """ChatGPT, Grok y Copilot (GitHub Models) exponen la misma API de chat;
    lo único que cambia es la URL base y de qué variable sale la clave."""
    model = _modelo(proveedor)
    if not model:
        return None
    try:
        import openai  # type: ignore
    except ImportError:
        return None
    try:
        client = openai.OpenAI(
            api_key=os.environ.get(_ENV_KEYS[proveedor]),
            base_url=_BASE_URL_OPENAI[proveedor],
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content if resp.choices else None
    except Exception:
        return None


def _gemini(system: str, user: str, max_tokens: int) -> str | None:
    model = _modelo("gemini")
    if not model:
        return None
    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        return None
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        client = genai.GenerativeModel(model)
        resp = client.generate_content(f"{system}\n\n{user}")
        return resp.text if getattr(resp, "text", None) else None
    except Exception:
        return None


_FUNCS = {
    "claude": _claude,
    "gemini": _gemini,
    "chatgpt": lambda s, u, m: _compatible_openai("chatgpt", s, u, m),
    "grok": lambda s, u, m: _compatible_openai("grok", s, u, m),
    "copilot": lambda s, u, m: _compatible_openai("copilot", s, u, m),
}


def completar(system: str, user: str, proveedor: str | None, max_tokens: int = 400) -> str | None:
    """Devuelve el texto del proveedor, o None si no hay clave / falla / no se
    pidió proveedor. Nunca levanta excepción — degrada en silencio."""
    if not proveedor or proveedor not in _FUNCS:
        return None
    if not os.environ.get(_ENV_KEYS[proveedor]):
        return None
    return _FUNCS[proveedor](system, user, max_tokens)
