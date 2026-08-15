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

La pestaña **Demo con datos reales** (`mvpm/demo_real.py`) va un paso más
allá: corre el motor sobre 132 proyectos **reales** del portafolio público
del Reino Unido (datos abiertos, Open Government Licence v3.0 — no son
sintéticos ni preparados a medida). El "ahorro estimado" que se muestra ahí
declara su supuesto explícitamente (minutos por revisión manual) en vez de
esconderlo detrás de una cifra de marketing.

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
  demo_data.py         datos sintéticos deterministas (solo para "cargar datos de ejemplo")
  db.py                  base de datos real (SQLite) — proyectos, tareas, usuarios, empresas y versiones
  # versiones: toda dato manual queda versionado por empresa (quién lo recomendó, quién lo validó, cuándo)
  auth.py                login con usuario y contraseña (PBKDF2, sin dependencias nuevas)
  licensing.py          plan de créditos de IA — licencias firmadas + cupo mensual
  pmbok.py                PMBOK técnico + "en criollo": 10 áreas de conocimiento y 5 grupos de proceso, con notas editables por empresa
  tutorial.py              contenido de la pestaña Tutorial — guía paso a paso de cada herramienta
  case_study.py            caso de uso simulado completo: recorre un proyecto real de punta a punta
  demo_real.py             demo con datos públicos reales (portafolio de gobierno del Reino Unido)
  demo_pharma.py           demo pharma end-to-end con datos públicos reales (ClinicalTrials.gov / NIH)
  governance.py            conceptos PM preestablecidos, recomendados por IA y validados por el data owner
  organigrama.py           carga de organigrama (Excel/CSV/SQLite) → IA autocompleta responsables por etapa
  advisor.py               asistente: detecta problemas y sugiere acciones, con seguimiento persistido
  ai.py                    capa multi-proveedor genérica (Claude/ChatGPT/Gemini), siempre opcional y aditiva
  i18n.py               traducciones ES/EN/PT de la app
