# © 2026 Martín Viera. Todos los derechos reservados.
"""Conexión a Azure DevOps y reglas de calidad del backlog.

Lo que se verifica acá no es que las funciones no revienten: es que las reglas
agarren el defecto que dicen agarrar, que la corrección efectivamente lo saque,
y sobre todo que **no invente dato que no está** — que es la parte que un
cliente va a mirar con lupa antes de dejar subir un archivo a su Azure DevOps.
"""

from __future__ import annotations

import io
import json
import urllib.error
from datetime import date

import pandas as pd
import pytest

from mvpm import azure_devops as ado
from mvpm import backlog_calidad as bc
from mvpm.demo_azure import backlog_demo

HOY = date(2026, 9, 15)


@pytest.fixture
def demo() -> pd.DataFrame:
    return backlog_demo()


# --------------------------------------------------------------- credenciales


def test_el_token_no_aparece_en_el_repr():
    # Un dataclass normal imprimiría el PAT entero en cualquier traceback.
    cred = ado.Credenciales("acme", "Datos", "a@b.com", "pat-secretísimo-1234")
    assert "pat-secretísimo-1234" not in repr(cred)
    assert "acme" in repr(cred)


def test_falta_el_token_antes_que_nada():
    assert ado.Credenciales("", "p", "", "t").faltante() == "ado_falta_org"
    assert ado.Credenciales("o", "", "", "t").faltante() == "ado_falta_proyecto"
    assert ado.Credenciales("o", "p", "", "").faltante() == "ado_falta_token"
    assert ado.Credenciales("o", "p", "", "t").faltante() is None


@pytest.mark.parametrize("entrada, esperado", [
    ("https://dev.azure.com/acme", "acme"),
    ("https://dev.azure.com/acme/Proyecto/_boards", "acme"),
    ("dev.azure.com/acme/", "acme"),
    ("https://acme.visualstudio.com/Proyecto", "acme"),
    ("acme", "acme"),
    ("  ", ""),
])
def test_acepta_que_peguen_la_url_entera(entrada, esperado):
    assert ado.organizacion_de_url(entrada) == esperado


def test_el_token_sale_del_entorno_si_esta(monkeypatch):
    monkeypatch.setenv(ado.VAR_TOKEN, "  desde-el-entorno  ")
    assert ado.token_del_entorno() == "desde-el-entorno"
    monkeypatch.delenv(ado.VAR_TOKEN)
    assert ado.token_del_entorno() == ""


# ----------------------------------------------------------------------- HTTP


class _Respuesta(io.BytesIO):
    def __init__(self, cuerpo: bytes, tipo: str = "application/json"):
        super().__init__(cuerpo)
        self.headers = {"Content-Type": tipo}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def _falso_urlopen(respuestas: list, vistos: list):
    def abrir(pedido, timeout=None):
        vistos.append(pedido)
        r = respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
    return abrir


def test_una_pagina_de_login_no_pasa_por_respuesta_valida(monkeypatch):
    # El detalle que rompe a casi todo cliente nuevo: con credenciales malas
    # Azure DevOps NO devuelve 401, devuelve 200 con HTML de login. Si sólo se
    # mira el código de estado, el error que se reporta es el equivocado.
    html = _Respuesta(b"<html>Sign in to your account</html>", "text/html")
    monkeypatch.setattr(ado.urllib.request, "urlopen", _falso_urlopen([html], []))
    r = ado.probar_conexion(ado.Credenciales("acme", "Datos", "a@b.com", "malo"))
    assert r["ok"] is False
    assert r["clave"] == "ado_err_auth"


@pytest.mark.parametrize("codigo, clave", [
    (401, "ado_err_auth"), (403, "ado_err_permiso"),
    (404, "ado_err_no_existe"), (500, "ado_err_http"),
])
def test_cada_codigo_http_da_un_motivo_distinto(monkeypatch, codigo, clave):
    err = urllib.error.HTTPError(
        "u", codigo, "x", {}, io.BytesIO(json.dumps({"message": "detalle"}).encode()))
    monkeypatch.setattr(ado.urllib.request, "urlopen", _falso_urlopen([err], []))
    r = ado.probar_conexion(ado.Credenciales("acme", "Datos", "a@b.com", "t"))
    assert r["clave"] == clave


