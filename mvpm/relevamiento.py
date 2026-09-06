# © 2026 Martín Viera. Todos los derechos reservados.
"""Relevamiento del pipeline del cliente: preguntas, respuestas y repreguntas.

Qué resuelve: entrar a Conaprole con las preguntas ya escritas, anotar quién
de cada área respondió qué, y saber en todo momento qué falta. El banco de
preguntas vive en `mvpm/relevamiento_preguntas.py` (es contenido y crece); acá
está lo que hace con él.

**Las respuestas se guardan versionadas por empresa**, con la misma regla que
el resto del producto (`mvpm/db.py`, tabla `versiones`): cada corrección es
una fila nueva, nunca un UPDATE. En un relevamiento eso importa más que en
ningún otro lado — la respuesta cambia cuando la persona lo consulta con su
equipo, y saber qué contestó primero es la mitad del hallazgo.

**La repregunta.** Cuando una respuesta llega vaga —"depende", "creo que",
"más o menos"— hay que volver a preguntar, y en el momento no siempre se sabe
QUÉ repreguntar. El motor lo sugiere con reglas, mirando qué le falta a la
respuesta. Si además hay un proveedor de IA configurado, se le puede pedir una
repregunta redactada sobre esa respuesta concreta — pero la sugerencia por
reglas existe siempre, porque el relevamiento no puede depender de que alguien
haya puesto una clave.
"""

from __future__ import annotations

import json
import re

from mvpm import db
from mvpm.relevamiento_preguntas import AREAS, PREGUNTAS

LANGS = ("es", "en", "pt")

#: La entidad con la que se guarda en la tabla `versiones`. No se traduce.
ENTIDAD = "relevamiento"

_CLAVES_AREA = {a["clave"] for a in AREAS}
for _p in PREGUNTAS:
    assert _p["area"] in _CLAVES_AREA, f"{_p['clave']}: área desconocida {_p['area']!r}"
_vistas: set[str] = set()
for _p in PREGUNTAS:
    assert _p["clave"] not in _vistas, f"clave repetida: {_p['clave']}"
    _vistas.add(_p["clave"])


def _t(campo: dict, lang: str) -> str:
    return campo.get(lang, campo["es"])


def areas(lang: str = "es") -> list[dict]:
    lang = lang if lang in LANGS else "es"
    return [{"clave": a["clave"], "nombre": _t(a["nombre"], lang),
             "por_que": _t(a["por_que"], lang),
             "preguntas": sum(1 for p in PREGUNTAS if p["area"] == a["clave"])}
            for a in AREAS]


def preguntas(area: str | None = None, lang: str = "es") -> list[dict]:
    """Las preguntas, opcionalmente de un área. En el orden en que conviene
    hacerlas."""
    lang = lang if lang in LANGS else "es"
    return [{"clave": p["clave"], "area": p["area"],
             "pregunta": _t(p["pregunta"], lang), "por_que": _t(p["por_que"], lang)}
            for p in PREGUNTAS if area is None or p["area"] == area]


def pregunta(clave: str, lang: str = "es") -> dict:
    for p in preguntas(lang=lang):
        if p["clave"] == clave:
            return p
    raise KeyError(f"no existe la pregunta {clave!r}")


# ------------------------------------------------- respuestas por empresa

def guardar_respuesta(empresa_id: int, clave: str, respuesta: str,
                      responsable: str = "", area_responsable: str = "",
                      estado: str = "borrador") -> int:
    """Guarda la respuesta de una pregunta. Fila nueva SIEMPRE.

    `estado` sigue la convención del resto del producto: `borrador` mientras
    es lo que dijo alguien en una reunión, `validado` cuando el responsable la
    confirmó. La diferencia importa: una respuesta de pasillo y una confirmada
    por el dueño del dato no valen lo mismo en un informe."""
    pregunta(clave)  # revienta si la pregunta no existe: no se guardan huérfanas
    contenido = json.dumps({
        "respuesta": respuesta.strip(),
        "responsable": responsable.strip(),
        "area_responsable": area_responsable.strip(),
    }, ensure_ascii=False)
    return db.guardar_version(
        empresa_id=empresa_id, entidad=ENTIDAD, clave=clave,
        contenido=contenido, estado=estado,
        validado_por_nombre=responsable.strip() or None,
        validado_por_cargo=area_responsable.strip() or None)


