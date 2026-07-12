# MV Project Management

Plataforma de gestión de proyectos con salud de portafolio medible, backlog
priorizado por valor esperado y un copiloto de IA aditivo (nunca bloqueante).
Construida con el mismo ADN de producto que [MV Kobra AI] y [MV Data Governance]:
motor Python desacoplado de la UI, trilingüe ES/EN/PT, 100% web y PC.

## Honestidad de los datos (leer antes de vender)

Toda la demo corre sobre datos **100% sintéticos** (`mvpm/demo_data.py`), con
defectos inyectados a propósito (proyectos sin dueño, dependencias que apuntan
a tareas inexistentes) para que el motor de salud tenga algo real que
detectar. Los números que aparecen en `landing/index.html` (índice 76.8/100,
22/211 tareas bloqueadas, etc.) son el resultado real de correr el motor
sobre esos datos demo — no están inventados, se pueden reproducir con
`./run.sh test` o abriendo el dashboard.

Las **reseñas de usuarios son igual de honestas**: `mvpm/reviews.py` nunca
genera testimonios falsos. Mientras no haya reseñas verificadas, la web
muestra el estado real ("programa en fase beta"), no marketing inventado.

## Estructura

```
mvpm/            motor de dominio (un solo lugar, consumido por dashboard + API)
  catalog.py        catálogo de proyectos y KPIs de portafolio
  health.py          índice de salud en 6 dimensiones
  dependencies.py    grafo de dependencias, bloqueos e impacto
  prioritizer.py      backlog priorizado por valor esperado
  copilot.py          respuestas en lenguaje natural, IA aditiva opcional
  policies.py         políticas de gestión verificadas contra evidencia real
  glossary.py         glosario de estados compartido por el equipo
  reviews.py           reseñas y calificación de usuarios reales
  help_center.py      matriz de automatización + guiones de adopción por rol
  reports.py          reporte ejecutivo generado del dato real
  exporters.py         export uniforme CSV/Excel/JSON
  demo_data.py         datos sintéticos deterministas
  i18n.py               traducciones ES/EN/PT de la app
app/app.py         dashboard operativo (Streamlit)
api/main.py         API REST para BI (Power BI, Tableau, Excel)
landing/index.html  landing pública (HTML/CSS/JS, sin build, deploy directo en Vercel)
tests/test_core.py   suite de tests del motor
```

## Cómo correrlo

```bash
./run.sh install   # crea .venv e instala dependencias
./run.sh app        # dashboard en http://localhost:8501
./run.sh api         # API REST en http://localhost:8600
./run.sh test         # corre la suite de tests
```

El copiloto funciona sin configuración (motor de reglas). Para sumar la capa
de IA opcional, exportá `ANTHROPIC_API_KEY` antes de correr `./run.sh app` —
si no está seteada, el producto sigue funcionando igual.

## Roadmap

- [x] Motor de dominio + tests
- [x] Dashboard operativo (Streamlit)
- [x] Landing pública trilingüe
- [x] API REST para BI
- [ ] Checkout / licencias (siguiendo el patrón de `MV Kobra AI`)
- [ ] Empaquetado triple: instalador Windows, portable, web (SaaS hosteado)
- [ ] Integraciones (Slack, Google Calendar, GitHub/Jira issues)
- [ ] Reseñas verificadas de clientes piloto reales

[MV Kobra AI]: https://github.com/vieraschiavi
[MV Data Governance]: https://github.com/vieraschiavi
