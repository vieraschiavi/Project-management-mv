# CLAUDE.md — MV Project Management

Guía para Claude Code al trabajar en este repo. Leela antes de tocar código.

## Qué es

**MV Project Management** es una plataforma de gestión de proyectos con salud de
portafolio medible (6 dimensiones), grafo de dependencias/bloqueos, backlog
priorizado por valor esperado y un copiloto de IA aditivo (nunca bloqueante).
Corre 100% web (Streamlit) + escritorio (portable `.bat`, `.exe` con PyInstaller,
o ventana Electron). La demo trabaja sobre **datos 100% sintéticos**
(`mvpm/demo_data.py`) con defectos inyectados a propósito; también incluye demos
con datos públicos reales (portafolio de gobierno del Reino Unido y ensayos
clínicos de ClinicalTrials.gov). El motor de reglas, la base SQLite y la API
para BI son reales.

## Stack

- **Python** — motor y app principal:
  - `mvpm/` : motor de dominio (i18n, catálogo, salud, dependencias, backlog,
    copiloto, políticas, glosario, auth, licencias, base de datos, PMBOK, etc.).
    Un solo lugar, consumido por dashboard + API.
  - `app/app.py` : dashboard **Streamlit**.
  - `api/main.py` : **FastAPI** que sirve las tablas de gobierno de portafolio
    para BI (Power BI/Tableau) en `http://127.0.0.1:8600`.
  - Deps clave: streamlit, pandas, pyarrow (fijado `<21` — la 25.0.0 hace
    segfault al renderizar DataFrames, ver comentario en `requirements.txt`),
    fastapi, uvicorn, openpyxl, pytest, anthropic.
- **Node / Vercel** — `package.json` (raíz): **no es una app Node** — son
  las dependencias de las funciones serverless de pago (`api/checkout.js`,
  `api/verify-payment.js`, `api/_license.js`, MercadoPago) y del paso de
  publicación del instalador en Vercel Blob (CI). El producto en sí es Python.
- **Desktop** — `desktop/`: **Electron + React** (esbuild, sin CDN) sobre el
  mismo motor. La UI React consume `api/main.py`, que la sirve en `/app`; el
  `.exe` la levanta con `MVPM_MODO=api`. El `.bat` portable sigue con
  Streamlit: son dos formas de ver EL MISMO motor, no dos productos. La lógica
  de arranque vive en `desktop/lib/server-manager.js` —separada de `main.js`
  para poder testearla sin el runtime de Electron— y `desktop/ui/dist` es un
  artefacto de build que no se commitea.
- **Tests**: `pytest` sobre `tests/` (`test_core.py`, `test_db.py`,
  `test_importer.py`, `test_conectores.py`, `test_conectores_bi.py`,
  `test_mcp_server.py`, `test_capacitacion.py`, `test_plantillas.py`).

## Comandos

| Objetivo | Comando |
|---|---|
| Instalar deps (crea `.venv`) | `./run.sh install` |
| Correr la app (dashboard) | `./run.sh app` (`http://localhost:8501`) |
| Levantar la API REST para BI | `./run.sh api` (`http://127.0.0.1:8600`) |
| Servidor MCP del portafolio | `./run.sh mcp` (lo arranca el cliente MCP, no una persona) |
| Verificar los servidores MCP | `python distribucion/mcp/verificar_mcp.py` |
| Tests | `./run.sh test` (= `pytest tests/ -v`) |
| Linter (lo corre CI) | `ruff check .` |
| Un test puntual | `pytest tests/test_core.py::<nombre> -v` |
| Generar paquete portable (.zip) | `./run.sh portable` |

