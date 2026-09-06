# © 2026 Martín Viera. Todos los derechos reservados.
"""Reuniones: de la transcripción a la minuta de quién dijo qué.

**De dónde sale el audio, dicho sin vueltas.** Un navegador NO puede capturar
el audio interno de Zoom, Teams, Meet o WebEx: el micrófono graba lo que entra
por el micrófono y nada más. Prometer "grabá tu videollamada desde acá" sería
mentir. Lo que sí existe, y es mejor, es que esas cuatro plataformas generan su
propia transcripción **con el nombre de cada orador**. Este módulo importa ese
archivo. La atribución no la adivina un modelo escuchando voces: viene del
propio Zoom, que sabe quién tenía el micrófono abierto.

Para la reunión presencial, donde no hay plataforma que transcriba, queda la
grabación del micrófono (`st.audio_input`) y las notas atribuidas a mano. Es
menos cómodo y se dice que lo es, en vez de simular una transcripción que no
tenemos con qué hacer.

**Lo que la minuta nunca hace: inventar.** Cada punto de la minuta es una
CITA TEXTUAL de una intervención real, con el nombre de quien la dijo. El
motor decide qué frases son decisión, compromiso o pregunta abierta con
reglas —verbos y giros—, no con un resumen generado. Un resumen que parafrasea
mal una decisión de directorio es peor que no tener minuta, y en una reunión
con un cliente eso se cobra caro.

La IA, si hay proveedor configurado, sirve para REPREGUNTAR (`mvpm/
relevamiento.py`), no para reescribir lo que alguien dijo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

LANGS = ("es", "en", "pt")

#: Formatos que sabemos leer. Los cuatro grandes exportan alguno de estos.
FORMATOS = ("vtt", "srt", "txt")


@dataclass(frozen=True)
class Intervencion:
    """Una cosa que dijo una persona, con el minuto en que la dijo."""
    orador: str
    texto: str
    segundo: float | None = None

    @property
    def marca(self) -> str:
        if self.segundo is None:
            return ""
        m, s = divmod(int(self.segundo), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


@dataclass
class Reunion:
    titulo: str
    cliente: str
    fecha: str
    intervenciones: list[Intervencion] = field(default_factory=list)
    #: De dónde salió: "vtt", "srt", "txt" o "manual".
    origen: str = "manual"


# --------------------------------------------------------------- parseo
#
# Tres formatos y un solo resultado. Se parsea a mano —sin dependencias— porque
# lo único que necesitamos de un WebVTT es el orador, el texto y el segundo de
# inicio; una librería de subtítulos traería un mundo de casos que no usamos.

_TIEMPO = re.compile(
    r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{1,3})\s*-->")
#: Teams envuelve al orador en `<v Nombre>texto</v>`; Zoom y Meet usan
#: `Nombre: texto`. Los dos aparecen en archivos .vtt del mundo real.
_VOZ_TEAMS = re.compile(r"<v\s+(?P<orador>[^>]+)>(?P<texto>.*?)</v>", re.S)
#: `Nombre: texto`, con el nombre acotado para no comerse una frase que
#: casualmente tenga dos puntos ("Entonces hicimos esto: lo otro").
_ORADOR_DOS_PUNTOS = re.compile(
    r"^\s*(?:\d{1,2}:\d{2}(?::\d{2})?\s+)?(?P<orador>[^:\n]{2,60}?)\s*:\s+(?P<texto>\S.*)$")

SIN_ORADOR = "?"


def _segundos(linea: str) -> float | None:
    m = _TIEMPO.search(linea)
    if not m:
        return None
    return (int(m["h"]) * 3600 + int(m["m"]) * 60 + int(m["s"])
            + int(m["ms"].ljust(3, "0")) / 1000)


def _limpiar(texto: str) -> str:
    """Saca etiquetas y espacios de más. Los .vtt traen `<c>`, `<i>` y
    similares que ensucian la cita."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", texto)).strip()


