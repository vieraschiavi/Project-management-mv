# © 2026 Martín Viera. Todos los derechos reservados.
"""Inventario de configuración: qué variable hace falta, para qué, y qué se
rompe si falta.

Nace de un problema concreto: las variables estaban documentadas en tres
lugares distintos (`owner/PUESTA_EN_PRODUCCION.md`, el manual en Word, y los
comentarios de cada módulo) y en ninguno estaba el inventario COMPLETO. Para
saber si faltaba algo había que leer los tres y cruzarlos a mano, así que la
respuesta a "¿está todo configurado?" era siempre una opinión.

Acá el inventario es dato: una lista, en un solo lugar, que
`revisar()` compara contra el entorno real y devuelve resuelta. `./run.sh
doctor` la imprime.

## Lo que este módulo NO hace

No guarda, no imprime y no compara VALORES de secretos. Sólo mira si la
variable está definida y si tiene contenido. Un módulo que imprimiera el valor
de `MVPM_LICENSE_PRIVATE_KEY` para "ayudar a verificar" sería exactamente la
forma de filtrarla: quedaría en la terminal, en el scrollback y en cualquier
log que alguien pegue en un chat pidiendo ayuda.

Para comprobar que la privada cargada es la del par correcto está
`packaging/generar_claves_licencia.py --verificar`, que corre en la máquina del
dueño y tampoco la imprime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

#: Dónde se carga el valor. No es decorativo: cada destino es un panel distinto
#: y el error más caro de esta configuración es cargar la variable correcta en
#: el lugar equivocado (p. ej. BLOB_READ_WRITE_TOKEN va en LOS DOS).
VERCEL = "Vercel · Settings → Environment Variables (scope Production)"
ACTIONS = "GitHub · Settings → Secrets and variables → Actions"
LOCAL = "Tu máquina · archivo .env"


@dataclass(frozen=True)
class Variable:
    nombre: str
    donde: str
    para_que: str
    si_falta: str
    #: True si sin esto NO se puede vender. El resto degrada, no bloquea.
    bloquea_venta: bool = False
    #: Un default razonable hace que "vacía" no sea un problema.
    tiene_default: bool = False


INVENTARIO: tuple[Variable, ...] = (
    # ---------------------------------------------------------------- cobro
    Variable("MP_ACCESS_TOKEN", VERCEL,
             "Cobrar con MercadoPago (Access token de producción, APP_USR-…).",
             "El checkout no puede cobrar: responde 503 medio_pago_no_configurado.",
             bloquea_venta=True),
    Variable("MP_CURRENCY", VERCEL, "Moneda del checkout.",
             "Usa el default (UYU).", tiene_default=True),
    Variable("MP_TASA_UYU", VERCEL, "Tipo de cambio de referencia del checkout.",
             "Usa el default (40).", tiene_default=True),

    # ------------------------------------------------------------ licencias
    Variable("MVPM_LICENSE_PRIVATE_KEY", VERCEL,
             "Firmar la licencia que recibe quien paga.",
             "QUIEN PAGUE RECIBE UN ERROR 500 EN VEZ DE SU LICENCIA.",
             bloquea_venta=True),
    Variable("MVPM_LICENSE_PUBLIC_KEY", VERCEL,
             "Pisar la pública embebida sin recompilar (rotación, pruebas).",
             "Usa la embebida en mvpm/licensing.py. Es lo normal.",
             tiene_default=True),

    # ------------------------------------------------- almacenamiento/panel
    Variable("BLOB_READ_WRITE_TOKEN", f"{VERCEL} + {ACTIONS}",
             "Guardar instalador, licencias canjeadas, pedidos de demo y métricas.",
             "/api/download-installer da 503 y /api/metricas no muestra nada. "
             "En Actions: el instalador se compila pero no se publica.",
             bloquea_venta=True),
    Variable("MVPM_OWNER_TOKEN", VERCEL,
             "Contraseña del tablero de ventas (/api/metricas).",
             "El panel del dueño queda cerrado (503 a propósito)."),

    # --------------------------------------------------------------- mails
    Variable("RESEND_API_KEY", VERCEL,
             "Mandar la licencia al cliente y los avisos al dueño.",
             "Todo se sigue registrando, pero no llega ningún correo."),
    Variable("DEMO_FROM_EMAIL", VERCEL,
             "Remitente de esos mails (dominio verificado en Resend).",
             "Sin dominio verificado Resend entrega SÓLO a tu propia casilla: "
             "el comprador paga y no recibe la licencia."),

    # ------------------------------------------------------------------ CI
    Variable("VERCEL_TOKEN", ACTIONS,
             "Que el botón «Rotar claves de licencia» cargue la privada en Vercel.",
             "Ese workflow no puede escribir la variable en Vercel."),
    Variable("VERCEL_PROJECT_ID", ACTIONS, "A qué proyecto de Vercel escribirle.",
             "Idem VERCEL_TOKEN."),
    Variable("VERCEL_TEAM_ID", ACTIONS, "A qué equipo de Vercel escribirle.",
             "Idem VERCEL_TOKEN."),

    # ------------------------------------------------------------------ IA
    Variable("ANTHROPIC_API_KEY", f"{VERCEL} / {LOCAL}",
             "Copiloto y asistente con Claude (ADITIVO).",
             "No se ofrece Claude. El motor de reglas funciona igual.",
             tiene_default=True),
    Variable("OPENAI_API_KEY", f"{VERCEL} / {LOCAL}",
             "Copiloto y asistente con ChatGPT (ADITIVO).",
             "No se ofrece ChatGPT. El motor de reglas funciona igual.",
             tiene_default=True),
    Variable("GEMINI_API_KEY", f"{VERCEL} / {LOCAL}",
             "Copiloto y asistente con Gemini (ADITIVO).",
             "No se ofrece Gemini. El motor de reglas funciona igual.",
             tiene_default=True),
    Variable("XAI_API_KEY", f"{VERCEL} / {LOCAL}",
             "Copiloto y asistente con Grok (ADITIVO).",
             "No se ofrece Grok. El motor de reglas funciona igual.",
             tiene_default=True),
    Variable("GITHUB_MODELS_TOKEN", f"{VERCEL} / {LOCAL}",
             "Copiloto y asistente con GitHub Models (ADITIVO).",
             "No se ofrece GitHub Models. El motor de reglas funciona igual.",
             tiene_default=True),

    # --------------------------------------------------------------- local
    Variable("MVPM_API_KEY", LOCAL,
             "Clave de la API de BI cuando se la expone fuera de 127.0.0.1.",
             "Sólo hace falta con MVPM_API_HOST=0.0.0.0. En local no se pide.",
             tiene_default=True),
)


def revisar(entorno: dict[str, str] | None = None) -> dict:
    """Compara el inventario contra el entorno. Nunca devuelve valores.

    `entorno` se inyecta para poder testear esto sin tocar el entorno real.
    """
    env = os.environ if entorno is None else entorno
    filas = []
    for v in INVENTARIO:
        puesta = bool((env.get(v.nombre) or "").strip())
        filas.append({
            "nombre": v.nombre,
            "configurada": puesta,
            "donde": v.donde,
            "para_que": v.para_que,
            "si_falta": v.si_falta,
            "bloquea_venta": v.bloquea_venta,
            "tiene_default": v.tiene_default,
        })
    faltan_criticas = [f["nombre"] for f in filas
                       if not f["configurada"] and f["bloquea_venta"]]
    faltan_opcionales = [f["nombre"] for f in filas
                         if not f["configurada"] and not f["bloquea_venta"]]
    return {
        "filas": filas,
        "faltan_criticas": faltan_criticas,
        "faltan_opcionales": faltan_opcionales,
        "puede_vender": not faltan_criticas,
        "total": len(filas),
        "configuradas": sum(1 for f in filas if f["configurada"]),
    }


def como_texto(entorno: dict[str, str] | None = None) -> str:
    """El informe que imprime `./run.sh doctor`."""
    r = revisar(entorno)
    lineas = [
        "MV Project Management — estado de configuración",
        "=" * 62,
        "",
        f"Variables configuradas en ESTE entorno: {r['configuradas']}/{r['total']}",
        "",
        "Nota: esto mira el entorno donde corre el comando. Las de Vercel y las",
        "de GitHub Actions viven en SUS paneles y acá van a figurar como",
        "faltantes aunque estén bien cargadas allá. Para el estado real de",
        "producción:  curl https://mv-project-management.vercel.app/api/estado-licencias",
        "",
    ]

    if r["faltan_criticas"]:
        lineas += ["BLOQUEAN LA VENTA — sin esto se cobra y no se entrega:", ""]
        for f in r["filas"]:
            if not f["configurada"] and f["bloquea_venta"]:
                lineas += [f"  [ ] {f['nombre']}",
                           f"        dónde : {f['donde']}",
                           f"        para  : {f['para_que']}",
                           f"        falta : {f['si_falta']}", ""]
    else:
        lineas += ["Ninguna variable crítica falta en este entorno.", ""]

    opcionales = [f for f in r["filas"]
                  if not f["configurada"] and not f["bloquea_venta"]]
    if opcionales:
        lineas += ["Opcionales sin configurar (el producto funciona igual):", ""]
        for f in opcionales:
            lineas.append(f"  [ ] {f['nombre']:<24} {f['si_falta']}")
        lineas.append("")

    puestas = [f["nombre"] for f in r["filas"] if f["configurada"]]
    if puestas:
        lineas += ["Configuradas acá: " + ", ".join(puestas), ""]

    lineas += [
        "Plantilla completa con de-dónde-sale-cada-valor:  .env.example",
        "Guía paso a paso:                                 owner/PUESTA_EN_PRODUCCION.md",
    ]
    return "\n".join(lineas)


if __name__ == "__main__":                                   # pragma: no cover
    print(como_texto())
