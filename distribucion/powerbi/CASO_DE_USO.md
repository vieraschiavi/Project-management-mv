# Caso de uso: un consultor de Power BI arma el tablero de portafolio

Este documento es el recorrido **completo y verificable** de lo que hace un
consultor de BI con MV Project Management: levantar la API, conectar Power BI,
y armar las medidas del tablero. Todos los números de acá salieron de correr
la cadena de verdad — no son ilustrativos. Al final está el comando para que
los reproduzcas en tu máquina.

> **Qué resuelve.** El cuello de botella de un tablero de portafolio nunca es
> el tablero: es conseguir que alguien te mande la planilla actualizada todos
> los meses. Acá la fuente se alimenta sola — la API sirve el dato en vivo
> desde el mismo motor que calcula la salud en el dashboard.

---

## El escenario

El cliente ya usa MV Project Management: su PMO carga proyectos y tareas en el
dashboard. Quiere un tablero ejecutivo en Power BI, con refresco automático y
sin exportar Excels a mano.

**Portafolio de este ejemplo:** 20 proyectos, 211 tareas, 11 personas.

---

## Paso 1 — Levantar la API (en la PC/servidor del cliente)

```bash
./run.sh api        # queda escuchando en http://127.0.0.1:8600
```

Corre **100% local**: por defecto escucha en loopback, así que el dato no sale
de la máquina. (Para que Power BI entre desde otra PC: `MVPM_API_HOST=0.0.0.0`
más `MVPM_API_KEY=<clave>`, que la API exige a todo pedido no local.)

## Paso 2 — Verificar la conexión ANTES de abrir Power BI

```bash
python distribucion/powerbi/verificar_conexion.py
```

Hace exactamente el mismo GET HTTP que hace el conector Web de Power BI, sobre
cada URL de los `.pbids`, en JSON y en CSV. Salida real:

```
Verificando la conexión de BI contra http://127.0.0.1:8600

  ✓ la API responde (/health → 200)

  MV_ProjectManagement_Pharma.pbids
    ✓ JSON  /api/demo/pharma           474 filas × 10 columnas · nct, titulo, laboratorio, estado…
    ✓ CSV   /api/demo/pharma           474 filas × 10 columnas

  MV_ProjectManagement_Portafolio.pbids
    ✓ JSON  /api/proyectos             20 filas × 15 columnas · _id, proyecto_id, nombre, portafolio…
    ✓ CSV   /api/proyectos             20 filas × 15 columnas
    ✓ JSON  /api/tareas                211 filas × 9 columnas · _id, tarea_id, proyecto_id, titulo…
    ✓ CSV   /api/tareas                211 filas × 9 columnas
    ✓ JSON  /api/equipo                11 filas × 4 columnas · nombre, rol, capacidad_semanal_hs, carga_actual_hs…
    ✓ CSV   /api/equipo                11 filas × 4 columnas
    ✓ JSON  /api/salud                 20 filas × 10 columnas · proyecto_id, nombre, indice, estado…
    ✓ CSV   /api/salud                 20 filas × 10 columnas
    ✓ JSON  /api/backlog_priorizado    122 filas × 12 columnas · _id, tarea_id, proyecto_id, titulo…
    ✓ CSV   /api/backlog_priorizado    122 filas × 12 columnas
    ✓ JSON  /api/politicas             6 filas × 4 columnas · politica, descripcion, estado, evidencia…
    ✓ CSV   /api/politicas             6 filas × 4 columnas

  Todo listo. Doble clic en cualquiera de los .pbids de esta carpeta y Power BI carga las tablas.
```

Si algo falla, el mensaje dice qué arreglar. Si pasa, la carga en Power BI está
garantizada: es el mismo pedido.

## Paso 3 — Conectar Power BI con un doble clic

| Archivo | Qué carga |
|---|---|
| [`MV_ProjectManagement_Portafolio.pbids`](MV_ProjectManagement_Portafolio.pbids) | las **6 tablas** del portafolio del cliente |
| [`MV_ProjectManagement_Pharma.pbids`](MV_ProjectManagement_Pharma.pbids) | 474 ensayos clínicos reales, para demostrar sin datos del cliente |

