#!/usr/bin/env bash
# MV Project Management — script todo en uno (Linux/Mac).
set -euo pipefail

cmd="${1:-app}"

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
    uvicorn api.main:app --host "${MVPM_API_HOST:-127.0.0.1}" --port "${MVPM_API_PORT:-8600}"
    ;;
  test)
    pytest tests/ -v
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
    # Necesita MVPM_LICENSE_PRIVATE_KEY: el marcador es un token firmado, y sólo
    # el dueño tiene con qué firmarlo. Antes alcanzaba con crear el archivo, que
    # es lo mismo que decir que cualquier cliente se activaba el modo owner.
    if [ -z "${MVPM_LICENSE_PRIVATE_KEY:-}" ]; then
      echo "Falta MVPM_LICENSE_PRIVATE_KEY: sin la clave privada no se puede firmar"
      echo "el marcador de modo owner. Generá el par una sola vez con:"
      echo "    python packaging/generar_claves_licencia.py --escribir"
      echo "y después:"
      echo "    MVPM_LICENSE_PRIVATE_KEY=<tu-clave> ./run.sh owner"
      exit 1
    fi
    python3 -c "from mvpm import owner; print('Modo owner activado:', owner.activar())"
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
    echo "Uso: ./run.sh [install|app|api|test|portable|owner|owner-off]"
    exit 1
    ;;
esac