def detectar_formato(contenido: str) -> str:
    """Qué formato es, mirando SÓLO el contenido.

    El nombre del archivo no entra en la decisión a propósito: el usuario
    renombra, reenvía y pega, y un WebVTT guardado como .txt —o al revés— es
    de lo más común. Lo que manda es lo que tiene adentro."""
    cabeza = contenido.lstrip()[:200].upper()
    if cabeza.startswith("WEBVTT"):
        return "vtt"
    if _TIEMPO.search(contenido[:2000]):
        # Con `-->` pero sin cabecera: SRT, o un VTT al que le cortaron la
        # primera línea. Se distinguen por la coma decimal del SRT.
        return "srt" if re.search(r"\d{2},\d{3}\s*-->", contenido[:2000]) else "vtt"
    # Sin cabecera y sin marcas de tiempo es texto plano, se llame como se
    # llame el archivo. Acá había una vuelta a la extensión que contradecía lo
    # que promete la función: un texto pegado a mano y guardado como .vtt se
    # reportaba como subtítulo. No cambiaba el resultado del parseo —las dos
    # ramas leen `Nombre: texto`— pero sí el formato que se muestra y se
    # guarda como origen de la reunión, o sea que mentía en la ficha.
    return "txt"


def parsear(contenido: str) -> list[Intervencion]:
    """Transcripción → intervenciones, sea cual sea de los tres formatos.

    Une los tramos consecutivos del mismo orador: Zoom parte una frase en
    varios subtítulos de cinco segundos, y una minuta con la misma persona
    repetida ocho veces seguidas no la lee nadie."""
    formato = detectar_formato(contenido)
    crudas = (_parsear_txt(contenido) if formato == "txt"
              else _parsear_subtitulos(contenido))
    return _unir_consecutivas(crudas)


def _parsear_subtitulos(contenido: str) -> list[Intervencion]:
    salida: list[Intervencion] = []
    segundo: float | None = None
    for linea in contenido.splitlines():
        cruda = linea.rstrip()
        if not cruda.strip():
            continue
        if "-->" in cruda:
            segundo = _segundos(cruda)
            continue
        if cruda.strip().upper().startswith("WEBVTT") or cruda.strip().isdigit():
            continue

        m = _VOZ_TEAMS.search(cruda)
        if m:
            texto = _limpiar(m["texto"])
            if texto:
                salida.append(Intervencion(m["orador"].strip(), texto, segundo))
            continue

        limpia = _limpiar(cruda)
        if not limpia:
            continue
        m2 = _ORADOR_DOS_PUNTOS.match(limpia)
        if m2:
            salida.append(Intervencion(m2["orador"].strip(), m2["texto"].strip(),
                                       segundo))
        elif salida and salida[-1].segundo == segundo:
            # Continuación del mismo subtítulo, sin repetir el nombre.
            ultima = salida[-1]
            salida[-1] = Intervencion(ultima.orador,
                                      f"{ultima.texto} {limpia}".strip(),
                                      ultima.segundo)
        else:
            salida.append(Intervencion(SIN_ORADOR, limpia, segundo))
    return salida


def _parsear_txt(contenido: str) -> list[Intervencion]:
    salida: list[Intervencion] = []
    for linea in contenido.splitlines():
        limpia = _limpiar(linea)
        if not limpia:
            continue
        m = _ORADOR_DOS_PUNTOS.match(limpia)
        if m:
            salida.append(Intervencion(m["orador"].strip(), m["texto"].strip()))
        elif salida:
            ultima = salida[-1]
            salida[-1] = Intervencion(ultima.orador,
                                      f"{ultima.texto} {limpia}".strip(),
                                      ultima.segundo)
        else:
            salida.append(Intervencion(SIN_ORADOR, limpia))
    return salida


def _unir_consecutivas(items: list[Intervencion]) -> list[Intervencion]:
    unidas: list[Intervencion] = []
    for it in items:
        if unidas and unidas[-1].orador == it.orador:
            previa = unidas[-1]
            unidas[-1] = Intervencion(previa.orador,
                                      f"{previa.texto} {it.texto}".strip(),
                                      previa.segundo)
        else:
            unidas.append(it)
    return unidas


# ------------------------------------------------------------ quién habló

def participantes(intervenciones: list[Intervencion]) -> list[dict]:
    """Quién habló, cuánto, y en qué orden apareció.

    "Cuánto" en palabras y no en minutos a propósito: el segundo de inicio lo
    da el subtítulo, pero cuánto DURÓ cada intervención no está en el archivo,
    y estimarlo sería inventar un número que después alguien cita."""
    orden: list[str] = []
    acumulado: dict[str, dict] = {}
    for i in intervenciones:
        if i.orador not in acumulado:
            orden.append(i.orador)
            acumulado[i.orador] = {"orador": i.orador, "intervenciones": 0,
                                   "palabras": 0, "primera_marca": i.marca}
        acumulado[i.orador]["intervenciones"] += 1
        acumulado[i.orador]["palabras"] += len(i.texto.split())
    return [acumulado[o] for o in orden]