def test_probar_conexion_no_llama_a_la_red_si_faltan_campos(monkeypatch):
    def explotar(*a, **k):
        raise AssertionError("no debería salir a la red sin token")
    monkeypatch.setattr(ado.urllib.request, "urlopen", explotar)
    assert ado.probar_conexion(ado.Credenciales("acme", "Datos")) == {
        "ok": False, "clave": "ado_falta_token", "proyecto": "", "detalle": ""}


def test_traer_backlog_manda_el_mail_como_usuario_y_no_escribe(monkeypatch):
    vistos: list = []
    wiql = _Respuesta(json.dumps({"workItems": [{"id": 7}]}).encode())
    lote = _Respuesta(json.dumps({"value": [{
        "id": 7, "rev": 3, "fields": {
            "System.WorkItemType": "Task",
            "System.Title": "Conectar el tablero",
            "System.State": "Doing",
            "System.AssignedTo": {"displayName": "Ana Pérez"},
            "System.IterationPath": "Datos\\Sprint 2",
            "System.Parent": 5,
            "System.ChangedDate": "2026-09-01T10:00:00Z",
            "System.Description": "<p>Objetivo:</p><p>Entregable: PBI</p>",
        }}]}).encode())
    monkeypatch.setattr(ado.urllib.request, "urlopen",
                        _falso_urlopen([wiql, lote], vistos))

    df = ado.traer_backlog(ado.Credenciales("acme", "Datos", "yo@empresa.com", "pat"))

    assert list(df.columns) == list(ado.COLUMNAS)
    fila = df.iloc[0]
    assert fila["ID"] == 7 and fila["Rev"] == 3
    assert fila["AsignadoA"] == "Ana Pérez"          # no el dict de identidad
    assert fila["Padre"] == "5"
    assert fila["Modificado"] == "2026-09-01"        # sin la hora
    assert fila["Descripcion_texto"] == "Objetivo: Entregable: PBI"

    # El mail va como usuario del Basic Auth: es lo que queda en la auditoría
    # del cliente. Y la única llamada con cuerpo es la consulta WIQL, que lee.
    import base64
    usuario = base64.b64decode(
        vistos[0].get_header("Authorization").split()[1]).decode().split(":")[0]
    assert usuario == "yo@empresa.com"
    assert vistos[1].get_method() == "GET"
    assert json.loads(vistos[0].data)["query"].lstrip().upper().startswith("SELECT")


def test_el_modulo_no_tiene_ninguna_llamada_de_escritura():
    # Vale más que cualquier promesa en el LEEME: es la afirmación que un área
    # de seguridad va a querer verificar, y acá se verifica sola.
    import ast
    with open(ado.__file__, encoding="utf-8") as f:
        texto = f.read()
    arbol = ast.parse(texto)
    verbos_http = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    # Todo literal del código (no de los comentarios ni del docstring) que sea
    # un verbo HTTP. Da igual si va en method= directo o en un condicional.
    usados = {n.value for n in ast.walk(arbol)
              if isinstance(n, ast.Constant) and n.value in verbos_http}
    assert usados <= {"POST", "GET"}, f"verbo de escritura en el módulo: {usados}"
    # Azure DevOps escribe work items con este content-type y sólo con éste.
    assert "json-patch" not in texto


def test_html_a_texto_no_pega_las_palabras():
    assert ado.texto_plano("<p>Uno</p><p>Dos</p>") == "Uno Dos"
    assert ado.texto_plano("a<br>b") == "a b"
    assert ado.texto_plano("&lt;tag&gt; &amp; m&aacute;s") == "<tag> & m&aacute;s"
    assert ado.texto_plano("") == ""


# -------------------------------------------------------------------- archivos