app/app.py         dashboard operativo (Streamlit)
api/main.py         API REST local para BI (Power BI, Tableau, Excel) + estado de licencia
distribucion/powerbi/  conector .pbids de un clic + guía para conectar Power BI a la API local
api/checkout.js      checkout de MercadoPago (función serverless en Vercel)
api/verify-payment.js  verifica el pago y emite la licencia (nunca confía en el cliente)
api/_license.js       mismo esquema de licencias que licensing.py, en JS
landing/index.html  landing pública (HTML/CSS/JS, sin build, deploy directo en Vercel)
packaging/           empaquetado para PC (launcher, PyInstaller, Inno Setup)
desktop/              instalador Electron — misma UI de Streamlit, ventana nativa
MV_ProjectManagement.bat  versión portable — doble clic, sin instalar nada
tests/test_core.py   suite de tests del motor
```

## Plan de créditos de IA

El motor de reglas (catálogo, salud, dependencias, backlog, políticas) **no
tiene cupo en ningún plan** — es gratis y sin límite siempre, porque no tiene
costo variable. Lo único medido es el **copiloto con IA** (Claude), porque
es lo único con costo real por uso:

| Plan | Cupo mensual de IA | Precio |
|---|---|---|
| Demo | 20 consultas | US$0 |
| Professional | 1.000 consultas | US$9/usuario/mes |
| Enterprise | Ilimitado | Desde US$1.500/mes |

Se paga con MercadoPago (`api/checkout.js`); al aprobarse el pago,
`api/verify-payment.js` re-verifica contra la API real de MercadoPago
(nunca confía en el query string de retorno) y emite un token de licencia
firmado con **Ed25519** (mismo esquema en Python y en JS, ver
`mvpm/licensing.py` y `api/_license.js`). Sin `MP_ACCESS_TOKEN` configurada,
el checkout cae a un link de pago fijo por plan (`MP_LINK_PROFESSIONAL`) en
vez de romper. Un mismo `payment_id` no se puede canjear dos veces por
licencias a nombres distintos (`api/_canjes.js`).

### ⚠️ Paso obligatorio antes de vender: generar el par de claves

Las licencias se firman con un par **Ed25519**: la clave privada emite y la
pública verifica. El repo **no trae ninguna de las dos** (una clave privada en
un repo es una clave privada quemada), así que hasta que generes el par
`verify_license()` rechaza todo token y nadie puede activar una licencia.

```bash
python packaging/generar_claves_licencia.py --escribir
```

Eso imprime las dos mitades y pega la **pública** en `mvpm/licensing.py`
(`CLAVE_PUBLICA_EMBEBIDA`) — commiteá ese cambio. La **privada** no se guarda
en ningún archivo: cargala como variable de entorno `MVPM_LICENSE_PRIVATE_KEY`
en dos lugares, y en ninguno más:

1. **Vercel** → Settings → Environment Variables (para que el checkout pueda
   emitir licencias al cobrar).
2. **Tu máquina**, si vas a emitir licencias a mano desde `owner/panel.py` o
   activar tu modo owner con `./run.sh owner`.

Guardala también en tu gestor de contraseñas: si la perdés, las licencias ya
emitidas siguen andando, pero para emitir nuevas hay que generar un par nuevo,
publicar una versión con la pública nueva y reemitir.

**Por qué asimétrico y no un secreto compartido.** El esquema anterior era HMAC
con un "secreto compartido" que, si no llegaba por variable de entorno, el
propio cliente se autogeneraba al azar en su disco. Eso rompía el candado en
las dos direcciones a la vez: cualquiera se emitía una licencia Enterprise con
dos líneas (`issue_license("enterprise", ...)`, firmada y verificada contra su
propio secreto local), y al mismo tiempo el token legítimo que emitía el
servidor **no** verificaba en la PC del que había pagado —secretos distintos—,
así que el cliente pagaba y seguía viendo "la prueba venció". Con firma
asimétrica las dos se caen solas: la clave que viaja en cada copia del programa
sirve para verificar y no para emitir.

### Edición Owner (la instalación del dueño, sin candado)

El dueño del producto usa su propia herramienta todos los días y no tiene
sentido que la prueba de 7 días lo deje afuera. Para marcar **esta** máquina:

```bash
export MVPM_LICENSE_PRIVATE_KEY=<tu-clave-privada>
./run.sh owner       # activa el modo owner en esta máquina, para siempre
./run.sh owner-off    # vuelve al comportamiento de cliente (prueba + licencia)
```

En Windows, `set MVPM_LICENSE_PRIVATE_KEY=<tu-clave>` y después doble clic en
`MV_ProjectManagement_OWNER.bat` (una sola vez).

Hace falta la clave privada porque el marcador es un **token firmado**, no un
archivo vacío: `es_owner()` verifica la firma en cada arranque. Antes alcanzaba
con que el archivo existiera —o con exportar `MVPM_OWNER_BYPASS=1`—, y las dos
cosas estaban documentadas en `mvpm/owner.py`, que viaja dentro del ZIP que
baja cualquiera: eran dos bypasses del candado a un `touch` de distancia.

Vale para **toda** forma de arrancar el programa —`run.sh app`, el `.bat`
portable, el `.exe`, `streamlit run` directo—: la decisión vive en
`mvpm/owner.py`, no en el launcher. Antes estaba sólo en
`packaging/mvpm_launcher.py`, así que el mismo dueño abriendo su programa con
`./run.sh app` caía igual en la pantalla de "la prueba venció".

**Esto no afloja la licencia de ningún cliente.** El modo se activa con un
archivo que se escribe en los datos del usuario (`~/.mv_project_management/`),
nunca en la carpeta del programa: no puede colarse en el ZIP portable ni en el
instalador. `mvpm/owner.py` no importa ni modifica `licensing.py` — el candado
de 7 días y la verificación de firma quedan intactos. `tests/test_owner.py`
fija las tres cosas: que el build de cliente no lleve el marcador, que el ZIP
portable no lo arrastre, y que `licensing.estado_acceso()` responda lo mismo
esté o no activo el modo owner.

## Asistente IA (multi-proveedor)

La pestaña **Asistente IA** (`mvpm/advisor.py`) detecta problemas reales del
portafolio con el motor de reglas (siempre disponible, sin configurar nada)
y sugiere una acción concreta. La redacción de esa sugerencia se puede pulir
con el proveedor de IA que tengas configurado — nunca inventa el problema ni
el número que lo sustenta:

| Proveedor | Variables de entorno | Paquete opcional |
|---|---|---|
| Claude | `ANTHROPIC_API_KEY` | ya incluido (`anthropic`) |
| ChatGPT | `OPENAI_API_KEY` | `pip install openai` |
| Gemini | `GEMINI_API_KEY` | `pip install google-generativeai` |
| Grok (xAI) | `XAI_API_KEY` | `pip install openai` |
| Copilot (GitHub Models) | `GITHUB_MODELS_TOKEN` | `pip install openai` |

El asistente sólo ofrece los proveedores con su clave configurada — nunca
uno que vaya a fallar.

> `GITHUB_MODELS_TOKEN` y no `GITHUB_TOKEN`: esta última está seteada por
> defecto en cualquier runner de GitHub Actions y en muchas máquinas de
> desarrollo, para cosas que no tienen que ver con IA. Si fuera la clave de
> Copilot, el producto ofrecería un proveedor que nadie configuró.

### Qué modelo usa cada proveedor

Se elige desde **Configuración de IA** en el dashboard (`mvpm/modelos.py`), y
es la palanca principal del gasto: dentro de un mismo proveedor, el modelo más
caro y el más barato se llevan más de un orden de magnitud por token.

El botón **«Actualizar modelos desde mi API»** le pregunta al proveedor qué
modelos tiene habilitados *tu* clave, y con esa respuesta arma la lista. **El
programa no trae ningún catálogo de modelos precargado**, a propósito: los
catálogos cambian todos los meses y no todas las claves tienen habilitados los
mismos modelos (depende del plan, la organización y la región). Una lista
escrita a mano te ofrecería modelos que tu clave no puede usar y te escondería
los que sí. Antes del primer «Actualizar» la lista está vacía, y la pantalla lo
dice con esas palabras.

La elección se guarda **versionada por empresa** (tabla `versiones`, igual que
gobernanza y organigrama): queda quién la hizo y cuándo, y no se pisa el
historial. Quien prefiera automatizar el arranque puede seguir fijando el
modelo por variable de entorno (`ANTHROPIC_MODEL`, `OPENAI_MODEL`,
`GEMINI_MODEL`, `XAI_MODEL`, `GITHUB_MODELS_MODEL`); lo elegido en la pantalla
le gana, porque es lo último que pidió el usuario.

Nada de esto afecta al motor de reglas: salud, dependencias, backlog y
políticas se calculan sin IA y no gastan un token.

Cada sugerencia se puede marcar **en seguimiento** y cambiar de estado
(abierto / en progreso / resuelto) — queda persistida en la base real, no se
pierde al recargar ni si el problema original deja de detectarse.

## Demo pharma end-to-end (dato público real → Power BI)

La pestaña **Demo laboratorio (Pharma)** (`mvpm/demo_pharma.py`) carga 474
ensayos clínicos reales de laboratorios multinacionales (AstraZeneca, Pfizer,
Novartis) tomados de **ClinicalTrials.gov** — base de la U.S. National Library
of Medicine (NIH), **dominio público, sin autenticación**. El estado clínico
de cada ensayo se traduce a criticidad del portafolio (TERMINATED/SUSPENDED →
Alta, RECRUITING/ACTIVE → Media, COMPLETED → Baja), de modo que el mismo motor
de portafolio funciona sin cambios.

Honestidad: ClinicalTrials.gov **no publica presupuesto**, así que
`presupuesto`/`ejecutado` quedan en 0 con una nota explícita — no se inventa
un número financiero que no existe.

El flujo llega hasta Power BI de una punta a la otra: la API local expone el
portafolio en `GET /api/demo/pharma` (JSON o CSV) y el archivo
`distribucion/powerbi/MV_ProjectManagement_Pharma.pbids` conecta Power BI de un
clic contra ese endpoint (ver `distribucion/powerbi/README.md`).

## Conectar BI y agentes (Power BI, Tableau, Fabric, MCP)

El mismo motor sale por cuatro bocas y todas sirven las mismas 6 tablas —hay un
test (`tests/test_conectores_bi.py`) que falla si alguna se desincroniza, para
que un cliente no vea un portafolio distinto según con qué herramienta lo abra.

| Herramienta | Cómo se conecta | Carpeta |
|---|---|---|
| **Power BI** | doble clic en un `.pbids`, lee la API en vivo | `distribucion/powerbi/` |
| **Tableau** | exportador a CSV (Tableau no tiene conector Web para una API REST arbitraria) | `distribucion/tableau/` |
| **Fabric** | Power Query para Dataflow Gen2 — requiere gateway, la API es local | `distribucion/fabric/` |
| **Claude y otros agentes** | servidor MCP (`./run.sh mcp`) | `distribucion/mcp/` |

El servidor MCP (`mvpm/mcp_server.py`) expone 9 herramientas **de sólo lectura**
—salud, bloqueos, backlog, políticas, KPIs, glosario— para que un agente
responda con los números que el motor calculó en vez de inventarlos. Habla
JSON-RPC por stdio con la biblioteca estándar, sin dependencias nuevas.

En `distribucion/mcp/` también quedan configurados los servidores MCP oficiales
de **Power BI**, **Fabric** (en modo sólo lectura, sin las 4 herramientas que
borran de OneLake) y **Tableau**, con un verificador que levanta cada uno y le
habla el protocolo de verdad:

```bash
python distribucion/mcp/verificar_mcp.py
```

## Gobernanza, organigrama y versionado por empresa

Todo dato manual del sistema sigue el mismo patrón: **la IA lo recomienda
primero, el responsable lo valida o lo corrige, y cada versión queda guardada
por empresa** (quién la recomendó, quién la validó — nombre y cargo — y cuándo).
La tabla `versiones` de `db.py` nunca sobrescribe: guarda una fila nueva y
mantiene el historial completo.

- **Gobernanza de datos** (`mvpm/governance.py`): 14 conceptos de PM ya vienen
  con su definición preestablecida. Cualquiera se puede afinar con IA y luego
  el data owner/steward lo valida y guarda. Queda el historial de cada cambio.
- **Organigrama y responsables** (`mvpm/organigrama.py`): se carga el
  organigrama de la empresa (Excel, CSV o base SQLite) y la IA autocompleta los
  responsables por etapa del PMBOK a partir de cargos y áreas. Todo se puede
  editar y guardar. (El parseo de organigramas en foto requiere IA de visión;
  se declara explícitamente en vez de simularlo.)
- **PMBOK técnico + "en criollo"** (`mvpm/pmbok.py`): cada área de conocimiento
  y cada grupo de proceso trae su definición técnica y su explicación en
  criollo, más una nota editable y guardable por empresa.

## Descargas

Ambos instaladores Windows se compilan en CI al taguear `vX.Y.Z` (ver
"Instalador de Windows" más abajo) y quedan como assets del mismo release
de GitHub — el motor Python/Streamlit es exactamente el mismo en los dos:

- **Instalador Windows — Python/Streamlit** (`.github/workflows/build_windows.yml`):
  PyInstaller + Inno Setup, abre el programa en el navegador del sistema.
  No necesita Python instalado en la PC del usuario.
- **Instalador Windows — Electron** (`.github/workflows/build_electron.yml`,
  código en [`desktop/`](desktop/)): el mismo motor Python/Streamlit,
  envuelto en una ventana nativa de escritorio (ícono propio, sin barra de
  navegador) en vez de abrir el navegador — la opción más "profesional"
  para quien busca un `.exe` que se sienta como un programa de escritorio
  de verdad, no una web. Tampoco necesita Python instalado; no reescribe
  ninguna pantalla, sigue siendo la misma UI de Streamlit.
- **Portable (.bat)**: `./run.sh portable` genera
  `dist/MVProjectManagement_portable_vX.Y.Z.zip` — se descomprime y se
  ejecuta `MV_ProjectManagement.bat`, sin instalar nada. Este sí necesita
  Python instalado en la PC (es la versión liviana, sin PyInstaller).
- **100% web**: `./run.sh app` y se comparte la URL en la red interna.

Más detalle en [`distribucion/README.md`](distribucion/README.md).

## Cómo correrlo

```bash
./run.sh install   # crea .venv e instala dependencias
./run.sh app        # dashboard en http://localhost:8501
./run.sh api         # API REST en http://localhost:8600
./run.sh test         # corre la suite de tests del motor (Python/pytest)
```

`./run.sh test` corre solo la suite de Python. La ruta del dinero (emitir
licencia, firmarla, cobrar) vive en funciones serverless **JavaScript**
(`api/checkout.js`, `api/verify-payment.js`, `api/_license.js`) que pytest no
levanta — sus tests son Node puro, sin dependencias que instalar:

```bash
node tests/test_licencias.js
node tests/test_checkout.js
node tests/test_verify_payment.js
```

Es exactamente lo que corre `.github/workflows/tests.yml` en cada push — una
máquina nueva con Python 3.11+ y Node instalados (nada más) puede reproducir
la suite completa con estos cuatro comandos, sin preguntarle nada a nadie.

El copiloto funciona sin configuración (motor de reglas). Para sumar la capa
de IA opcional, exportá `ANTHROPIC_API_KEY` antes de correr `./run.sh app` —
si no está seteada, el producto sigue funcionando igual.

La primera vez que abrís el dashboard, te pide crear la cuenta de
administrador (usuario y contraseña) — el resto del equipo se registra
después con su propio usuario. Los datos quedan en una base SQLite real
(`~/.mv_project_management/datos.db`, en el equipo/servidor donde corre la
app, nunca en la nube por defecto) y se pueden crear, editar, archivar o
borrar proyectos y tareas desde el dashboard.

La sección **Tutorial** (primera del menú) explica paso a paso cada
herramienta del programa, **Caso de uso completo** recorre un proyecto
simulado por todas esas herramientas con los números reales que calcula el
motor, y **Metodología PMBOK** muestra, área por área, qué tanto se alinea
el producto con la guía del PMI — sin inflar lo que no cubre (adquisiciones
y comunicaciones, por ejemplo, quedan declaradas como huecos reales, no
maquilladas).

## Instalador de Windows (pendiente de publicar)

Dos workflows compilan sendos instaladores Windows reales cada vez que se
publica un tag `vX.Y.Z` — ninguno requiere Python instalado en la PC del
usuario:

- `.github/workflows/build_windows.yml` — PyInstaller + Inno Setup.
- `.github/workflows/build_electron.yml` — el mismo motor, envuelto en
  Electron (ver [`desktop/`](desktop/)) para una ventana nativa en vez de
  abrir el navegador del sistema.

**Todavía no se publicó ningún tag**, así que la página de releases está
vacía y la única opción hoy es la versión portable (`.bat`), que sí
necesita Python instalado. Para publicar los dos instaladores reales:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Esto dispara los dos builds en GitHub Actions y publica ambos `.exe` en
[Releases](https://github.com/vieraschiavi/Project-management-mv/releases)
automáticamente.

## Roadmap

- [x] Motor de dominio + tests
- [x] Dashboard operativo (Streamlit)
- [x] Landing pública trilingüe
- [x] API REST para BI
- [x] Checkout / licencias (MercadoPago + plan de créditos de IA, patrón de `MV Kobra AI`)
- [x] Empaquetado: portable (.bat) generado y probado; instalador Windows vía CI (pendiente compilar un release real)
- [x] Base de datos real (SQLite local), login con usuario y contraseña, y fichas para crear/editar/archivar proyectos y tareas
- [x] Pestaña de Tutorial (guía de cada herramienta), Caso de uso completo y alineación honesta con PMBOK
- [x] Iconos profesionales (SVG) en la landing, reemplazando los emoji
- [x] Demo con datos públicos reales (portafolio de gobierno UK) y Asistente IA multi-proveedor con seguimiento
- [x] Instalador de escritorio con Electron (ventana nativa, mismo motor Python/Streamlit), código en `desktop/`
- [ ] Publicar el primer tag (`v0.1.0`) para que existan los instaladores Windows reales descargables (Python y Electron)
- [ ] Integraciones (Slack, Google Calendar, GitHub/Jira issues)
- [ ] Reseñas verificadas de clientes piloto reales

## Al desplegar con dominio propio

Las etiquetas Open Graph llevan la URL **absoluta** del sitio: los scrapers de
WhatsApp, LinkedIn y X no resuelven rutas relativas, así que con una ruta
relativa la tarjeta al compartir sale sin imagen. Esto se repite en **3
archivos** (la landing y sus dos variantes de idioma, que existen solo para
que compartir un link en inglés o portugués muestre la tarjeta social en ese
idioma en vez de en español — ver comentario al principio de cada uno):

- `landing/index.html` (es, `/`)
- `landing/en/index.html` (en, `/en/`)
- `landing/pt/index.html` (pt, `/pt/`)

Hoy apuntan a `https://mv-project-management.vercel.app`. Si se compra un
dominio propio, hay que cambiarlo en estas etiquetas del `<head>` de **cada
uno** de los 3 archivos:

