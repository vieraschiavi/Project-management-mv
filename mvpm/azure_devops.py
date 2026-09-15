# © 2026 Martín Viera. Todos los derechos reservados.
"""Conexión a Azure DevOps Boards: traer el backlog, y devolverlo corregido.

Por qué existe: el backlog de un equipo en Azure DevOps es donde se ve —o no se
ve— si el trabajo está bien definido. En la práctica se degrada solo: tareas que
quedaron con el título "DELETE", ítems en Doing hace tres meses, iteraciones que
se llaman "Sprint Actual" (un nombre que se mueve y rompe la historia), mitad del
backlog sin estimar. Nada de eso lo marca Azure DevOps, porque ninguna de esas
cosas es un error para la herramienta.

Este módulo hace las dos puntas:

* **Traer** — se conecta a la API REST y baja los work items con una consulta
  WIQL. Sólo lectura: no hay en todo el módulo ninguna llamada que escriba.
* **Devolver** — `a_csv_azure()` arma el CSV con los nombres de columna que el
  importador de Azure DevOps espera, así la corrección vuelve a la herramienta
  en vez de quedar en un informe que nadie aplica.

El análisis en sí no está acá: está en `backlog_calidad.py`, que trabaja sobre
un DataFrame y no sabe nada de HTTP. Eso es a propósito — la demo corre el
análisis completo sin conexión ni credenciales.

## Sobre la autenticación (esto sorprende a todo el mundo la primera vez)

**El mail corporativo y su contraseña no sirven para la API.** No es una
limitación de este programa: es Microsoft. Una cuenta de Entra ID (ex Azure AD)
con MFA o acceso condicional —que es lo normal en cualquier empresa mediana—
tiene bloqueado el login por contraseña contra la API, y las "credenciales
alternativas" de Azure DevOps fueron retiradas.

Lo que sí funciona es un **token de acceso personal (PAT)**, que se saca en
`https://dev.azure.com/{organización}/_usersSettings/tokens` en un minuto. Se
pide con alcance **Work Items → Read** y nada más: con eso este módulo funciona
entero y el token no puede escribir aunque quisiera.

El mail sí se pide, y se usa: va como usuario en el Basic Auth y es lo que
queda en el log de auditoría de Azure DevOps del lado del cliente, que es
exactamente lo que el área de seguridad quiere ver.

## Sobre el token

No se guarda en la base. No entra en la tabla `versiones`, no se escribe en
disco y `Credenciales.__repr__` lo tapa, para que no se filtre por un traceback
o por un `print` de depuración. Vive en la sesión del navegador, o en la
variable de entorno `AZURE_DEVOPS_PAT` si preferís no tipearlo.
"""

from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import quote, urlencode

import pandas as pd

from mvpm.backlog_calidad import CLAVE_ORIGEN

# Cuántos ítems dejó afuera el límite de la consulta, anotado en el DataFrame.
CLAVE_TRUNCADO = "mvpm_truncado"

HOST = "https://dev.azure.com"
API_VERSION = "7.1"
TIMEOUT = 30
VAR_TOKEN = "AZURE_DEVOPS_PAT"

# Azure DevOps acepta hasta 200 work items por llamada al endpoint de lote.
LOTE = 200
LIMITE_POR_DEFECTO = 500

# Columnas canónicas del backlog. Son las mismas que exporta la grilla de Azure
# DevOps en español, y las que consume `backlog_calidad`.
COLUMNAS = (
    "ID", "Rev", "Tipo", "Titulo", "Estado", "AsignadoA", "Iteracion",
    "Padre", "Prioridad", "Esfuerzo", "Tags", "Creado", "Modificado",
    "Descripcion_texto",
)

# Campo de Azure DevOps → columna canónica.
_CAMPOS = {
    "System.WorkItemType": "Tipo",
    "System.Title": "Titulo",
    "System.State": "Estado",
    "System.AssignedTo": "AsignadoA",
    "System.IterationPath": "Iteracion",
    "System.Parent": "Padre",
    "System.Tags": "Tags",
    "System.CreatedDate": "Creado",
    "System.ChangedDate": "Modificado",
    "System.Description": "Descripcion_texto",
    "Microsoft.VSTS.Common.Priority": "Prioridad",
    "Microsoft.VSTS.Scheduling.Effort": "Esfuerzo",
}

