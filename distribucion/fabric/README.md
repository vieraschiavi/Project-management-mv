# Conectar Microsoft Fabric a MV Project Management

Las 6 tablas del portafolio entran a Fabric como un **Dataflow Gen2**, con el
Power Query de esta carpeta:
[`MV_ProjectManagement_Portafolio.pq`](MV_ProjectManagement_Portafolio.pq).

## Lo primero, porque cambia todo el resto

La API de este producto corre en `127.0.0.1` de la máquina del cliente —a
propósito: sirve el portafolio completo y por eso no se expone a la red sin
que alguien lo decida—. Fabric es un servicio en la nube. **No hay forma de
que Fabric llegue solo a esa API.** Hacen falta una de estas dos:

- **Gateway de datos local** (lo normal): se instala el
  [on-premises data gateway](https://learn.microsoft.com/power-bi/connect-data/service-gateway-onprem)
  en la misma máquina donde corre la API y el dataflow lo usa como puente. Como
  el gateway y la API quedan en la misma máquina, los pedidos salen por
  loopback y no hace falta clave.
- **Exponer la API a la red**, levantándola con `MVPM_API_HOST=0.0.0.0` y
  `MVPM_API_KEY=<clave>`. En ese caso hay que poner esa misma clave en
  `ClaveApi` dentro del Power Query. `api/main.py` exige la clave para todo
  pedido que no venga de la propia máquina, así que sin ella no sirve nada.

Si sólo querés ver los datos en Power BI sin montar nada de esto, el camino
corto es `../powerbi/` (conector Web, un doble clic, todo local).

## Pasos

1. **Levantá la API** en la máquina del cliente:

   ```bash
   ./run.sh api
   ```

2. **Verificá que responde** antes de tocar Fabric:

   ```bash
   python distribucion/powerbi/verificar_conexion.py
   ```

   Hace los pedidos HTTP de verdad sobre cada endpoint, en JSON y CSV, y dice
   qué falta arreglar.

3. **En Fabric**: `Workspace → Nuevo → Dataflow Gen2 → Obtener datos →
   Consulta en blanco → Editor avanzado`. Pegá el contenido del `.pq`.

4. **Ajustá las dos variables de arriba del archivo** si hace falta:
   `BaseUrl` (host y puerto) y `ClaveApi` (vacía si hay gateway en la misma
   máquina).

5. **Elegí el destino** (Lakehouse o Warehouse) y publicá. La consulta devuelve
   una tabla de navegación: expandí la columna `Data` o entrá a la tabla que
   quieras.

## Detalles del Power Query que importan

- Usa `Web.Contents(BaseUrl, [RelativePath = ...])` en vez de pegar la URL
  entera. Con la URL completa armada a mano, Power Query no puede validar el
  origen y **la actualización programada falla** con "no se puede determinar el
  origen de datos", aunque la vista previa haya funcionado.
- `ClaveApi` viene vacía en el repo y así tiene que quedar: hay un test
  (`tests/test_conectores_bi.py`) que falla si alguien commitea una clave ahí.
- Las 6 tablas que trae son exactamente las mismas que cargan el `.pbids` de
  Power BI y el exportador de Tableau. También hay un test que lo verifica, para
  que un cliente no vea un portafolio distinto según la herramienta.

## Fabric MCP (aparte de esto)

Que Claude pueda *consultar* Fabric es otra cosa distinta y ya está configurada
en el repo: ver [`../mcp/README.md`](../mcp/README.md).
