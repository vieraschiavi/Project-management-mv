# © 2026 Martín Viera. Todos los derechos reservados.
"""Las dos formas de instalar el producto, y en cuál estás parado ahora.

El caso real que esto resuelve: una consultora trabaja para un cliente, y la
PC donde se instala no siempre es la misma persona jurídica que el dueño del
dato. Hay dos formas, y confundirlas cuesta caro en direcciones opuestas:

  · **local** — una persona, una PC, el dato en esa PC. Nadie más entra:
    escucha SÓLO en 127.0.0.1. Es la instalación normal y es el default.

  · **servidor** — el programa corre en una máquina del cliente (una VM
    suya) y varias personas entran por el navegador. El dato se queda del
    lado del cliente y nunca toca la laptop de la consultora. Escuchar en la
    red es una decisión EXPLÍCITA, no algo que pase por omisión.

Por qué el default cambió a 127.0.0.1: Streamlit, sin `server.address`,
escucha en TODAS las interfaces. O sea que la instalación "normal" en una
laptop corporativa quedaba publicada a la red de la oficina, con el login de
la app como única puerta — mientras la API de BI, al lado, ya venía cerrada a
loopback y pidiendo clave desde otra IP. Eran dos criterios distintos para el
mismo riesgo, y el más expuesto era el que nadie había elegido.

Este módulo no arranca nada: describe los modos, dice en cuál estás, y avisa
qué falta para que el modo elegido sea seguro. Quien arranca es `run.sh` (y
`packaging/mvpm_launcher.py` en el .exe).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

LANGS = ("es", "en", "pt")

LOCAL = "local"
SERVIDOR = "servidor"
MODOS = (LOCAL, SERVIDOR)

#: Lo que escucha cada modo. `local` es la única dirección que no sale de la
#: máquina; cualquier otra cosa es exponer, y por eso el modo servidor pide
#: cosas que el local no.
HOST_LOCAL = "127.0.0.1"
HOST_TODAS = "0.0.0.0"  # noqa: S104 — es el punto del modo servidor, declarado


@dataclass(frozen=True)
class Modo:
    clave: str
    #: Textos por idioma. Van juntos para que una traducción no quede vieja.
    nombre: dict
    para_que: dict
    datos: dict
    quien_entra: dict
    exige: dict


_MODOS: dict[str, Modo] = {
    LOCAL: Modo(
        clave=LOCAL,
        nombre={"es": "Instalación normal (una PC)",
                "en": "Normal install (one PC)",
                "pt": "Instalação normal (um PC)"},
        para_que={
            "es": "Una persona, su propia máquina. Es el modo por defecto y el "
                  "que instala el .exe: doble clic y se abre en el navegador de "
                  "esa PC.",
            "en": "One person, their own machine. It is the default mode and the "
                  "one the .exe installs: double-click and it opens in that PC's "
                  "browser.",
            "pt": "Uma pessoa, a própria máquina. É o modo padrão e o que o .exe "
                  "instala: duplo clique e abre no navegador daquele PC."},
        datos={
            "es": "En esa misma PC, en la carpeta del usuario. No sale a ningún "
                  "lado.",
            "en": "On that same PC, in the user's folder. It goes nowhere.",
            "pt": "Nesse mesmo PC, na pasta do usuário. Não sai para lugar nenhum."},
        quien_entra={
            "es": "Sólo quien esté sentado en esa máquina: escucha en 127.0.0.1, "
                  "así que desde otra PC de la red no se llega ni sabiendo la "
                  "contraseña.",
            "en": "Only whoever is sitting at that machine: it listens on "
                  "127.0.0.1, so from another PC on the network you cannot reach "
                  "it even knowing the password.",
            "pt": "Só quem estiver naquela máquina: escuta em 127.0.0.1, então de "
                  "outro PC da rede não se chega nem sabendo a senha."},
        exige={"es": "Nada. Es el default.",
               "en": "Nothing. It is the default.",
               "pt": "Nada. É o padrão."},
    ),
    SERVIDOR: Modo(
        clave=SERVIDOR,
        nombre={"es": "Servidor / VM del cliente",
                "en": "Client server / VM",
                "pt": "Servidor / VM do cliente"},
        para_que={
            "es": "El programa corre en una máquina del cliente y el equipo entra "
                  "por el navegador. Es el modo para cuando el área de seguridad "
                  "del cliente no acepta que su dato viva en la laptop de un "
                  "proveedor.",
            "en": "The program runs on a client machine and the team connects "
                  "through the browser. It is the mode for when the client's "
                  "security team will not accept their data living on a vendor's "
                  "laptop.",
            "pt": "O programa roda numa máquina do cliente e a equipe entra pelo "
                  "navegador. É o modo para quando a área de segurança do cliente "
                  "não aceita que o dado dela viva no notebook de um fornecedor."},
        datos={
            "es": "En la VM del cliente, y sólo ahí. La laptop de la consultora "
                  "nunca guarda una fila: entra por el navegador y ve, no copia.",
            "en": "On the client's VM, and only there. The consultancy's laptop "
                  "never stores a row: it connects through the browser and looks, "
                  "it does not copy.",
            "pt": "Na VM do cliente, e só ali. O notebook da consultoria nunca "
                  "guarda uma linha: entra pelo navegador e vê, não copia."},
        quien_entra={
            "es": "Quien tenga cuenta Y alcance la máquina por red. El login de la "
                  "app pasa a ser la única puerta, así que las contraseñas dejan de "
                  "ser un trámite.",
            "en": "Whoever has an account AND can reach the machine over the "
                  "network. The app's login becomes the only door, so passwords "
                  "stop being a formality.",
            "pt": "Quem tiver conta E alcançar a máquina pela rede. O login do app "
                  "passa a ser a única porta, então as senhas deixam de ser "
                  "formalidade."},
        exige={
            "es": "Elegirlo a propósito (MVPM_MODO_INSTALACION=servidor) y, si se "
                  "va a usar la API de BI desde otra máquina, MVPM_API_KEY.",
            "en": "Choosing it on purpose (MVPM_MODO_INSTALACION=servidor) and, if "
                  "the BI API will be used from another machine, MVPM_API_KEY.",
            "pt": "Escolhê-lo de propósito (MVPM_MODO_INSTALACION=servidor) e, se a "
                  "API de BI for usada de outra máquina, MVPM_API_KEY."},
    ),
}

#: La variable que elige el modo. Se llama así de largo a propósito: no es algo
#: que alguien deba poder poner sin querer.
VAR_MODO = "MVPM_MODO_INSTALACION"

for _m in _MODOS.values():
    for _campo in ("nombre", "para_que", "datos", "quien_entra", "exige"):
        _faltan = set(LANGS) - set(getattr(_m, _campo))
        assert not _faltan, f"{_m.clave}.{_campo} sin traducir a {_faltan}"


def modo_actual(entorno: dict[str, str] | None = None) -> str:
    """El modo en el que está esta instalación.

    Cualquier valor que no sea exactamente `servidor` cae en `local`: ante la
    duda, la opción cerrada. Un typo en la variable no puede terminar
    publicando el tablero en la red del cliente."""
    env = os.environ if entorno is None else entorno
    valor = (env.get(VAR_MODO) or "").strip().lower()
    return SERVIDOR if valor == SERVIDOR else LOCAL


def host_para(modo: str) -> str:
    """En qué interfaz escucha el dashboard según el modo."""
    return HOST_TODAS if modo == SERVIDOR else HOST_LOCAL


def describir(modo: str, lang: str = "es") -> dict:
    lang = lang if lang in LANGS else "es"
    m = _MODOS[modo if modo in _MODOS else LOCAL]
    return {
        "clave": m.clave,
        "host": host_para(m.clave),
        "nombre": m.nombre[lang],
        "para_que": m.para_que[lang],
        "datos": m.datos[lang],
        "quien_entra": m.quien_entra[lang],
        "exige": m.exige[lang],
    }


def catalogo(lang: str = "es") -> list[dict]:
    """Los dos modos, para mostrarlos uno al lado del otro."""
    return [describir(clave, lang) for clave in MODOS]


def revisar(entorno: dict[str, str] | None = None) -> dict:
    """Qué le falta a ESTA máquina para que su modo sea seguro.

    Devuelve avisos, nunca valores: igual que `mvpm/configuracion.py`, acá no
    se imprime el contenido de ninguna variable."""
    env = dict(os.environ if entorno is None else entorno)
    modo = modo_actual(env)
    avisos: list[str] = []

    if modo == SERVIDOR:
        # La API de BI ya se niega a responder desde otra IP sin clave, pero si
        # alguien la abrió a la red sin ponerla, se entera recién cuando Power
        # BI recibe un 401 y nadie sabe por qué.
        if (env.get("MVPM_API_HOST") or "").strip() == HOST_TODAS and \
                not (env.get("MVPM_API_KEY") or "").strip():
            avisos.append(
                "La API de BI está abierta a la red (MVPM_API_HOST=0.0.0.0) sin "
                "MVPM_API_KEY: va a rechazar todo pedido que no venga de la propia "
                "máquina.")
        avisos.append(
            "Modo servidor: el login de la app es la única puerta. Revisá que no "
            "haya cuentas de prueba y que las contraseñas no sean las de la demo.")
    else:
        if (env.get("MVPM_API_HOST") or "").strip() == HOST_TODAS:
            avisos.append(
                "Instalación normal con la API de BI abierta a la red "
                "(MVPM_API_HOST=0.0.0.0): o es un descuido, o el modo que "
                "corresponde es 'servidor'.")

    return {
        "modo": modo,
        "host_dashboard": host_para(modo),
        "expuesto_en_red": modo == SERVIDOR,
        "avisos": avisos,
    }


def como_texto(entorno: dict[str, str] | None = None, lang: str = "es") -> str:
    """Informe para la terminal — lo que imprime `./run.sh doctor`."""
    r = revisar(entorno)
    d = describir(r["modo"], lang)
    lineas = [
        "Modo de instalación",
        "===================",
        f"  Modo      : {d['nombre']}  [{r['modo']}]",
        f"  Escucha en: {r['host_dashboard']}"
        + ("  (accesible desde la red)" if r["expuesto_en_red"]
           else "  (sólo esta máquina)"),
        f"  Los datos : {d['datos']}",
        f"  Entra     : {d['quien_entra']}",
    ]
    if r["avisos"]:
        lineas.append("")
        lineas.append("  Avisos:")
        lineas += [f"    - {a}" for a in r["avisos"]]
    return "\n".join(lineas)


if __name__ == "__main__":
    print(como_texto())
