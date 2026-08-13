# © 2026 Martín Viera. Todos los derechos reservados.
"""Catálogo de modelos de IA por proveedor, consultado contra la API del cliente.

## Para qué

Hasta acá el modelo estaba decidido en el código (`claude-opus-4-8` fijo en
`ai.py`) o en una variable de entorno que hay que exportar antes de abrir el
programa (`OPENAI_MODEL`, `GEMINI_MODEL`). Ninguna de las dos la puede tocar un
cliente desde la aplicación instalada, y el modelo es la palanca principal del
gasto: entre el modelo más caro y el más barato de un mismo proveedor hay más
de un orden de magnitud por token. Este módulo permite elegirlo desde la
pantalla de Configuración.

## De dónde sale la lista

De la API del propio cliente, con la clave del propio cliente. No hay ninguna
lista de modelos escrita en este archivo, y es a propósito: cualquier catálogo
hardcodeado envejece —salen modelos nuevos todos los meses, se retiran otros— y
además miente, porque no todas las claves tienen habilitados los mismos modelos
(depende del plan, de la organización y de la región). Una lista inventada le
ofrecería al cliente modelos que su clave no puede usar y le escondería los que
sí.

Consecuencia deliberada: antes del primer "Actualizar" el catálogo está vacío.
Eso es información correcta —todavía no se le preguntó a nadie— y la pantalla
lo dice con esas palabras, en vez de rellenar con nombres verosímiles. Para el
caso en que un proveedor no tenga endpoint de listado o falle, se puede escribir
el identificador del modelo a mano.

## Qué NO hace

No valida que el modelo elegido exista ni que sirva para generar texto: eso lo
dice el proveedor recién al primer pedido. Igual que el resto de la capa de IA,
si algo falla se degrada en silencio y el motor de reglas sigue respondiendo
(ver `mvpm/ai.py`).
"""

import contextvars
import json
import os
import urllib.error
import urllib.request

TIMEOUT = 15


class ErrorDeProveedor(RuntimeError):
    """La consulta al catálogo falló. Lleva un mensaje pensado para mostrarle
    al usuario, no un volcado de la excepción de red."""


# Cada proveedor declara de dónde saca su clave, con qué variable de entorno se
# puede fijar el modelo sin pasar por la interfaz, y cómo se le pregunta el
# catálogo. `estilo` resume el dialecto HTTP: 'anthropic' y 'openai' difieren
# sólo en el encabezado de autenticación, 'gemini' manda la clave en la URL.
PROVEEDORES: dict[str, dict] = {
    "claude": {
        "etiqueta": "Claude (Anthropic)",
        "env_clave": "ANTHROPIC_API_KEY",
        "env_modelo": "ANTHROPIC_MODEL",
        "url": "https://api.anthropic.com/v1/models?limit=100",
        "estilo": "anthropic",
    },
    "chatgpt": {
        "etiqueta": "ChatGPT (OpenAI)",
        "env_clave": "OPENAI_API_KEY",
        "env_modelo": "OPENAI_MODEL",
        "url": "https://api.openai.com/v1/models",
        "estilo": "openai",
    },
    "gemini": {
        "etiqueta": "Gemini (Google)",
        "env_clave": "GEMINI_API_KEY",
        "env_modelo": "GEMINI_MODEL",
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "estilo": "gemini",
    },
    "grok": {
        "etiqueta": "Grok (xAI)",
        "env_clave": "XAI_API_KEY",
        "env_modelo": "XAI_MODEL",
        "url": "https://api.x.ai/v1/models",
        "estilo": "openai",
    },
    "copilot": {
        # La API de Copilot dentro del editor no es pública para terceros; lo
        # que sí expone GitHub con un token personal es el catálogo de GitHub
        # Models, que es el que se consulta acá. La etiqueta lo dice para que
        # nadie espere el Copilot del IDE.
        #
        # La variable es GITHUB_MODELS_TOKEN y no GITHUB_TOKEN a propósito:
        # GITHUB_TOKEN está seteada por defecto en cualquier runner de Actions
        # y en muchas máquinas de desarrollo, para cosas que no tienen nada que
        # ver con IA. Si fuera esa, el producto ofrecería un proveedor de IA
        # que el usuario nunca configuró y que casi seguro no tiene permiso de
        # inferencia — un 403 al primer uso, sin explicación posible.
        "etiqueta": "Copilot (GitHub Models)",
        "env_clave": "GITHUB_MODELS_TOKEN",
        "env_modelo": "GITHUB_MODELS_MODEL",
        "url": "https://models.github.ai/catalog/models",
        "estilo": "openai",
    },
}

