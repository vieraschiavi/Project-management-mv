# MV Project Management · aplicación de escritorio

Electron + React sobre el mismo motor Python. No es otro producto: es otra
forma de ver el mismo `mvpm/`.

    .exe instalado   ->  React consumiendo api/main.py
    .bat portable    ->  Streamlit

## Por qué React y no Streamlit adentro de la ventana

Antes esta ventana envolvía Streamlit: un navegador sin barra mostrando la
misma página que abre `./run.sh app`. Funcionaba, y el techo era el de
Streamlit — nunca se iba a ver como un producto a medida.

Ahora la ventana carga `/app`, que sirve `api/main.py`. La interfaz son ~700
líneas de React empaquetadas con esbuild, **sin librería de gráficos**: las dos
vistas que la pedirían son barras de 0 a 100, y un `<div>` con ancho porcentual
las resuelve sin sumarle cientos de KB al instalador.

## Cómo correrlo

    cd desktop
    npm install
    npm start          # construye la UI y abre la ventana

En desarrollo, `main.js` levanta `uvicorn` contra el código del repositorio.
Instalado, lanza el `.exe` de PyInstaller con `MVPM_MODO=api` — ese binario
lleva `mvpm/` compilado a `.pyd`, así que el motor no viaja como fuente legible.

## Lo que no es obvio

**`ui/dist` no se commitea.** Es un artefacto de build; commitearlo lo deja
envejecer respecto del código, que es exactamente lo que pasó con el ZIP de la
landing durante meses. `npm run dist` lo reconstruye antes de empaquetar.

**El puerto se LEE, no se asume.** Electron busca uno libre y se lo pasa al
motor, pero `mvpm/puertos.py` elige otro si en el medio se ocupó. Por eso se
escucha el `MVPM_READY_PORT:<n>` que el motor anuncia por stdout; asumir el
pedido deja la ventana esperando en una puerta vacía con el servidor vivo.

**Los endpoints de licencia no llevan candado de licencia.** Sería un candado
con la llave adentro: una instalación con la prueba vencida no podría ni
preguntar por su estado ni activar lo que acaba de comprar.

**`main.js` no tiene lógica.** Importa `electron`, que no se puede cargar en
CI. Todo lo testeable vive en `lib/server-manager.js` y lo cubre
`lib/server-manager.test.js`, que corre con Node puro.
