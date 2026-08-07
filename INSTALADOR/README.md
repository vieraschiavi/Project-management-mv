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
| Prueba de 7 días | sí | no |
| Cupo de IA | según el plan | ilimitado |
| Hay que activar algo | pega el token al pagar | nada, ya viene activado |
| Quién lo puede usar | cualquiera que lo baje | quien lo tenga desbloquea todo |

El de CLIENTE se instala en modo demo. Cuando el cliente paga, el token que
recibe desbloquea **esa misma instalación**: no vuelve a bajar nada, no pierde
los datos que cargó.

El de OWNER lleva adentro un marcador de licencia **firmado**. Quien tenga ese
archivo tiene el producto desbloqueado, sin pagar y sin tocar nada. Por eso vive
en un repositorio privado y no se comparte, no se sube a la landing, no se manda
por mail. Si se filtra, hay que rotar el par de claves y republicar.

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
