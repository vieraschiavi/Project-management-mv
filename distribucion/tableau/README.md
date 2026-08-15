# Conectar Tableau a MV Project Management

El mismo motor que calcula la salud del portafolio en el dashboard sirve los
datos por la **API REST local** (`api/main.py`). Para Tableau el camino es:
bajar las tablas a CSV con el exportador de esta carpeta y abrirlas desde
Tableau.

## Por qué un exportador y no un archivo de un clic

Power BI trae un conector Web nativo, así que un `.pbids` puede apuntar
directamente a una URL y funciona solo. Tableau no tiene un equivalente para
una API REST arbitraria: lo que existía (Web Data Connector 1.x/2.x) quedó
discontinuado, y el reemplazo obliga a empaquetar y firmar un conector propio.

Se podría igual meter acá un `.tds` escrito a mano, pero no hay forma de
probarlo sin Tableau instalado, y un archivo que falla en la máquina del
cliente es peor que tres clics documentados. Por eso lo que se entrega es lo
que sí está verificado de punta a punta: el exportador hace los pedidos HTTP
reales y valida lo que recibe.

## Pasos

1. **Levantá la API** en la PC/servidor donde corre el programa:

   ```bash
   ./run.sh api        # queda escuchando en http://127.0.0.1:8600
   ```

2. **Bajá las tablas**:

   ```bash
   python distribucion/tableau/exportar_para_tableau.py
   ```

   Escribe en `dist/tableau/` un CSV por tabla más un `manifiesto.json` con qué
   se bajó, de dónde y cuándo. Se le puede pasar otra carpeta destino como
   argumento.

3. **Abrí en Tableau**: `Conectar → Archivo de texto` y elegí el CSV. Para
   cruzar tablas, arrastrá las demás al lienzo de relaciones (`proyecto_id` es
   la clave entre `proyectos`, `salud`, `tareas` y `backlog_priorizado`).

## Qué trae cada archivo

| Archivo | Qué es |
|---|---|
| `proyectos.csv` | el catálogo del portafolio con presupuesto y ejecución |
| `tareas.csv` | tareas con estado, vencimiento y de qué dependen |
| `equipo.csv` | personas y su carga |
| `salud.csv` | índice por proyecto y las 6 dimensiones que lo componen |
| `backlog_priorizado.csv` | backlog ordenado por valor esperado |
| `politicas.csv` | evaluación de las políticas de gobernanza |

## Actualizar el dato

El exportador toma una foto: para refrescar hay que volver a correrlo y en
Tableau usar `Actualizar origen de datos`. Si necesitás dato vivo en lugar de
una foto, el camino es Power BI (`../powerbi/`), que sí se conecta a la URL.

## Si algo falla

El exportador corta con el motivo en vez de escribir archivos rotos: si la API
no responde, si un endpoint no devuelve `text/csv`, o si el CSV viene envuelto
como JSON (un defecto real que ya apareció una vez en esta API, y que en
Tableau se ve como una sola columna gigante con cero filas).
