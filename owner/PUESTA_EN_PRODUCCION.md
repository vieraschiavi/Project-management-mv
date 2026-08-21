# Puesta en producción — qué configurar y dónde

Guía de una sola pasada para dejar el cobro y las licencias funcionando.
No contiene ninguna clave: sólo los **nombres** de las variables, de dónde sale
el valor de cada una y cómo comprobar que quedó bien.

Regla que no se rompe nunca: **la clave privada de licencias no se commitea, no
se pega en un chat y no se manda por mail.** Vive en dos lugares, los dos como
secreto: tu gestor de contraseñas y las variables de entorno de Vercel.

---

## 1. El estado de hoy, en un comando

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

Última medición (2026-08-21): `pagos_configurados: true`,
`privada_configurada: false`. O sea: cobra, pero no entrega.

---

## 2. Las variables, una por una

### Obligatorias para vender

| Nombre | Dónde va | De dónde sale el valor |
|---|---|---|
| `MP_ACCESS_TOKEN` | Vercel (Production) | MercadoPago → [Tus integraciones](https://www.mercadopago.com.uy/developers/panel/app) → tu aplicación → **Credenciales de producción** → *Access token*. Empieza con `APP_USR-`. Ya está cargada. |
| `MVPM_LICENSE_PRIVATE_KEY` | Vercel (Production) | **No se genera de nuevo**: es la mitad privada del par cuya pública ya viaja embebida en los instaladores repartidos. Ver el paso 3. |

### Opcionales (el producto funciona sin ninguna)

| Nombre | Para qué | Dónde sacarla |
|---|---|---|
| `MVPM_LICENSE_PUBLIC_KEY` | pisar la pública embebida sin recompilar (rotación de claves, pruebas) | se deriva de la privada |
| `MP_CURRENCY`, `MP_TASA_UYU` | moneda y tasa de conversión del checkout | las fijás vos |
| `MP_LINK_PROFESSIONAL` | link de pago fijo como respaldo si no hay `MP_ACCESS_TOKEN` | MercadoPago → Link de pago |
| `BLOB_READ_WRITE_TOKEN` | publicar el instalador en Vercel Blob; **sin esto `/api/download-installer` responde 503 y el botón de descarga de la landing no baja nada** | Vercel → Storage → Blob → *Connect* (genera el token solo) |
| `MVPM_API_KEY` | exigir clave a la API de BI cuando se la expone fuera de la máquina (`MVPM_API_HOST=0.0.0.0`) | la inventás vos: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ANTHROPIC_API_KEY` · `OPENAI_API_KEY` · `GEMINI_API_KEY` · `XAI_API_KEY` · `GITHUB_MODELS_TOKEN` | el asistente de IA, que es **aditivo**: el motor de reglas funciona igual sin ninguna | [console.anthropic.com](https://console.anthropic.com/settings/keys) · [platform.openai.com](https://platform.openai.com/api-keys) · [aistudio.google.com](https://aistudio.google.com/apikey) · [console.x.ai](https://console.x.ai) · [github.com/settings/tokens](https://github.com/settings/tokens) |
| `ANTHROPIC_MODEL`, `OPENAI_MODEL`, `GEMINI_MODEL`, `XAI_MODEL`, `GITHUB_MODELS_MODEL` | fijar el modelo por variable | lo elegido en la pantalla **Configuración de IA** le gana igual |

Ninguna de estas variables tiene "contraseña" que vos elijas, salvo
`MVPM_API_KEY`. El resto son credenciales que emite el proveedor.

---

## 3. La clave de licencias: comprobar antes de cargar

Esta es la que hoy falta, y la que hay que tratar con cuidado. El problema que
tiene esta pieza: `api/_license.js` **deriva la clave pública de la privada que
tenga cargada**, así que el servidor siempre es coherente consigo mismo. Si la
privada no es la del par de producción, la emisión sale 200, el token está bien
firmado, y no lo verifica ninguna instalación — porque cada copia del programa
trae embebida la *otra* pública. No lo detecta un deploy verde: lo detecta el
cliente que ya pagó.

**En tu computadora** (nunca en un chat, nunca en un servidor ajeno):

```bash
python packaging/generar_claves_licencia.py --verificar
```

- Si no encuentra la clave, exportala primero desde tu gestor de contraseñas:
  ```bash
  export MVPM_LICENSE_PRIVATE_KEY=<la-clave>     # PowerShell: $env:MVPM_LICENSE_PRIVATE_KEY="..."
  ```
- **Si dice `COINCIDEN`**: imprime el nombre, el scope y el valor exactos.
  Cargalos en Vercel → tu proyecto → *Settings* → *Environment Variables* →
  `MVPM_LICENSE_PRIVATE_KEY`, scope **Production**, y **redeployá** (una
  variable nueva no entra en un despliegue ya hecho).
- **Si dice `NO COINCIDEN` o perdiste la clave**: hay que rotar el par.
  ```bash
  python packaging/generar_claves_licencia.py --escribir
  ```
  Eso pega la pública nueva en `mvpm/licensing.py`. Después hay que
  **reconstruir y volver a repartir los instaladores**: los que ya entregaste
  verifican contra la pública vieja y dejarían de abrir licencias nuevas. Las
  licencias ya emitidas con la clave vieja siguen valiendo en las copias viejas.

Comprobación final:

```bash
curl https://mv-project-management.vercel.app/api/estado-licencias
# {"ok":true,"privada_configurada":true,"coincide_con_el_programa":true,"pagos_configurados":true,...}
```

---

## 4. Tu propia instalación (edición Owner)

**No necesitás emitirte una licencia.** El instalador owner
(`INSTALADOR/OWNER/MVProjectManagementOwner_Setup_v0.2.0.exe`) trae
`ES_OWNER_BUILD = True` compilado adentro: corre sin el reloj de 7 días y sin
pedir token.

Si además usás el repo o el paquete portable, una sola vez:

```bash
./run.sh owner        # firma el marcador de ESTA máquina
```

El marcador está atado a la máquina y firmado: copiarlo a otra computadora no
activa nada. Para revertir, `./run.sh owner-off`.

---

## 5. Qué queda pendiente del lado del repositorio

- **El repositorio es público** y tiene los dos instaladores commiteados.
  Mientras siga público, cualquiera puede bajar el `.exe` owner. Pasalo a
  privado apenas te descargues el tuyo: *Settings* → *General* → abajo de todo,
  *Change repository visibility*.
- `/api/download-installer` devuelve **503** hasta que se cargue
  `BLOB_READ_WRITE_TOKEN` y se publique el instalador
  (`packaging/publish_blob.js`). Hasta entonces el botón de descarga de la
  landing no entrega archivo.

---

## 6. Lo que sí está verificado

- La licencia que emite Node (como lo hace Vercel tras el pago) la verifica
  Python (como lo hace la PC del cliente), en las dos direcciones, incluidos
  cupo de IA, vigencia del plan anual y rechazo de tokens manoseados —
  `tests/test_licencia_extremo_a_extremo.py`.
- Con la prueba de 7 días vencida, la API de BI devuelve 402; al guardar la
  licencia pasa a 200 en las seis tablas, el CSV de Tableau y la demo pharma —
  medido contra servidores corriendo, no sólo en tests.
- Las tres demos (sintética, portafolio del Reino Unido, ClinicalTrials.gov)
  cargan sin errores.
- Lo que **no** está verificado y no se puede verificar desde acá: una compra
  real en MercadoPago y las tres ediciones corriendo en una PC con Windows.
