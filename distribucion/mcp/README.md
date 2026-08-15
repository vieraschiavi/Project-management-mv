# Servidores MCP: que Claude consulte el portafolio y las herramientas de BI

MCP (Model Context Protocol) es el estándar por el que un agente —Claude Code,
Claude Desktop, Copilot— se conecta a herramientas externas. En este repo el
`.mcp.json` declara cinco servidores: uno **de** este producto y cuatro **hacia**
las plataformas de BI.

Antes de confiar en cualquiera de ellos, corré el verificador: levanta cada
servidor y le habla el protocolo de verdad (`initialize` + `tools/list`).

```bash
python distribucion/mcp/verificar_mcp.py
```

Distingue tres estados y sólo devuelve error en el tercero: **OK**,
**sin configurar** (le faltan variables de entorno) y **falla** (está
configurado y aun así no arranca).

## Qué hay configurado

| Servidor | Qué hace | Estado verificado |
|---|---|---|
| `mvpm` | **este producto**: portafolio, salud, bloqueos, backlog, políticas | ✅ 9 herramientas, sin configurar nada |
| `fabric` | Microsoft Fabric / OneLake, en modo sólo lectura | ✅ 26 herramientas, sin configurar nada |
| `powerbi` | consultar semantic models de Power BI en lenguaje natural | requiere Entra ID + permiso del admin |
| `tableau` | consultar Tableau | requiere sitio de Tableau y un PAT |
| `graft` | índice de código del repo (ya estaba) | ✅ |

### `mvpm` — el propio producto

Lo implementa [`mvpm/mcp_server.py`](../../mvpm/mcp_server.py) y lo levanta
`./run.sh mcp`. Es la tercera boca del mismo motor, al lado del dashboard y de
la API REST: un agente pregunta "¿qué proyectos están en rojo y por qué?" y
recibe los números que el motor ya calculó, en vez de inventarlos.

**Las 9 herramientas son todas de sólo lectura.** Ninguna escribe, borra ni
modifica datos del cliente:

`listar_tablas` · `consultar_tabla` · `salud_portafolio` ·
`bloqueos_y_dependencias` · `impacto_si_se_atrasa` · `backlog_priorizado` ·
`politicas` · `kpis_portafolio` · `glosario`

Sobre una instalación vacía devuelven ceros **con un aviso explícito** de que
el portafolio está vacío, en vez de rellenar con la demo: un agente que recibe
`indice_general: 0` sin contexto concluye que el portafolio está en crisis.

Está cubierto por `tests/test_mcp_server.py`, que habla el protocolo contra el
proceso real.

### `fabric` — Microsoft Fabric

Servidor oficial de Microsoft (`@microsoft/fabric-mcp`), se baja solo con npx y
**arranca sin credenciales**. Está configurado con `--read-only` a propósito:

| | herramientas |
|---|---|
| `--mode all` | 48, incluidas `onelake_delete_file`, `onelake_delete_directory`, `onelake_delete_shortcut`, `onelake_delete_data_access_role` |
| `--mode all --read-only` | **26, ninguna destructiva** |

Un agente con las 48 puede borrar archivos y roles de acceso de OneLake sin que
nadie confirme. Si en algún momento hace falta escribir, se saca la bandera a
mano y sabiendo lo que implica.

Las operaciones contra datos reales de Fabric piden autenticación de Azure
igual; sin ella funcionan las herramientas de documentación y specs.

### `powerbi` — Power BI (remoto)

Endpoint oficial hospedado por Microsoft, en **vista previa**:
`https://api.fabric.microsoft.com/v1/mcp/powerbi`. Genera y ejecuta consultas
DAX contra tus semantic models respetando tus permisos (incluido RLS).

Para que ande hacen falta tres cosas, y ninguna se resuelve desde el repo:

1. Que el admin de Power BI habilite el ajuste de organización
   *"Users can use the Power BI Model Context Protocol server endpoint (preview)"*.
2. Permisos de **Build** sobre al menos un semantic model.
3. Autenticarse con Microsoft Entra ID — el login sale por el navegador desde
   el cliente MCP, por eso el verificador lo marca como no comprobable.

La herramienta `Generate Query` consume licencia de Copilot; si no la querés
usar, desactivala en el cliente y dejá que el modelo escriba el DAX.

> **No confundir con editar modelos.** El servidor de arriba *consulta*. Para
> *modificar* semantic models Microsoft tiene otro, `@microsoft/powerbi-modeling-mcp`,
> que **no** está en el `.mcp.json` y es deliberado: está en beta (0.5.x), sus
> herramientas escriben sobre el modelo y la propia Microsoft recomienda hacer
> backup antes de usarlo. Si lo querés igual, el comando verificado es
> `npx -y @microsoft/powerbi-modeling-mcp@latest --start` — el `--start` no es
> opcional: sin él, el paquete corre un instalador interactivo que espera una
> tecla y el cliente MCP lo ve colgado.

### `tableau` — Tableau

Servidor oficial de Tableau (`@tableau/mcp-server`, Apache-2.0). Necesita cuatro
variables de entorno; hasta que las exportes, el cliente MCP va a mostrar este
servidor como caído, y es lo esperado:

```bash
export TABLEAU_SERVER="https://tu-sitio.online.tableau.com"
export TABLEAU_SITE_NAME="tu_sitio"
export TABLEAU_PAT_NAME="nombre-del-token"
export TABLEAU_PAT_VALUE="valor-del-token"
```

El PAT se crea en Tableau → *Configuración de la cuenta → Tokens de acceso
personal*. Las credenciales van por variable de entorno y nunca al repo: el
`.mcp.json` sólo tiene los `${...}`.

Este servidor contacta al sitio de Tableau **durante el `initialize`**, así que
con credenciales mal puestas no arranca en absoluto. El verificador muestra el
error que devuelve Tableau (502, DNS, TLS), que es lo que dice qué corregir.

Tableau también ofrece una variante hospedada en `https://mcp.tableau.com` con
OAuth 2.1 en vez de PAT, para Tableau Cloud.

## Esto no es lo mismo que conectar BI al producto

Son las dos direcciones opuestas y conviene no mezclarlas:

- **Acá**: Claude consulta Power BI / Fabric / Tableau.
- **Al revés** —Power BI, Tableau o Fabric leen el portafolio de este
  producto— se hace con los conectores de
  [`../powerbi/`](../powerbi/), [`../tableau/`](../tableau/) y
  [`../fabric/`](../fabric/).
