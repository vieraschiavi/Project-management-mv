"""Escape explícito para texto externo que se interpola en un st.markdown/st.write.

Streamlit ya neutraliza HTML crudo y esquemas `javascript:` en links markdown
cuando no se usa `unsafe_allow_html=True` (verificado empíricamente, ver
tests/test_seguro.py) — pero ese comportamiento es una propiedad de la
librería, no del código propio, y puede cambiar entre versiones o romperse si
alguien agrega `unsafe_allow_html=True` sin pensarlo. `escapar()` corta el
vector de raíz: HTML-escapea el texto y además neutraliza la sintaxis
markdown (`[]`, `*`, `_`, backtick) que un f-string interpola sin querer junto
al texto del usuario, así ese texto nunca llega activo al parser.

Mismo rol que `seguro.js` en el producto de Tasación: un único punto de
escape antes de insertar cualquier dato de usuario, API externa o base de
datos en el DOM.
"""

import html

_MD_ESCAPE = str.maketrans({
    "\\": "\\\\",
    "`": "\\`",
    "*": "\\*",
    "_": "\\_",
    "[": "\\[",
    "]": "\\]",
    "#": "\\#",
})


def escapar(texto) -> str:
    """Devuelve `texto` seguro para interpolar en un st.markdown/st.write.

    Orden importante: primero se neutraliza la sintaxis markdown y DESPUÉS se
    HTML-escapea. Al revés, `html.escape` genera entidades como `&#x27;` cuyo
    `#` la pasada de markdown volvería a escapar (`&\\#x27;`), rompiendo la
    entidad.
    """
    if texto is None:
        return ""
    return html.escape(str(texto).translate(_MD_ESCAPE), quote=True)