| Etiqueta | Qué es |
|---|---|
| `<link rel="canonical">` | URL preferida de la página |
| `<link rel="alternate" hreflang="...">` | las 4 variantes (es/en/pt/x-default) |
| `og:url` | la que muestran las redes al compartir |
| `og:image` + `og:image:secure_url` | la tarjeta (1200×630) |
| `twitter:image` | la misma tarjeta para X |

Para comprobar que quedó bien, después de desplegar:

```bash
curl -sI https://TU-DOMINIO/og-image.jpg | head -1        # tiene que dar 200, no 404
curl -s https://TU-DOMINIO/en/ | grep '<title>'              # título en inglés
curl -s https://TU-DOMINIO/pt/ | grep '<title>'              # título en portugués
```

y pegar la URL del sitio (y la de `/en/` y `/pt/`) en el
[validador de LinkedIn](https://www.linkedin.com/post-inspector/) o el de
Facebook, que además fuerzan a que refresquen su caché.

## Licencia

Software propietario — ver [`LICENSE`](LICENSE). El instalador de
Windows muestra y requiere aceptar el [EULA](packaging/EULA.txt) antes de
instalar. El paquete `mvpm/` que corre dentro de los instaladores (Windows
y Electron) se compila a binario nativo con Cython en CI para no
distribuir el código fuente en texto plano.

[MV Kobra AI]: https://github.com/vieraschiavi
[MV Data Governance]: https://github.com/vieraschiavi

<!-- deploy: checkout MercadoPago en UYU activo (trigger) -->
<!-- redeploy 2: forzar alias al build de git con checkout UYU -->