Doble clic → Power BI Desktop abre con las conexiones ya apuntadas → **Cargar**.
Sin ODBC, sin driver, sin script de carga.

> A mano: **Obtener datos → Web** y pegar `http://127.0.0.1:8600/api/proyectos`.
> Para Tableau/Excel, agregá `?format=csv` a cualquier endpoint.

## Paso 4 — El modelo de datos

Las 6 tablas se relacionan por `proyecto_id` (y las tareas por `tarea_id`):

```
proyectos ──┬── salud                (1:1 por proyecto_id — el índice ya viene calculado)
            ├── tareas               (1:N por proyecto_id)
            │     └── backlog_priorizado  (subconjunto de tareas, ya ordenado)
            └── politicas            (evaluación del portafolio, sin clave: tabla suelta)
   equipo   (sin relación directa: se cruza por responsable si hace falta)
```

**Lo importante para el consultor:** `salud` ya trae el índice y las 6
dimensiones **calculadas por el motor**. No hay que reconstruir la fórmula en
DAX — y si el cliente discute un número, la fuente de verdad es una sola.

## Paso 5 — Las medidas del tablero

Números reales de este portafolio, calculados sobre lo que devolvió la API:

| Medida | Valor | De dónde sale |
|---|---:|---|
| Proyectos activos | 20 | `COUNTROWS(proyectos)` |
| Índice de salud del portafolio | 78.2/100 | `AVERAGE(salud[indice])` |
| Proyectos en riesgo (índice < 55) | 1 | `CALCULATE(COUNTROWS(salud), salud[indice] < 55)` |
| Tareas bloqueadas | 22 de 211 | `CALCULATE(COUNTROWS(tareas), tareas[estado] = "blocked")` |
| Presupuesto total | 930.000 | `SUM(proyectos[presupuesto])` |
| Ejecutado | 574.695 (61,8%) | `SUM(proyectos[ejecutado])` |
| Proyectos sobre presupuesto | 6 | `ejecutado > presupuesto` |
| Políticas incumplidas | 2 de 6 | `CALCULATE(COUNTROWS(politicas), politicas[estado] <> "cumple")` |

**Salud promedio por dimensión** — el gráfico de radar que pide todo PMO:

| Dimensión | Promedio |
|---|---:|
| Alcance | 88,1 |
| Cronograma | **44,2** |
| Presupuesto | 87,9 |
| Riesgo | 71,4 |
| Dependencias | 100,0 |
| Equipo | 77,5 |

Esa es la lectura que vende el tablero: el portafolio tiene 78,2 de salud
global, pero **cronograma en 44,2** — el problema no está repartido, está
concentrado en fechas. Es la conversación que el consultor lleva a la reunión.

## Un detalle que evita una discusión al pedo

El dashboard muestra **78.2** y tu `AVERAGE(salud[indice])` va a dar
**78.185**. No es una discrepancia: `health.overall_index()` redondea a un
decimal para mostrar. El dato crudo que sirve la API es el bueno; si querés que
el tablero coincida con la pantalla, redondeá en la medida.

## Reproducir estos números

Con la API levantada:

```bash
python distribucion/powerbi/verificar_conexion.py   # la cadena entera
python -m pytest tests/test_powerbi.py -v            # el contrato, automatizado
```

`tests/test_powerbi.py` verifica que las URLs de los `.pbids` existan de
verdad en la API, que `?format=csv` devuelva CSV parseable y que la tabla
`salud` traiga el índice ya calculado — así esta guía no se puede desactualizar
en silencio.

## Fuente y licencia de los datos de demo

Ensayos clínicos: **ClinicalTrials.gov** (U.S. National Library of Medicine,
NIH) — dominio público. No implica aval de NLM/NIH sobre este producto.
El portafolio de 20 proyectos de este ejemplo son los datos sintéticos de
`mvpm/demo_data.py` (defectos inyectados a propósito), los mismos que carga
cualquiera con "Cargar datos de ejemplo para explorar".