> **CI corre `ruff check .`** (`.github/workflows/tests.yml`) y falla el build si
> algo no pasa. Corrélo antes de pushear — la suite local puede estar verde y el
> PR romper igual. No hay formatter: no introduzcas uno sin pedirlo.
> `MV_ProjectManagement.bat` y lo que hay en `packaging/` son para Windows
> (PyInstaller + Inno Setup); no corren en este entorno Linux.
> No hay `.env.example` en el repo: las claves (`ANTHROPIC_API_KEY`,
> `OPENAI_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `GITHUB_MODELS_TOKEN`,
> `MP_ACCESS_TOKEN`, `MP_LINK_PROFESSIONAL`) se exportan como variables de
> entorno — el producto funciona sin ninguna de ellas configurada. El modelo
> de cada proveedor se elige desde la pantalla **Configuración de IA**
> (`mvpm/modelos.py`) y también acepta variable de entorno
> (`ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GEMINI_MODEL`, `XAI_MODEL`,
> `GITHUB_MODELS_MODEL`); lo elegido en la pantalla le gana.

## Estructura

```
mvpm/                 motor de dominio (catálogo, salud, dependencias, backlog,
                        copiloto, políticas, glosario, auth, licencias, db,
                        i18n, PMBOK, gobernanza, organigrama, modelos de IA, demos)
mvpm/mcp_server.py    servidor MCP del portafolio — tercera boca del mismo motor,
                        sólo lectura, stdio + JSON-RPC con la biblioteca estándar
app/app.py            dashboard operativo (Streamlit)
api/main.py           API REST local para BI (Power BI, Tableau, Excel)
api/checkout.js       checkout de MercadoPago (función serverless Vercel)
api/verify-payment.js verifica el pago y emite la licencia (nunca confía en el cliente)
api/_license.js        mismo esquema de licencias que mvpm/licensing.py, en JS
landing/              landing pública trilingüe (HTML/CSS/JS, sin build)
desktop/              app de escritorio: Electron + React sobre la API del motor
                        (ui/ interfaz, lib/ arranque, scripts/ build con esbuild)
packaging/            empaquetado para PC (launcher, PyInstaller, Inno Setup)
distribucion/         distribución y conectores de BI: powerbi/ (.pbids en vivo),
                        tableau/ (exportador a CSV), fabric/ (Power Query para
                        Dataflow Gen2), mcp/ (servidores MCP + verificador)
comercial/, owner/     material comercial y de administración interna
assets/                recursos (video demo, etc.)
tests/                 suite pytest (test_core, test_db, test_importer, test_conectores, ...)
MV_ProjectManagement.bat  versión portable — doble clic, sin instalar nada
```

## Flujo de trabajo

1. **Plan** — ante un cambio no trivial, planificá primero (`/plan`). Solo lectura hasta aprobar.
2. **Cambio** — editá el mínimo necesario. Respetá la separación motor (`mvpm/`) vs. UI (`app/app.py`) vs. API (`api/main.py`).
3. **Test** — `./run.sh test` (`/test`). No declares éxito sin correrlos.
4. **Ship** — `/ship`: test → commit descriptivo → push → PR draft.

## Convenciones

- **Trilingüe siempre (ES/EN/PT)**: todo texto de cara al usuario vive en
  `mvpm/i18n.py` con las 3 claves. La paridad de idiomas está cubierta por
  `test_i18n_parity_all_languages` en `tests/test_core.py` — si agregás una
  clave, agregá los 3 idiomas o el test rompe.
- **Versionado por empresa, nunca sobrescribe**: todo dato manual (gobernanza,
  organigrama, notas PMBOK) se guarda en la tabla `versiones` de `mvpm/db.py`
  como fila nueva (`guardar_version`); el estado vigente es la más reciente por
  `(empresa_id, entidad, clave)`. Nunca hagas un `UPDATE` que borre historial.
- **Honestidad de los datos, siempre explícita**: la demo usa datos 100%
  sintéticos con defectos inyectados a propósito (`mvpm/demo_data.py`); las
  reseñas nunca se inventan (`mvpm/reviews.py`); cuando una fuente real no
  tiene un dato (p. ej. presupuesto en `demo_pharma.py`), se deja en 0 con una
  nota explícita en vez de inventarlo.
- **IA externa (Claude/ChatGPT/Gemini) opcional y aditiva**: el motor de reglas
  (catálogo, salud, dependencias, backlog, políticas) funciona siempre sin IA;
  el asistente (`mvpm/advisor.py`, `mvpm/ai.py`) solo ofrece el proveedor cuya
  clave de entorno esté configurada. Nunca hardcodees claves.
- El motor (`mvpm/`) debe poder importarse y testearse sin levantar Streamlit ni la API.

## Do / Don't

**Do**
- Correr `./run.sh test` antes de cerrar cualquier cambio de motor o i18n.
- Mantené la paridad ES/EN/PT en cada string nuevo.
- Preferí editar el motor en `mvpm/` y consumirlo desde `app/app.py` y `api/main.py`.
- Usá `git status`/`git diff` para revisar antes de commitear.

**Don't**
- No leas ni commitees secretos (`.env`, tokens de pago, claves de IA).
- No corras los `.bat` ni el build PyInstaller/Inno en Linux.
- No introduzcas dependencias pesadas nuevas sin justificarlo.
- No uses `git push --force` ni `rm -rf`.
- No inventes reseñas, testimonios o cifras financieras que la fuente de datos no provee.

## Agentes disponibles

`explorer` (mapear el repo) · `planificador` (plan antes de cambiar) · `parallel-worker` (fan-out)
· `especialista` (gestión de portafolios y gobernanza de proyectos) · `revisor` (review del diff) · `verificador` (gate de evidencia).

## Contexto / Compact

- Empezá por este archivo y el `README.md` (tiene el detalle de cada módulo).
- Para entender la superficie de UI: `app/app.py`. Para el motor: el módulo puntual en `mvpm/`.
- Si el contexto se llena, compactá reteniendo: comandos de esta tabla, la regla de i18n
  trilingüe, la regla de versionado por empresa, y qué archivos tocaste.
