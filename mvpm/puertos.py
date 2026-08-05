"""Elección del puerto del dashboard, sin pisarle el puerto a otra aplicación.

El programa se abre de cuatro formas (el `.exe` del instalador, el `.bat`
portable, `./run.sh app` y la ventana de Electron) y cada una elegía el puerto
por su cuenta:

* el `.bat` no pasaba puerto, así que Streamlit tomaba su 8501 por defecto —
  el más ocupado de todos, porque lo usa cualquier otra app de Streamlit;
* `./run.sh app` tenía 8501 fijo;
* el `.exe` buscaba puerto con `connect_ex()`, que **da falsos negativos**: si
  otra aplicación tiene el puerto reservado pero todavía no acepta conexiones
  (la ventana de arranque de cualquier servidor), `connect_ex` devuelve
  "conexión rechazada" y el puerto se daba por libre. Streamlit después moría
  con `Address already in use` y el usuario veía una ventana que se cerraba
  sola.

Acá se decide una sola vez, y la prueba es **bindear de verdad**: si el
sistema operativo deja abrir el puerto, está libre; si no, no. Es la misma
operación que va a hacer Streamlit un instante después, así que no hay forma
de que una diga una cosa y la otra, otra.
"""

from __future__ import annotations

import contextlib
import socket

#: Puertos propios, fuera de los rangos que usa el resto del mundo. Se
#: prefieren a uno al azar para que la URL sea estable entre sesiones (el
#: usuario puede dejarla en favoritos). 8501 queda deliberadamente afuera: es
#: el default de Streamlit y por eso el más disputado.
PUERTOS_PREFERIDOS = (8731, 8742, 8753, 8764)

#: Lo mismo para la API de BI, que hasta acá tenía 8600 clavado en `run.sh`.
#: 8600 no es un puerto reservado de nadie, pero "no es de nadie" no es lo
#: mismo que "está libre": si el usuario ya tiene algo escuchando ahí (otra
#: API local, un túnel, un contenedor), uvicorn moría con `Address already in
#: use` y Power BI se quedaba sin origen de datos sin explicación. Se mantiene
#: 8600 como primera opción para no invalidar los `.pbids` ya repartidos, y se
#: agregan alternativas para cuando esté tomado.
PUERTOS_API_PREFERIDOS = (8600, 8611, 8622, 8633)

HOST = "127.0.0.1"


def esta_libre(puerto: int, host: str = HOST) -> bool:
    """¿Se puede abrir un servidor en este puerto, ahora?

    Se comprueba bindeando, no conectando. `connect_ex` sólo detecta puertos
    que ya están ACEPTANDO conexiones; un puerto reservado por otro proceso que
    todavía no llama a `listen()` le parece libre, y ahí es donde se rompía.
    """
    # Fuera de rango no es "ocupado", es inválido — pero para quien pregunta el
    # efecto es el mismo: no se puede abrir ahí. Se filtra antes de bindear
    # porque `bind()` con un número absurdo lanza OverflowError, no OSError, y
    # eso reventaba el arranque en vez de caer al puerto siguiente (pasa con un
    # MVPM_PORT mal tipeado).
    if not (1 <= int(puerto) <= 65535):
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Sin SO_REUSEADDR a propósito: con esa opción, en Linux dos procesos
        # pueden bindear el mismo puerto en estados TIME_WAIT y el chequeo
        # diría "libre" para un puerto que Streamlit no va a poder usar.
        try:
            s.bind((host, puerto))
            return True
        except OSError:
            return False


def elegir(preferidos: tuple[int, ...] = PUERTOS_PREFERIDOS, host: str = HOST) -> int:
    """Devuelve un puerto libre: el primero de la lista que lo esté, o uno que
    asigne el sistema operativo si están todos ocupados.

    Queda una ventana mínima entre este chequeo y el momento en que Streamlit
    bindea (otra aplicación podría ganar de mano en ese milisegundo). Es
    inevitable sin pasarle el socket ya abierto al servidor, que Streamlit no
    admite; por eso quien arranca debería reintentar — ver `elegir_con_reintento`.
    """
    for puerto in preferidos:
        if esta_libre(puerto, host):
            return puerto
    return _puerto_del_sistema(host)


def elegir_con_reintento(intentos: int = 3, host: str = HOST,
                         preferidos: tuple[int, ...] = PUERTOS_PREFERIDOS) -> int:
    """Igual que `elegir()`, pero descarta el candidato si dejó de estar libre
    entre que se eligió y que se verificó. Cierra la carrera de la que habla
    `elegir()` para el caso realista: otra app arrancando al mismo tiempo.
    """
    descartados: set[int] = set()
    for _ in range(max(1, intentos)):
        disponibles = tuple(p for p in preferidos if p not in descartados)
        puerto = elegir(disponibles, host)
        if esta_libre(puerto, host):
            return puerto
        descartados.add(puerto)
    return _puerto_del_sistema(host)


def elegir_con_reintento_api(intentos: int = 3, host: str = HOST) -> int:
    """El puerto de la API de BI. Lista propia para que dashboard y API no se
    peleen el mismo número cuando arrancan juntos."""
    return elegir_con_reintento(intentos, host, PUERTOS_API_PREFERIDOS)


def _puerto_del_sistema(host: str = HOST) -> int:
    """Un puerto efímero que el sistema garantiza libre en este instante."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def desde_entorno(valor: str | None, host: str = HOST) -> int:
    """Resuelve el puerto pedido por `MVPM_PORT`/`PORT`, con red de seguridad.

    Se respeta lo que pidió quien arranca (Electron necesita saber de antemano
    a qué puerto apuntar su ventana), pero si ese puerto está ocupado se elige
    otro en vez de morir: más vale abrir en otro puerto que no abrir.
    """
    if valor:
        with contextlib.suppress(ValueError):
            pedido = int(valor)
            if esta_libre(pedido, host):
                return pedido
    return elegir_con_reintento(host=host)


if __name__ == "__main__":
    # Lo usan MV_ProjectManagement.bat y run.sh: imprimen esto y se lo pasan a
    # Streamlit. Un único lugar donde se decide, para las cuatro formas de abrir.
    # Con `--api` devuelve el de la API de BI, que tiene su propia lista para no
    # rifarle a uvicorn un puerto que el dashboard podría estar por tomar.
    import sys as _sys

    if "--api" in _sys.argv[1:]:
        print(elegir_con_reintento_api())
    else:
        print(elegir_con_reintento())
