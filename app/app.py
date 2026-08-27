# © 2026 Martín Viera. Todos los derechos reservados.
"""MV Project Management — dashboard operativo (Streamlit).

Un único motor (mvpm/) alimenta este dashboard, la API REST (api/main.py) y
los exportadores — sin lógica de negocio duplicada entre capas. Los datos
viven en una base SQLite real (mvpm/db.py) en el equipo del cliente, detrás
de un login con usuario y contraseña (mvpm/auth.py).
"""

import pathlib
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from mvpm import (
    BRAND,
    advisor,
    ai,
    auth,
    capacitacion,
    case_study,
    catalog,
    conectores,
    data_engineering as dataeng,
    db,
    demo_pharma,
    demo_real,
    dependencies as dep_mod,
    exporters,
    glossary,
    governance,
    health,
    help_center,
    i18n,
    importer,
    invitado,
    licensing,
    modelos,
    organigrama,
    owner,
    plantillas,
    pmbok,
    policies,
    prioritizer,
    reports,
    reviews,
    seguro,
    tutorial,
)
from mvpm import copilot as copilot_mod

#: El logo MV. Vive dentro de `mvpm/` porque el spec de PyInstaller copia ese
#: directorio entero (`datas`), así que viaja en el .exe sin sumar una regla de
#: empaquetado nueva. Se resuelve desde el paquete y no desde este archivo:
#: congelado, app.py y mvpm/ no quedan uno al lado del otro.
LOGO = pathlib.Path(copilot_mod.__file__).resolve().parent / "data" / "logo-mv.png"

st.set_page_config(
    page_title="MV Project Management",
    # Si el archivo faltara —una copia incompleta—, Streamlit levanta igual con
    # el icono por defecto en vez de morir en la primera línea de la app.
    page_icon=str(LOGO) if LOGO.exists() else ":material/checklist:",
    layout="wide",
    # Sin esto el menú "···" ofrece Record a screencast, Report a bug y About
    # Streamlit: tres cosas que le cuentan al cliente con qué está hecho el
    # producto que compró, y ninguna que le sirva.
    menu_items={"Get help": None, "Report a Bug": None, "About": None},
)

