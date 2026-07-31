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
    streamlit run app/app.py --server.port "${PORT:-8501}"
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
  *)
    echo "Uso: ./run.sh [install|app|api|test|portable]"
    exit 1
    ;;
esac
