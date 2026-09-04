# © 2026 Martín Viera. Todos los derechos reservados.
"""MV Project Management — motor de gestión de proyectos con IA aditiva."""

APP_NAME = "MV Project Management"

#: La versión del producto, y la única. El instalador de escritorio ya venía
#: en 0.2.0 —es la que está compilada y distribuida— mientras el motor seguía
#: diciendo 0.1.0: el número lo ataba `packaging/instalador.iss`, que se fue
#: junto con el build de Inno Setup. Se alinea con lo que ya salió, no al
#: revés. Lo fija `tests/test_instalador_escritorio.py`.
VERSION = "0.2.0"

BRAND = {
    "navy": "#081527",
    "navy2": "#0c2137",
    "amber": "#f2b441",
    "amber2": "#e39a2e",
    "ink": "#eaf1fb",
    "muted": "#9db0c8",
    "paper": "#ffffff",
    "tint": "#f4f7fb",
    "green": "#00c896",
    "red": "#e05c5c",
    "blue": "#2f74c0",
}
