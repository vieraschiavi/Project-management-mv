# © 2026 Martín Viera. Todos los derechos reservados.
"""Recorre TODAS las pestañas del dashboard real (Streamlit AppTest) con un
archivo del usuario importado encima de la demo sembrada: ninguna pestaña
puede mostrar un proyecto de la demo, y "Volver a la demo" la trae de vuelta."""

import pathlib

import pandas as pd
import pytest

from mvpm import db, demo_data, fuente

NOMBRES_DEMO = set(demo_data.projects()["nombre"])


def _textos(at) -> str:
    partes = [e.value for e in at.markdown] + [e.value for e in at.caption]
    partes += [str(getattr(e, "body", "")) for e in at.info] + [e.value for e in at.code]
    partes += [str(getattr(e, "value", "")) for e in at.text]
    for m in at.metric:
        partes.append(str(m.value))
    for df in at.dataframe:
        v = df.value
        partes.append(v.to_csv() if isinstance(v, pd.DataFrame) else str(v))
    return "\n".join(str(p) for p in partes)


@pytest.fixture
def app(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from mvpm import licensing

    monkeypatch.setenv("MVPM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")
    monkeypatch.setattr(licensing, "_TRIAL_FILE", tmp_path / "trial.json")
    monkeypatch.setattr(licensing, "_RUTAS_TRIAL", (tmp_path / "trial.json",))

    raiz = pathlib.Path(__file__).resolve().parent.parent
    at = AppTest.from_file(str(raiz / "app" / "app.py"), default_timeout=120)
    at.run()
    at.text_input[0].set_value("Tester")
    at.text_input[1].set_value("tester@ejemplo.com")
    at.text_input[2].set_value("Turbina-9-Verde")
    [b for b in at.button if "administrador" in b.label][0].click().run()
    assert not at.exception
    return at


def test_todas_las_pestanas_leen_solo_el_archivo_del_usuario(app):
    at = app
    db.cargar_datos_de_ejemplo()
    for nombre in ("Obra Norte", "Obra Sur"):
        db.crear_proyecto(nombre=nombre, portafolio="Ingeniería", segmento="Interno",
                          criticidad="Alta", presupuesto=1000, ejecutado=100,
                          fecha_inicio="2026-03-01", fecha_fin="2026-12-01",
                          origen=fuente.origen_archivo("cartera.xlsx"))
    at.run()
    assert not at.exception

    nav = at.sidebar.radio[0]
    assert "Demo con datos reales" not in " ".join(nav.options)
    assert any("cartera.xlsx" in s.value for s in at.sidebar.success)

    for opcion in list(nav.options):
        at.sidebar.radio[0].set_value(opcion).run()
        assert not at.exception, f"'{opcion}' explotó: {at.exception}"
        texto = _textos(at)
        filtradas = sorted(n for n in NOMBRES_DEMO if n in texto)
        assert not filtradas, f"'{opcion}' muestra la demo: {filtradas}"

    [b for b in at.sidebar.button if b.key == "fuente_volver_demo"][0].click().run()
    assert not at.exception
    assert any("ejemplo" in s.value for s in at.sidebar.info)
    at.sidebar.radio[0].set_value(at.sidebar.radio[0].options[at.sidebar.radio[0].options.index("Portafolio")]).run()
    assert any(n in _textos(at) for n in NOMBRES_DEMO)
