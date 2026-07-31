"""Configuración de pytest para todo el repo.

Pone la raíz del proyecto en sys.path para que los tests puedan importar
`mvpm` y `api` sin depender de cómo se los invoque.

Por qué hace falta: `python -m pytest` agrega el directorio actual a sys.path,
pero `pytest` a secas NO. Como los tests se venían corriendo con `python -m`,
nadie notó que `pytest tests/` —que es lo que hace `./run.sh test` y lo que
corre el CI— fallaba en la recolección con "No module named 'mvpm'". Con este
archivo, las dos formas funcionan igual.

Vive en la raíz y no en tests/ a propósito: pytest inserta el directorio del
conftest más externo, que es justo la raíz que se necesita en sys.path.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
