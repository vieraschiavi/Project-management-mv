"""Verifica, de punta a punta, que Power BI va a poder leer este portafolio.

Hace exactamente lo que hace el conector Web de Power BI —un GET HTTP a cada
URL de los `.pbids` y parseo del resultado— y dice qué salió bien y qué no,
ANTES de que el consultor abra Power BI. Si algo falla, el mensaje dice qué
arreglar; si todo pasa, la conexión está garantizada.

Se corre desde la carpeta del programa, con la API ya levantada (`./run.sh api`):

    python distribucion/powerbi/verificar_conexion.py

No necesita Power BI instalado ni Windows: es el mismo pedido HTTP.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8600"
CARPETA = Path(__file__).resolve().parent
TIMEOUT = 30

VERDE, ROJO, GRIS, FIN = "\033[92m", "\033[91m", "\033[90m", "\033[0m"
OK, FALLA = f"{VERDE}✓{FIN}", f"{ROJO}✗{FIN}"


def _get(url: str) -> tuple[int, str, str]:
    """Devuelve (código, content-type, cuerpo). Igual que el conector Web."""
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.headers.get("content-type", ""), r.read().decode("utf-8")


def urls_del_pbids(archivo: Path) -> list[str]:
    """Las URLs que Power BI va a abrir al hacer doble clic en ese .pbids.

    Se leen del archivo en vez de escribirlas acá: si alguien agrega una
    conexión al .pbids y se olvida de probarla, este verificador la prueba igual.
    """
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return [c["details"]["address"]["url"] for c in datos["connections"]]


def verificar_json(url: str) -> tuple[bool, str]:
    try:
        codigo, tipo, cuerpo = _get(url)
    except urllib.error.URLError as e:
        return False, (f"no responde ({e.reason}). ¿Levantaste la API con "
                       f"`./run.sh api`?")
    if codigo != 200:
        return False, f"HTTP {codigo}"
    try:
        datos = json.loads(cuerpo)
    except json.JSONDecodeError as e:
        return False, f"la respuesta no es JSON válido: {e}"
    if not isinstance(datos, list):
        return True, "objeto JSON (no es una tabla, no se carga como tal)"
    if not datos:
        return True, "0 filas — la tabla existe pero está vacía todavía"
    columnas = list(datos[0].keys())
    return True, f"{len(datos)} filas × {len(columnas)} columnas · {', '.join(columnas[:4])}…"


def verificar_csv(url: str) -> tuple[bool, str]:
    """El `?format=csv` que usan Tableau/Excel.

    Se afirma que el cuerpo es CSV CRUDO: iba envuelto como texto JSON (entre
    comillas y con los saltos escapados) pero rotulado `text/csv`, así que
    cualquier parser leía una sola columna y cero filas.
    """
    try:
        codigo, tipo, cuerpo = _get(url + "?format=csv")
    except urllib.error.URLError as e:
        return False, f"no responde ({e.reason})"
    if codigo != 200:
        return False, f"HTTP {codigo}"
    if not tipo.startswith("text/csv"):
        return False, f"content-type inesperado: {tipo}"
    if cuerpo.startswith('"') or "\\n" in cuerpo[:200]:
        return False, "viene serializado como JSON, no es CSV crudo"
    filas = list(csv.reader(io.StringIO(cuerpo)))
    if len(filas) < 1 or len(filas[0]) < 2:
        return False, f"no se parsea como tabla (columnas leídas: {len(filas[0]) if filas else 0})"
    return True, f"{len(filas) - 1} filas × {len(filas[0])} columnas"


def main() -> int:
    print(f"\nVerificando la conexión de BI contra {BASE}\n")

    try:
        codigo, _, _ = _get(f"{BASE}/health")
        print(f"  {OK} la API responde (/health → {codigo})")
    except urllib.error.URLError as e:
        print(f"  {FALLA} la API no responde en {BASE} ({e.reason})")
        print(f"\n  {GRIS}Levantala primero:  ./run.sh api{FIN}\n")
        return 1

    fallos = 0
    for pbids in sorted(CARPETA.glob("*.pbids")):
        print(f"\n  {pbids.name}")
        for url in urls_del_pbids(pbids):
            ruta = url.replace(BASE, "")
            ok_json, det_json = verificar_json(url)
            print(f"    {OK if ok_json else FALLA} JSON  {ruta:26s} {GRIS}{det_json}{FIN}")
            fallos += not ok_json

            ok_csv, det_csv = verificar_csv(url)
            print(f"    {OK if ok_csv else FALLA} CSV   {ruta:26s} {GRIS}{det_csv}{FIN}")
            fallos += not ok_csv

    print()
    if fallos:
        print(f"  {ROJO}{fallos} verificación(es) fallaron — Power BI no va a poder "
              f"cargar esas tablas.{FIN}\n")
        return 1
    print(f"  {VERDE}Todo listo.{FIN} Doble clic en cualquiera de los .pbids de esta "
          f"carpeta y Power BI carga las tablas.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