def quien_dijo_que(intervenciones: list[Intervencion],
                   orador: str) -> list[Intervencion]:
    return [i for i in intervenciones if i.orador == orador]


# --------------------------------------------------------------- minuta
#
# Reglas, no resumen generado. Cada punto de la minuta es una cita textual con
# nombre y minuto: se puede ir al audio y verificarla. Los verbos están en los
# tres idiomas porque una reunión con un cliente brasileño no se transcribe en
# español.

_SENIALES: dict[str, dict[str, tuple[str, ...]]] = {
    "decision": {
        "es": ("decidimos", "queda definido", "vamos a ir por", "se aprueba",
               "acordamos", "definimos", "queda cerrado", "optamos por"),
        "en": ("we decided", "it is decided", "we'll go with", "approved",
               "we agreed", "let's go with", "settled"),
        "pt": ("decidimos", "fica definido", "vamos com", "aprovado",
               "combinamos", "definimos"),
    },
    "compromiso": {
        "es": ("me encargo", "lo hago yo", "te lo mando", "queda a cargo",
               "para el lunes", "antes del", "me comprometo", "lo tengo listo"),
        "en": ("i'll take", "i will send", "i'm on it", "by monday",
               "before the", "i'll have it", "assigned to"),
        "pt": ("eu cuido", "eu mando", "fico responsável", "até segunda",
               "antes de", "eu faço"),
    },
    "riesgo": {
        "es": ("el problema es", "no vamos a llegar", "riesgo", "nos bloquea",
               "depende de", "no tenemos", "falta"),
        "en": ("the problem is", "we won't make", "risk", "blocks us",
               "depends on", "we don't have", "missing"),
        "pt": ("o problema é", "não vamos chegar", "risco", "nos bloqueia",
               "depende de", "não temos", "falta"),
    },
    "pregunta_abierta": {
        "es": ("hay que averiguar", "no sé", "habría que ver", "queda pendiente",
               "lo confirmo", "tengo que consultar"),
        "en": ("we need to find out", "i don't know", "we should check",
               "pending", "i'll confirm", "i need to ask"),
        "pt": ("temos que averiguar", "não sei", "teria que ver", "fica pendente",
               "vou confirmar", "preciso consultar"),
    },
}

TIPOS = tuple(_SENIALES)


def clasificar(texto: str) -> list[str]:
    """Qué señales trae una frase. Puede traer más de una: "el problema es que
    no llegamos, así que me encargo yo" es riesgo Y compromiso."""
    bajo = texto.lower()
    return [tipo for tipo, por_idioma in _SENIALES.items()
            if any(s in bajo for idioma in por_idioma.values() for s in idioma)]


def minuta(intervenciones: list[Intervencion]) -> list[dict]:
    """Los puntos de la minuta: cita textual + quién + minuto + qué tipo.

    Se corta la cita en la oración que disparó la señal y no en la
    intervención entera: una intervención de dos minutos citada completa no es
    una minuta, es la transcripción otra vez."""
    puntos: list[dict] = []
    for i in intervenciones:
        for oracion in _oraciones(i.texto):
            tipos = clasificar(oracion)
            if tipos:
                puntos.append({
                    "orador": i.orador,
                    "marca": i.marca,
                    "cita": oracion.strip(),
                    "tipos": tipos,
                })
    return puntos


def _oraciones(texto: str) -> list[str]:
    partes = re.split(r"(?<=[.!?])\s+", texto)
    return [p for p in partes if p.strip()]


def por_tipo(puntos: list[dict], tipo: str) -> list[dict]:
    return [p for p in puntos if tipo in p["tipos"]]


def resumen(reunion: Reunion) -> dict:
    """Los números de la reunión. Todos contados, ninguno estimado."""
    puntos = minuta(reunion.intervenciones)
    return {
        "titulo": reunion.titulo,
        "cliente": reunion.cliente,
        "fecha": reunion.fecha,
        "origen": reunion.origen,
        "intervenciones": len(reunion.intervenciones),
        "participantes": len(participantes(reunion.intervenciones)),
        "puntos": len(puntos),
        "por_tipo": {t: len(por_tipo(puntos, t)) for t in TIPOS},
        "sin_atribuir": sum(1 for i in reunion.intervenciones
                            if i.orador == SIN_ORADOR),
    }
