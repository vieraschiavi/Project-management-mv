# Puesta en producción — qué configurar y dónde

Guía de una sola pasada para dejar el cobro y las licencias funcionando.
No contiene ninguna clave: sólo los **nombres** de las variables, de dónde sale
el valor de cada una, en qué panel se carga y cómo comprobar que quedó bien.

Regla que no se rompe nunca: **la clave privada de licencias no se commitea, no
se pega en un chat y no se manda por mail.** El botón del paso 3 la maneja sin
que pase por tus manos.

---

## 1. El estado de hoy, en dos comandos

**Qué me falta configurar** (mira tu entorno local y el archivo `.env`; nunca
imprime el valor de nada, sólo si está o no está):

```bash
./run.sh doctor
```

Sale la lista separada en dos: lo que **bloquea la venta** y lo que sólo
degrada. La plantilla con todos los nombres y de dónde sale cada valor está en
[`.env.example`](../.env.example) — se copia a `.env` y se completa.

**Qué está realmente cargado en producción:**

```bash
curl https://mv-project-management.vercel.app/api/estado-licencias
```

Devuelve sólo booleanos (nunca firma nada, así que no es una fábrica de
licencias para quien encuentre la URL):

| campo | qué significa si es `false` |
|---|---|
| `pagos_configurados` | falta `MP_ACCESS_TOKEN`: el checkout no puede cobrar |
| `privada_configurada` | falta `MVPM_LICENSE_PRIVATE_KEY`: **quien pague recibe un error 500 en vez de su licencia** |
| `coincide_con_el_programa` | la clave cargada es de OTRO par: se emitirían licencias que ninguna instalación puede abrir |
| `ok` | los tres anteriores en verde |

Última medición (2026-08-24): `pagos_configurados: true`,
`privada_configurada: false`. O sea: cobra, pero no entrega. Es el único
bloqueante real — todo lo demás de esta guía es mejora, no candado roto.

---

## 2. Dos lugares distintos, no confundir

Hay variables que van en **Vercel** (las lee el sitio en producción) y
variables que van en **GitHub Actions** (las lee el robot que rota la clave y
compila los instaladores). Algunas van en los dos.

- **Vercel** → tu proyecto → *Settings* → *Environment Variables* → scope
  **Production** (y Preview si querés probarlo antes).
- **GitHub** → el repositorio → *Settings* → *Secrets and variables* →
  *Actions* → *New repository secret*.

---

## 3. Variables de Vercel

### Obligatorias para vender

