; © 2026 Martín Viera. Todos los derechos reservados.
;
; Personalización del instalador NSIS que arma electron-builder.
; Se engancha con `build.nsis.include` en desktop/package.json.
;
; QUÉ RESUELVE
;
; electron-builder propone siempre una carpeta en C: —%LOCALAPPDATA%\Programs
; si se instala para un solo usuario, Archivos de programa si es para todos—.
; Este programa ocupa unos 400 MB (lleva el motor de Python entero adentro), y
; en una notebook con el C: chico eso es justo lo que no entra. Acá se elige
; como carpeta POR DEFECTO el disco fijo con más espacio libre, así que en una
; PC con C: y D: la sugerencia sale sola en D:.
;
; Es sólo la sugerencia: la página de destino se muestra igual y el botón
; Examinar sigue mandando. Si algo de esto no funciona, el instalador sigue
; andando con el default de electron-builder — no hay ninguna rama que aborte.
;
; Sólo se toca la PRIMERA instalación: si ya hay una versión instalada,
; electron-builder reinstala donde estaba y este script no se mete. Reinstalar
; en otro disco y dejar la copia vieja tirada es exactamente el bug que ya se
; corrigió una vez en el instalador owner.

!include "FileFunc.nsh"
!include "LogicLib.nsh"

; Margen sobre los ~400 MB que ocupa la instalación: no se sugiere un disco
; donde el programa entra justo y después no hay lugar para la base de datos.
!define MVPM_MIN_MB 1500

; Cuánto más grande tiene que ser otro disco para desplazar a C:. Sin este
; margen, un D: con 100 MB más que C: cambiaba la sugerencia por nada.
!define MVPM_VENTAJA_MB 5000

Var MvpmMejorUnidad
Var MvpmMejorLibre
Var MvpmUnidad
Var MvpmLibre
Var MvpmLetra

; Espacio libre en MB de una unidad ("C:\"), o 0 si no se puede saber.
!macro MvpmLibreMB Raiz Salida
  StrCpy ${Salida} 0
  ${GetRoot} "${Raiz}" $MvpmUnidad
  ; DriveType devuelve vacío para una letra que no existe.
  ${DriveSpace} "$MvpmUnidad\" "/D=F /S=M" ${Salida}
!macroend

!macro preInit
  ; --------------------------------------------------------------------
  ; Sugerir la carpeta de instalación en el disco con más lugar.
  ; --------------------------------------------------------------------
  ; Sólo en instalación nueva: si ya está instalado, no se toca nada.
  ReadRegStr $0 HKLM "${INSTALL_REGISTRY_KEY}" "InstallLocation"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "${INSTALL_REGISTRY_KEY}" "InstallLocation"
  ${EndIf}

  ${If} $0 == ""
    ; Arranca con C: como referencia, para no mover la sugerencia sin motivo.
    StrCpy $MvpmMejorUnidad "C:"
    !insertmacro MvpmLibreMB "C:\" $MvpmMejorLibre
    IntOp $MvpmMejorLibre $MvpmMejorLibre + ${MVPM_VENTAJA_MB}

    ; Recorre D..Z. Se saltea A y B (disqueteras) y C (ya es la referencia).
    StrCpy $1 68   ; 'D'
    ${Do}
      IntFmt $MvpmLetra "%c" $1
      StrCpy $MvpmUnidad "$MvpmLetra:"

      ; Sólo discos fijos: 3 = DRIVE_FIXED. Así no se sugiere instalar en un
      ; pendrive ni en una unidad de red, que es peor que instalar en C:.
      System::Call 'kernel32::GetDriveTypeW(w "$MvpmUnidad\") i .r2'
      ${If} $2 == 3
        !insertmacro MvpmLibreMB "$MvpmUnidad\" $MvpmLibre
        ${If} $MvpmLibre > ${MVPM_MIN_MB}
        ${AndIf} $MvpmLibre > $MvpmMejorLibre
          StrCpy $MvpmMejorUnidad "$MvpmUnidad"
          StrCpy $MvpmMejorLibre $MvpmLibre
        ${EndIf}
      ${EndIf}

      IntOp $1 $1 + 1
    ${LoopUntil} $1 > 90   ; 'Z'

    ${IfNot} $MvpmMejorUnidad == "C:"
      StrCpy $INSTDIR "$MvpmMejorUnidad\${APP_FILENAME}"
      ; electron-builder lee InstallLocation para decidir la carpeta que
      ; muestra en la página de destino, así que la sugerencia se deja escrita
      ; ahí y no sólo en $INSTDIR.
      WriteRegExpandStr HKCU "${INSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
    ${EndIf}
  ${EndIf}
!macroend
