# © 2026 Martín Viera. Todos los derechos reservados.
"""Baja el portafolio a CSV para abrirlo con Tableau.

Por qué un exportador y no un `.tds` de un clic como el `.pbids` de Power BI:
Power BI trae un conector Web nativo que un `.pbids` puede apuntar a una URL,
así que ese archivo funciona solo. Tableau no tiene equivalente para una API
REST arbitraria —lo que había (Web Data Connector 1.x/2.x) quedó discontinuado,
y el reemplazo exige empaquetar y firmar un conector—, así que el camino que
efectivamente anda es dejar los datos en archivos que Tableau abre de fábrica.

Se usa `?format=csv`, que la API ya sirve como CSV crudo, en vez de convertir
el JSON acá: así el formato que consume Tableau es el mismo que la API declara
y no hay dos conversiones que puedan discrepar.

Uso, con la API levantada (`./run.sh api`):

    python distribucion/tableau/exportar_para_tableau.py [carpeta_destino]

Escribe un CSV por tabla y un `manifiesto.json` con qué se bajó y de dónde.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8600"
TIMEOUT = 60

# Las 6 tablas del portafolio, las mismas que sirve `exporters.portfolio_tables`
# y que carga el `.pbids` de Power BI.
TABLAS = ["proyectos", "tareas", "equipo", "salud", "backlog_priorizado", "politicas"]

VERDE, ROJO, GRIS, FIN = "\033[92m", "\033[91m", "\033[90m", "\033[0m"
OK, FALLA = f"{VERDE}✓{FIN}", f"{ROJO}✗{FIN}"


def bajar_csv(tabla: str, base: str = BASE) -> str:
    """El CSV crudo de una tabla, tal cual lo sirve la API."""
    url = f"{base}/api/{tabla}?format=csv"
    req = urllib.request.Request(url, headers={"Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} en {url}")
        tipo = r.headers.get("content-type", "")
        cuerpo = r.read().decode("utf-8")
    if not tipo.startswith("text/csv"):
        raise RuntimeError(f"{url} respondió {tipo!r}, no text/csv")
    if cuerpo.startswith('"') or "\\n" in cuerpo[:200]:
        # El mismo defecto que ya cazó el verificador de Power BI: CSV
        # serializado como JSON entra en Tableau como una sola columna.
        raise RuntimeError(f"{url} devolvió el CSV envuelto como JSON")
    return cuerpo


def exportar(destino: Path, base: str = BASE) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    manifiesto = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "origen": base,
        "tablas": [],
    }
    for tabla in TABLAS:
        cuerpo = bajar_csv(tabla, base)
        filas = list(csv.reader(io.StringIO(cuerpo)))
        archivo = destino / f"{tabla}.csv"
        archivo.write_text(cuerpo, encoding="utf-8-sig")
        manifiesto["tablas"].append({
            "tabla": tabla,
            "archivo": archivo.name,
            "endpoint": f"/api/{tabla}",
            "filas": max(0, len(filas) - 1),
            "columnas": filas[0] if filas else [],
        })
    (destino / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifiesto


def main(argv: list[str]) -> int:
    destino = Path(argv[1]) if len(argv) > 1 else Path("dist/tableau")
    print(f"\nBajando el portafolio desde {BASE} a {destino}/\n")
    try:
        urllib.request.urlopen(f"{BASE}/health", timeout=TIMEOUT)
    except urllib.error.URLError as e:
        print(f"  {FALLA} la API no responde en {BASE} ({e.reason})")
        print(f"\n  {GRIS}Levantala primero:  ./run.sh api{FIN}\n")
        return 1

    try:
        manifiesto = exportar(destino)
    except (RuntimeError, urllib.error.URLError) as e:
        print(f"  {FALLA} {e}\n")
        return 1

    for t in manifiesto["tablas"]:
        print(f"  {OK} {t['archivo']:26s} {GRIS}{t['filas']} filas × "
              f"{len(t['columnas'])} columnas{FIN}")
    print(f"\n  {VERDE}Listo.{FIN} En Tableau: Conectar → Archivo de texto → "
          f"elegí un CSV de {destino}/\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
