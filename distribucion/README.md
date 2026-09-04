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

El workflow `.github/workflows/build_electron.yml` compila con PyInstaller +
Electron/NSIS y publica `MVProjectManagement-Desktop-Setup-X.Y.Z.exe` como asset del
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

## Integraciones con herramientas de BI y agentes

Aparte de cómo se instala el programa, en esta carpeta está cómo se lo conecta
con lo que el cliente ya usa. Las tres primeras van en la dirección
"tu herramienta de BI lee el portafolio"; la última, al revés.

| Carpeta | Qué resuelve |
|---|---|
| [`powerbi/`](powerbi/) | Power BI lee la API en vivo — doble clic en un `.pbids` |
| [`tableau/`](tableau/) | Tableau abre el portafolio — exportador a CSV |
| [`fabric/`](fabric/) | Fabric ingesta el portafolio — Power Query para Dataflow Gen2 |
| [`mcp/`](mcp/) | Claude consulta el portafolio, y también Power BI/Fabric/Tableau |

Las tres primeras sirven exactamente las mismas 6 tablas, y hay un test
(`tests/test_conectores_bi.py`) que falla si alguna se desincroniza: un cliente
no puede ver un portafolio distinto según con qué herramienta lo abra.

## Opción C — 100% web

Si ninguna de las dos anteriores es viable: `./run.sh app` en un servidor
interno y se comparte la URL por la red local. Cero instalación en las PCs
de los usuarios.
