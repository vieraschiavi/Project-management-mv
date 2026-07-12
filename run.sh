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
    uvicorn api.main:app --host 0.0.0.0 --port "${MVPM_API_PORT:-8600}"
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
