"""Capa genérica de IA multi-proveedor (Claude / ChatGPT / Gemini).

Mismo principio que el resto del producto: la IA es SIEMPRE opcional y aditiva.
Si no hay una clave configurada, o el proveedor falla, `completar()` devuelve
None y el que llama usa su texto de reglas/preestablecido. Nunca se ofrece un
proveedor sin su clave, y ChatGPT/Gemini exigen declarar el modelo por env var
(OPENAI_MODEL / GEMINI_MODEL) para no asumir un ID que puede quedar viejo.

`advisor.py` tiene su propia copia especializada de esto por razones históricas;
los módulos nuevos (governance, organigrama) usan esta capa genérica.
"""

import os

_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

ETIQUETAS = {"claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini"}


def proveedores_disponibles() -> list[str]:
    """Sólo los proveedores con clave configurada. ChatGPT/Gemini además
    necesitan su modelo declarado (OPENAI_MODEL / GEMINI_MODEL)."""
    disponibles = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        disponibles.append("claude")
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_MODEL"):
        disponibles.append("chatgpt")
    if os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_MODEL"):
        disponibles.append("gemini")
    return disponibles


def _claude(system: str, user: str, max_tokens: int) -> str | None:
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=max_tokens,
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text if msg.content else None
    except Exception:
        return None


def _openai(system: str, user: str, max_tokens: int) -> str | None:
    model = os.environ.get("OPENAI_MODEL")
    if not model:
        return None
    try:
        import openai  # type: ignore
    except ImportError:
        return None
    try:
        client = openai.OpenAI()
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
    model = os.environ.get("GEMINI_MODEL")
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


_FUNCS = {"claude": _claude, "chatgpt": _openai, "gemini": _gemini}


def completar(system: str, user: str, proveedor: str | None, max_tokens: int = 400) -> str | None:
    """Devuelve el texto del proveedor, o None si no hay clave / falla / no se
    pidió proveedor. Nunca levanta excepción — degrada en silencio."""
    if not proveedor or proveedor not in _FUNCS:
        return None
    if not os.environ.get(_ENV_KEYS[proveedor]):
        return None
    return _FUNCS[proveedor](system, user, max_tokens)
