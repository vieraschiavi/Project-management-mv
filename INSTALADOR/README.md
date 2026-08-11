# INSTALADOR

Acá quedan los instaladores `.exe` de Windows, listos para descargar desde
GitHub sin pasar por Actions.

```
INSTALADOR/
  CLIENTE/   MVProjectManagement_Setup_vX.Y.Z.exe        <- lo que baja un cliente
  OWNER/     MVProjectManagementOwner_Setup_vX.Y.Z.exe   <- sólo para el dueño
```

## Quién los pone acá

**Nadie a mano.** Los compila GitHub Actions en un runner de Windows y los
commitea solo, cada vez que cambia el producto (`mvpm/`, `app/`, `packaging/`,
`requirements.txt`). Compilarlos requiere Windows: PyInstaller e Inno Setup no
corren en Linux ni en macOS, así que no hay forma de generarlos fuera del CI.

## La diferencia entre los dos

| | CLIENTE | OWNER |
|---|---|---|
| Prueba de 7 días | sí | no, una vez activado |
| Cupo de IA | según el plan | ilimitado |
| Hay que activar algo | pega el token al pagar | **nada** |
| Quién lo puede usar | cualquiera que lo baje | quien lo baje de este repo privado |

El de CLIENTE se instala en modo demo. Cuando el cliente paga, el token que
recibe desbloquea **esa misma instalación**: no vuelve a bajar nada, no pierde
los datos que cargó.

El de OWNER es el mismo programa, con AppId y carpeta propios para poder
tenerlo instalado al lado del de cliente. Instalás y abre: sin clave, sin token
y sin archivo al lado.

### Cómo está hecho, y en qué se apoya

Lo que lo desbloquea es una **constante compilada** (`ES_OWNER_BUILD` en
`mvpm/edicion.py`), que el build pone en `True` antes de compilar `mvpm/` a
`.pyd` con Cython. Va como código nativo adentro del ejecutable.

Antes esto se hacía metiendo un marcador de licencia **firmado** adentro del
`.exe`, y se justificaba diciendo "vive en un repositorio privado" mientras el
repositorio era **público**. Ese instalador —y el `packaging/OWNER_EDITION` que
estaba versionado— le regalaban el producto pago a cualquiera que pasara.

La constante es estrictamente mejor que aquel marcador:

* **No es un token.** No hay nada que pegar en el campo de licencia de otra
  copia. Aquel marcador sí servía para eso: era una licencia `enterprise`.
* **No es un archivo.** No se puede copiar de esta instalación a la de un
  cliente, porque no hay nada que copiar.
* **No desbloquea otro binario que no sea éste.**

Lo que sí sigue dependiendo de que **este repositorio sea privado** es que este
`.exe` no lo baje cualquiera. Si algún día vuelve a ser público, esto deja de
proteger nada y hay que volver al marcador firmado y atado a la máquina, que
sigue funcionando en paralelo (`mvpm/owner.py`) y no depende de la visibilidad.

El token que se filtró quedó revocado en `mvpm/licensing.py` — sacarlo del repo
no alcanza, queda en el historial.

## Los dos instalan igual

Icono en el escritorio (casilla marcada, desmarcable), entrada en el menú
Inicio, desinstalador en "Agregar o quitar programas", y elección de carpeta y
disco con validación de espacio y permisos.

El programa abre en **su propia ventana**, con su icono en la barra de tareas:
sin barra de direcciones, sin pestañas y sin nada que delate con qué está hecho.

## El costo de tener esto versionado

Cada `.exe` pesa entre 150 y 250 MB, y git guarda **todas** las versiones para
siempre: el repositorio crece con cada rebuild y nunca se achica. Se aceptó a
propósito, para poder bajarlos directo del repo. La alternativa —publicarlos
como assets de un Release— da la misma descarga privada sin inflar el historial,
por si algún día el tamaño molesta.
