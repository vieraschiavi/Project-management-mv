# Cómo se distribuye MV Project Management

Dos vías, según lo que permita instalar la política de TI del cliente —
mismo criterio que MV Kobra AI y MV Data Governance MV.

## Opción A — Instalador Windows (.exe)

Para empresas que permiten instalar ejecutables. No requiere tener Python
instalado — todo viene empaquetado.

Se compila en CI (GitHub Actions, runner Windows) a partir de un tag
`vX.Y.Z`:

```
git tag v0.1.0
git push origin v0.1.0
```

El workflow `.github/workflows/build_windows.yml` compila con PyInstaller +
Inno Setup y publica `MVProjectManagement_Setup_vX.Y.Z.exe` como asset del
release de GitHub.

## Opción B — Portable (.bat)

Para empresas que bloquean instalar `.exe` pero permiten correr Python. Se
descarga un ZIP, se descomprime, y se hace doble clic en
`MV_ProjectManagement.bat` — crea su propio entorno virtual la primera vez.

Se genera localmente (no requiere Windows) con:

```
python packaging/build_release.py
```

Produce `dist/MVProjectManagement_portable_vX.Y.Z.zip`.

## Opción C — 100% web

Si ninguna de las dos anteriores es viable: `./run.sh app` en un servidor
interno y se comparte la URL por la red local. Cero instalación en las PCs
de los usuarios.
