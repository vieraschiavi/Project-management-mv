# MV Project Management — paquete servidor (Owner)

Para el caso en que una consultora entra a un proyecto de un cliente y **el
dato del cliente no puede quedar en la laptop de la consultora**.

Sin `.exe`, sin `.bat`, sin instalador y sin permisos de administrador.

---

## Antes que nada: dónde puede correr

El programa tiene que ejecutarse en algún lado. No hay formato de paquete que
evite eso, así que conviene saber en cuál de estos casos estás **antes** de
prometerle algo a un área de seguridad.

| Situación | Qué usar | ¿El dato toca tu laptop? |
|---|---|---|
| El cliente tiene Docker | `docker compose up -d --build` | **No** |
| El cliente tiene una VM/servidor con Python | `python3 iniciar.py` ahí | **No** |
| No hay máquina del cliente, sólo tu laptop | `python3 iniciar.py --local` | **Sí** |
| Tu laptop no ejecuta nada y no hay máquina del cliente | *no hay solución de paquete* | — |

La última fila es la incómoda y es real: si la política bloquea toda ejecución
y el cliente no aporta una máquina, lo que hace falta es un escritorio remoto
(VDI, Citrix) o un servidor del cliente. Pedir eso es más barato que descubrir
a mitad del proyecto que la única forma de trabajar era copiar el dato al
disco equivocado.

---

## Opción A — Docker en la infraestructura del cliente

La más limpia para defender ante seguridad, porque todo lo que hay que
verificar está en dos archivos de texto que el cliente puede leer.

```bash
unzip MVPM_Owner_Servidor_v*.zip -d mvpm && cd mvpm
docker compose up -d --build
```

Queda en `http://<ip-del-servidor>:8501`.

Lo que el cliente puede comprobar leyendo el `Dockerfile` y el
`docker-compose.yml`, sin confiar en nadie:

- **No hay ninguna URL de salida.** El motor de reglas es local y la IA es
  opcional: sólo se enciende si el cliente pone **su** clave. Streamlit manda
  estadísticas de uso por defecto y acá están **apagadas** explícitamente; se
  comprueba en `docker logs`, donde no debe aparecer *"Collecting usage
  statistics"*.
- **El dato vive en un volumen suyo** (`/datos`), no adentro de la imagen.
  Borrar el contenedor no se lleva el dato; copiar la imagen tampoco.
- Corre como usuario sin privilegios, con el sistema de archivos de sólo
  lectura y `no-new-privileges`.

Para que el dato quede en una ruta que se pueda respaldar y auditar, cambiar
el volumen por un bind mount en `docker-compose.yml`:

```yaml
    volumes:
      - /srv/mvpm/datos:/datos
```

Si el acceso va por VPN o detrás de un proxy inverso, publicá sólo el proxy:

```yaml
    ports:
      - "127.0.0.1:8501:8501"
```

## Opción B — Python en la máquina del cliente

Cuando hay VM pero no Docker.

```bash
unzip MVPM_Owner_Servidor_v*.zip -d mvpm && cd mvpm
python3 iniciar.py
```

La primera vez arma un entorno virtual **dentro de esta misma carpeta** e
instala las dependencias ahí. No instala nada en el sistema, no pide
administrador y no toca el registro de Windows: borrar la carpeta lo deshace
todo, sin dejar residuos en el perfil del usuario.

Eso último es deliberado: la instalación usa `--no-cache-dir`, porque pip por
defecto deja cientos de megas de wheels en el perfil, que es justo donde una
máquina corporativa suele tener cuota de disco. Se paga con que una
reinstalación vuelva a descargar.

Antes de abrir el puerto imprime en qué modo está, en qué dirección escucha y
en qué carpeta va a guardar. Eso último es el argumento entero, y se verifica
abriendo la carpeta.

```
  Escucha en   : 0.0.0.0:8501
  Dato guardado: /srv/mvpm/datos
```

Opciones:

```bash
python3 iniciar.py --local              # sólo esa máquina, nadie más entra
python3 iniciar.py --puerto 9000
python3 iniciar.py --datos /srv/mvpm    # o la variable MVPM_DATA_DIR
```

> **Si la VM del cliente es Windows**, el comando es `python iniciar.py` — sin
> el `3`. En Windows `python3` normalmente no existe y, peor, en las versiones
> recientes abre la Microsoft Store en vez de dar un error, así que parece que
> el paquete no funciona cuando en realidad es el nombre del comando.
> Todo lo demás es idéntico: mismo entorno virtual dentro de la carpeta, misma
> carpeta `datos\`, mismos modos.

## Opción C — Tu laptop, sin instalar nada

```bash
python3 iniciar.py --local
```

Funciona igual, pero **el dato queda en tu disco**. Si el motivo por el que
estás leyendo esto es que el dato del cliente no puede estar en tu laptop,
esta opción no sirve para ese proyecto: sirve para tus propias pruebas y
demos.

---

## Sobre la licencia: este paquete no pide ninguna

Abre desbloqueado, sin clave, sin token y sin archivo al lado.

Eso tiene una consecuencia que conviene tener presente y no descubrir después:
`mvpm/` viaja en texto plano, así que **cualquiera que tenga este archivo
tiene el producto completo**, incluido el equipo de sistemas del cliente donde
lo dejes instalado. No es un paquete para publicar ni para dejar en un
repositorio: es para llevarlo uno mismo a donde se va a usar.

Si en algún momento preferís lo contrario —que el paquete quede atado a la
máquina donde se activa, de modo que copiarlo a otro lado no sirva de nada—
ese mecanismo existe y sigue funcionando: es el marcador firmado de
`mvpm/owner.py`, que se activa una vez por máquina con tu clave privada.

## Qué se lleva la laptop de la consultora

En las opciones A y B: **nada**. Abre un navegador contra la máquina del
cliente. No hay archivos, no hay base de datos, no hay caché de datos del
cliente en tu disco.

## Qué escribe el programa, exactamente

Dicho con precisión, porque "no escribe nada" no sería cierto y un área de
seguridad lo va a verificar:

| Qué | Dónde | ¿Dato del cliente? |
|---|---|---|
| Base SQLite con todo el portafolio | `datos/datos.db` (o el volumen) | **Sí** — y es lo único |
| Fecha de primer uso | perfil del usuario de la máquina | No |
| Hash identificador de la máquina | perfil del usuario de la máquina | No |

Verificado escribiendo un dato de prueba y buscándolo después en todo el
disco: aparece únicamente en `datos/datos.db`. En el contenedor los dos
archivos de estado caen en un `tmpfs` y desaparecen al apagarlo.
