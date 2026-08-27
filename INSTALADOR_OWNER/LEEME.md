# Instalador — Owner Edition (versión completa)

`MVPM_Owner_Setup.exe` · Windows 64 bits · ~29 MB

Este es el instalador de **uso exclusivo del dueño**. Abre MV Project Management
**completo**: sin la prueba de 7 días, sin pedir token y sin pedir clave. Es la
misma funcionalidad que recibe un cliente que paga el plan Professional.

## Instalar

1. Descargá `MVPM_Owner_Setup.exe` (botón **Download** de GitHub, o clonando el repo).
2. Doble clic. Windows SmartScreen va a avisar que el editor no está verificado
   —el ejecutable no está firmado con un certificado de código— así que:
   **Más información → Ejecutar de todas formas**.
3. Elegí disco y carpeta. No pisa una instalación de cliente: la Owner Edition
   tiene su propio AppId y su propia carpeta, así que podés tener las dos en la
   misma PC.
4. Listo. Se abre en el navegador. **No hay que configurar nada más.**

No necesitás emitirte una licencia ni pegar ningún token: el permiso va compilado
adentro del binario (`ES_OWNER_BUILD = True`, ver `mvpm/edicion.py`).

## Qué incluye

Todo lo que incluye el plan Professional pago:

- Portafolio con salud medible en 6 dimensiones
- Grafo de dependencias y detección de bloqueos
- Backlog priorizado por valor esperado
- Copiloto e Asistente de IA (aditivos: el motor de reglas funciona sin ninguna
  clave de IA configurada)
- Reportes automáticos, Ingeniería de datos, Conectores ERP, Gobernanza,
  Organigrama, PMBOK, Plantillas por rubro, Capacitación
- Interfaz trilingüe ES / EN / PT

## Verificar la descarga

```
certutil -hashfile MVPM_Owner_Setup.exe SHA256
```

Tiene que dar:

```
b7bdc32bf8b9490dcb86c59c85724984e3be56cb220feaff953515fa91ba5c95
```

## ⚠️ Advertencia de seguridad — leer antes de compartir el link

Este repositorio es **público** hoy. Este `.exe` abre el producto completo en
cualquier máquina donde se instale, así que **cualquiera que llegue al repo se
baja la versión paga gratis**, sin dejar rastro.

Mientras esa sea la situación:

- **No compartas el link de este archivo con nadie.** El instalador que va a un
  cliente es otro (`build_windows.yml`), y ése sí respeta la prueba de 7 días y
  pide licencia.
- Para eliminar el riesgo: **Settings → General → abajo de todo → Change
  repository visibility → Private**. Eso deja esta carpeta exactamente igual que
  el patrón de `Buscador-Inmobiliario`, que es un repo privado.

Tener el `.exe` acá no reemplaza los otros dos canales del dueño, que siguen
funcionando y no dependen de la visibilidad del repo:

| Canal | Cómo se obtiene |
|---|---|
| Artefacto de Actions | workflow **Build Windows installer (Owner Edition)** → *Summary* → artefacto `MVProjectManagement-Owner-Setup-Windows` (exige estar logueado con acceso al repo) |
| Prerelease | push de un tag `owner-v*` |
| Repo / paquete portable | `./run.sh owner` — firma un marcador atado a ESTA máquina; se revierte con `./run.sh owner-off` |

## Actualizar este archivo

Cuando cambie el producto, se reemplaza (no se acumulan versiones — el test
`test_el_instalador_de_cliente_nunca_esta_versionado` exige un solo binario acá):

1. Corré el workflow **Build Windows installer (Owner Edition)** en Actions.
2. Bajá el artefacto, renombrá el `.exe` a `MVPM_Owner_Setup.exe`.
3. Reemplazá el de esta carpeta, actualizá el SHA-256 de arriba y commiteá.
