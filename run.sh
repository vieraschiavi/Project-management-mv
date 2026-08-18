#!/usr/bin/env bash
# MV Project Management — script todo en uno (Linux/Mac).
set -euo pipefail

cmd="${1:-app}"

# `install` crea .venv y mete ahí las dependencias, pero el `source` de esa
# rama muere con el proceso del script: los demás comandos volvían a arrancar
# con el Python del SISTEMA, donde nada de eso está instalado. O sea que el
# flujo documentado —`./run.sh install` y después `./run.sh app`— fallaba en
# una máquina limpia: `streamlit: command not found` en app/api, y
# `ModuleNotFoundError` en test (el pytest del PATH no ve `cryptography`).
# Activarlo acá arriba hace que todos los comandos usen el mismo intérprete
# que `install` preparó. Si no hay .venv, se sigue con el del sistema.
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

case "$cmd" in
  install)
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ;;
  app)
    # Sin PORT explícito se elige uno libre en vez de asumir 8501 (el default
    # de Streamlit, y por eso el más disputado: cualquier otra app de Streamlit
    # abierta lo tiene). mvpm/puertos.py decide, igual que el .exe y el .bat.
    PUERTO="${PORT:-$(python3 -m mvpm.puertos)}"
    echo "Abriendo el dashboard en http://localhost:${PUERTO}"
    streamlit run app/app.py --server.port "${PUERTO}"
    ;;
  api)
    # 127.0.0.1 por defecto: esta API sirve el portafolio completo del cliente
    # y antes escuchaba en 0.0.0.0, o sea que cualquiera en la misma red la
    # podía leer sin credenciales. Para exponerla a propósito (Power BI desde
    # otra máquina): MVPM_API_HOST=0.0.0.0 y además MVPM_API_KEY=<clave>, que
    # api/main.py exige para todo pedido que no venga de esta misma máquina.
    # El puerto sale de mvpm/puertos.py igual que el del dashboard: 8600 sigue
    # siendo el primero (para no invalidar los .pbids ya repartidos) pero si
    # está tomado se elige otro en vez de morir con "Address already in use".
    API_PUERTO="${MVPM_API_PORT:-$(python3 -m mvpm.puertos --api)}"
    echo "API de BI en http://127.0.0.1:${API_PUERTO}"
    uvicorn api.main:app --host "${MVPM_API_HOST:-127.0.0.1}" --port "${API_PUERTO}"
    ;;
  mcp)
    # Servidor MCP del portafolio: lo arranca un cliente MCP (Claude Code), no
    # una persona. Habla JSON-RPC por stdout, así que esta rama NO puede
    # imprimir nada — un solo `echo` acá corrompe el stream y el cliente ve el
    # servidor como caído. `exec` reemplaza el proceso para que el cliente le
    # pueda mandar señales al Python directamente.
    exec python3 -m mvpm.mcp_server
    ;;
  test)
    pytest tests/ -v
    ;;
  ci)
    # LAS MISMAS compuertas que corre GitHub Actions, en el mismo orden
    # (.github/workflows/tests.yml). Correr sólo `./run.sh test` deja pasar dos
    # cosas que en el PR salen en rojo:
    #
    #   1. ruff. La suite puede estar verde y el linter voltear el build igual
    #      (pasó con cuatro E741 por usar `l` de variable).
    #   2. Los tests de las funciones de pago, que son de Node y pytest no ve.
    #
    # Si esto pasa, el PR pasa. Se corta en el primer fallo: el segundo error
    # suele ser consecuencia del primero.
    set -e
    echo "── ruff ─────────────────────────────────────────────"
    ruff check .
    echo "── pytest ───────────────────────────────────────────"
    pytest tests/ -q
    echo "── tests de pago (Node) ─────────────────────────────"
    if command -v node > /dev/null; then
      for t in tests/test_verify_payment.js tests/test_licencias.js tests/test_checkout.js; do
        echo "  $t"; node "$t"
      done
    else
      echo "  (node no está instalado: CI sí los corre)"
    fi
    echo
    echo "Todo verde. Esto es lo mismo que va a correr el PR."
    ;;
  portable)
    python3 packaging/build_release.py
    ;;
  owner)
    # Marca ESTA máquina como la del dueño: el programa corre sin el candado de
    # la prueba de 7 días, se abra como se abra (run.sh, .bat, .exe, streamlit
    # directo). Escribe un archivo en los datos del usuario, no en el repo, así
    # que no hay forma de que se cuele en un ZIP o instalador de cliente.
    #
    # El marcador es un token firmado y sólo el dueño tiene con qué firmarlo
    # (antes alcanzaba con crear el archivo, o sea que cualquier cliente se
    # activaba el modo owner). packaging/activar_owner.py resuelve la clave
    # solo: variable de entorno, o el archivo donde la dejó la primera vez, o
    # la genera si esto es un checkout del repo. Un doble clic, una sola vez.
    python3 packaging/activar_owner.py
    ;;
  owner-off)
    python3 -c "
from mvpm import owner
borrados = owner.desactivar()
print('Modo owner desactivado. Marcadores borrados:', borrados or 'ninguno')
print('Esta instalación vuelve a comportarse como la de un cliente (prueba + licencia).')
"
    ;;
  *)
    echo "Uso: ./run.sh [install|app|api|mcp|test|ci|portable|owner|owner-off]"
    exit 1
    ;;
esac