# Encabezados que puede traer un CSV exportado a mano, en los tres idiomas en
# que Azure DevOps muestra la grilla. Sin esto, un export en inglés entra con
# todas las columnas vacías y el informe sale limpio por el motivo equivocado.
_ALIAS = {
    "id": "ID", "work item id": "ID",
    "rev": "Rev", "revision": "Rev", "revisión": "Rev",
    "tipo": "Tipo", "work item type": "Tipo", "tipo de elemento de trabajo": "Tipo",
    "tipo de item de trabalho": "Tipo",
    "titulo": "Titulo", "título": "Titulo", "title": "Titulo",
    "estado": "Estado", "state": "Estado",
    "asignadoa": "AsignadoA", "asignado a": "AsignadoA", "assigned to": "AsignadoA",
    "atribuido a": "AsignadoA",
    "iteracion": "Iteracion", "iteración": "Iteracion", "iteration path": "Iteracion",
    "ruta de iteración": "Iteracion", "caminho de iteração": "Iteracion",
    "padre": "Padre", "parent": "Padre", "primario": "Padre", "pai": "Padre",
    "prioridad": "Prioridad", "priority": "Prioridad", "prioridade": "Prioridad",
    "esfuerzo": "Esfuerzo", "effort": "Esfuerzo", "esforço": "Esfuerzo",
    "story points": "Esfuerzo", "puntos de historia": "Esfuerzo",
    "tags": "Tags", "etiquetas": "Tags",
    "creado": "Creado", "created date": "Creado", "fecha de creación": "Creado",
    "data de criação": "Creado",
    "modificado": "Modificado", "changed date": "Modificado",
    "fecha de cambio": "Modificado", "data da alteração": "Modificado",
    "descripcion_texto": "Descripcion_texto", "descripción": "Descripcion_texto",
    "descripcion": "Descripcion_texto", "description": "Descripcion_texto",
    "descrição": "Descripcion_texto",
}

# Nombres que espera el importador CSV de Azure DevOps al subir el archivo.
_A_AZURE = {
    "ID": "ID",
    "Tipo": "Work Item Type",
    "Titulo": "Title",
    "Estado": "State",
    "AsignadoA": "Assigned To",
    "Iteracion": "Iteration Path",
    "Prioridad": "Priority",
    "Esfuerzo": "Effort",
    "Tags": "Tags",
    "Descripcion_texto": "Description",
}

WIQL_BACKLOG = (
    "SELECT [System.Id] FROM WorkItems "
    "WHERE [System.TeamProject] = @project "
    "AND [System.WorkItemType] NOT IN ('Test Case', 'Test Suite', 'Test Plan') "
    "ORDER BY [System.Id]"
)


class ErrorAzure(Exception):
    """Falla al hablar con Azure DevOps, con un motivo que se pueda leer.

    `clave` es una clave de i18n, para que la pantalla muestre el motivo
    traducido en vez del texto crudo que devuelve la API.
    """

    def __init__(self, clave: str, detalle: str = "") -> None:
        super().__init__(detalle or clave)
        self.clave = clave
        self.detalle = detalle


@dataclass(frozen=True)
class Credenciales:
    """Lo que hace falta para leer un proyecto. El token nunca se persiste."""

    organizacion: str
    proyecto: str
    email: str = ""
    token: str = ""

    def __repr__(self) -> str:  # pragma: no cover - trivial, pero importa
        # Deliberado: un dataclass normal imprimiría el PAT entero en cualquier
        # traceback o log. Acá no aparece nunca.
        tiene = "sí" if self.token else "no"
        return (f"Credenciales(organizacion={self.organizacion!r}, "
                f"proyecto={self.proyecto!r}, email={self.email!r}, token={tiene})")

    def faltante(self) -> str | None:
        """Primer campo obligatorio que está vacío, como clave de i18n."""
        if not self.organizacion.strip():
            return "ado_falta_org"
        if not self.proyecto.strip():
            return "ado_falta_proyecto"
        if not self.token.strip():
            return "ado_falta_token"
        return None


def token_del_entorno() -> str:
    """El PAT de la variable de entorno, si el usuario prefiere no tipearlo."""
    return os.environ.get(VAR_TOKEN, "").strip()


def organizacion_de_url(texto: str) -> str:
    """Acepta que peguen la URL entera y saca la organización.

    Es lo que la gente tiene en el portapapeles: nadie se acuerda de que hay que
    escribir sólo el último pedazo de `https://dev.azure.com/xxx/yyy`.
    """
    s = (texto or "").strip().rstrip("/")
    if not s:
        return ""
    m = re.search(r"dev\.azure\.com/([^/?#]+)", s)
    if m:
        return m.group(1)
    m = re.search(r"https?://([^.]+)\.visualstudio\.com", s)
    if m:
        return m.group(1)
    return s.split("/")[-1] if "/" in s else s