# Modelo elegido, por proveedor. En memoria a propósito: la persistencia es por
# empresa y versionada (tabla `versiones`), y de eso se encarga quien llama con
# serializar_seleccion() / aplicar_seleccion().
#
# Es un ContextVar y no un dict suelto porque Streamlit atiende a TODAS las
# sesiones en un solo proceso, corriendo el script de cada una en su propio
# hilo. Con estado de módulo compartido, el modelo que elige una empresa se lo
# comería la sesión de otra —silenciosamente, y cobrado a la clave de la otra—.
# Un ContextVar arranca en su valor por defecto en cada hilo, así que cada
# sesión ve sólo lo suyo.
_ELEGIDOS: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar(
    "mvpm_modelos_elegidos", default={})


def _actual() -> dict[str, str]:
    return _ELEGIDOS.get()


def _reemplazar(nuevos: dict[str, str]) -> None:
    # Siempre se pone un dict NUEVO: mutar el default del ContextVar lo
    # convertiría en el estado compartido que se quiere evitar.
    _ELEGIDOS.set(nuevos)


def etiqueta(proveedor: str) -> str:
    return PROVEEDORES.get(proveedor, {}).get("etiqueta", proveedor)


def tiene_clave(proveedor: str) -> bool:
    cfg = PROVEEDORES.get(proveedor)
    return bool(cfg and os.environ.get(cfg["env_clave"]))


def con_clave() -> list[str]:
    """Proveedores que el cliente tiene realmente configurados. Nunca se le
    ofrece uno sin clave: fallaría al primer pedido y sin decir por qué."""
    return [nombre for nombre in PROVEEDORES if tiene_clave(nombre)]


def modelo_actual(proveedor: str) -> str | None:
    """Modelo vigente para un proveedor, en orden de precedencia:

    1. lo elegido en Configuración (gana siempre: es lo último que hizo el
       usuario, y sería desconcertante que una variable de entorno vieja le
       pisara la elección que acaba de hacer con el mouse);
    2. la variable de entorno del proveedor, para quien automatiza;
    3. None — el que llama decide si tiene un valor por defecto propio.
    """
    elegidos = _actual()
    if proveedor in elegidos:
        return elegidos[proveedor]
    cfg = PROVEEDORES.get(proveedor)
    if not cfg:
        return None
    return os.environ.get(cfg["env_modelo"]) or None


def fijar_modelo(proveedor: str, modelo: str | None) -> None:
    """Fija (o borra, con None/vacío) el modelo elegido para un proveedor."""
    if proveedor not in PROVEEDORES:
        raise ValueError(f"Proveedor desconocido: {proveedor}")
    nuevos = dict(_actual())
    if modelo and modelo.strip():
        nuevos[proveedor] = modelo.strip()
    else:
        nuevos.pop(proveedor, None)
    _reemplazar(nuevos)


def seleccion() -> dict[str, str]:
    return dict(_actual())


def serializar_seleccion() -> str:
    """JSON para guardar como una versión más en la tabla `versiones`."""
    return json.dumps(_actual(), ensure_ascii=False, sort_keys=True)


def aplicar_seleccion(contenido: str | None) -> dict[str, str]:
    """Carga lo guardado. Tolera JSON roto o de una versión vieja del formato
    devolviendo lo que había: una elección de modelo corrupta no puede ser
    motivo para que no abra el programa."""
    _reemplazar({})
    if not contenido:
        return {}
    try:
        datos = json.loads(contenido)
    except (ValueError, TypeError):
        return {}
    if not isinstance(datos, dict):
        return {}
    nuevos = {
        proveedor: modelo.strip()
        for proveedor, modelo in datos.items()
        if proveedor in PROVEEDORES and isinstance(modelo, str) and modelo.strip()
    }
    _reemplazar(nuevos)
    return dict(nuevos)


