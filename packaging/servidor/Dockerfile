# © 2026 Martín Viera. Todos los derechos reservados.
#
# MV Project Management en la infraestructura del cliente.
#
# El argumento ante un área de seguridad se sostiene en tres hechos que se
# pueden verificar mirando este archivo, sin creerle a nadie:
#
#   1. No hay ninguna URL de salida. El motor de reglas es local y la IA es
#      opcional: sólo se activa si el cliente configura SU propia clave.
#      Streamlit manda estadísticas de uso a su servidor POR DEFECTO, así que
#      el CMD las apaga explícitamente — sin esa línea la frase de arriba sería
#      mentira, y es verificable con `docker logs` (no debe aparecer
#      "Collecting usage statistics").
#   2. El dato vive en un volumen del cliente (/datos), no adentro de la
#      imagen. Borrar el contenedor no se lleva el dato, y copiar la imagen no
#      se lleva el dato tampoco.
#   3. Corre como usuario sin privilegios.
#
# Construir y levantar:
#     docker compose up -d --build
#
# El dashboard queda en el puerto 8501 de esa máquina. La laptop de la
# consultora sólo abre un navegador: no instala nada y no guarda una fila.

FROM python:3.11-slim

# Sin bytecode y sin buffer: los logs salen en orden en `docker logs`, que es
# lo único que va a mirar el sysadmin del cliente cuando algo falle.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Las dependencias primero y solas: así una edición del código no invalida la
# capa de pip, que es la cara.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# El dato NO va adentro de la imagen. /datos se monta como volumen del cliente:
# es lo que hace verificable la frase "el dato se queda acá".
ENV MVPM_DATA_DIR=/datos \
    MVPM_MODO_INSTALACION=servidor

# Usuario sin privilegios, dueño de /datos para poder escribir el SQLite.
RUN useradd --create-home --uid 10001 mvpm \
 && mkdir -p /datos \
 && chown -R mvpm:mvpm /datos /app
USER mvpm

EXPOSE 8501

# `--server.address 0.0.0.0` acá NO es el agujero que era en una laptop: es un
# contenedor, y lo que se publica hacia afuera lo decide el mapeo de puertos
# del compose, no este proceso.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).status==200 else 1)"

CMD ["python", "-m", "streamlit", "run", "app/app.py", \
     "--server.port", "8501", "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--browser.gatherUsageStats", "false"]