# ------------------------------------------------------------------- HTTP


def _cabecera_auth(cred: Credenciales) -> str:
    par = f"{cred.email}:{cred.token}".encode()
    return "Basic " + base64.b64encode(par).decode("ascii")


def _url(cred: Credenciales, ruta: str, **params) -> str:
    params.setdefault("api-version", API_VERSION)
    base = f"{HOST}/{quote(cred.organizacion.strip(), safe='')}/{ruta.lstrip('/')}"
    return f"{base}?{urlencode(params)}"


class _SinRedirect(urllib.request.HTTPRedirectHandler):
    """Corta los redirects en vez de seguirlos con el PAT puesto.

    `HTTPRedirectHandler` copia las cabeceras del pedido original al redirigido:
    un 3xx hacia otro host se llevaría el Basic Auth con el PAT en claro. La API
    de Azure DevOps no necesita redirects para nada de lo que se usa acá, así
    que lo correcto es no seguir ninguno: si aparece uno, es justamente la
    página de login, y eso ya es un error de autenticación.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_ABRIDOR = urllib.request.build_opener(_SinRedirect)


def _pedir(cred: Credenciales, url: str, cuerpo: dict | None = None,
           timeout: int = TIMEOUT) -> dict:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pedido = urllib.request.Request(url, data=datos, method="POST" if datos else "GET")
    pedido.add_header("Authorization", _cabecera_auth(cred))
    pedido.add_header("Accept", "application/json")
    if datos:
        pedido.add_header("Content-Type", "application/json")
    try:
        with _ABRIDOR.open(pedido, timeout=timeout) as r:  # noqa: S310
            crudo = r.read()
            tipo = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raise _error_http(e) from e
    except urllib.error.URLError as e:
        raise ErrorAzure("ado_err_red", str(e.reason)) from e
    except TimeoutError as e:
        raise ErrorAzure("ado_err_red", "timeout") from e
    except OSError as e:
        # urllib NO envuelve lo que levanta getresponse(): un proxy que corta la
        # conexión sale como http.client.RemoteDisconnected / BadStatusLine en
        # crudo. Sin esto, la pantalla se cae con un traceback rojo en vez de
        # decir "no se pudo llegar a Azure DevOps".
        raise ErrorAzure("ado_err_red", type(e).__name__) from e

    # El detalle que más confunde de esta API: con credenciales inválidas NO
    # devuelve 401. Devuelve 200/203 con la página HTML de login, y el cliente
    # que no mira el Content-Type termina reportando "respuesta vacía".
    if "application/json" not in tipo.lower():
        raise ErrorAzure("ado_err_auth", f"Content-Type={tipo or 'desconocido'}")
    try:
        return json.loads(crudo.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise ErrorAzure("ado_err_respuesta", str(e)) from e


def _error_http(e: urllib.error.HTTPError) -> ErrorAzure:
    detalle = ""
    try:
        cuerpo = json.loads(e.read().decode("utf-8"))
        detalle = str(cuerpo.get("message", ""))[:300]
    except Exception:  # noqa: BLE001 - el cuerpo del error es opcional
        detalle = ""
    if e.code in (401, 203):
        return ErrorAzure("ado_err_auth", detalle)
    if e.code == 403:
        return ErrorAzure("ado_err_permiso", detalle)
    if e.code == 404:
        return ErrorAzure("ado_err_no_existe", detalle)
    return ErrorAzure("ado_err_http", f"HTTP {e.code} {detalle}".strip())


# ------------------------------------------------------------------- lectura


def probar_conexion(cred: Credenciales) -> dict:
    """Verifica organización + proyecto + token antes de traer nada.

    Devuelve `{ok, clave, proyecto, detalle}`. No levanta: la pantalla necesita
    mostrar el motivo, no un traceback.
    """
    falta = cred.faltante()
    if falta:
        return {"ok": False, "clave": falta, "proyecto": "", "detalle": ""}
    ruta = f"_apis/projects/{quote(cred.proyecto.strip(), safe='')}"
    try:
        r = _pedir(cred, _url(cred, ruta))
    except ErrorAzure as e:
        return {"ok": False, "clave": e.clave, "proyecto": "", "detalle": e.detalle}
    except Exception as e:  # noqa: BLE001
        # El docstring promete que esta función no levanta, y la pantalla
        # depende de eso. Cualquier cosa inesperada sale como un motivo legible,
        # nunca como un traceback que deja la sección sin renderizar.
        return {"ok": False, "clave": "ado_err_respuesta", "proyecto": "",
                "detalle": type(e).__name__}
    return {
        "ok": True,
        "clave": "ado_ok",
        "proyecto": str(r.get("name", cred.proyecto)),
        "detalle": str(r.get("description", "") or "")[:300],
    }


def _ids(cred: Credenciales, wiql: str, limite: int) -> tuple[list[int], int]:
    """Devuelve (ids recortados al límite, cuántos había en total)."""
    ruta = f"{quote(cred.proyecto.strip(), safe='')}/_apis/wit/wiql"
    # Se pide uno más que el límite justamente para poder avisar que sobra.
    r = _pedir(cred, _url(cred, ruta, **{"$top": limite + 1}), {"query": wiql})
    filas = r.get("workItems") or []
    todos = []
    for f in filas:
        try:
            todos.append(int(f["id"]))
        except (KeyError, TypeError, ValueError):
            continue
    return todos[:limite], len(todos)


def _lote(cred: Credenciales, ids: list[int]) -> list[dict]:
    campos = ",".join(_CAMPOS)
    ruta = "_apis/wit/workitems"
    url = _url(cred, ruta, ids=",".join(str(i) for i in ids), fields=campos)
    return list(_pedir(cred, url).get("value") or [])


def traer_backlog(cred: Credenciales, wiql: str | None = None,
                  limite: int = LIMITE_POR_DEFECTO) -> pd.DataFrame:
    """Baja el backlog del proyecto como DataFrame con las columnas canónicas.

    Sólo lectura: WIQL es un lenguaje de consulta y el endpoint de lote es GET.
    """
    falta = cred.faltante()
    if falta:
        raise ErrorAzure(falta)
    ids, total = _ids(cred, wiql or WIQL_BACKLOG, limite)
    if not ids:
        vacio = pd.DataFrame(columns=list(COLUMNAS))
        vacio.attrs[CLAVE_ORIGEN] = frozenset(COLUMNAS)
        vacio.attrs[CLAVE_TRUNCADO] = 0
        return vacio
    items: list[dict] = []
    for i in range(0, len(ids), LOTE):
        items.extend(_lote(cred, ids[i:i + LOTE]))
    df = _a_dataframe(items)
    # Cuántos quedaron afuera. Analizar 500 de 2.000 y no decirlo deja al
    # usuario creyendo que revisó su backlog: el informe sale "limpio" porque
    # no vio el resto, que es la misma mentira que inventar un dato.
    df.attrs[CLAVE_TRUNCADO] = max(0, total - len(ids))
    return df


def sobraron(df: pd.DataFrame) -> int:
    """Ítems que la consulta dejó afuera por el límite. 0 = se trajo todo."""
    return int(df.attrs.get(CLAVE_TRUNCADO, 0) or 0)


def _a_dataframe(items: list[dict]) -> pd.DataFrame:
    filas = []
    for it in items:
        campos = it.get("fields") or {}
        fila = {"ID": it.get("id", ""), "Rev": it.get("rev", "")}
        for clave, columna in _CAMPOS.items():
            fila[columna] = _valor(campos.get(clave), columna)
        filas.append(fila)
    df = pd.DataFrame(filas)
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = ""
    return df[list(COLUMNAS)]


def _valor(bruto, columna: str) -> str:
    if bruto is None:
        return ""
    if columna == "AsignadoA" and isinstance(bruto, dict):
        # La API devuelve la identidad entera; acá sólo interesa el nombre.
        return str(bruto.get("displayName", "") or bruto.get("uniqueName", ""))
    if columna in ("Creado", "Modificado"):
        return str(bruto)[:10]
    if columna == "Descripcion_texto":
        return texto_plano(str(bruto))
    return str(bruto)


_ETIQUETA = re.compile(r"<[^>]+>")
_ENTIDAD = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&quot;": '"', "&#39;": "'"}


def texto_plano(html: str) -> str:
    """La descripción viene en HTML; para analizarla hace falta el texto.

    Los `<br>` y los cierres de párrafo se vuelven espacios y no se pegan las
    palabras: sin eso, "Objetivo:</p><p>Entregable:" daría "Objetivo:Entregable:"
    y las reglas que buscan secciones no encontrarían ninguna.
    """
    if not html:
        return ""
    s = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6])\s*/?>", " ", html)
    s = _ETIQUETA.sub("", s)
    for ent, car in _ENTIDAD.items():
        s = s.replace(ent, car)
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------------- archivos


def leer_csv(origen) -> pd.DataFrame:
    """Lee un export de Azure DevOps y lo normaliza a las columnas canónicas.

    Acepta ruta, bytes o texto. Tolera el BOM que Excel deja al frente —si no,
    la primera columna se llamaría '\\ufeffID' y quedaría sin reconocer.
    """
    if isinstance(origen, bytes):
        texto = origen.decode("utf-8-sig", errors="replace")
    elif isinstance(origen, str) and ("\n" in origen or "," in origen):
        texto = origen.lstrip("﻿")
    else:
        with open(origen, encoding="utf-8-sig") as f:
            texto = f.read()
    df = pd.read_csv(io.StringIO(texto), dtype=str, keep_default_na=False)
    return normalizar(df)


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra encabezados conocidos y garantiza que estén todas las columnas."""
    renombres = {}
    for col in df.columns:
        clave = str(col).strip().lstrip("﻿").lower()
        if clave in _ALIAS:
            renombres[col] = _ALIAS[clave]
    salida = df.rename(columns=renombres).copy()
    # Un export puede traer dos columnas que mapean al mismo destino (p.ej.
    # 'Description' y 'Descripción'). Quedarse con la primera a secas elegía la
    # vacía la mitad de las veces, se disparaba `sin_descripcion` por un motivo
    # falso y la plantilla terminaba pisando el texto real.
    salida = _fusionar_duplicadas(salida)

    # Qué columnas venían DE VERDAD. Es la diferencia entre "el campo está
    # vacío en Azure" y "el export no trajo ese campo", y de eso depende que el
    # corrector no escriba encima de un dato que nunca vio. La grilla de Azure
    # Boards no puede exportar Descripción, así que este caso es el normal.
    presentes = frozenset(c for c in COLUMNAS if c in salida.columns)
    for c in COLUMNAS:
        if c not in salida.columns:
            salida[c] = ""
    salida = salida[list(COLUMNAS)]
    salida = salida.fillna("").astype(str).apply(lambda s: s.str.strip())
    salida.attrs[CLAVE_ORIGEN] = presentes
    return salida