def test_lee_un_export_en_ingles_y_con_bom():
    crudo = ("﻿ID,Work Item Type,Title,State,Assigned To,Iteration Path,"
             "Priority,Effort,Tags,Description\n"
             "12,Task,Hacer algo,Doing,Ana,Proy\\Sprint 1,2,,,texto\n").encode("utf-8")
    df = ado.leer_csv(crudo)
    assert list(df.columns) == list(ado.COLUMNAS)
    assert df.iloc[0]["Titulo"] == "Hacer algo"
    assert df.iloc[0]["Iteracion"] == "Proy\\Sprint 1"
    assert df.iloc[0]["Descripcion_texto"] == "texto"


def test_el_csv_de_salida_conserva_el_id(demo):
    # Si el ID se pierde, subir el archivo corregido DUPLICA el backlog entero
    # en vez de actualizarlo. Es la diferencia entre arreglar y romper.
    corregido, _ = bc.corregir(demo, hoy=HOY)
    salida = ado.a_csv_azure(corregido)
    encabezado = salida.splitlines()[0]
    assert encabezado.startswith("ID,Work Item Type,Title,")
    assert "Iteration Path" in encabezado
    leido = pd.read_csv(io.StringIO(salida), dtype=str)
    assert leido["ID"].notna().all()
    assert len(leido) == len(corregido)


def test_el_csv_de_salida_vuelve_a_entrar_por_leer_csv(demo):
    # Ida y vuelta: lo que sale tiene que poder volver a leerse sin perder nada.
    corregido, _ = bc.corregir(demo, hoy=HOY)
    vuelta = ado.leer_csv(ado.a_csv_azure(corregido))
    assert len(vuelta) == len(corregido)
    assert list(vuelta["Titulo"]) == list(corregido["Titulo"])


# --------------------------------------------------------------- demo y reglas


def test_la_demo_dispara_todas_las_reglas(demo):
    # Una demo donde la mitad de las reglas no tiene ejemplo miente por omisión.
    por_regla = bc.resumen(bc.revisar(demo, hoy=HOY))["por_regla"]
    sin_ejemplo = set(bc.REGLAS) - set(por_regla)
    assert not sin_ejemplo, f"reglas sin caso en la demo: {sorted(sin_ejemplo)}"


def test_la_demo_es_sintetica(demo):
    """La regla del repo: la demo no lleva dato de ningún cliente.

    Se verifica por lista blanca y no por lista negra a propósito. Enumerar acá
    los nombres reales que NO tienen que aparecer los metería en un repositorio
    público, que es exactamente lo que se quiere evitar. Así, además, la regla
    no se puede saltear con un nombre que nadie pensó en prohibir.
    """
    from mvpm import demo_azure

    personas = {p for p in demo["AsignadoA"] if p}
    assert personas <= {demo_azure._P, demo_azure._D}, \
        f"apareció alguien que no está declarado en la demo: {personas}"

    # Ninguna celda puede traer un mail: un backlog real los arrastra siempre.
    texto = " ".join(demo.astype(str).to_numpy().ravel())
    assert "@" not in texto

    rutas = {r.split("\\")[0] for r in demo["Iteracion"] if r}
    assert rutas == {demo_azure.RAIZ}


def test_un_backlog_vacio_no_rompe():
    vacio = pd.DataFrame(columns=list(ado.COLUMNAS))
    assert bc.revisar(vacio) == []
    corregido, cambios = bc.corregir(vacio)
    assert corregido.empty and cambios == []


def test_no_acusa_prioridad_uniforme_con_dos_items():
    # Con un backlog chico, "el 80% comparte prioridad" es ruido, no hallazgo.
    chico = pd.DataFrame([
        {**dict.fromkeys(ado.COLUMNAS, ""), "ID": "1", "Titulo": "A", "Prioridad": "2"},
        {**dict.fromkeys(ado.COLUMNAS, ""), "ID": "2", "Titulo": "B", "Prioridad": "2"},
    ])
    reglas = {h.regla for h in bc.revisar(chico, hoy=HOY)}
    assert "prioridad_uniforme" not in reglas
    assert "bus_factor" not in reglas


# ------------------------------------------------------- reglas, una por una