st.markdown(
    f"""
    <style>
    /* El programa se instala con su icono, su acceso directo y su ventana
       propia (mvpm/ventana.py). Lo que quedaba delatando que abajo hay
       Streamlit es su barra de herramientas: el botón Deploy, el menú
       hamburguesa, la franja de color de arriba y el "Made with Streamlit" del
       pie. Nada de eso significa algo para quien usa el programa —el Deploy
       incluso invita a publicar el portafolio del cliente en la nube de
       Streamlit— así que se oculta.

       Se ocultan los elementos puntuales y NO el header entero a propósito: la
       flecha para plegar y desplegar la barra lateral vive ahí, y esconder el
       header completo deja al usuario sin forma de recuperarla si la cierra. */
    [data-testid="stToolbar"] {{ visibility: hidden; height: 0; position: fixed; }}
    [data-testid="stDecoration"] {{ display: none; }}
    [data-testid="stStatusWidget"] {{ display: none; }}
    [data-testid="stAppDeployButton"] {{ display: none; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; height: 0; }}
    [data-testid="stHeader"] {{ background: transparent; }}

    .stApp {{ background-color: {BRAND['navy']}; }}
    [data-testid="stMetricValue"] {{ color: {BRAND['amber']}; }}
    h1, h2, h3 {{ color: {BRAND['ink']}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

db.init_db()


def T(key: str) -> str:
    return i18n.t(key, LANG_ES_DEFAULT)


# El selector de idioma va ACÁ, antes del login: si se definiera después (como
# antes), la primera pantalla que ve cualquier persona —probar sin cuenta,
# crear la cuenta de administrador, iniciar sesión— quedaba fija en español
# pasara lo que pasara, porque T() ya se había usado con el default antes de
# que existiera el widget. `key=` para que Streamlit lo recuerde entre reruns
# de la misma sesión sin depender de dónde en el código se lo vuelva a llamar.
LANG = st.sidebar.selectbox("Idioma / Language / Idioma", ["es", "en", "pt"],
                            index=0, key="lang_sel")
LANG_ES_DEFAULT = LANG  # T() ya definida arriba usa esta variable global


# ------------------------------------------------------------- autenticación

if "user" not in st.session_state:
    st.session_state["user"] = None

# Modo invitado: se puede usar el producto sin crear cuenta. Los datos viven en
# la sesión (mvpm/invitado.py), no en la base — ver ese módulo para el porqué.
INVITADO = st.session_state.get("invitado", False)


def _entrar_como_invitado(almacen) -> None:
    st.session_state["invitado"] = True
    st.session_state["invitado_almacen"] = almacen
    st.session_state["user"] = {"nombre": "Invitado", "rol": "invitado", "id": None}
    st.rerun()


if st.session_state["user"] is None:
    st.title("MV Project Management")

    # Primero lo que no pide nada a cambio: probar el producto. La cuenta se
    # ofrece abajo, para quien ya decidió que quiere guardar su trabajo.
    st.markdown(f"#### {T('login_try_now_header')}")
    _c1, _c2 = st.columns(2)
    if _c1.button(T("login_btn_upload_excel"), type="primary", icon=":material/upload_file:",
                  use_container_width=True):
        _entrar_como_invitado(invitado.almacen_vacio())
    if _c2.button(T("login_btn_uk_demo"),
                   icon=":material/public:",
                  use_container_width=True):
        _entrar_como_invitado(invitado.con_portafolio_real())
    st.caption(T("login_guest_caption"))
    st.divider()

    if db.contar_usuarios() == 0:
        st.subheader(T("login_create_admin_header"))
        st.caption(T("login_create_admin_caption"))
        with st.form("bootstrap_admin"):
            nombre = st.text_input(T("field_name"))
            email = st.text_input(T("field_email"))
            password = st.text_input(T("field_password_min8"), type="password")
            enviado = st.form_submit_button(T("login_btn_create_admin"))
            if enviado:
                try:
                    user = auth.registrar(email, nombre, password)
                    st.session_state["user"] = user
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        tab_login, tab_registro = st.tabs([T("tab_login"), T("tab_register")])
        with tab_login:
            with st.form("login"):
                email = st.text_input(T("field_email"), key="login_email")
                password = st.text_input(T("field_password"), type="password", key="login_password")
                enviado = st.form_submit_button(T("tab_login"))
                if enviado:
                    user = auth.iniciar_sesion(email, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error(T("login_err_bad_credentials"))
        with tab_registro:
            with st.form("registro"):
                nombre = st.text_input(T("field_name"), key="reg_nombre")
                email = st.text_input(T("field_email"), key="reg_email")
                password = st.text_input(T("field_password_min8"), type="password", key="reg_password")
                enviado = st.form_submit_button(T("tab_register"))
                if enviado:
                    try:
                        user = auth.registrar(email, nombre, password)
                        st.session_state["user"] = user
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

user = st.session_state["user"]

LICENSE_TOKEN = st.sidebar.text_input(
    T("license_token_label"), type="password",
    help=T("license_token_help"),
) or None

# El dueño no tiene que pegar ningún token en su propia herramienta: si esta
# máquina tiene su clave privada, el marcador se firma solo en el arranque.
# En la máquina de un cliente esto no hace nada —no hay clave que firmar— así
# que no afloja el candado: ver mvpm/owner.py.
owner.activar_automatico()

# Y si escribe su email ahí arriba, se intenta lo mismo explícitamente. El
# email NO es la credencial: sin la clave en la máquina no desbloquea nada,
# justamente para que un cliente no entre gratis escribiendo el mail del dueño,
# que está publicado en la landing.
if LICENSE_TOKEN and owner.es_email_owner(LICENSE_TOKEN):
    if owner.activar_automatico() or owner.es_owner():
        LICENSE_TOKEN = None
    else:
        st.sidebar.error(T("owner_no_key_error"))
        LICENSE_TOKEN = None

# La licencia se pega UNA vez. Antes vivía sólo acá, en la sesión de Streamlit:
# había que volver a buscarla en el mail en cada apertura, y la API de BI —otro
# proceso, el que consumen Power BI y Tableau— no la veía nunca, así que a los
# 7 días le devolvía 402 a un cliente con licencia paga vigente.
if LICENSE_TOKEN:
    if licensing.verify_license(LICENSE_TOKEN):
        licensing.guardar_token(LICENSE_TOKEN)
    # Un token inválido no borra el que ya estaba guardado: el error más
    # probable es un copiado a medias, y en ese caso perder la licencia buena
    # sería peor que ignorar la mala.
else:
    LICENSE_TOKEN = licensing.token_guardado()

_ROL_LABEL = {"admin": "role_admin", "miembro": "role_miembro", "invitado": "role_invitado"}
st.sidebar.divider()
st.sidebar.caption(f"{user['nombre']} · {T(_ROL_LABEL.get(user['rol'], 'role_miembro'))}")
if st.sidebar.button(T("btn_logout")):
    st.session_state["user"] = None
    st.rerun()

# Candado de la prueba de 7 días. El programa se descarga completo y funciona
# 100% durante una semana; al vencer se bloquea hasta cargar una licencia paga
# vigente. Bloquear NO borra datos: al pagar, se sigue con todo lo cargado.
#
# Edición Owner: la instalación del dueño del producto corre sin candado. La
# decisión vive en mvpm/owner.py y no acá, porque antes dependía de una env var
# que sólo seteaba el launcher del .exe: el mismo dueño abriendo su programa con
# ./run.sh app o con el .bat portable caía igual en "la prueba venció". Nada de
# esto viaja en lo que recibe un cliente (tests/test_owner.py lo fija) ni toca
# licensing.py — ver owner/panel.py para emitir licencias reales de venta.
_es_owner = owner.es_owner()
_acceso = (
    owner.estado_acceso()
    if _es_owner else
    # El invitado no pasa por el candado: todavía no es cliente, está viendo si
    # el producto le sirve. Cobrarle una prueba a alguien que ni siquiera dejó
    # un email es el orden inverso.
    {"acceso": True, "modo": "invitado", "plan": None, "dias_restantes": None,
     "mensaje": "Modo invitado — los datos no se guardan."}
    if INVITADO else licensing.estado_acceso(LICENSE_TOKEN)
)
# `_acceso["mensaje"]` viene de mvpm/licensing.py y mvpm/owner.py, fijo en
# español (esas funciones no dependen del idioma de la UI a propósito — ver
# el motor mvpm/, que se importa y testea sin Streamlit). Acá se arma de
# nuevo con T() a partir de los campos estructurados (modo/plan/dias) en vez
# de mostrar ese texto tal cual, así el mensaje sale en el idioma elegido sin
# tocar el contrato del motor.
if _acceso["modo"] == "owner":
    st.sidebar.success(T("msg_modo_owner"), icon=":material/verified:")
elif _acceso["modo"] == "invitado":
    st.sidebar.info(T("msg_modo_invitado"), icon=":material/person:")
elif _acceso["modo"] == "trial":
    st.sidebar.info(T("trial_dias_restantes").format(dias=_acceso["dias_restantes"]),
                    icon=":material/hourglass_top:")
elif _acceso["modo"] == "licencia":
    st.sidebar.success(
        T("msg_licencia_activa").format(plan=licensing.PLANES[_acceso["plan"]]["nombre"]),
        icon=":material/schedule:")

if not _acceso["acceso"]:
    st.title(T("trial_vencida_title"))
    st.warning(T("msg_trial_vencida"))
    st.markdown(T("trial_vencida_data_ok"))
    st.markdown(T("trial_vencida_steps"))
    st.caption(T("trial_vencida_contact"))
    st.stop()

# Empresa activa — alcance de todo lo versionado (definiciones, organigrama,
# responsables, notas PMBOK). Cada empresa guarda su propia historia.
#
# El invitado no crea ni elige empresa: crear una escribiría en la base
# compartida a nombre de alguien que no tiene cuenta. Las secciones que usan
# EMPRESA_ID quedan fuera de su menú, así que no hace falta un id real.
if INVITADO:
    EMPRESA_ID = None
else:
    db.obtener_o_crear_empresa("Mi empresa")
    _empresas = db.listar_empresas()
    _empresa_nombres = _empresas["nombre"].tolist()
    with st.sidebar.expander(T("empresa_expander"), icon=":material/business:"):
        empresa_sel = st.selectbox(T("empresa_activa_label"), _empresa_nombres,
                                   index=0, key="empresa_sel")
        _nueva = st.text_input(T("empresa_nueva_label"), key="empresa_nueva")
        if st.button(T("empresa_crear_btn"), key="crear_empresa_btn") and _nueva.strip():
            db.crear_empresa(_nueva.strip())
            st.rerun()
    EMPRESA_ID = int(_empresas[_empresas["nombre"] == empresa_sel]["id"].iloc[0])

# Modelo de IA elegido por esta empresa. Se aplica en CADA corrida del script y
# no una sola vez: Streamlit vuelve a ejecutar todo el archivo en cada
# interacción, y la elección vive en un contextvar por hilo de sesión (ver
# mvpm/modelos.py). Reponerla acá arriba garantiza que cualquier llamada a la IA
# más abajo use el modelo de la empresa activa, incluso si el usuario acaba de
# cambiar de empresa en el selector.
if not INVITADO:
    _cfg_ia = db.obtener_version_actual(EMPRESA_ID, "config_ia", "modelos")
    modelos.aplicar_seleccion(_cfg_ia["contenido"] if _cfg_ia else None)

st.sidebar.title(T("app_title"))

if INVITADO:
    # Se ofrece sólo lo que funciona sin cuenta: subir el archivo y analizar el
    # portafolio. Lo que queda afuera (gobernanza, organigrama, plantillas,
    # PMBOK) no se esconde por capricho: guarda versiones por empresa en la
    # base, y sin cuenta no hay empresa a la cual atribuirlas.
    nav_options = [
        T("nav_import"), T("nav_portfolio"), T("nav_health"),
        T("nav_dependencies"), T("nav_backlog"), T("nav_tasks"),
        T("nav_copilot"), T("nav_reports"), T("nav_glossary"),
        T("nav_policies"), T("nav_tutorial"),
    ]
else:
    nav_options = [
        T("nav_tutorial"), T("nav_case_study"), T("nav_real_demo"), T("nav_pharma"),
        T("nav_portfolio"), T("nav_tasks"), T("nav_health"), T("nav_dependencies"),
        T("nav_backlog"), T("nav_copilot"), T("nav_advisor"), T("nav_reports"),
        T("nav_governance"), T("nav_organigrama"), T("nav_pmbok"), T("nav_plantillas"),
        T("nav_reviews"), T("nav_glossary"), T("nav_policies"),
        T("nav_import"), T("nav_conectores"), T("nav_data_eng"), T("nav_capacitacion"),
        T("nav_config_ia"),
    ]
    if user["rol"] == "admin":
        nav_options.append(T("nav_users"))

# Un invitado que entró con el botón de "subir mi Excel" cae directo en
# Importar: es el único paso que tiene sentido con el portafolio vacío.
_indice_inicial = 0
if INVITADO and st.session_state["invitado_almacen"].vacio:
    _indice_inicial = nav_options.index(T("nav_import"))

section = st.sidebar.radio(T("sidebar_section_label"), nav_options, index=_indice_inicial)

st.title(T("app_title"))


def load_data():
    # El invitado lee de su almacén de sesión; el usuario registrado, de la base.
    # Ambos devuelven las mismas columnas, así que de acá para abajo el
    # dashboard no distingue entre uno y otro.
    if INVITADO:
        a = st.session_state["invitado_almacen"]
        return a.proyectos(), a.tareas(), a.equipo()
    return db.projects(), db.tasks(), db.team()


proj_df, task_df, team_df = load_data()
equipo_df = (pd.DataFrame(columns=["id", "nombre", "email", "rol"])
             if INVITADO else db.listar_usuarios())


# Escritura: el invitado escribe en su almacén de sesión y el usuario
# registrado en la base. Se despacha acá una sola vez para que los formularios
# de más abajo no tengan que preguntar quién es en cada uno.
def _crear_proyecto(**campos):
    if INVITADO:
        return st.session_state["invitado_almacen"].crear_proyecto(**campos)
    return db.crear_proyecto(**campos)


def _crear_tarea(**campos):
    if INVITADO:
        return st.session_state["invitado_almacen"].crear_tarea(**campos)
    return db.crear_tarea(**campos)


def _solo_con_cuenta(accion: str) -> bool:
    """True (y avisa) si la acción pide cuenta y estamos en modo invitado.

    Editar y archivar necesitan un registro estable al cual volver; el almacén
    de invitado se borra al cerrar la pestaña, así que ofrecerlo sería prometer
    algo que no se cumple. Importar y crear sí funcionan.
    """
    if not INVITADO:
        return False
    st.info(f"{accion} necesita una cuenta. En modo invitado podés importar tu "
            f"Excel, crear proyectos y analizar todo el portafolio — lo que no "
            f"se puede es guardar cambios de forma permanente.")
    return True


_GRADIENTE_ROJO = (215, 48, 39)
_GRADIENTE_AMARILLO = (255, 255, 191)
_GRADIENTE_VERDE = (26, 152, 80)


def _interpolar_color(c1, c2, t):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _color_por_indice(valor):
    """Rojo→amarillo→verde sobre 0-100, sin matplotlib (Styler.background_gradient
    lo requiere y no está en requirements.txt — esto evita sumar esa dependencia
    sólo para un gradiente de color)."""
    if pd.isna(valor):
        return ""
    v = max(0.0, min(100.0, float(valor)))
    if v <= 50:
        r, g, b = _interpolar_color(_GRADIENTE_ROJO, _GRADIENTE_AMARILLO, v / 50)
    else:
        r, g, b = _interpolar_color(_GRADIENTE_AMARILLO, _GRADIENTE_VERDE, (v - 50) / 50)
    brillo = (r * 299 + g * 587 + b * 114) / 1000
    texto = "#000" if brillo > 140 else "#fff"
    return f"background-color: rgb({r},{g},{b}); color: {texto}"


def _selector_usuario(label: str, key: str, actual_id=None):
    opciones = ["(sin asignar)"] + equipo_df["nombre"].tolist()
    idx = 0
    if actual_id is not None and not equipo_df.empty:
        match = equipo_df[equipo_df["id"] == actual_id]
        if not match.empty:
            idx = opciones.index(match.iloc[0]["nombre"])
    elegido = st.selectbox(label, opciones, index=idx, key=key)
    if elegido == "(sin asignar)":
        return None
    return int(equipo_df[equipo_df["nombre"] == elegido]["id"].iloc[0])


if proj_df.empty and task_df.empty:
    # El invitado y el usuario registrado tienen estados vacíos DISTINTOS. Antes
    # compartían este bloque y el invitado terminaba llamando a
    # db.cargar_datos_de_ejemplo(): eso sembraba 20 proyectos en la base
    # compartida del servidor (rompiendo el "nada se guarda" que promete la
    # barra lateral, y ensuciando el portafolio de los usuarios reales) mientras
    # el invitado —que lee de su almacén de sesión— no veía aparecer nada.
    if INVITADO:
        st.info(T("empty_guest_caption"))
        if st.button(T("empty_guest_btn"), icon=":material/public:"):
            st.session_state["invitado_almacen"] = invitado.con_portafolio_real()
            st.rerun()
    else:
        st.info(T("empty_server_caption"))
        if st.button(T("empty_server_btn"), icon=":material/potted_plant:"):
            db.cargar_datos_de_ejemplo()
            st.rerun()

# ------------------------------------------------------------------ secciones

if section == T("nav_tutorial"):
    st.subheader(T("nav_tutorial"))
    st.caption(T("tutorial_caption"))
    for i, s in enumerate(tutorial.sections(LANG)):
        with st.expander(f"{s['titulo']}", expanded=(i == 0)):
            st.write(s["resumen"])
            st.markdown(T("tutorial_como_usarlo"))
            for paso in s["pasos"]:
                st.markdown(f"- {paso}")
            if s["tips"]:
                st.markdown(T("tutorial_tips"))
                for tip in s["tips"]:
                    st.markdown(tip)

elif section == T("nav_case_study"):
    st.subheader(T("nav_case_study"))
    st.caption(T("case_study_caption"))
    caso = case_study.narrar_caso(lang=LANG)
    st.markdown(T("case_study_chosen").format(
        nombre=caso["nombre"], id=caso["proyecto_id"], indice=caso["indice"], estado=caso["estado"]))
    st.divider()
    for paso in caso["pasos"]:
        st.markdown(f"##### {paso['titulo']}")
        st.caption(paso["seccion"])
        st.write(paso["texto"])
        st.write("")
    if proj_df.empty:
        st.info(T("case_study_no_data"))

elif section == T("nav_real_demo"):
    st.subheader(T("nav_real_demo"))
    st.caption(T("real_demo_source_prefix").format(fuente=demo_real.fuente(LANG)))
    st.caption(T("real_demo_caption").format(url=demo_real.FUENTE_URL))

    resumen = demo_real.resumen_portafolio()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T("real_demo_kpi_total"), resumen["total_proyectos"])
    c2.metric(T("real_demo_kpi_over"), resumen["sobre_presupuesto"])
    c3.metric(T("real_demo_kpi_budget"), f"£{resumen['presupuesto_total_m']:,.0f}M")
    c4.metric(T("real_demo_kpi_spent"), f"£{resumen['ejecutado_total_m']:,.0f}M")
    st.caption(T("real_demo_over_caption"))

    st.info(T("real_demo_ahorro").format(
        n=resumen["total_proyectos"], min=resumen["minutos_por_revision_manual_supuesto"],
        hs=resumen["horas_ahorradas_estimadas"]))

    st.subheader(T("real_demo_top10"))
    st.dataframe(resumen["proyectos_sobre_presupuesto_detalle"], use_container_width=True)

    st.divider()
    st.subheader(T("real_demo_two_cases"))
    for nombre in ["Social Housing Decarbonisation Fund", "Borders & Trade Programme"]:
        c = demo_real.caso(nombre, lang=LANG)
        icon = {"Red": "🔴", "Amber": "🟡", "Green": "🟢"}[c["rag"]]
        with st.expander(f"{icon} {c['nombre']} — {c['depto']}"):
            st.write(c["resumen"])
            _flag = T("real_demo_over_flag") if c["sobre_presupuesto"] else T("real_demo_under_flag")
            st.markdown(T("real_demo_case_calc").format(
                pres=c["presupuesto_m"], ejec=c["ejecutado_m"], pct=c["ejecucion_pct"], estado=_flag))
            st.markdown(T("real_demo_narrativa_h"))
            st.caption(c["narrativa_real"])
            st.markdown(T("real_demo_revision_h"))
            st.caption(c["revision_real"])

elif section == T("nav_pharma"):
    st.subheader(T("nav_pharma"))
    st.caption(T("pharma_caption1").format(fuente=demo_pharma.fuente(LANG), url=demo_pharma.FUENTE_URL))
    st.caption(T("pharma_caption2"))

    r = demo_pharma.resumen_portafolio(LANG)
    c1, c2, c3 = st.columns(3)
    c1.metric(T("pharma_kpi_total"), r["total_ensayos"])
    c2.metric(T("pharma_kpi_risk"), r["en_riesgo"])
    c3.metric(T("pharma_kpi_labs"), len(r["por_sponsor"]))
    st.info(T("pharma_ahorro").format(
        n=r["total_ensayos"], min=r["minutos_por_revision_manual_supuesto"],
        hs=r["horas_ahorradas_estimadas"]))

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(T("pharma_by_status"))
        _est = pd.DataFrame({"estado": list(r["por_estado"].keys()),
                             "ensayos": list(r["por_estado"].values())})
        st.bar_chart(_est, x="estado", y="ensayos")
    with cc2:
        st.markdown(T("pharma_by_lab"))
        _lab = pd.DataFrame({"laboratorio": list(r["por_sponsor"].keys()),
                             "ensayos": list(r["por_sponsor"].values())})
        st.bar_chart(_lab, x="laboratorio", y="ensayos")

    st.subheader(T("pharma_at_risk_h"))
    st.dataframe(demo_pharma.en_riesgo_detalle(15, LANG), use_container_width=True)

    st.divider()
    st.subheader(T("pharma_to_bi_h"))
    st.markdown(T("pharma_to_bi_body"))
    st.download_button(T("pharma_download_bi"),
                       demo_pharma.tabla_para_bi().to_csv(index=False),
                       file_name="ensayos_pharma_bi.csv")

elif section == T("nav_portfolio"):
    kpis = catalog.kpis(proj_df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(T("kpi_projects"), kpis["proyectos_activos"])
    c2.metric(T("kpi_health"), f"{health.overall_index(proj_df, task_df, team_df)}/100")
    riesgo = int((health.project_health(proj_df, task_df, team_df)["estado"] == "riesgo").sum())
    c3.metric(T("kpi_at_risk"), riesgo)
    c4.metric(T("kpi_budget"), f"{kpis['ejecucion_pct_promedio']}%")
    bloqueadas = int((task_df["estado"] == "blocked").sum())
    c5.metric(T("kpi_blocked"), bloqueadas)
    a_tiempo = int((health.project_health(proj_df, task_df, team_df)["dim_cronograma"] >= 70).sum())
    c6.metric(T("kpi_on_time"), a_tiempo)

    with st.expander(T("new_project_expander"), icon=":material/add:"):
        with st.form("nuevo_proyecto", clear_on_submit=True):
            nombre = st.text_input(T("field_project_name"))
            col1, col2 = st.columns(2)
            portafolio = col1.text_input(T("field_portfolio"), value="Producto Core")
            sponsor = col2.text_input(T("field_sponsor"))
            dueno_id = _selector_usuario(T("field_owner"), "nuevo_proy_dueno")
            segmento = st.selectbox(T("field_segment"), ["Interno", "Cliente externo", "Regulatorio"])
            col3, col4 = st.columns(2)
            fecha_inicio = col3.date_input(T("field_start_date"), value=date.today())
            fecha_fin = col4.date_input(T("field_end_date"), value=date.today())
            col5, col6 = st.columns(2)
            presupuesto = col5.number_input(T("field_budget"), min_value=0.0, step=100.0)
            ejecutado = col6.number_input(T("field_spent"), min_value=0.0, step=100.0)
            criticidad = st.selectbox(T("field_criticality"), ["Alta", "Media", "Baja"], index=1)
            enviado = st.form_submit_button(T("btn_create_project"))
            if enviado:
                if not nombre.strip():
                    st.error(T("err_name_required"))
                else:
                    _crear_proyecto(
                        nombre=nombre.strip(), portafolio=portafolio.strip() or "Sin portafolio",
                        sponsor=sponsor.strip() or None, dueno_id=dueno_id, segmento=segmento,
                        fecha_inicio=str(fecha_inicio), fecha_fin=str(fecha_fin),
                        presupuesto=presupuesto, ejecutado=ejecutado, criticidad=criticidad,
                    )
                    st.success(T("msg_project_created").format(nombre=nombre))
                    st.rerun()

    if not proj_df.empty:
        st.subheader(T("nav_portfolio"))
        st.dataframe(catalog.catalog(proj_df).drop(columns=["_id"]), use_container_width=True)

        # Editar y archivar necesitan un registro estable al cual volver; el
        # almacén del invitado se borra al cerrar la pestaña, así que se le
        # ofrece la cuenta en vez de un botón que promete algo que no cumple.
        if INVITADO:
            _solo_con_cuenta(T("action_edit_or_archive_project"))
        else:
            with st.expander(T("project_card_expander"), icon=":material/edit:"):
                opciones = (proj_df["nombre"] + " — " + proj_df["proyecto_id"]).tolist()
                elegido = st.selectbox(T("pick_a_project"), opciones, key="ficha_proyecto_selector")
                fila = proj_df.iloc[opciones.index(elegido)]
                with st.form("editar_proyecto"):
                    nombre_e = st.text_input(T("field_name"), value=fila["nombre"])
                    col1, col2 = st.columns(2)
                    portafolio_e = col1.text_input(T("field_portfolio"), value=fila["portafolio"])
                    sponsor_e = col2.text_input(T("field_sponsor"), value=fila["sponsor"] or "")
                    dueno_id_e = _selector_usuario(
                        T("field_owner"), "editar_proy_dueno",
                        actual_id=equipo_df[equipo_df["nombre"] == fila["dueno"]]["id"].iloc[0]
                        if fila["dueno"] and (equipo_df["nombre"] == fila["dueno"]).any() else None,
                    )
                    segmento_e = st.selectbox(T("field_segment"), ["Interno", "Cliente externo", "Regulatorio"],
                                               index=["Interno", "Cliente externo", "Regulatorio"].index(fila["segmento"])
                                               if fila["segmento"] in ["Interno", "Cliente externo", "Regulatorio"] else 0)
                    col3, col4 = st.columns(2)
                    presupuesto_e = col3.number_input(T("field_budget"), min_value=0.0, step=100.0, value=float(fila["presupuesto"]))
                    ejecutado_e = col4.number_input(T("field_spent"), min_value=0.0, step=100.0, value=float(fila["ejecutado"]))
                    criticidad_e = st.selectbox(T("field_criticality"), ["Alta", "Media", "Baja"],
                                                 index=["Alta", "Media", "Baja"].index(fila["criticidad"]))
                    guardar = st.form_submit_button(T("btn_save_changes"), icon=":material/save:")
                    if guardar:
                        db.actualizar_proyecto(
                            int(fila["_id"]), nombre=nombre_e.strip(), portafolio=portafolio_e.strip(),
                            sponsor=sponsor_e.strip() or None, dueno_id=dueno_id_e, segmento=segmento_e,
                            presupuesto=presupuesto_e, ejecutado=ejecutado_e, criticidad=criticidad_e,
                        )
                        st.success(T("msg_changes_saved"))
                        st.rerun()
                col_a, col_b = st.columns(2)
                if col_a.button(T("btn_archive_project"), key="archivar_proy", icon=":material/archive:"):
                    db.archivar_proyecto(int(fila["_id"]))
                    st.success(T("msg_project_archived"))
                    st.rerun()
                if col_b.button(T("btn_delete_permanently"), key="eliminar_proy", icon=":material/delete:"):
                    db.eliminar_proyecto(int(fila["_id"]))
                    st.success(T("msg_project_deleted"))
                    st.rerun()

        st.subheader(T("by_portfolio_h"))
        st.bar_chart(catalog.por_portafolio(proj_df).set_index("portafolio")[["presupuesto", "ejecutado"]])

elif section == T("nav_tasks"):
    st.subheader(T("nav_tasks"))

    with st.expander(T("new_task_expander"), icon=":material/add:"):
        if proj_df.empty:
            st.warning(T("warn_create_project_first"))
        else:
            with st.form("nueva_tarea", clear_on_submit=True):
                proyecto_opciones = (proj_df["nombre"] + " — " + proj_df["proyecto_id"]).tolist()
                proyecto_elegido = st.selectbox(T("field_project"), proyecto_opciones)
                proyecto_real_id = int(proj_df.iloc[proyecto_opciones.index(proyecto_elegido)]["_id"])
                titulo = st.text_input(T("field_task_title"))
                responsable_id = _selector_usuario(T("field_assignee"), "nueva_tarea_resp")
                col1, col2 = st.columns(2)
                estado = col1.selectbox(T("field_status"), ["todo", "in_progress", "blocked", "done"])
                prioridad = col2.selectbox(T("field_priority"), ["Alta", "Media", "Baja"], index=1)
                vencimiento = st.date_input(T("field_due_date"), value=date.today())
                dep_opciones = [T("opt_none_fem")] + (task_df["titulo"] + " — " + task_df["tarea_id"]).tolist()
                dependencia = st.selectbox(T("field_depends_on"), dep_opciones)
                enviado = st.form_submit_button(T("btn_create_task"))
                if enviado:
                    if not titulo.strip():
                        st.error(T("err_title_required"))
                    else:
                        depende_de_id = None
                        if dependencia != T("opt_none_fem"):
                            depende_de_id = int(task_df.iloc[dep_opciones.index(dependencia) - 1]["_id"])
                        _crear_tarea(
                            proyecto_id=proyecto_real_id, titulo=titulo.strip(),
                            responsable_id=responsable_id, estado=estado,
                            vencimiento=str(vencimiento), prioridad=prioridad, depende_de=depende_de_id,
                        )
                        st.success(T("msg_task_created").format(titulo=titulo))
                        st.rerun()

    if not task_df.empty:
        st.dataframe(task_df.drop(columns=["_id"]), use_container_width=True)

        if INVITADO:
            _solo_con_cuenta(T("action_edit_or_delete_task"))
        else:
            with st.expander(T("task_card_expander"), icon=":material/edit:"):
                t_opciones = (task_df["titulo"] + " — " + task_df["tarea_id"]).tolist()
                t_elegida = st.selectbox(T("pick_a_task"), t_opciones, key="ficha_tarea_selector")
                t_fila = task_df.iloc[t_opciones.index(t_elegida)]
                with st.form("editar_tarea"):
                    titulo_e = st.text_input(T("field_task_title"), value=t_fila["titulo"])
                    responsable_actual = equipo_df[equipo_df["nombre"] == t_fila["responsable"]]["id"].iloc[0] \
                        if t_fila["responsable"] and (equipo_df["nombre"] == t_fila["responsable"]).any() else None
                    responsable_id_e = _selector_usuario(T("field_assignee"), "editar_tarea_resp", actual_id=responsable_actual)
                    col1, col2 = st.columns(2)
                    estado_e = col1.selectbox(T("field_status"), ["todo", "in_progress", "blocked", "done"],
                                               index=["todo", "in_progress", "blocked", "done"].index(t_fila["estado"]))
                    prioridad_e = col2.selectbox(T("field_priority"), ["Alta", "Media", "Baja"],
                                                  index=["Alta", "Media", "Baja"].index(t_fila["prioridad"]))
                    guardar_t = st.form_submit_button(T("btn_save_changes"), icon=":material/save:")
                    if guardar_t:
                        db.actualizar_tarea(int(t_fila["_id"]), titulo=titulo_e.strip(),
                                             responsable_id=responsable_id_e, estado=estado_e, prioridad=prioridad_e)
                        st.success(T("msg_changes_saved"))
                        st.rerun()
                if st.button(T("btn_delete_task"), key="eliminar_tarea", icon=":material/delete:"):
                    db.eliminar_tarea(int(t_fila["_id"]))
                    st.success(T("msg_task_deleted"))
                    st.rerun()

elif section == T("nav_health"):
    h = health.project_health(proj_df, task_df, team_df)
    st.subheader(T("health_global_index").format(
        nav=T("nav_health"), n=health.overall_index(proj_df, task_df, team_df)))
    estado_color = {"saludable": "🟢", "observacion": "🟡", "riesgo": "🔴"}
    estado_label = {"saludable": T("status_ok"), "observacion": T("status_warn"), "riesgo": T("status_risk")}
    h_display = h.copy()
    h_display["estado"] = h_display["estado"].map(lambda e: f"{estado_color.get(e,'')} {estado_label.get(e, e)}")
    st.dataframe(h_display, use_container_width=True)
    st.subheader(T("dim_matrix_h"))
    matriz = health.matriz_por_dimension(proj_df, task_df, team_df).set_index("nombre")
    columnas_dim = [c for c in matriz.columns if c.startswith("dim_")]
    st.dataframe(matriz.style.map(_color_por_indice, subset=columnas_dim), use_container_width=True)

elif section == T("nav_dependencies"):
    st.subheader(T("nav_dependencies"))
    bloqueos = dep_mod.bloqueos_activos(task_df)
    if bloqueos.empty:
        st.success(T("no_blocked_tasks"))
    else:
        st.dataframe(bloqueos[["tarea_id", "titulo", "proyecto_id", "tareas_impactadas"]], use_container_width=True)
    st.subheader(T("inconsistent_deps_h"))
    orphans = dep_mod.orphan_dependencies(task_df)
    if orphans.empty:
        st.success(T("no_orphan_deps"))
    else:
        st.warning(T("orphan_deps_warn").format(n=len(orphans)))
        st.dataframe(orphans, use_container_width=True)

elif section == T("nav_backlog"):
    st.subheader(T("nav_backlog"))
    st.caption(T("backlog_caption"))
    st.dataframe(
        prioritizer.prioritized_backlog(proj_df, task_df)[
            ["tarea_id", "titulo", "proyecto_id", "estado", "valor_esperado", "tareas_impactadas", "dias_restantes"]
        ],
        use_container_width=True,
    )

elif section == T("nav_copilot"):
    st.subheader(T("nav_copilot"))
    st.caption(T("copilot_caption"))
    # El cupo es la mitad del control; la otra es que el plan incluya la IA.
    # Antes sólo se miraba el cupo, así que un plan sin "copiloto_ia" habría
    # tenido IA igual mientras le quedaran consultas — la feature del plan no
    # se consultaba en ningún lado.
    puede_ia, detalle_cupo = (
        (True, T("copilot_cupo_owner")) if _es_owner
        else licensing.puede_usar_ia(LICENSE_TOKEN)
        if licensing.tiene_feature(LICENSE_TOKEN, "copiloto_ia")
        else (False, T("copilot_cupo_no_plan")))
    st.caption(T("copilot_cupo_label").format(detalle=detalle_cupo))
    q = st.text_input(T("copilot_ask_label"), T("copilot_ask_default"))
    if st.button(T("btn_ask")):
        result = copilot_mod.answer(q, proj_df, task_df, team_df, license_token=LICENSE_TOKEN, lang=LANG)
        st.info(result["answer"])
        st.caption(T("copilot_ai_enriched") if result["ai_enriched"] else T("copilot_rules_only"))

elif section == T("nav_advisor"):
    st.subheader(T("nav_advisor"))
    st.caption(T("advisor_caption"))
    disponibles = advisor.proveedores_disponibles()
    etiquetas = {"claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini"}
    opciones_ia = [T("advisor_rules_only")] + [etiquetas[p] for p in disponibles]
    elegido = st.radio(T("advisor_suggestion_label"), opciones_ia, horizontal=True)
    proveedor = next((p for p in disponibles if etiquetas[p] == elegido), None)
    if not disponibles:
        st.caption(T("advisor_no_providers"))

    problemas = advisor.detectar_problemas(proj_df, task_df, team_df, lang=LANG)
    icon_severidad = {"alta": "🔴", "media": "🟡", "baja": "⚪"}
    if not problemas:
        st.success(T("advisor_none_found"))
    for p in problemas:
        seg = db.obtener_seguimiento_por_problema(p["id"])
        with st.expander(f"{icon_severidad[p['severidad']]} {p['titulo']}"):
            resultado = advisor.sugerir(p, proveedor=proveedor, lang=LANG)
            st.write(resultado["sugerencia"])
            st.caption(T("advisor_written_by").format(proveedor=etiquetas[resultado["proveedor"]])
                       if resultado["ai_enriched"] else T("advisor_rules_only"))
            if seg:
                nuevo_estado = st.selectbox(
                    T("field_followup_status"), ["abierto", "en_progreso", "resuelto"],
                    index=["abierto", "en_progreso", "resuelto"].index(seg["estado"]),
                    key=f"estado_{p['id']}",
                )
                if nuevo_estado != seg["estado"]:
                    db.actualizar_estado_seguimiento(seg["id"], nuevo_estado)
                    st.rerun()
            elif st.button(T("btn_track"), key=f"seguir_{p['id']}", icon=":material/push_pin:"):
                db.crear_o_actualizar_seguimiento(p["id"], p["tipo"], p["titulo"],
                                                   resultado["sugerencia"], resultado["proveedor"])
                st.rerun()

    seguimientos_df = db.listar_seguimientos()
    if not seguimientos_df.empty:
        st.divider()
        st.subheader(T("followups_h"))
        st.caption(T("followups_caption"))
        st.dataframe(seguimientos_df[["titulo", "tipo", "estado", "proveedor", "actualizado_en"]],
                     use_container_width=True)

elif section == T("nav_reports"):
    st.subheader(T("nav_reports"))
    if not (_es_owner or licensing.tiene_feature(LICENSE_TOKEN, "reportes_automaticos")):
        st.warning(T("reports_no_plan"), icon=":material/lock:")
        st.stop()
    st.code(reports.as_text(proj_df, task_df, team_df), language=None)
    st.download_button(T("download_json"), exporters.to_json_bundle(proj_df, task_df, team_df), file_name="portafolio_mvpm.json")
    st.download_button(T("download_excel"), exporters.to_excel_bytes(proj_df, task_df, team_df), file_name="portafolio_mvpm.xlsx")

elif section == T("nav_reviews"):
    st.subheader(T("nav_reviews"))
    s = reviews.summary()
    if s["es_beta_sin_resenas"]:
        st.info(f"{T('reviews_empty_title')} — {T('reviews_empty_body')}", icon=":material/star:")
    else:
        st.metric(T("avg_rating"), T("rating_value").format(n=s["promedio"], total=s["total"]))
        for r in reviews.list_reviews():
            autor, rol, empresa = (seguro.escapar(r[k]) for k in ("autor", "rol", "empresa"))
            st.markdown(f"**{'⭐' * r['calificacion']}** — *{autor}, {rol} en {empresa}*")
            st.write(seguro.escapar(r["comentario"]))
            st.divider()
    with st.expander(T("leave_a_review")):
        with st.form("nueva_resena"):
            autor = st.text_input(T("field_your_name"))
            empresa = st.text_input(T("field_company"))
            rol = st.text_input(T("field_role"))
            calificacion = st.slider(T("field_rating"), 1, 5, 5)
            comentario = st.text_area(T("field_comment"))
            enviado = st.form_submit_button(T("btn_submit_review"))
            if enviado and autor and comentario:
                reviews.add_review(autor, empresa, rol, calificacion, comentario, verificado=False)
                st.success(T("msg_review_thanks"))

elif section == T("nav_glossary"):
    st.subheader(T("nav_glossary"))
    st.dataframe(glossary.glossary(), use_container_width=True)

elif section == T("nav_policies"):
    st.subheader(T("nav_policies"))
    pol = policies.evaluate(proj_df, task_df, team_df, lang=LANG)
    for _, row in pol.iterrows():
        icon = "✅" if row["estado"] == "cumple" else "⚠️"
        st.markdown(f"{icon} **{row['politica']}** — {row['evidencia']}")
    st.divider()
    st.subheader(T("automation_matrix_h"))
    nivel_icon = {"auto": f"🟢 {T('nivel_auto')}", "parcial": f"🟡 {T('nivel_parcial')}", "humano": f"🔴 {T('nivel_humano')}"}
    for row in help_center.automation_rows(LANG):
        st.markdown(f"**{row['area']}** — {nivel_icon[row['nivel']]}")
        st.caption(row["detalle"])

elif section == T("nav_pmbok"):
    st.subheader(T("nav_pmbok"))
    st.caption(T("pmbok_caption"))
    r = pmbok.resumen()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T("pmbok_kpi_areas"), r["total_areas"])
    c2.metric(T("pmbok_kpi_groups"), r["grupos_proceso"])
    c3.metric(T("pmbok_kpi_full"), r["completa"])
    c4.metric(T("pmbok_kpi_none"), r["no_cubierta"])

    tab_areas, tab_grupos = st.tabs([T("pmbok_tab_areas"), T("pmbok_tab_groups")])
    icon = {"completa": "✅", "parcial": "🟡", "no_cubierta": "⚪"}
    with tab_areas:
        for a in pmbok.areas(LANG):
            with st.expander(f"{icon[a['cobertura']]} {a['area']} ({a['area_en']})"):
                st.markdown(T("pmbok_technical_h"))
                st.write(a["definicion_tecnica"])
                st.markdown(T("pmbok_plain_h"))
                st.info(a["criollo"])
                if a["como_lo_cubre"]:
                    st.markdown(T("pmbok_how_covered").format(texto=a["como_lo_cubre"]))
                if a["lo_que_falta"]:
                    st.caption(T("pmbok_whats_missing").format(texto=a["lo_que_falta"]))
                _nota = pmbok.nota_empresa(EMPRESA_ID, a["clave"])
                if _nota:
                    st.success(T("pmbok_company_note").format(
                        nombre=seguro.escapar(_nota["validado_por_nombre"]),
                        cargo=seguro.escapar(_nota["validado_por_cargo"]),
                        texto=seguro.escapar(_nota["texto"])))
                with st.form(f"nota_pmbok_{a['clave']}"):
                    st.caption(T("pmbok_note_caption"))
                    txt = st.text_area(T("field_note"), value=_nota["texto"] if _nota else "",
                                       key=f"nota_txt_{a['clave']}")
                    cn, cc = st.columns(2)
                    val_n = cn.text_input(T("field_validated_by_name"), key=f"nota_n_{a['clave']}")
                    val_c = cc.text_input(T("field_role_or_title"), key=f"nota_c_{a['clave']}")
                    if st.form_submit_button(T("btn_save_note"), icon=":material/save:") and txt.strip() and val_n.strip():
                        pmbok.guardar_nota(EMPRESA_ID, a["clave"], txt.strip(), val_n.strip(), val_c.strip())
                        st.success(T("msg_note_saved"))
                        st.rerun()
    with tab_grupos:
        st.caption(T("pmbok_lifecycle_caption"))
        for g in pmbok.grupos_proceso(LANG):
            with st.expander(f"{g['nombre']} ({g['nombre_en']})"):
                st.markdown(T("pmbok_technical_h"))
                st.write(g["definicion_tecnica"])
                st.markdown(T("pmbok_plain_h"))
                st.info(g["criollo"])
                _resp = organigrama.responsable_vigente(EMPRESA_ID, g["clave"])
                if _resp:
                    st.success(T("pmbok_resp_assigned").format(
                        persona=_resp["persona"].get("nombre"),
                        cargo=_resp["persona"].get("cargo") or T("sd_none"),
                        nombre=_resp["validado_por_nombre"], cargo_val=_resp["validado_por_cargo"]))

elif section == T("nav_governance"):
    st.subheader(T("nav_governance"))
    st.caption(T("governance_caption"))
    _provs = ai.proveedores_disponibles()
    _etq = {"claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini"}
    _opts = [T("advisor_rules_only")] + [_etq[p] for p in _provs]
    _elegido = st.radio(T("governance_who_recommends"), _opts, horizontal=True)
    _prov = next((p for p in _provs if _etq[p] == _elegido), None)
    if not _provs:
        st.caption(T("governance_no_providers"))

    for c in governance.catalogo(LANG):
        vig = governance.definicion_vigente(EMPRESA_ID, c["clave"], LANG)
        estado_icon = "✅" if vig["estado"] == "validado" else "📋"
        with st.expander(f"{estado_icon} {c['termino']}  ·  {c['categoria']}"):
            st.markdown(T("governance_current_def").format(origen=vig["origen"]))
            st.write(seguro.escapar(vig["texto"]))
            if vig["validado_por_nombre"]:
                st.caption(T("governance_validated_by").format(
                    nombre=seguro.escapar(vig["validado_por_nombre"]),
                    cargo=seguro.escapar(vig["validado_por_cargo"]), rec=vig["recomendado_por"]))
            rec = governance.recomendar_definicion(c["clave"], _prov, LANG)
            with st.form(f"gov_{c['clave']}"):
                st.caption(T("governance_recommended_by").format(rec=rec["recomendado_por"]))
                txt = st.text_area(T("governance_definition_field"), value=rec["texto"], key=f"gov_txt_{c['clave']}")
                co, cs = st.columns(2)
                # `validador`, no `owner`: este scope importa el módulo mvpm.owner
                # (edición del dueño del producto) y reusar el nombre lo pisaba.
                validador = co.text_input(T("governance_owner_validates"), key=f"gov_o_{c['clave']}")
                cargo = cs.text_input(T("field_role_or_title"), value="Data Owner", key=f"gov_c_{c['clave']}")
                if st.form_submit_button(T("btn_validate_save"), icon=":material/save:") and txt.strip() and validador.strip():
                    governance.guardar(EMPRESA_ID, c["clave"], txt.strip(), rec["recomendado_por"],
                                       validador.strip(), cargo.strip())
                    st.success(T("msg_definition_saved"))
                    st.rerun()
            hist = db.historial_versiones(EMPRESA_ID, "concepto", c["clave"])
            if len(hist) > 0:
                st.caption(T("governance_history_count").format(n=len(hist)))
                st.dataframe(hist[["contenido", "estado", "validado_por_nombre", "creado_en"]],
                             use_container_width=True)

elif section == T("nav_organigrama"):
    st.subheader(T("nav_organigrama"))
    st.caption(T("org_caption"))

    _provs = ai.proveedores_disponibles()
    _org_actual = db.listar_organigrama(EMPRESA_ID)

    with st.expander(T("org_upload_expander"), icon=":material/cloud_upload:", expanded=_org_actual.empty):
        st.caption(T("org_upload_caption"))
        fuente_tipo = st.radio(T("field_source"), [T("org_source_excel"), T("org_source_sqlite")], horizontal=True)
        if fuente_tipo == T("org_source_excel"):
            up = st.file_uploader(T("org_upload_file"), type=["csv", "xlsx"], key="org_upl")
            if up is not None:
                # dtype=str, igual que en el importador de proyectos: un legajo
                # "00123" leído como número pierde los ceros de adelante y pasa
                # a ser 123 — deja de coincidir con el legajo del ERP y la
                # persona no se puede cruzar contra ningún otro sistema. Lo
                # mismo con cédulas, códigos de centro de costo y teléfonos.
                df_org = (pd.read_csv(up, dtype=str) if up.name.endswith("csv")
                          else pd.read_excel(up, dtype=str))
                personas = organigrama.parsear(df_org)
                st.write(T("org_people_detected").format(n=len(personas)))
                st.dataframe(pd.DataFrame(personas), use_container_width=True)
                if st.button(T("org_save_btn"), icon=":material/save:"):
                    n = db.reemplazar_organigrama(EMPRESA_ID, personas, "excel/csv")
                    st.success(T("org_saved").format(n=n))
                    st.rerun()
        else:
            up = st.file_uploader(T("org_upload_sqlite"), type=["db", "sqlite", "sqlite3"], key="org_db")
            tabla = st.text_input(T("org_table_name"), value="empleados")
            if up is not None and tabla.strip():
                import sqlite3 as _sqlite3
                import tempfile as _tmp
                import os as _os
                _p = _os.path.join(_tmp.gettempdir(), "org_upload.db")
                with open(_p, "wb") as _f:
                    _f.write(up.getbuffer())
                try:
                    _conn = _sqlite3.connect(_p)
                    df_org = pd.read_sql_query(f"SELECT * FROM {tabla.strip()}", _conn)
                    _conn.close()
                    personas = organigrama.parsear(df_org)
                    st.write(T("org_people_detected").format(n=len(personas)))
                    st.dataframe(pd.DataFrame(personas), use_container_width=True)
                    if st.button(T("org_save_btn"), icon=":material/save:"):
                        n = db.reemplazar_organigrama(EMPRESA_ID, personas, "sqlite")
                        st.success(T("org_saved").format(n=n))
                        st.rerun()
                except Exception as e:
                    st.error(T("org_table_read_err").format(tabla=tabla, e=e))
        st.caption(T("org_photo_caption"))

    if not _org_actual.empty:
        st.subheader(T("org_current_h"))
        st.dataframe(_org_actual, use_container_width=True)

        st.divider()
        st.subheader(T("org_resp_by_stage_h"))
        personas = _org_actual.to_dict("records")
        sugerencias = organigrama.sugerir_responsables(personas, _provs[0] if _provs else None, LANG)
        for s in sugerencias:
            per = s["persona"]
            _resp = organigrama.responsable_vigente(EMPRESA_ID, s["etapa_clave"])
            with st.expander(s["etapa_nombre"]):
                st.caption(s["etapa_desc"])
                if _resp:
                    st.success(T("org_assigned").format(
                        nombre=seguro.escapar(_resp["persona"].get("nombre")),
                        cargo=seguro.escapar(_resp["persona"].get("cargo") or T("sd_none")),
                        val_n=seguro.escapar(_resp["validado_por_nombre"]),
                        val_c=seguro.escapar(_resp["validado_por_cargo"])))
                if per:
                    st.markdown(T("org_recommended").format(
                        rec=s["recomendado_por"], nombre=seguro.escapar(per["nombre"]),
                        cargo=seguro.escapar(per.get("cargo") or T("sd_none"))))
                    if s["justificacion"]:
                        st.caption(s["justificacion"])
                else:
                    st.warning(T("org_no_fit"))
                with st.form(f"resp_{s['etapa_clave']}"):
                    nombres = [p["nombre"] for p in personas]
                    idx = nombres.index(per["nombre"]) if per and per["nombre"] in nombres else 0
                    elegido = st.selectbox(T("org_responsible_label"), nombres, index=idx, key=f"resp_sel_{s['etapa_clave']}")
                    cargo_p = next((p.get("cargo") for p in personas if p["nombre"] == elegido), None)
                    cv1, cv2 = st.columns(2)
                    val_n = cv1.text_input(T("org_validated_by_name"), key=f"resp_vn_{s['etapa_clave']}")
                    val_c = cv2.text_input(T("org_validator_role"), key=f"resp_vc_{s['etapa_clave']}")
                    if st.form_submit_button(T("org_validate_btn"), icon=":material/save:") and val_n.strip():
                        organigrama.guardar_responsable(
                            EMPRESA_ID, s["etapa_clave"], elegido, cargo_p or "",
                            s["recomendado_por"], val_n.strip(), val_c.strip())
                        st.success(T("org_resp_saved"))
                        st.rerun()

elif section == T("nav_import"):
    st.subheader(T("nav_import"))
    st.caption(T("import_caption"))

    # El resultado se guarda en sesión porque después de importar hay un rerun:
    # sin esto el st.success() se pierde y la pantalla queda mostrando "no queda
    # ninguna fila", que parece un error cuando en realidad salió todo bien.
    if st.session_state.get("import_resultado"):
        st.success(st.session_state.pop("import_resultado"))

    tipo_label = st.radio(T("import_what_label"), [T("import_opt_projects"), T("import_opt_tasks")], horizontal=True)
    tipo = "proyectos" if tipo_label == T("import_opt_projects") else "tareas"

    with st.expander(T("import_template_expander")):
        plantilla_df = importer.plantilla(tipo, LANG)
        st.dataframe(plantilla_df, use_container_width=True)
        st.download_button(
            T("import_template_btn").format(tipo=tipo_label.lower()),
            plantilla_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"plantilla_{tipo}.csv", mime="text/csv",
            icon=":material/download:")
        st.caption(T("import_template_caption"))

    uploaded = st.file_uploader(T("import_upload_label"), type=["csv", "xlsx"])

    if uploaded is not None:
        try:
            # dtype=str a propósito: si se deja que pandas adivine el tipo,
            # convierte "320.000" (trescientos veinte mil, formato de acá) en el
            # float 320.0 ANTES de que lo vea parsear_numero() — y el
            # presupuesto entra mil veces más chico, en silencio, con lo cual
            # "sobre_presupuesto" queda mal. Leyendo todo como texto, el que
            # decide es el parser del importador, que para eso distingue
            # separador de miles de separador decimal y avisa cuando es ambiguo.
            df_import = (pd.read_csv(uploaded, dtype=str)
                         if uploaded.name.lower().endswith("csv")
                         else pd.read_excel(uploaded, dtype=str))
        except Exception as exc:                                  # archivo ilegible
            st.error(T("import_read_err").format(e=exc))
            df_import = None

        if df_import is not None and df_import.empty:
            st.warning(T("import_no_rows"))
            df_import = None

        if df_import is not None:
            df_import.columns = [str(c) for c in df_import.columns]
            st.write(T("import_rows_cols").format(filas=len(df_import), cols=len(df_import.columns)))
            st.dataframe(df_import.head(10), use_container_width=True)

            # --- paso 1: mapeo de columnas -------------------------------------
            st.markdown(T("import_step1"))
            sugerencias = importer.detectar_columnas(df_import, tipo, LANG)
            _sin_usar = T("import_opt_unused")
            opciones = [_sin_usar] + list(df_import.columns)
            mapeo: dict[str, str] = {}

            for campo in importer.campos_de(tipo, LANG):
                sug = sugerencias[campo.clave]
                col1, col2 = st.columns([3, 2])
                etiqueta = campo.etiqueta + (" *" if campo.requerido else "")
                indice = opciones.index(sug.columna) if sug.columna in opciones else 0
                elegida = col1.selectbox(etiqueta, opciones, index=indice,
                                         key=f"map_{tipo}_{campo.clave}",
                                         help=campo.ayuda or None)
                if sug.columna:
                    icono = "✅" if sug.confianza >= 0.9 else "🟡"
                    col2.caption(T("import_detected").format(icono=icono, motivo=sug.motivo))
                elif campo.requerido:
                    col2.caption(T("import_needs_column"))
                else:
                    col2.caption("—")
                if elegida != _sin_usar:
                    mapeo[campo.clave] = elegida

            # --- paso 2: opciones ----------------------------------------------
            st.markdown(T("import_step2"))
            omitir_dup = st.checkbox(T("import_skip_dup"), value=True)

            proyecto_default_id = None
            if tipo == "tareas":
                if proj_df.empty:
                    st.error(T("import_no_projects_err"))
                else:
                    nombres = list(proj_df["nombre"])
                    usar_default = st.checkbox(
                        T("import_use_default_project"), value="proyecto" not in mapeo)
                    if usar_default:
                        elegido = st.selectbox(T("import_default_project"), nombres)
                        proyecto_default_id = int(
                            proj_df[proj_df["nombre"] == elegido].iloc[0]["_id"])

            # --- paso 3: informe previo ----------------------------------------
            st.markdown(T("import_step3"))
            # Para el invitado, "lo que ya existe" es lo que subió en esta misma
            # sesión: no se puede consultar la base porque sus datos no están
            # ahí (y los del servidor no son suyos).
            _existentes = (
                (proj_df if tipo == "proyectos" else task_df) if INVITADO else
                (db.projects(incluir_archivados=True) if tipo == "proyectos"
                 else db.tasks()))
            reporte = importer.validar(
                df_import, tipo, mapeo,
                proyectos=proj_df if tipo == "tareas" else None,
                usuarios=(None if INVITADO else
                          (db.listar_usuarios() if tipo == "tareas" else None)),
                existentes=_existentes,
                proyecto_default_id=proyecto_default_id,
                omitir_duplicados=omitir_dup,
                lang=LANG)

            if reporte.faltan_requeridos:
                st.error(reporte.resumen(LANG))
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric(T("import_will_create"), reporte.filas_validas)
                m2.metric(T("import_will_discard"), reporte.filas_rechazadas)
                m3.metric(T("import_duplicates"), reporte.duplicados_archivo + reporte.duplicados_base)
                st.caption(reporte.resumen(LANG))

                for aviso in reporte.avisos_columna:
                    st.warning(aviso)

                if reporte.problemas:
                    with st.expander(T("import_details_expander").format(n=len(reporte.problemas))):
                        st.dataframe(reporte.problemas_df(), use_container_width=True)
                        st.caption(T("import_severity_caption"))

                if reporte.filas:
                    st.write(T("import_preview"))
                    st.dataframe(reporte.vista_previa(), use_container_width=True)

                # --- paso 4: confirmar -----------------------------------------
                st.markdown(T("import_step4"))
                if not reporte.puede_importar:
                    st.info(T("import_no_rows_left"))
                elif st.button(T("import_btn").format(n=reporte.filas_validas, tipo=tipo_label),
                               icon=":material/check:", type="primary"):
                    # El importador recibe las funciones de escritura, así que
                    # el invitado usa las de su almacén de sesión y el usuario
                    # registrado las de la base — sin ramificar el importador.
                    _almacen = st.session_state.get("invitado_almacen")
                    _crear_p = _almacen.crear_proyecto if INVITADO else db.crear_proyecto
                    _crear_t = _almacen.crear_tarea if INVITADO else db.crear_tarea
                    creadas = importer.aplicar(reporte, _crear_p, _crear_t)
                    st.session_state["import_resultado"] = T("import_done").format(
                        n=creadas, tipo=tipo_label,
                        seccion=T("nav_portfolio") if tipo == "proyectos" else T("nav_tasks"))
                    st.rerun()

elif section == T("nav_plantillas"):
    st.subheader(T("nav_plantillas"))
    st.caption(T("plantillas_caption"))

    _activa = plantillas.aplicada(EMPRESA_ID)
    if _activa and _activa["plantilla"]:
        _v = _activa["version"]
        _firma = (T("plantillas_validated_by").format(nombre=_v["validado_por_nombre"])
                  if _v.get("validado_por_nombre") else T("plantillas_draft"))
        st.success(T("plantillas_adopted").format(rubro=_activa["plantilla"].rubro, firma=_firma))

    _rubros = plantillas.rubros(LANG)
    _indice = 0
    if _activa:
        _claves = [c for c, _ in _rubros]
        _indice = _claves.index(_activa["clave"]) if _activa["clave"] in _claves else 0
    _elegido = st.selectbox(T("field_industry"), _rubros, index=_indice,
                            format_func=lambda r: r[1])[0]
    _p = plantillas.obtener(_elegido, LANG)
    st.write(f"**{_p.rubro}** — {_p.resumen}")
    if _p.nota:
        st.info(_p.nota)

    _t1, _t2, _t3, _t4 = st.tabs([T("plantillas_tab_stages"), T("plantillas_tab_roles"),
                                  T("plantillas_tab_kpi"), T("plantillas_tab_adopt")])
    with _t1:
        for _i, _e in enumerate(_p.etapas, 1):
            with st.expander(f"{_i}. {_e.nombre}  ·  {_e.grupo_pmbok}"):
                st.write(f"*{_e.objetivo}*")
                st.write(T("plantillas_deliverables"))
                for _x in _e.entregables:
                    st.write(f"- {_x}")
                st.write(T("plantillas_exit_gate").format(texto=_e.criterio_salida))
                st.write(T("plantillas_approves").format(texto=_e.aprueba))
        st.download_button(T("plantillas_download_gov"),
                           plantillas.como_texto(_elegido, LANG).encode("utf-8"),
                           file_name=f"gobernanza_{_elegido}.md", mime="text/markdown",
                           icon=":material/download:")
    with _t2:
        st.write(T("plantillas_roles_h"))
        st.dataframe(pd.DataFrame(_p.roles, columns=[T("col_role"), T("col_what_decides")]),
                     use_container_width=True, hide_index=True)
        st.write(T("plantillas_risks_h"))
        st.dataframe(pd.DataFrame([{T("col_risk"): _r.titulo, T("col_pmbok_area"): _r.area_pmbok,
                                    T("col_early_signal"): _r.senal_temprana,
                                    T("col_mitigation"): _r.mitigacion} for _r in _p.riesgos]),
                     use_container_width=True, hide_index=True)
        st.write(T("plantillas_focus_areas_h"))
        for _a in plantillas.areas_criticas_explicadas(_elegido, LANG):
            st.write(f"- **{_a['area']}** — {_a['criollo']}")
        st.caption(T("plantillas_focus_caption"))
    with _t3:
        st.write(T("plantillas_kpi_h"))
        for _x in _p.indicadores:
            st.write(f"- {_x}")
        st.write(T("plantillas_regs_h"))
        for _x in _p.normativa:
            st.write(f"- {_x}")
        st.warning(T("plantillas_legal_warning"))
    with _t4:
        st.write(T("plantillas_adopt_body"))
        with st.form("adoptar_plantilla"):
            _vn = st.text_input(T("plantillas_validated_by_field"))
            _vc = st.text_input(T("plantillas_validator_role"))
            if st.form_submit_button(T("plantillas_adopt_btn").format(rubro=_p.rubro)):
                plantillas.adoptar(EMPRESA_ID, _elegido, _vn.strip(), _vc.strip())
                st.success(T("plantillas_adopted_msg"))
                st.rerun()
        st.caption(T("plantillas_adopt_caption"))

elif section == T("nav_conectores"):
    st.subheader(T("nav_conectores"))
    st.caption(T("conectores_caption"))

    _fam = conectores.familias(LANG)
    _cf1, _cf2 = st.columns([1, 2])
    _familia = _cf1.selectbox(T("field_family"), list(_fam))
    _perfil = _cf2.selectbox(T("field_system"), _fam[_familia], format_func=lambda p: p.nombre)

    st.write(T("conectores_how").format(texto=_perfil.como_conectar))
    for _a in _perfil.advertencias:
        st.warning(_a)

    if not _perfil.consultas:
        st.info(T("conectores_no_queries"))
    else:
        _tipo = st.radio(T("conectores_what_to_bring"), list(_perfil.consultas),
                         horizontal=True, format_func=str.capitalize)
        _ce1, _ce2 = st.columns(2)
        _esquema = _ce1.text_input(T("field_schema"), value=_perfil.esquema_default,
                                   help=T("conectores_schema_help"))
        _empresa_erp = _ce2.text_input(
            T("conectores_company_field"), value="", help=T("conectores_company_help"))

        _sql = conectores.sql_de(_perfil.clave, _tipo, esquema=_esquema,
                                 empresa=_empresa_erp or "EMPRESA", lang=LANG)
        st.write(T("conectores_query_to_run"))
        _sql_editado = st.text_area("SQL", value=_sql, height=220,
                                    label_visibility="collapsed")

        _consulta = _perfil.consultas[_tipo]
        if _consulta.nota:
            st.caption(_consulta.nota)
        st.write(T("conectores_col_interpretation"))
        st.dataframe(pd.DataFrame([
            {T("col_column_name"): _c.columna, T("col_goes_to"): _c.destino,
             T("col_conversion"): _c.transformacion, T("col_note"): _c.nota}
            for _c in _consulta.campos]), use_container_width=True, hide_index=True)

        st.markdown(T("conectores_connect_h"))
        _cadena = st.text_input(
            T("dataeng_conn_string"), type="password", placeholder="mssql+pyodbc://...",
            help=T("conectores_conn_string_help"))

        _cb1, _cb2 = st.columns(2)
        if _cb1.button(T("conectores_probe_btn"), disabled=not _cadena, icon=":material/search:"):
            try:
                _ej = conectores.crear_ejecutor(_cadena, LANG)
                _s = conectores.sondear(_ej, _perfil.clave, _tipo, esquema=_esquema,
                                        empresa=_empresa_erp, lang=LANG)
                (st.success if _s.sirve else st.error)(_s.resumen(LANG))
                if _s.detalle:
                    with st.expander(T("conectores_engine_error_expander")):
                        st.json(_s.detalle)
            except Exception as _exc:
                st.error(T("conectores_connect_failed").format(e=_exc))

        if _cb2.button(T("conectores_fetch_btn"), disabled=not _cadena, type="primary", icon=":material/download:"):
            try:
                _ej = conectores.crear_ejecutor(_cadena, LANG)
                conectores.validar_solo_lectura(_sql_editado, LANG)
                _crudo = _ej(_sql_editado)
                _df_erp = conectores.convertir(_crudo, _perfil.clave, _tipo, LANG)
                st.session_state["erp_df"] = _df_erp
                st.success(T("conectores_erp_result").format(n=len(_df_erp)))
            except conectores.ConsultaInsegura as _exc:
                st.error(str(_exc))
            except Exception as _exc:
                st.error(T("conectores_query_failed").format(e=_exc))

        _df_erp = st.session_state.get("erp_df")
        if _df_erp is not None and not _df_erp.empty:
            st.write(T("conectores_erp_converted"))
            st.dataframe(_df_erp.head(20), use_container_width=True)
            st.caption(T("conectores_check_caption"))
            _destino = "proyectos" if _tipo == "proyectos" else "tareas"
            _destino_label = T("import_opt_projects") if _destino == "proyectos" else T("import_opt_tasks")
            _sug = importer.detectar_columnas(_df_erp, _destino, LANG)
            _rep_erp = importer.validar(
                _df_erp, _destino, {k: v.columna for k, v in _sug.items() if v.columna},
                proyectos=proj_df if _destino == "tareas" else None,
                usuarios=db.listar_usuarios() if _destino == "tareas" else None,
                existentes=(db.projects(incluir_archivados=True)
                            if _destino == "proyectos" else db.tasks()),
                proyecto_default_id=(int(proj_df.iloc[0]["_id"])
                                     if _destino == "tareas" and not proj_df.empty
                                     else None),
                lang=LANG)
            _m1, _m2, _m3 = st.columns(3)
            _m1.metric(T("import_will_create"), _rep_erp.filas_validas)
            _m2.metric(T("import_will_discard"), _rep_erp.filas_rechazadas)
            _m3.metric(T("import_duplicates"), _rep_erp.duplicados_archivo + _rep_erp.duplicados_base)
            st.caption(_rep_erp.resumen(LANG))
            for _av in _rep_erp.avisos_columna:
                st.warning(_av)
            if _rep_erp.problemas:
                with st.expander(T("erp_details_expander").format(n=len(_rep_erp.problemas))):
                    st.dataframe(_rep_erp.problemas_df(), use_container_width=True)
            if _rep_erp.puede_importar and st.button(
                    T("erp_import_btn").format(n=_rep_erp.filas_validas, tipo=_destino_label),
                    type="primary", icon=":material/check:", key="importar_erp"):
                _n = importer.aplicar(_rep_erp, db.crear_proyecto, db.crear_tarea)
                st.session_state.pop("erp_df", None)
                st.success(T("erp_import_done").format(n=_n, tipo=_destino_label))
                st.rerun()

elif section == T("nav_data_eng"):
    st.subheader(T("nav_data_eng"))
    if not (_es_owner or licensing.tiene_feature(LICENSE_TOKEN, "reportes_automaticos")):
        st.warning(T("dataeng_no_plan"), icon=":material/lock:")
        st.stop()
    st.caption(T("dataeng_caption"))

    _origen = st.radio(T("dataeng_source_label"),
                       [T("dataeng_source_file"), T("dataeng_source_sql")], horizontal=True)

    _df_de = None
    _nombre_de = "tabla"

    if _origen == T("dataeng_source_file"):
        _subido_de = st.file_uploader(T("dataeng_upload_label"),
                                      type=["csv", "xlsx"], key="dataeng_uploader")
        if _subido_de is not None:
            try:
                _df_de = (pd.read_csv(_subido_de) if _subido_de.name.lower().endswith("csv")
                          else pd.read_excel(_subido_de))
                _nombre_de = re.sub(r"\.\w+$", "", _subido_de.name)
            except Exception as _exc:                                # archivo ilegible
                st.error(T("dataeng_read_err").format(e=_exc))
    else:
        st.caption(T("dataeng_sql_caption"))
        _cadena_de = st.text_input(
            T("dataeng_conn_string"), type="password", placeholder="postgresql://usuario:clave@host/base",
            key="dataeng_cadena", help=T("dataeng_conn_help"))
        _consulta_de = st.text_area(
            T("dataeng_select_query"), placeholder="SELECT * FROM mi_tabla", key="dataeng_consulta")
        _nombre_de = st.text_input(T("dataeng_report_name"), value="consulta_sql",
                                   key="dataeng_nombre")
        if st.button(T("btn_profile"), disabled=not (_cadena_de and _consulta_de),
                     type="primary", icon=":material/search:"):
            try:
                st.session_state["dataeng_reporte"] = dataeng.perfilar_consulta_sql(
                    _cadena_de, _consulta_de, nombre=_nombre_de or "consulta_sql")
            except conectores.ConsultaInsegura as _exc:
                st.error(str(_exc))
            except RuntimeError as _exc:                    # falta SQLAlchemy/driver
                st.error(str(_exc))
            except Exception as _exc:
                st.error(T("conectores_query_failed").format(e=_exc))

    if _df_de is not None:
        if _df_de.empty:
            st.warning(T("import_no_rows"))
        else:
            st.session_state["dataeng_reporte"] = dataeng.perfilar_tabla(_nombre_de, _df_de)

    _reporte_de = st.session_state.get("dataeng_reporte")
    if _reporte_de is not None:
        st.markdown(T("dataeng_result_h").format(nombre=_reporte_de.nombre))
        _p = _reporte_de.perfil
        _c = _reporte_de.calidad
        _m1, _m2, _m3, _m4 = st.columns(4)
        _m1.metric(T("col_rows"), _p["filas"])
        _m2.metric(T("col_columns"), _p["columnas"])
        _m3.metric(T("dataeng_quality_score"), f"{_c['score']:.0f} / 100")
        _m4.metric(T("dataeng_issues_found"), len(_c["issues"]))

        if _reporte_de.cambios_tipado:
            with st.expander(T("dataeng_types_fixed").format(n=len(_reporte_de.cambios_tipado))):
                st.dataframe(pd.DataFrame(_reporte_de.cambios_tipado,
                                          columns=[T("col_column"), T("col_type_before"), T("col_type_after")]),
                            use_container_width=True, hide_index=True)

        st.markdown(T("dataeng_profile_by_col"))
        st.dataframe(pd.DataFrame(_p["detalle"]), use_container_width=True, hide_index=True)

        st.markdown(T("dataeng_quality_issues"))
        if _c["issues"]:
            st.dataframe(pd.DataFrame(_c["issues"]), use_container_width=True, hide_index=True)
        else:
            st.success(T("dataeng_no_issues"))

        if _reporte_de.claves["pk"]:
            st.markdown(T("dataeng_candidate_pk"))
            st.dataframe(pd.DataFrame(_reporte_de.claves["pk"]),
                        use_container_width=True, hide_index=True)

        if _reporte_de.tiempo:
            st.markdown(T("dataeng_time_coverage"))
            _t = _reporte_de.tiempo
            _t1, _t2, _t3 = st.columns(3)
            _t1.metric(T("col_from"), str(_t["desde"])[:10])
            _t2.metric(T("col_to"), str(_t["hasta"])[:10])
            _t3.metric(T("dataeng_days_no_data"), _t["dias_faltantes"])
            if _t["futuras"]:
                st.warning(T("dataeng_future_dates").format(n=_t["futuras"], col=_t["columna"]))

        st.markdown(T("dataeng_downloads_h"))
        _dd1, _dd2 = st.columns(2)
        _dd1.download_button(T("dataeng_ddl_btn"), _reporte_de.ddl,
                             file_name=f"{_reporte_de.nombre}.sql", icon=":material/download:")
        _dd2.download_button(T("dataeng_excel_btn"),
                             dataeng.exportar_excel_bytes(_reporte_de),
                             file_name=f"perfil_{_reporte_de.nombre}.xlsx",
                             icon=":material/download:")

elif section == T("nav_capacitacion"):
    st.subheader(T("nav_capacitacion"))
    st.caption(T("capacitacion_caption"))

    _rol = st.selectbox(T("field_role_select"), capacitacion.roles(LANG),
                        format_func=lambda r: f"{r[1]} — {r[2]} min")[0]
    _c = capacitacion.obtener(_rol, LANG)

    st.write(T("capacitacion_summary").format(rol=_c.rol, min=_c.minutos, n=len(_c.modulos)))
    st.write(T("capacitacion_for_whom").format(texto=_c.para_quien))
    st.write(T("capacitacion_promise").format(texto=_c.promesa))
    if _c.requiere:
        st.info(T("capacitacion_prereq").format(
            lista=", ".join(capacitacion.obtener(_r, LANG).rol for _r in _c.requiere)))

    _tc1, _tc2, _tc3 = st.tabs([T("capacitacion_tab_modules"), T("capacitacion_tab_verify"),
                                T("capacitacion_tab_plan")])
    with _tc1:
        for _i, _m in enumerate(_c.modulos, 1):
            with st.expander(f"{_i}. {_m.titulo}  ·  {_m.minutos} min"):
                st.write(T("capacitacion_where").format(obj=_m.objetivo, seccion=_m.seccion_app))
                st.write(T("capacitacion_script_h"))
                for _j, _paso in enumerate(_m.guion, 1):
                    st.write(f"{_j}. {_paso}")
                st.write(T("capacitacion_practice").format(texto=_m.practica))
                st.write(T("capacitacion_verify_h"))
                for _v in _m.verificacion:
                    st.write(f"- {_v}")
        st.download_button(T("capacitacion_download_script"),
                           capacitacion.guion_de(_rol, LANG).encode("utf-8"),
                           file_name=f"capacitacion_{_rol}.md", mime="text/markdown",
                           icon=":material/download:")
    with _tc2:
        st.write(T("capacitacion_verify_caption"))
        st.dataframe(pd.DataFrame(capacitacion.checklist_de_verificacion(_rol, LANG)),
                     use_container_width=True, hide_index=True)
    with _tc3:
        _plan = capacitacion.plan_de_grabacion(LANG)
        st.write(T("capacitacion_plan_summary").format(
            n=len(_plan), min=capacitacion.minutos_totales_a_grabar(LANG)))
        st.dataframe(pd.DataFrame([
            {T("col_module"): _m["titulo"], T("col_min"): _m["minutos"],
             T("col_where"): _m["seccion_app"], T("col_roles"): ", ".join(_m["roles"])}
            for _m in _plan]), use_container_width=True, hide_index=True)

elif section == T("nav_config_ia"):
    st.subheader(T("cfg_titulo"))
    st.caption(T("cfg_intro"))

    _provs_cfg = modelos.con_clave()
    if not _provs_cfg:
        st.info(T("cfg_sin_proveedores"))
        st.code("\n".join(
            f"export {_cfg['env_clave']}=...    # {_cfg['etiqueta']}"
            for _cfg in modelos.PROVEEDORES.values()), language="bash")
    else:
        # El catálogo traído de la API vive en la sesión, no en la base: es una
        # foto de lo que el proveedor contestó hoy y mañana puede ser otra. Lo
        # que sí se persiste —porque es una decisión del cliente— es el modelo
        # elegido.
        _catalogos = st.session_state.setdefault("catalogos_ia", {})

        for _prov_cfg in _provs_cfg:
            with st.expander(modelos.etiqueta(_prov_cfg), expanded=True, icon=":material/smart_toy:"):
                _elegido_actual = modelos.modelo_actual(_prov_cfg)
                st.caption(f"{T('cfg_en_uso')}: "
                           f"**{_elegido_actual or T('cfg_sin_elegir')}**")

                if st.button(T("cfg_actualizar"), key=f"cfg_upd_{_prov_cfg}",
                             icon=":material/refresh:",
                             help=T("cfg_actualizar_ayuda")):
                    try:
                        _catalogos[_prov_cfg] = modelos.listar_desde_api(_prov_cfg)
                        st.success(f"{len(_catalogos[_prov_cfg])} {T('cfg_traidos')}.")
                    except modelos.ErrorDeProveedor as exc:
                        # Se muestra el motivo: el usuario apretó un botón que
                        # dice "actualizar" y merece saber por qué no pasó nada.
                        st.error(seguro.escapar(str(exc)))

                _lista = _catalogos.get(_prov_cfg, [])
                if not _lista:
                    st.caption(T("cfg_sin_catalogo"))

                with st.form(f"cfg_form_{_prov_cfg}"):
                    _opciones = [T("cfg_sin_elegir"), *_lista]
                    _idx = (_opciones.index(_elegido_actual)
                            if _elegido_actual in _opciones else 0)
                    _sel = st.selectbox(T("cfg_modelo"), _opciones, index=_idx,
                                        key=f"cfg_sel_{_prov_cfg}")
                    # Escape para el proveedor sin endpoint de listado, o
                    # cuando el catálogo falla y el cliente igual sabe qué ID
                    # quiere usar. Lo escrito a mano le gana a lo elegido.
                    _manual = st.text_input(T("cfg_modelo_manual"),
                                            key=f"cfg_man_{_prov_cfg}")
                    if st.form_submit_button(T("cfg_guardar"), icon=":material/save:"):
                        _nuevo = _manual.strip() or (
                            _sel if _sel != T("cfg_sin_elegir") else None)
                        modelos.fijar_modelo(_prov_cfg, _nuevo)
                        db.guardar_version(EMPRESA_ID, "config_ia", "modelos",
                                           modelos.serializar_seleccion(),
                                           estado="vigente",
                                           recomendado_por=user["nombre"])
                        st.success(T("cfg_guardado"))
                        st.rerun()

        _hist_ia = db.historial_versiones(EMPRESA_ID, "config_ia", "modelos")
        if len(_hist_ia) > 0:
            with st.expander(f"{T('cfg_historial')} ({len(_hist_ia)})", icon=":material/history_edu:"):
                st.dataframe(_hist_ia[["contenido", "recomendado_por", "creado_en"]],
                             use_container_width=True, hide_index=True)

elif section == T("nav_users"):
    st.subheader(T("nav_users"))
    st.dataframe(equipo_df, use_container_width=True)
    st.caption(T("users_caption"))