def respuesta_de(empresa_id: int, clave: str) -> dict | None:
    """La respuesta vigente, o None. Las anteriores siguen en la base."""
    fila = db.obtener_version_actual(empresa_id, ENTIDAD, clave)
    if not fila:
        return None
    try:
        datos = json.loads(fila["contenido"])
    except (ValueError, TypeError):
        # Contenido viejo o escrito a mano: se muestra crudo antes que perderlo.
        datos = {"respuesta": str(fila["contenido"]), "responsable": "",
                 "area_responsable": ""}
    datos["estado"] = fila["estado"] if "estado" in fila.keys() else "borrador"
    return datos


def respuestas(empresa_id: int) -> dict[str, dict]:
    return {p["clave"]: r for p in PREGUNTAS
            if (r := respuesta_de(empresa_id, p["clave"])) is not None}


def historial(empresa_id: int, clave: str) -> list:
    """Todo lo que se contestó a esa pregunta, no sólo lo vigente."""
    return db.historial_versiones(empresa_id, ENTIDAD, clave)


# ------------------------------------------------------------- el avance

def avance(empresa_id: int, lang: str = "es") -> list[dict]:
    """Cuánto se relevó de cada área. Lo que un gerente mira primero."""
    contestadas = respuestas(empresa_id)
    salida = []
    for a in areas(lang):
        del_area = [p for p in PREGUNTAS if p["area"] == a["clave"]]
        con = [p for p in del_area if contestadas.get(p["clave"], {}).get("respuesta")]
        validadas = [p for p in con
                     if contestadas[p["clave"]].get("estado") == "validado"]
        salida.append({
            "clave": a["clave"], "nombre": a["nombre"],
            "total": len(del_area), "respondidas": len(con),
            "validadas": len(validadas),
            "pct": round(100 * len(con) / len(del_area), 1) if del_area else 0.0,
        })
    return salida


def pendientes(empresa_id: int, lang: str = "es") -> list[dict]:
    contestadas = respuestas(empresa_id)
    return [p for p in preguntas(lang=lang)
            if not contestadas.get(p["clave"], {}).get("respuesta")]


# ---------------------------------------------------------- la repregunta
#
# Reglas primero. Cada patrón dice qué le FALTA a la respuesta, no que esté
# mal: "depende" suele ser cierto, y la repregunta útil es "¿de qué depende?".

_PATRONES: list[tuple[str, dict]] = [
    (r"\bdepende\b|\bdepends\b",
     {"es": "¿De qué depende exactamente, y quién decide en cada caso?",
      "en": "What exactly does it depend on, and who decides in each case?",
      "pt": "De que depende exatamente, e quem decide em cada caso?"}),
    (r"\bcreo\b|\bme parece\b|\bi think\b|\bacho que\b",
     {"es": "¿Quién lo puede confirmar con certeza, y para cuándo?",
      "en": "Who can confirm this for certain, and by when?",
      "pt": "Quem pode confirmar com certeza, e para quando?"}),
    (r"\bno s[eé]\b|\bni idea\b|\bi don'?t know\b|\bnão sei\b",
     {"es": "¿A quién habría que preguntarle esto?",
      "en": "Who should we ask about this?",
      "pt": "A quem deveríamos perguntar isto?"}),
    (r"\bm[aá]s o menos\b|\baproximadamente\b|\bmore or less\b|\bcerca de\b",
     {"es": "¿Hay un número exacto en algún lado, o hay que medirlo?",
      "en": "Is there an exact figure somewhere, or does it need measuring?",
      "pt": "Existe um número exato em algum lugar, ou é preciso medir?"}),
    (r"\bmanual(mente)?\b|\ba mano\b|\bby hand\b",
     {"es": "¿Quién lo hace, cuánto le lleva y qué pasa si esa persona no está?",
      "en": "Who does it, how long does it take, and what if that person is away?",
      "pt": "Quem faz, quanto tempo leva e o que acontece se essa pessoa faltar?"}),
    (r"\bexcel\b|\bplanilla\b|\bspreadsheet\b",
     {"es": "¿Dónde vive esa planilla, quién la edita y hay una sola versión?",
      "en": "Where does that spreadsheet live, who edits it, and is there one "
            "single version?",
      "pt": "Onde vive essa planilha, quem a edita e há uma só versão?"}),
    (r"\bnadie\b|\bno hay\b|\bnobody\b|\bninguém\b|\bnão há\b",
     {"es": "Si hoy no existe, ¿quién debería hacerse cargo?",
      "en": "If it does not exist today, who should take it on?",
      "pt": "Se hoje não existe, quem deveria assumir?"}),
]

#: Debajo de esto una respuesta no alcanza para cerrar una pregunta de
#: relevamiento, por más que técnicamente esté contestada.
MINIMO_PALABRAS = 6