def _reglas_de(df, item):
    return {h.regla for h in bc.revisar(df, hoy=HOY) if h.item == item}


def test_titulo_delete_se_detecta_y_sale_del_backlog(demo):
    assert "titulo_marcador" in _reglas_de(demo, "204")
    corregido, cambios = bc.corregir(demo, hoy=HOY)
    assert "204" not in set(corregido["ID"])
    assert any(c.item == "204" and c.accion == "quitar" for c in cambios)


def test_un_titulo_vago_se_marca_pero_no_se_inventa(demo):
    # 212 es "TBD": puede haber trabajo real detrás, así que se queda.
    assert "titulo_marcador" in _reglas_de(demo, "212")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "212"].iloc[0]
    assert fila["Titulo"] == "TBD"                      # nadie le inventó un nombre
    assert bc.ETIQUETA_REVISAR in fila["Tags"]


def test_titulos_duplicados_se_desambiguan_con_el_padre(demo):
    assert "titulo_duplicado" in _reglas_de(demo, "206")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    titulos = {corregido[corregido["ID"] == i].iloc[0]["Titulo"] for i in ("206", "207")}
    assert len(titulos) == 2
    assert all(t.endswith(")") for t in titulos)
    assert "Tablero acotado de venta diaria" in " ".join(titulos)


def test_el_estado_sale_del_titulo_y_va_a_la_descripcion(demo):
    assert "titulo_con_estado" in _reglas_de(demo, "215")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "215"].iloc[0]
    assert fila["Titulo"] == "Refresco automático cada 8 horas"
    # No se pierde: la aclaración queda registrada en la descripción.
    assert "MANUAL mientras no se resuelve" in fila["Descripcion_texto"]
    assert bc.NOTA_ESTADO.strip() in fila["Descripcion_texto"]


def test_la_iteracion_movil_pasa_a_un_sprint_numerado(demo):
    assert "iteracion_movil" in _reglas_de(demo, "216")
    corregido, cambios = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "216"].iloc[0]
    # La demo tiene Sprint 1 y Sprint 2, así que "Actual" se resuelve a Sprint 3.
    assert fila["Iteracion"].endswith("Sprint 3")
    # Y el supuesto queda escrito: antes y después, para poder pisarlo.
    cambio = next(c for c in cambios if c.item == "216" and c.campo == "Iteracion")
    assert "Sprint Actual" in cambio.antes and "Sprint 3" in cambio.despues


def test_el_estancado_lleva_los_dias_reales(demo):
    assert "estancado" in _reglas_de(demo, "201")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "201"].iloc[0]
    # 2026-06-11 → 2026-09-15 son 96 días. El número sale de la fecha, no de una
    # opinión: por eso el test lo fija.
    assert f"{bc.ETIQUETA_ESTANCADO}-96d" in fila["Tags"]


def test_no_marca_estancado_lo_que_esta_cerrado(demo):
    # 204 y 219 están Done desde junio; estar quieto es lo correcto.
    assert "estancado" not in _reglas_de(demo, "219")


def test_la_etiqueta_informal_se_reemplaza_por_una_que_se_filtra(demo):
    assert "tag_informal" in _reglas_de(demo, "214")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    tags = corregido[corregido["ID"] == "214"].iloc[0]["Tags"]
    assert "VERLO DESPUES" not in tags
    assert "revisar" in tags


def test_la_descripcion_vacia_queda_con_estructura_pero_sin_contenido(demo):
    assert "sin_descripcion" in _reglas_de(demo, "203")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    d = corregido[corregido["ID"] == "203"].iloc[0]["Descripcion_texto"]
    assert "Objetivo" in d and "Criterio de aceptación" in d
    # Lo importante: los huecos quedan marcados, no rellenados con algo plausible.
    assert d.count("<completar>") == 3


def test_el_criterio_de_aceptacion_se_agrega_sin_pisar_lo_que_habia(demo):
    assert "sin_criterio_aceptacion" in _reglas_de(demo, "205")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    d = corregido[corregido["ID"] == "205"].iloc[0]["Descripcion_texto"]
    assert "Maqueta" in d or "previsualizar" in d          # lo original sigue ahí
    assert "Criterio de aceptación: <completar>" in d


