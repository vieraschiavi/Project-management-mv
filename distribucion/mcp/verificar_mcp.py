# © 2026 Martín Viera. Todos los derechos reservados.
"""Verifica que los servidores MCP declarados en `.mcp.json` realmente andan.

Hace lo mismo que hace un cliente MCP —levanta el proceso y habla el protocolo
de verdad: `initialize`, `notifications/initialized`, `tools/list`— y dice
cuántas herramientas expone cada uno, o con qué error se murió.

Los servidores se leen del `.mcp.json`, no se escriben acá: si se agrega uno y
nadie lo prueba, este verificador lo prueba igual.

Tres resultados posibles por servidor:

* **OK** — completó el handshake y listó sus herramientas.
* **sin configurar** — le faltan variables de entorno (`${VAR}` sin exportar).
  No es una falla: es un servidor que todavía no se conectó a nada.
* **FALLA** — está configurado y aun así no arrancó. Eso sí es un problema.

Uso:

    python distribucion/mcp/verificar_mcp.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
CONFIG = RAIZ / ".mcp.json"
TIMEOUT = 180

VERDE, ROJO, AMARILLO, GRIS, FIN = (
    "\033[92m", "\033[91m", "\033[93m", "\033[90m", "\033[0m")
OK, FALLA, PENDIENTE = f"{VERDE}✓{FIN}", f"{ROJO}✗{FIN}", f"{AMARILLO}·{FIN}"

_VARIABLE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def variables_faltantes(entorno: dict) -> list[str]:
    """Las `${VAR}` del bloque `env` que no están exportadas."""
    faltan = []
    for valor in (entorno or {}).values():
        for nombre in _VARIABLE.findall(str(valor)):
            if not os.environ.get(nombre):
                faltan.append(nombre)
    return sorted(set(faltan))


def expandir(entorno: dict) -> dict:
    return {clave: _VARIABLE.sub(lambda m: os.environ.get(m.group(1), ""), str(valor))
            for clave, valor in (entorno or {}).items()}


def handshake(comando: list[str], entorno: dict) -> tuple[bool, str, list[str]]:
    """Levanta el servidor y le habla MCP. Devuelve (ok, detalle, herramientas)."""
    proceso = subprocess.Popen(
        comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, cwd=RAIZ,
        env={**os.environ, **entorno}, bufsize=1)

    errores: list[str] = []
    lector = threading.Thread(target=lambda: errores.extend(proceso.stderr.readlines()),
                              daemon=True)
    lector.start()

    def motivo() -> str:
        """El error del servidor, no un 'no respondió' pelado.

        Cuando un servidor muere en el arranque, stdout se cierra enseguida y
        el motivo real llega por stderr un instante después. Sin esta espera el
        verificador reportaba 'no respondió a initialize' y se comía el 502 o
        el DNS que explicaba todo.
        """
        proceso.kill()
        lector.join(timeout=5)
        texto = "".join(errores).strip()
        if not texto:
            return "no respondió a initialize"
        # Varios de estos servidores loguean JSON y terminan con un stack
        # trace. Recortar por la cola devuelve el stack —inútil— y esconde el
        # "Request failed with status code 502", que es lo único que le dice al
        # usuario qué arreglar. Así que se buscan los `message` y se prefiere
        # el más largo, que es el específico.
        mensajes = re.findall(r'"message"\s*:\s*"((?:[^"\\]|\\.)*)"', texto)
        if mensajes:
            return max(mensajes, key=len)[:200]
        return texto.replace("\n", " ")[-200:]

    def enviar(objeto):
        proceso.stdin.write(json.dumps(objeto) + "\n")
        proceso.stdin.flush()

    def esperar(ident):
        """La respuesta con ese id. Se saltea todo lo que no sea JSON-RPC:
        varios servidores escupen banners y logs en stdout antes de arrancar."""
        for _ in range(500):
            linea = proceso.stdout.readline()
            if not linea:
                return None
            linea = linea.strip()
            if not linea.startswith("{"):
                continue
            try:
                mensaje = json.loads(linea)
            except ValueError:
                continue
            if mensaje.get("id") == ident:
                return mensaje
        return None

    try:
        enviar({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "verificar_mcp", "version": "1.0"}}})
        inicio = esperar(1)
        if inicio is None:
            return False, motivo(), []
        if "error" in inicio:
            return False, json.dumps(inicio["error"])[:200], []

        info = inicio.get("result", {}).get("serverInfo", {})
        etiqueta = f"{info.get('name', '?')} {info.get('version', '')}".strip()

        enviar({"jsonrpc": "2.0", "method": "notifications/initialized"})
        enviar({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listado = esperar(2)
        if listado is None or "error" in (listado or {}):
            return False, f"{etiqueta}: no respondió tools/list — {motivo()}", []
        nombres = [t["name"] for t in listado["result"].get("tools", [])]
        return True, etiqueta, nombres
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}", []
    finally:
        proceso.kill()


def main() -> int:
    if not CONFIG.exists():
        print(f"\n  {FALLA} no existe {CONFIG}\n")
        return 1

    servidores = json.loads(CONFIG.read_text(encoding="utf-8")).get("mcpServers", {})
    print(f"\nVerificando los servidores MCP de {CONFIG.name}\n")

    fallos = 0
    for nombre, config in sorted(servidores.items()):
        if "url" in config:
            # Un servidor remoto se autentica por OAuth en el navegador: no hay
            # handshake que hacer desde acá sin sesión. Se informa y se sigue.
            print(f"  {PENDIENTE} {nombre:12s} {GRIS}remoto ({config['url']}) — "
                  f"se autentica desde el cliente MCP, no se puede probar acá{FIN}")
            continue

        faltan = variables_faltantes(config.get("env", {}))
        if faltan:
            print(f"  {PENDIENTE} {nombre:12s} {GRIS}sin configurar — faltan "
                  f"{', '.join(faltan)}{FIN}")
            continue

        comando = [config["command"], *config.get("args", [])]
        ok, detalle, herramientas = handshake(comando, expandir(config.get("env", {})))
        if ok:
            print(f"  {OK} {nombre:12s} {GRIS}{detalle} — {len(herramientas)} "
                  f"herramientas{FIN}")
        else:
            fallos += 1
            print(f"  {FALLA} {nombre:12s} {GRIS}{detalle}{FIN}")

    print()
    if fallos:
        print(f"  {ROJO}{fallos} servidor(es) configurados que no arrancan.{FIN}\n")
        return 1
    print(f"  {VERDE}Todos los servidores configurados responden.{FIN}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