def _fusionar_duplicadas(df: pd.DataFrame) -> pd.DataFrame:
    """Colapsa columnas con el mismo nombre quedándose con el primer valor útil."""
    if not df.columns.duplicated().any():
        return df
    salida = pd.DataFrame(index=df.index)
    for nombre in dict.fromkeys(df.columns):
        bloque = df.loc[:, df.columns == nombre]
        if bloque.shape[1] == 1:
            salida[nombre] = bloque.iloc[:, 0]
            continue
        combinada = bloque.iloc[:, 0]
        for k in range(1, bloque.shape[1]):
            vacia = combinada.isna() | (combinada.astype(str).str.strip() == "")
            combinada = combinada.where(~vacia, bloque.iloc[:, k])
        salida[nombre] = combinada
    return salida


def a_csv_azure(df: pd.DataFrame) -> str:
    """Arma el CSV con los nombres de columna del importador de Azure DevOps.

    Se conserva el ID: con el ID puesto, el importador **actualiza** el ítem que
    ya existe en vez de crear uno nuevo. Ese es el punto de todo esto — si el ID
    va vacío, subir el archivo corregido duplica el backlog entero.

    **Sólo salen las columnas que venían en la fuente.** Emitir una columna que
    el export no trajo la escribiría vacía (o con lo que el corrector hubiera
    puesto) encima del valor real de todos los ítems al reimportar. Con un
    export de la grilla de Azure Boards, que no puede incluir Descripción, eso
    borraba la descripción del proyecto entero.
    """
    salida = io.StringIO()
    origen = df.attrs.get(CLAVE_ORIGEN)
    permitidas = frozenset(origen) if origen else frozenset(df.columns)
    columnas = [c for c in _A_AZURE if c in df.columns and c in permitidas]
    escritor = csv.writer(salida, lineterminator="\n")
    escritor.writerow([_A_AZURE[c] for c in columnas])
    for _, fila in df.iterrows():
        escritor.writerow([str(fila[c]) if pd.notna(fila[c]) else "" for c in columnas])
    return salida.getvalue()