def test_el_que_ya_tenia_criterio_no_se_toca(demo):
    assert "sin_criterio_aceptacion" not in _reglas_de(demo, "221")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    antes = demo[demo["ID"] == "221"].iloc[0]["Descripcion_texto"]
    despues = corregido[corregido["ID"] == "221"].iloc[0]["Descripcion_texto"]
    assert antes == despues


def test_el_adjunto_se_marca_porque_no_viaja(demo):
    assert "depende_de_adjunto" in _reglas_de(demo, "210")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    d = corregido[corregido["ID"] == "210"].iloc[0]["Descripcion_texto"]
    assert bc.NOTA_ADJUNTO in d


def test_la_estimacion_faltante_se_etiqueta_pero_nunca_se_inventa(demo):
    assert "sin_esfuerzo" in _reglas_de(demo, "203")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "203"].iloc[0]
    assert fila["Esfuerzo"] == ""                    # sigue vacío, y así debe ser
    assert bc.ETIQUETA_SIN_ESTIMAR in fila["Tags"]


def test_no_pide_estimacion_a_lo_que_ya_esta_cerrado(demo):
    # 219 está Done sin esfuerzo: estimarlo ahora no sirve para nada.
    assert "sin_esfuerzo" not in _reglas_de(demo, "219")


def test_el_huerfano_se_etiqueta_pero_no_se_le_inventa_un_padre(demo):
    assert "sin_padre" in _reglas_de(demo, "208")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "208"].iloc[0]
    assert fila["Padre"] == ""
    # Es un Issue, no una Task: se informa, y la etiqueta va en las hojas.
    assert "208" in {h.item for h in bc.revisar(demo, hoy=HOY) if h.regla == "sin_padre"}


def test_sin_responsable_se_etiqueta_sin_asignarle_a_nadie(demo):
    assert "sin_asignar" in _reglas_de(demo, "220")
    corregido, _ = bc.corregir(demo, hoy=HOY)
    fila = corregido[corregido["ID"] == "220"].iloc[0]
    assert fila["AsignadoA"] == ""
    assert bc.ETIQUETA_SIN_RESPONSABLE in fila["Tags"]


def test_rev_alto_se_informa_y_no_se_corrige(demo):
    assert "rev_alta" in _reglas_de(demo, "213")
    corregido, cambios = bc.corregir(demo, hoy=HOY)
    assert not any(c.regla == "rev_alta" for c in cambios)
    assert corregido[corregido["ID"] == "213"].iloc[0]["Rev"] == "27"


def test_prioridad_y_bus_factor_son_del_backlog_no_de_un_item(demo):
    hallazgos = bc.revisar(demo, hoy=HOY)
    globales = [h for h in hallazgos if h.regla in ("prioridad_uniforme", "bus_factor")]
    assert len(globales) == 2
    assert all(h.item == "" for h in globales)
    # El dato exacto es lo que hace que la conversación arranque de un hecho.
    assert all("/" in h.dato for h in globales)


# -------------------------------------------------------------- lo que corrige


def test_corregir_resuelve_todo_lo_que_es_derivable(demo):
    # Las reglas que sí se pueden arreglar con lo que hay en el propio backlog
    # tienen que desaparecer en la segunda pasada.
    _, _ = bc.corregir(demo, hoy=HOY)
    corregido, _ = bc.corregir(demo, hoy=HOY)
    quedan = set(bc.resumen(bc.revisar(corregido, hoy=HOY))["por_regla"])
    derivables = {"titulo_duplicado", "titulo_con_estado", "sin_descripcion",
                  "sin_criterio_aceptacion", "iteracion_movil", "tag_informal"}
    assert not (quedan & derivables), f"quedaron sin corregir: {quedan & derivables}"


def test_corregir_no_toca_el_dataframe_original(demo):
    antes = demo.copy()
    bc.corregir(demo, hoy=HOY)
    pd.testing.assert_frame_equal(demo, antes)


