# © 2026 Martín Viera. Todos los derechos reservados.
"""Backlog de demo para el módulo de Azure DevOps. 100% sintético, a propósito.

Ninguna fila viene de un cliente. La empresa, las personas y los proyectos no
existen: están inventados. Lo que sí es real es **la forma de los defectos** —
cada uno de los que trae este backlog es un patrón que aparece una y otra vez en
backlogs de equipos de datos reales, y cada uno está puesto acá deliberadamente
para que la demo muestre la regla que lo detecta.

La tabla de abajo es el contrato entre este archivo y `tests/test_azure_devops.py`:
si se agrega una regla a `backlog_calidad`, acá va el caso que la dispara, y el
test verifica que ninguna regla se quede sin ejemplo. Una demo donde la mitad de
las reglas no tienen nada que mostrar es una demo que miente por omisión.

| Ítem | Defecto inyectado | Regla que lo agarra |
|---|---|---|
| 204, 219 | El título es "DELETE" | titulo_marcador |
| 212 | El título es "TBD" | titulo_marcador |
| 206, 207 | Dos ítems con el mismo título | titulo_duplicado |
| 215 | El título arrastra el workaround vigente | titulo_con_estado |
| varios | Descripción vacía | sin_descripcion |
| varios | Descripción sin criterio de aceptación | sin_criterio_aceptacion |
| 210 | La descripción depende de una imagen adjunta | depende_de_adjunto |
| casi todos | Sin estimación | sin_esfuerzo |
| 208, 209, 218 | Issue huérfano habiendo Epics | sin_padre |
| 216, 217 | Iteración "Sprint Actual": un nombre que se mueve | iteracion_movil |
| 201, 220 | Unos en la raíz y otros en \\Sprint N | iteracion_inconsistente |
| 201, 213, 215 | En Doing desde hace meses | estancado |
| 220 | Sin responsable | sin_asignar |
| 214 | Etiqueta "VERLO DESPUES" | tag_informal |
| 210, 213, 215 | Rev muy alto: la definición no estaba clara | rev_alta |
| todo | Prioridad 2 en casi todo | prioridad_uniforme |
| todo | Casi todo asignado a una persona | bus_factor |
"""

from __future__ import annotations

import pandas as pd

from mvpm.azure_devops import COLUMNAS

ORGANIZACION_DEMO = "nordeste-demo"
PROYECTO_DEMO = "Datos Comerciales"
RAIZ = "Datos Comerciales"
S1 = f"{RAIZ}\\Sprint 1"
S2 = f"{RAIZ}\\Sprint 2"
MOVIL = f"{RAIZ}\\Sprint Actual"

_P = "Paula Arocena"
_D = "Diego Sanguinetti"

# ID, Rev, Tipo, Titulo, Estado, AsignadoA, Iteracion, Padre, Prioridad,
# Esfuerzo, Tags, Creado, Modificado, Descripcion_texto
_FILAS: tuple[tuple, ...] = (
    (201, 6, "Issue", "Contingencia - estrategia comercial (PPT)", "Doing", _P,
     RAIZ, "", 2, "", "Clientes", "2026-06-11", "2026-06-11", ""),
    (202, 5, "Epic", "Tablero de venta y margen ECOM", "To Do", _P, S1, "", 2,
     "", "", "2026-06-12", "2026-08-19", ""),
    (203, 4, "Issue", "Tablero acotado de venta diaria", "To Do", _P, S1, 202, 2,
     "", "", "2026-06-12", "2026-06-12", ""),
    (204, 10, "Task", "DELETE", "Done", _P, S1, 203, 2, "", "",
     "2026-06-17", "2026-06-23", ""),
    (205, 8, "Task", "Maqueta HTML del tablero", "Doing", _P, S1, 203, 2, "", "",
     "2026-08-30", "2026-09-10",
     "Objetivo: previsualizar el reporte antes de construir el modelo. "
     "Entregable: maqueta HTML navegable."),
    (206, 4, "Task", "Revisión con el área de analítica", "To Do", _P, S1, 203, 2,
     "", "", "2026-06-12", "2026-06-12", ""),
    (207, 2, "Task", "Revisión con el área de analítica", "To Do", _P, S1, 211, 2,
     "", "", "2026-06-12", "2026-06-12", ""),
    (208, 4, "Issue", "Tableros de comportamiento de cliente", "To Do", _P, S1,
     "", 2, "", "", "2026-06-17", "2026-06-17", ""),
    (209, 3, "Issue", "Tablero genérico de retail sobre SQL", "To Do", _P, S1,
     "", 2, "", "", "2026-06-17", "2026-06-17", ""),
    (210, 22, "Task", "Modelo de datos en estrella", "Doing", _P, S2, 209, 2, "",
     "", "2026-06-17", "2026-09-08",
     "Armar el modelo como en la pizarra. Ver imagen adjunta."),
    (211, 5, "Issue", "Tablero secundario de reposición", "To Do", _P, S1, 202,
     2, "", "", "2026-06-12", "2026-06-18", ""),
    (212, 3, "Task", "TBD", "To Do", _P, S2, 211, 2, "", "",
     "2026-07-02", "2026-07-02", ""),
    (213, 27, "Task", "Refresco del conjunto de datos", "Doing", _P, S2, 209, 2,
     "", "", "2026-07-01", "2026-06-30",
     "Objetivo: que el tablero muestre el día anterior sin intervención."),
    (214, 4, "Task", "Permisos de la fuente SQL", "To Do", _D, S2, 209, 2, "",
     "VERLO DESPUES", "2026-07-03", "2026-07-03", ""),
    (215, 24, "Task",
     "Refresco automático cada 8 horas (refresco MANUAL mientras no se resuelve)",
     "Doing", _P, S2, 209, 2, "", "", "2026-07-05", "2026-07-08", ""),
    (216, 5, "Task", "Alertas de quiebre de stock B", "To Do", _P, MOVIL, 208, 2,
     "", "", "2026-08-04", "2026-08-04", ""),
    (217, 4, "Task", "Alertas de quiebre de stock C", "To Do", _P, MOVIL, 208, 2,
     "", "", "2026-08-04", "2026-08-04", ""),
    (218, 3, "Issue", "Inducción al equipo nuevo", "To Do", _P, S1, "", 2, "",
     "", "2026-06-17", "2026-06-17", ""),
    (219, 7, "Task", "DELETE", "Done", _P, S1, 218, 2, "", "",
     "2026-06-17", "2026-06-20", ""),
    (220, 2, "Task", "Monitorear el gateway", "To Do", "", RAIZ, 209, 3, "", "",
     "2026-08-12", "2026-08-12", ""),
    (221, 6, "Task", "Conectar el tablero a la API", "Done", _P, S1, 203, 2, 5,
     "", "2026-06-17", "2026-06-24",
     "Objetivo: pasar de la maqueta a datos reales. Entregable: tablero "
     "conectado. Criterio de aceptación: el total del día cuadra contra la "
     "fuente con diferencia cero."),
    (222, 3, "Task", "Variantes de diseño del tablero", "Done", _P, S1, 203, 2,
     3, "", "2026-06-12", "2026-06-16",
     "Objetivo: elegir una de tres variantes. Criterio de aceptación: la "
     "variante elegida está aprobada por el referente comercial."),
)


def backlog_demo() -> pd.DataFrame:
    """El backlog sintético, con las columnas canónicas de `azure_devops`."""
    df = pd.DataFrame(list(_FILAS), columns=list(COLUMNAS))
    return df.astype(str).apply(lambda s: s.str.strip())
