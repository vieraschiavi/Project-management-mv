# Conectar Power BI a MV Project Management (end-to-end)

El mismo motor que calcula la salud del portafolio en el dashboard sirve los
datos por una **API REST local** (`api/main.py`), así que Power BI (o Tableau,
Looker, Excel) se conecta al dato en vivo sin exportar planillas a mano.

## Flujo completo (ensayos clínicos reales de laboratorios multinacionales)

```
ClinicalTrials.gov ──► mvpm/demo_pharma.py ──► motor (salud/criticidad) ──► API REST ──► Power BI
   (dato real,            (474 ensayos de           (mismo motor que          (/api/demo/       (un clic con
    dominio público)       AstraZeneca/Pfizer/        el dashboard)             pharma)           el .pbids)
                           Novartis)
```

## Pasos

1. **Levantá la API local** en la PC/servidor donde corre el programa:

   ```bash
   ./run.sh api        # queda escuchando en http://127.0.0.1:8600
   ```

   (En el instalador de escritorio la API se puede levantar igual desde la
   carpeta del programa; corre 100% local, no expone nada afuera de tu red.)

2. **Verificá que responde** (opcional): abrí en el navegador
   `http://127.0.0.1:8600/api/demo/pharma` — tenés que ver los 474 ensayos en JSON.

3. **Conectá Power BI con un clic**: doble clic en
   [`MV_ProjectManagement_Pharma.pbids`](MV_ProjectManagement_Pharma.pbids).
   Power BI Desktop abre y ya trae la conexión apuntada a
   `http://127.0.0.1:8600/api/demo/pharma`. Elegí **Cargar** y listo — la tabla
   entra con: `nct`, `titulo`, `laboratorio`, `estado`, `fase`, `criticidad`,
   `fecha_inicio`, `fecha_fin`.

   > Si preferís hacerlo a mano: en Power BI → **Obtener datos → Web** y pegá
   > `http://127.0.0.1:8600/api/demo/pharma`.

4. **Armá el tablero**: campos que salen naturales para un PMO de portafolio —
   ensayos por `laboratorio`, por `estado`, y un semáforo por `criticidad`
   (Alta = terminados/suspendidos, la señal de riesgo real del portafolio).

## Otros endpoints útiles para BI

| Endpoint | Qué trae |
|---|---|
| `/api/demo/pharma` | los 474 ensayos reales (el del `.pbids`) |
| `/api/proyectos` | tu portafolio real (el que cargás en el dashboard) |
| `/api/tareas` | tus tareas |
| `/api/salud` | índice de salud por proyecto calculado por el motor |
| `/api/backlog_priorizado` | backlog ordenado por valor esperado |

Todos aceptan `?format=csv` si tu herramienta prefiere CSV.

## Fuente y licencia

Datos de ensayos: **ClinicalTrials.gov** (U.S. National Library of Medicine,
NIH) — dominio público. No implica aval de NLM/NIH sobre este producto.