def test_corregir_es_idempotente(demo):
    una, _ = bc.corregir(demo, hoy=HOY)
    dos, _ = bc.corregir(una, hoy=HOY)
    tres, _ = bc.corregir(dos, hoy=HOY)
    # Sin esto, cada pasada agregaría otra vez "Criterio de aceptación" o
    # renombraría un título ya desambiguado: el archivo se degradaría solo.
    pd.testing.assert_frame_equal(dos, tres)


def test_ningun_campo_de_dato_se_rellena_solo(demo):
    # La promesa central del módulo, verificada campo por campo: Esfuerzo,
    # Padre y AsignadoA nunca pasan de vacío a tener algo.
    corregido, _ = bc.corregir(demo, hoy=HOY)
    por_id = {r["ID"]: r for _, r in corregido.iterrows()}
    for _, original in demo.iterrows():
        fila = por_id.get(original["ID"])
        if fila is None:
            continue
        for campo in ("Esfuerzo", "Padre", "AsignadoA", "Prioridad", "Estado"):
            if not str(original[campo]).strip():
                assert not str(fila[campo]).strip(), \
                    f"se inventó {campo} en el ítem {original['ID']}"


def test_los_hallazgos_vienen_ordenados_por_severidad(demo):
    severidades = [h.severidad for h in bc.revisar(demo, hoy=HOY)]
    orden = [bc.ORDEN_SEVERIDAD[s] for s in severidades]
    assert orden == sorted(orden)


def test_cada_regla_tiene_nombre_porque_y_como_queda_en_los_tres_idiomas():
    from mvpm import i18n
    for regla in bc.REGLAS:
        for prefijo in ("adoq_r_", "adoq_p_", "adoq_f_"):
            clave = prefijo + regla
            assert clave in i18n._STRINGS, f"falta la clave {clave}"
            for idioma in ("es", "en", "pt"):
                assert i18n._STRINGS[clave].get(idioma), f"falta {clave} en {idioma}"


def test_la_pantalla_abre_y_ofrece_el_csv_corregido(tmp_path, monkeypatch):
    """La sección entera, dibujada de verdad por Streamlit y sin conexión.

    Importa acá más que en otras pantallas porque el análisis y la corrección se
    evalúan AL dibujar: si `corregir()` levantara con el backlog de demo, la
    sección quedaría inservible justo en la demo que se le muestra a un cliente.
    """
    import pathlib

    from streamlit.testing.v1 import AppTest

    from mvpm import db

    monkeypatch.setenv("MVPM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "_STORE_DIR", tmp_path)
    monkeypatch.setattr(db, "_DB_FILE", tmp_path / "datos.db")

    raiz = pathlib.Path(__file__).resolve().parent.parent
    at = AppTest.from_file(str(raiz / "app" / "app.py"), default_timeout=180)
    at.run()

    at.text_input[0].set_value("Tester")
    at.text_input[1].set_value("tester@ejemplo.com")
    at.text_input[2].set_value("Turbina-9-Verde")
    [b for b in at.button if "administrador" in b.label][0].click().run()
    assert not at.exception

    at.radio[0].set_value("Azure DevOps — calidad del backlog").run()
    assert not at.exception, f"la pantalla de Azure DevOps explotó: {at.exception}"

    etiquetas = [b.label for b in at.download_button]
    assert any("corregido" in e for e in etiquetas), \
        f"no está el botón del CSV corregido; los que hay: {etiquetas}"
    # El origen por defecto es la demo, así que tiene que haber hallazgos a la
    # vista sin haber tipeado una sola credencial.
    assert any(m.value != "0" for m in at.metric)


def test_la_tabla_de_hallazgos_sale_traducida(demo):
    from mvpm import i18n
    tabla = bc.a_dataframe(bc.revisar(demo, hoy=HOY), lambda k: i18n.t(k, "en"))
    assert list(tabla.columns) == ["ID", "severidad", "regla", "titulo", "dato",
                                   "por_que", "como_queda"]
    assert not tabla["por_que"].eq("").any()
    assert "placeholder" in " ".join(tabla["regla"]).lower()
