`MVProjectManagement.exe` se copia acá automáticamente en CI (ver
`.github/workflows/build_electron.yml`) antes de compilar el instalador de
Electron — es el mismo ejecutable que produce PyInstaller
(`packaging/mvpm.spec`), sin Python instalado en la PC del usuario. No se
versiona en git (pesa cientos de MB); este archivo sólo documenta qué va acá.