| Nombre | De dónde sale |
|---|---|
| `MP_ACCESS_TOKEN` | MercadoPago → [Tus integraciones](https://www.mercadopago.com.uy/developers/panel/app) → tu aplicación → **Credenciales de producción** → *Access token*. Empieza con `APP_USR-`. **Ya está cargada.** |
| `MVPM_LICENSE_PRIVATE_KEY` | **No la generás vos.** La carga el botón del paso 4. Es lo único que falta hoy. |

### Fuertemente recomendadas

| Nombre | Para qué | De dónde sale |
|---|---|---|
| `BLOB_READ_WRITE_TOKEN` | El almacén de todo lo que no es código: instalador publicado, licencias canjeadas, pedidos de demo, avisos de intención de compra, contador de descargas. Sin esto, `/api/download-installer` da 503 y `/api/metricas` no tiene nada que mostrar. | Vercel → tu proyecto → **Storage** → **Blob** → *Connect* (genera el token solo). |
| `MVPM_OWNER_TOKEN` | La contraseña del tablero de ventas (`/api/metricas`): clientes, descargas, pedidos de demo, plata cobrada. Sin esto el endpoint da 503 a propósito — muestra facturación y emails, así que por defecto tiene que estar cerrado. | La inventás vos: cualquier cadena larga al azar, por ejemplo `openssl rand -hex 32`. Guardala en tu gestor de contraseñas: es la que vas a pegar en `Authorization: Bearer <esto>`. |
| `RESEND_API_KEY` | El mail que te avisa cuando alguien pide una demo o aprieta "Comprar". Sin esto, todo se sigue **registrando** igual (lo ves en `/api/metricas`), pero no te llega ningún correo. | [resend.com](https://resend.com) → cuenta gratis hasta 3.000 mails/mes → *API Keys* → *Create API Key*. Empieza con `re_`. |
| `DEMO_FROM_EMAIL` | El remitente de esos mails. Tiene que ser de un dominio verificado en Resend — usar un Gmail como remitente hace que el mail se rechace por SPF. | Resend → *Domains* → *Add Domain*, agregás los registros DNS que te da (unos minutos), y usás algo como `Ventas <ventas@tudominio.com>`. |

### Opcionales

| Nombre | Para qué | De dónde sale |
|---|---|---|
| `MVPM_LICENSE_PUBLIC_KEY` | pisar la pública embebida sin recompilar (sólo para pruebas puntuales) | se deriva de la privada; normalmente no hace falta tocarla |
| `MP_CURRENCY`, `MP_TASA_UYU` | moneda y tasa de conversión del checkout (default: UYU, 40) | las fijás vos si el tipo de cambio se movió mucho |
| `MP_LINK_PROFESSIONAL`, `MP_LINK_PROFESSIONAL_ANUAL` | link de pago fijo como respaldo si `MP_ACCESS_TOKEN` fallara | MercadoPago → *Link de pago*, uno por plan |
| `MVPM_API_KEY` | exigir clave a la API de BI cuando se la expone fuera de la máquina del cliente (`MVPM_API_HOST=0.0.0.0`) | la inventás vos: `python -c "import secrets; print(secrets.token_urlsafe(32))"` — esto es LOCAL, no de Vercel |
| `ANTHROPIC_API_KEY` · `OPENAI_API_KEY` · `GEMINI_API_KEY` · `XAI_API_KEY` · `GITHUB_MODELS_TOKEN` | el copiloto con IA, que es **aditivo**: el motor de reglas funciona igual sin ninguna | [console.anthropic.com](https://console.anthropic.com/settings/keys) · [platform.openai.com](https://platform.openai.com/api-keys) · [aistudio.google.com](https://aistudio.google.com/apikey) · [console.x.ai](https://console.x.ai) · [github.com/settings/tokens](https://github.com/settings/tokens) |

---

## 4. Variables de GitHub Actions (secrets del repositorio)

| Nombre | Para qué | De dónde sale |
|---|---|---|
| `VERCEL_TOKEN` | Deja que el botón "Rotar claves de licencia" cargue la privada en Vercel sin que vos la veas ni la pegues en ningún lado. | [vercel.com/account/tokens](https://vercel.com/account/tokens) → *Create Token* (scope: la cuenta `mv13`). Copiás el valor una sola vez, no se vuelve a mostrar. |
| `VERCEL_PROJECT_ID` | Le dice al mismo botón A CUÁL proyecto escribirle. | `prj_dGBR0Jlu5n2K05iR0EQKgu8nRpY3` — ya lo tengo de tu cuenta, lo pegás tal cual. |
| `VERCEL_TEAM_ID` | Idem, para el equipo (tus 18 proyectos viven en uno solo). | `team_csgim6tFJ3qJpbq9a8SOJWum`. |
| `BLOB_READ_WRITE_TOKEN` | El mismo valor del paso 3, pero pegado ACÁ TAMBIÉN. Sin esto, `build_electron.yml` compila el instalador pero no lo sube a Vercel Blob — el botón de descarga de la landing sigue sin tener qué entregar aunque el token ya esté en Vercel. | El mismo que generaste en el paso 3. Es un solo valor, dos lugares. |

---

## 5. La clave de licencias — con un botón, sin terminal

Esto es lo único que hoy bloquea el cobro. Antes había que correr un script de
Python en tu máquina; ahora es un click.

1. Cargá los tres secretos de GitHub del punto 4 (`VERCEL_TOKEN`,
   `VERCEL_PROJECT_ID`, `VERCEL_TEAM_ID`) — una sola vez, si no lo hiciste ya.
2. GitHub → el repositorio → **Actions** → **Rotar claves de licencia** →
   **Run workflow**.
3. En el campo de confirmación escribí exactamente `ROTAR` y ejecutá.

Qué hace solo, sin que la clave privada pase por vos en ningún momento:
genera el par, carga la privada en Vercel, pega la pública en el código,
corre los tests que cruzan Python y Node para confirmar que las dos mitades
coinciden, y commitea — lo que dispara los tres builds de instalador, así
los `.exe` salen ya con la pública correcta.

**Cuándo NO correrlo:** rotar invalida toda licencia ya emitida. Hoy es
gratis (nadie recibió nunca un token que funcione). Después de la primera
venta, correrlo de nuevo obliga a reemitir la licencia de cada cliente a
mano — por eso el campo de confirmación no tiene valor por defecto.

Comprobación, esperá un minuto a que Vercel termine de desplegar y corré:

```bash
curl https://mv-project-management.vercel.app/api/estado-licencias
# {"ok":true,"privada_configurada":true,"coincide_con_el_programa":true,"pagos_configurados":true,...}
```

---

## 6. Tu propia instalación (edición Owner)

**No necesitás emitirte ninguna licencia.** El instalador owner trae
`ES_OWNER_BUILD = True` compilado adentro: corre sin el reloj de 7 días y sin
pedir token. Hay tres formas de conseguirlo:

| Canal | Cómo | Depende de que el repo sea privado |
|---|---|---|
| **`INSTALADOR_OWNER/`** en este repo | descarga directa, un clic | **sí** — ver la advertencia de §8 |
| Artefacto de Actions | workflow *Build Windows installer (Owner Edition)* → Summary | no (exige login con acceso al repo) |
| Prerelease | push de un tag `owner-v*` | no |

Si además usás el repo o el paquete portable, una sola vez:

```bash
./run.sh owner        # firma el marcador de ESTA máquina
```

El marcador está atado a la máquina y firmado: copiarlo a otra computadora
no activa nada. Para revertir, `./run.sh owner-off`.

---

## 7. El tablero de ventas

Una vez cargado `MVPM_OWNER_TOKEN` (§3):

```bash
curl -H "Authorization: Bearer <tu MVPM_OWNER_TOKEN>" \
  https://mv-project-management.vercel.app/api/metricas
```

Devuelve clientes distintos, licencias emitidas, descargas del instalador,
pedidos de demo, clicks en "Comprar" vs. pagos aprobados, y el dinero —
bruto, neto real (el que informa MercadoPago, no una comisión estimada) y
la comisión. El campo que hay que mirar todos los días es
`alertas.pagos_sin_licencia`: si no es cero, alguien pagó y no tiene su
licencia.

---

## 8. Qué queda pendiente del lado del repositorio

- ⚠️ **El repositorio es público Y tiene el instalador owner commiteado** en
  `INSTALADOR_OWNER/`. Ese `.exe` abre el producto completo en cualquier
  máquina, sin prueba, sin token y sin clave. Mientras el repo siga público,
  **cualquiera que pase por él se baja la versión paga gratis**, sin dejar
  rastro.

  Se hizo así a pedido, para poder probar la versión completa de un clic. El
  costo desaparece con un solo cambio: *Settings* → *General* → abajo de todo →
  *Change repository visibility* → **Private**. Con el repo privado esto queda
  igual que el patrón de `Buscador-Inmobiliario`, que es privado.

  Mientras tanto: **no compartas el link de ese archivo con nadie**.
- El instalador del **cliente** sí sigue protegido y nunca se commitea:
  `/api/download-installer` exige una licencia `MVPM2` válida y vigente
  (verificado: `HTTP 401` sin token). Lo fijan
  `test_ningun_ejecutable_esta_versionado` y
  `test_el_instalador_de_cliente_nunca_esta_versionado`.
- El código fuente también es visible para cualquiera mientras el repo sea
  público.

---

## 9. Lo que sí está verificado

- La licencia que emite Node (como lo hace Vercel tras el pago) la verifica
  Python (como lo hace la PC del cliente), en las dos direcciones, incluidos
  cupo de IA, vigencia de cada plan y rechazo de tokens manoseados o
  vencidos — `tests/test_licencia_extremo_a_extremo.py`.
- Con la prueba de 7 días vencida, la API de BI devuelve 402; al guardar la
  licencia pasa a 200 en las seis tablas, el CSV de Tableau y la demo pharma
  — medido contra servidores corriendo, no sólo en tests.
- El aviso de "alguien apretó Comprar" se manda una sola vez por persona,
  plan y día — cinco clicks del mismo indeciso no generan cinco mails.
- Las tres demos (sintética, portafolio del Reino Unido, ClinicalTrials.gov)
  cargan sin errores.
- Lo que **no** está verificado y no se puede verificar desde acá: una compra
  real en MercadoPago y las tres ediciones corriendo en una PC con Windows.
