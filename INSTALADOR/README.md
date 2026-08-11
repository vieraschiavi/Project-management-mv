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
| Hay que activar algo | pega el token al pagar | la clave privada, una vez por máquina |
| Quién lo puede usar | cualquiera que lo baje | sólo quien tenga la clave privada |

El de CLIENTE se instala en modo demo. Cuando el cliente paga, el token que
recibe desbloquea **esa misma instalación**: no vuelve a bajar nada, no pierde
los datos que cargó.

El de OWNER es el mismo programa, con AppId y carpeta propios para poder
tenerlo instalado al lado del de cliente. Lo que lo desbloquea no viaja adentro:
vive en la máquina del dueño (`~/.mv_project_management/clave_privada_owner`).
Se activa una vez con `MV_ProjectManagement_OWNER.bat` y queda para siempre en
esa computadora, para todas las formas de abrir el programa.

### Por qué no viene ya activado

Venía. Llevaba adentro un marcador de licencia **firmado**, y quien tuviera ese
archivo tenía el producto desbloqueado sin pagar. Esto decía que era seguro
"porque vive en un repositorio privado". **Este repositorio es público**, y
también lo son los Releases de Actions: o sea que ese instalador —y el
`packaging/OWNER_EDITION` que estaba versionado— le regalaban el producto pago a
cualquiera que pasara por acá.

Lo que se hizo: el token filtrado quedó revocado en `mvpm/licensing.py`
(sacarlo del repo no alcanza — queda en el historial), ningún build empaqueta
ya un marcador, y los marcadores nuevos se emiten **atados a una máquina**, así
que uno copiado a otra computadora no desbloquea nada.

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
