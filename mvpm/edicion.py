"""Qué edición es ESTE binario. Se decide al compilar, no al ejecutar.

`ES_OWNER_BUILD` vale False en el repositorio y en todo lo que recibe un
cliente. El build de la Owner Edition lo pone en True justo antes de compilar
(`packaging/marcar_build_owner.py`), y a partir de ahí el programa abre sin la
prueba de 7 días sin pedir absolutamente nada: ni clave, ni token, ni archivo al
lado. Es el `.exe` que el dueño instala y usa.

## Por qué una constante y no un archivo

Porque un archivo ya se probó tres veces y las tres salió mal:

1. `MVPM_OWNER_BYPASS=1` — una variable de entorno documentada en el código que
   viaja en el ZIP. Un `export` desbloqueaba el producto.
2. `OWNER_EDITION` vacío — alcanzaba con que el archivo existiera. Un
   `type nul > OWNER_EDITION` desbloqueaba el producto.
3. `OWNER_EDITION` con un token firmado — ya no alcanzaba con crearlo, pero el
   archivo quedó versionado en un repositorio público. Peor que las anteriores,
   porque ese token no sólo activaba el modo dueño: pegado en el campo de
   licencia de la app era una licencia `enterprise` válida.

Una constante compilada no tiene ninguna de esas formas de fallar:

* **No es un token.** No hay nada que pegar en el campo de licencia. Lo que
  desbloquea este binario no desbloquea ningún otro.
* **No es un archivo.** No se puede copiar de la instalación del dueño a la de
  un cliente, porque no hay nada que copiar: en el `.exe` esto viaja como código
  nativo (`mvpm/` se compila a `.pyd` con Cython y los `.py` se borran antes de
  empaquetar — ver `packaging/strip_py_sources.py`).
* **No viaja fuera de su binario.** Desbloquea el ejecutable en el que se
  compiló y nada más.

## En qué se apoya, dicho de frente

En que el `.exe` de la Owner Edition no sea descargable por cualquiera. Sale
como artefacto de Actions y como prerelease de este repositorio, así que el
control de acceso es que el repositorio sea PRIVADO.

Ese es exactamente el razonamiento que falló antes: el diseño anterior decía lo
mismo y el repositorio era público. Hoy sí es privado. Si algún día vuelve a ser
público, esto deja de proteger nada y hay que volver al marcador firmado y atado
a la máquina (`mvpm/owner.py`), que sigue funcionando en paralelo y no depende
de la visibilidad del repositorio.

Los tests de `tests/test_owner.py` fijan que esta constante esté en False en
todo lo que se le entrega a un cliente: el instalador de cliente, el ZIP de la
landing y el propio repositorio.
"""

#: True sólo en el binario de la Owner Edition, puesto por el build.
#: En el repositorio SIEMPRE False — si esto se commitea en True, cualquier
#: copia del programa queda sin candado, incluida la que baja un cliente.
ES_OWNER_BUILD = False