# ------------------------------------------------------- consulta al proveedor

def _pedir(url: str, cabeceras: dict[str, str], timeout: int) -> dict | list:
    peticion = urllib.request.Request(url, headers=cabeceras)
    with urllib.request.urlopen(peticion, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _ids_anthropic(datos) -> list[str]:
    return [m["id"] for m in datos.get("data", []) if m.get("id")]


def _ids_openai(datos) -> list[str]:
    # El catálogo de GitHub Models devuelve una lista pelada; OpenAI y xAI la
    # envuelven en {"data": [...]}. Se aceptan las dos formas.
    filas = datos if isinstance(datos, list) else datos.get("data", [])
    return [m["id"] for m in filas if isinstance(m, dict) and m.get("id")]


def _ids_gemini(datos) -> list[str]:
    ids = []
    for m in datos.get("models", []):
        # Gemini lista también modelos de embeddings y de conteo de tokens, que
        # no sirven para generar texto: se filtran por el método que soportan.
        metodos = m.get("supportedGenerationMethods") or []
        if metodos and "generateContent" not in metodos:
            continue
        nombre = m.get("name", "")
        if nombre:
            ids.append(nombre.removeprefix("models/"))
    return ids


def listar_desde_api(proveedor: str, timeout: int = TIMEOUT) -> list[str]:
    """Trae del proveedor los modelos que ESTA clave tiene habilitados.

    Levanta ErrorDeProveedor con un mensaje explicable. A diferencia del resto
    de la capa de IA, acá no se degrada en silencio: el usuario apretó un botón
    que dice "actualizar" y merece saber por qué no pasó nada.
    """
    cfg = PROVEEDORES.get(proveedor)
    if not cfg:
        raise ErrorDeProveedor(f"Proveedor desconocido: {proveedor}")

    clave = os.environ.get(cfg["env_clave"])
    if not clave:
        raise ErrorDeProveedor(
            f"Falta {cfg['env_clave']}: sin clave no hay a quién preguntarle."
        )

    url = cfg["url"]
    cabeceras = {"Accept": "application/json"}
    if cfg["estilo"] == "anthropic":
        cabeceras["x-api-key"] = clave
        cabeceras["anthropic-version"] = "2023-06-01"
    elif cfg["estilo"] == "gemini":
        # Gemini autentica por parámetro de URL, no por encabezado.
        url = f"{url}?key={clave}&pageSize=200"
    else:
        cabeceras["Authorization"] = f"Bearer {clave}"

    try:
        datos = _pedir(url, cabeceras, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ErrorDeProveedor(
                f"{etiqueta(proveedor)} rechazó la clave ({exc.code}). "
                f"Revisá {cfg['env_clave']}."
            ) from exc
        raise ErrorDeProveedor(
            f"{etiqueta(proveedor)} respondió {exc.code} al pedir el catálogo."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErrorDeProveedor(
            f"No se pudo llegar a {etiqueta(proveedor)}: {exc}"
        ) from exc
    except ValueError as exc:  # JSON ilegible
        raise ErrorDeProveedor(
            f"{etiqueta(proveedor)} devolvió algo que no es JSON."
        ) from exc

    parser = {
        "anthropic": _ids_anthropic,
        "openai": _ids_openai,
        "gemini": _ids_gemini,
    }[cfg["estilo"]]
    try:
        ids = parser(datos)
    except (AttributeError, TypeError) as exc:
        raise ErrorDeProveedor(
            f"No se entendió el catálogo que devolvió {etiqueta(proveedor)}."
        ) from exc

    if not ids:
        raise ErrorDeProveedor(
            f"{etiqueta(proveedor)} no devolvió ningún modelo para esta clave."
        )
    return sorted(set(ids))