def repreguntas_sugeridas(clave: str, respuesta: str, lang: str = "es") -> list[str]:
    """Qué conviene repreguntar sobre ESA respuesta. Siempre por reglas: el
    relevamiento no puede depender de que alguien haya configurado una IA."""
    lang = lang if lang in LANGS else "es"
    texto = (respuesta or "").strip()
    sugerencias: list[str] = []

    if not texto:
        return []
    if len(texto.split()) < MINIMO_PALABRAS:
        sugerencias.append({
            "es": "La respuesta es muy corta para cerrar el punto: ¿podés dar un "
                  "ejemplo concreto?",
            "en": "The answer is too short to close the point: can you give a "
                  "concrete example?",
            "pt": "A resposta é curta demais para fechar o ponto: pode dar um "
                  "exemplo concreto?"}[lang])

    bajo = texto.lower()
    for patron, textos in _PATRONES:
        if re.search(patron, bajo):
            sugerencias.append(textos[lang])
    return sugerencias


def prompt_de_repregunta(clave: str, respuesta: str, lang: str = "es") -> tuple[str, str]:
    """El (system, user) para pedirle una repregunta a la IA.

    Se arma acá y no en la pestaña para que se pueda testear sin levantar
    Streamlit y sin llamar a ningún proveedor. La instrucción es deliberada:
    que repregunte, no que resuma ni que opine sobre lo que dijo el cliente."""
    p = pregunta(clave, lang)
    system = {
        "es": "Sos un consultor de datos haciendo un relevamiento. Te doy una "
              "pregunta y la respuesta que dio el cliente. Devolvé UNA sola "
              "repregunta, corta y concreta, que sirva para cerrar lo que quedó "
              "abierto. No resumas, no opines, no supongas datos que no están.",
        "en": "You are a data consultant running a discovery interview. I give "
              "you a question and the client's answer. Return ONE single "
              "follow-up question, short and concrete, that closes what was left "
              "open. Do not summarise, do not opine, do not assume facts that are "
              "not there.",
        "pt": "Você é um consultor de dados fazendo um levantamento. Dou uma "
              "pergunta e a resposta do cliente. Devolva UMA única repergunta, "
              "curta e concreta, que sirva para fechar o que ficou aberto. Não "
              "resuma, não opine, não suponha dados que não estão.",
    }[lang if lang in LANGS else "es"]
    user = (f"{p['pregunta']}\n\n"
            f"({p['por_que']})\n\n"
            f"---\n{respuesta.strip()}")
    return system, user


# ------------------------------------------- lo que la reunión ya contestó

def areas_tocadas(intervenciones, lang: str = "es") -> list[dict]:
    """Qué áreas del relevamiento se mencionaron en una reunión.

    Cierra el círculo con `mvpm/reuniones.py`: después de una reunión con el
    cliente se ve qué áreas quedaron cubiertas y cuáles no se tocaron, que es
    lo que define la agenda de la próxima. La detección es por palabras clave y
    se declara como tal: dice DÓNDE mirar, no da el área por relevada."""
    señales = {
        "fuentes": ("sap", "erp", "sistema", "fuente", "maestro", "planilla",
                    "excel", "base de datos", "source", "fonte"),
        "ingesta": ("carga", "frecuencia", "diario", "nocturno", "batch",
                    "actualiza", "ingesta", "load", "refresh"),
        "calidad": ("calidad", "duplicado", "nulo", "vacío", "regla", "excluir",
                    "anulado", "quality", "qualidade"),
        "modelado": ("definición", "indicador", "kpi", "granularidad", "jerarquía",
                     "categoría", "modelo", "definition"),
        "orquestacion": ("agenda", "scheduler", "orquesta", "falla", "corre a las",
                         "dependencia", "job", "pipeline"),
        "gobernanza": ("dueño", "owner", "responsable", "glosario", "gobernanza",
                       "governance", "diccionario"),
        "seguridad": ("acceso", "permiso", "seguridad", "personal", "sensible",
                      "credencial", "security", "vpn"),
        "consumo": ("reporte", "tablero", "power bi", "dashboard", "usuario",
                    "licencia", "informe"),
        "operacion": ("soporte", "mantener", "documentación", "capacitación",
                      "entrega", "support", "handover"),
    }
    texto = " ".join(i.texto for i in intervenciones).lower()
    salida = []
    for a in areas(lang):
        menciones = [s for s in señales.get(a["clave"], ()) if s in texto]
        salida.append({**a, "menciones": len(menciones), "señales": menciones[:5]})
    return salida
