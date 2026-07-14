"""MV Project Management — dashboard operativo (Streamlit).

Un único motor (mvpm/) alimenta este dashboard, la API REST (api/main.py) y
los exportadores — sin lógica de negocio duplicada entre capas. Los datos
viven en una base SQLite real (mvpm/db.py) en el equipo del cliente, detrás
de un login con usuario y contraseña (mvpm/auth.py).
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from mvpm import (
    BRAND,
    advisor,
    auth,
    case_study,
    catalog,
    db,
    demo_real,
    dependencies as dep_mod,
    exporters,
    glossary,
    health,
    help_center,
    i18n,
    licensing,
    pmbok,
    policies,
    prioritizer,
    reports,
    reviews,
    tutorial,
)
from mvpm import copilot as copilot_mod

st.set_page_config(page_title="MV Project Management", page_icon="📋", layout="wide")

st.markdown(
    f"""
    <style>
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


LANG_ES_DEFAULT = "es"  # se reasigna abajo una vez que hay sesión iniciada, T() ya está definida


# ------------------------------------------------------------- autenticación

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.title("📋 MV Project Management")

    if db.contar_usuarios() == 0:
        st.subheader("Creá la cuenta de administrador")
        st.caption("Sos la primera persona en usar este servidor — tu cuenta va a ser admin. El resto del equipo se registra después con su propio usuario y contraseña.")
        with st.form("bootstrap_admin"):
            nombre = st.text_input("Nombre")
            email = st.text_input("Email")
            password = st.text_input("Contraseña (mín. 8 caracteres)", type="password")
            enviado = st.form_submit_button("Crear cuenta de administrador")
            if enviado:
                try:
                    user = auth.registrar(email, nombre, password)
                    st.session_state["user"] = user
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        tab_login, tab_registro = st.tabs(["Ingresar", "Crear cuenta"])
        with tab_login:
            with st.form("login"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Contraseña", type="password", key="login_password")
                enviado = st.form_submit_button("Ingresar")
                if enviado:
                    user = auth.iniciar_sesion(email, password)
                    if user:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("Email o contraseña incorrectos.")
        with tab_registro:
            with st.form("registro"):
                nombre = st.text_input("Nombre", key="reg_nombre")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Contraseña (mín. 8 caracteres)", type="password", key="reg_password")
                enviado = st.form_submit_button("Crear cuenta")
                if enviado:
                    try:
                        user = auth.registrar(email, nombre, password)
                        st.session_state["user"] = user
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

user = st.session_state["user"]

LANG = st.sidebar.selectbox("Idioma / Language / Idioma", ["es", "en", "pt"], index=0)
LANG_ES_DEFAULT = LANG  # T() ya definida arriba usa esta variable global

LICENSE_TOKEN = st.sidebar.text_input(
    "Token de licencia (opcional)", type="password",
    help="Se emite automáticamente al pagar el plan Professional. Sin token, corrés en plan demo.",
) or None

st.sidebar.divider()
st.sidebar.caption(f"👤 {user['nombre']} · {user['rol']}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state["user"] = None
    st.rerun()

st.sidebar.title(T("app_title"))

nav_options = [
    T("nav_tutorial"), T("nav_case_study"), T("nav_real_demo"), T("nav_portfolio"), T("nav_tasks"),
    T("nav_health"), T("nav_dependencies"), T("nav_backlog"), T("nav_copilot"), T("nav_advisor"),
    T("nav_reports"), T("nav_reviews"), T("nav_glossary"), T("nav_policies"), T("nav_pmbok"), T("nav_import"),
]
if user["rol"] == "admin":
    nav_options.append(T("nav_users"))

section = st.sidebar.radio("Sección", nav_options)

st.title(T("app_title"))


def load_data():
    return db.projects(), db.tasks(), db.team()


proj_df, task_df, team_df = load_data()
equipo_df = db.listar_usuarios()


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
    st.info("Todavía no cargaste proyectos en este servidor.")
    if st.button("🌱 Cargar datos de ejemplo para explorar"):
        db.cargar_datos_de_ejemplo()
        st.rerun()

# ------------------------------------------------------------------ secciones

if section == T("nav_tutorial"):
    st.subheader(T("nav_tutorial"))
    st.caption("Guía operativa de cada herramienta del programa — cómo usarla, no solo qué es.")
    for i, s in enumerate(tutorial.sections()):
        with st.expander(f"{s['titulo']}", expanded=(i == 0)):
            st.write(s["resumen"])
            st.markdown("**Cómo usarlo:**")
            for paso in s["pasos"]:
                st.markdown(f"- {paso}")
            if s["tips"]:
                st.markdown("**Tips:**")
                for tip in s["tips"]:
                    st.markdown(f"💡 {tip}")

elif section == T("nav_case_study"):
    st.subheader(T("nav_case_study"))
    st.caption("Un proyecto simulado completo, recorrido por las herramientas del programa paso a "
               "paso — con los números reales que calcula el motor sobre el dato de ejemplo, no un "
               "guion inventado para la demo.")
    caso = case_study.narrar_caso()
    st.markdown(f"**Proyecto elegido:** {caso['nombre']} ({caso['proyecto_id']}) — "
                f"índice de salud {caso['indice']}/100, estado *{caso['estado']}*.")
    st.divider()
    for paso in caso["pasos"]:
        st.markdown(f"##### {paso['titulo']}")
        st.caption(paso["seccion"])
        st.write(paso["texto"])
        st.write("")
    if proj_df.empty:
        st.info("Todavía no cargaste tus propios proyectos — este recorrido usa el dato de ejemplo "
                "para que veas el flujo completo antes de cargar los tuyos.")

elif section == T("nav_real_demo"):
    st.subheader(T("nav_real_demo"))
    st.caption(f"Fuente: {demo_real.FUENTE}")
    st.caption(f"No son datos sintéticos — son 132 proyectos reales de gobierno, filtrados a los "
               f"que tienen calificación de confianza y presupuesto numérico completos en el "
               f"informe original. [Descargar el dataset original]({demo_real.FUENTE_URL}).")

    resumen = demo_real.resumen_portafolio()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proyectos reales analizados", resumen["total_proyectos"])
    c2.metric("Sobre presupuesto (año fiscal)", resumen["sobre_presupuesto"])
    c3.metric("Presupuesto total", f"£{resumen['presupuesto_total_m']:,.0f}M")
    c4.metric("Ejecutado total", f"£{resumen['ejecutado_total_m']:,.0f}M")
    st.caption("'Sobre presupuesto' compara el baseline y el ejecutado del año fiscal 2021/22 "
               "reportado por cada departamento — no el costo total a lo largo de vida del proyecto.")

    st.info(
        f"⏱️ **Ahorro estimado de tiempo**: revisar a mano estos {resumen['total_proyectos']} "
        f"proyectos para encontrar cuáles están sobre presupuesto — a un supuesto de "
        f"{resumen['minutos_por_revision_manual_supuesto']} minutos por proyecto, un número "
        f"explícito, no medido — tomaría ~{resumen['horas_ahorradas_estimadas']} horas de trabajo "
        f"manual de un PMO. El motor los detecta a todos en segundos, cada vez que se le pide."
    )

    st.subheader("Los 10 más desviados, detectados por el motor")
    st.dataframe(resumen["proyectos_sobre_presupuesto_detalle"], use_container_width=True)

    st.divider()
    st.subheader("Dos casos, con el texto real del informe anual")
    for nombre in ["Social Housing Decarbonisation Fund", "Borders & Trade Programme"]:
        c = demo_real.caso(nombre)
        icon = {"Red": "🔴", "Amber": "🟡", "Green": "🟢"}[c["rag"]]
        with st.expander(f"{icon} {c['nombre']} — {c['depto']}"):
            st.write(c["resumen"])
            st.markdown(f"**Lo que calcula el motor sobre este proyecto:** presupuesto £{c['presupuesto_m']:.1f}M, "
                        f"ejecutado £{c['ejecutado_m']:.1f}M ({c['ejecucion_pct']}%) — "
                        + ("marcado sobre presupuesto." if c["sobre_presupuesto"] else "dentro de presupuesto."))
            st.markdown("**Texto real del informe anual sobre el presupuesto:**")
            st.caption(c["narrativa_real"])
            st.markdown("**Texto real del informe anual sobre la revisión de entrega:**")
            st.caption(c["revision_real"])

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

    with st.expander("➕ Nuevo proyecto"):
        with st.form("nuevo_proyecto", clear_on_submit=True):
            nombre = st.text_input("Nombre del proyecto")
            col1, col2 = st.columns(2)
            portafolio = col1.text_input("Portafolio", value="Producto Core")
            sponsor = col2.text_input("Sponsor")
            dueno_id = _selector_usuario("Dueño", "nuevo_proy_dueno")
            segmento = st.selectbox("Segmento", ["Interno", "Cliente externo", "Regulatorio"])
            col3, col4 = st.columns(2)
            fecha_inicio = col3.date_input("Fecha de inicio", value=date.today())
            fecha_fin = col4.date_input("Fecha de fin", value=date.today())
            col5, col6 = st.columns(2)
            presupuesto = col5.number_input("Presupuesto", min_value=0.0, step=100.0)
            ejecutado = col6.number_input("Ejecutado", min_value=0.0, step=100.0)
            criticidad = st.selectbox("Criticidad", ["Alta", "Media", "Baja"], index=1)
            enviado = st.form_submit_button("Crear proyecto")
            if enviado:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    db.crear_proyecto(
                        nombre=nombre.strip(), portafolio=portafolio.strip() or "Sin portafolio",
                        sponsor=sponsor.strip() or None, dueno_id=dueno_id, segmento=segmento,
                        fecha_inicio=str(fecha_inicio), fecha_fin=str(fecha_fin),
                        presupuesto=presupuesto, ejecutado=ejecutado, criticidad=criticidad,
                    )
                    st.success(f"Proyecto '{nombre}' creado.")
                    st.rerun()

    if not proj_df.empty:
        st.subheader(T("nav_portfolio"))
        st.dataframe(catalog.catalog(proj_df).drop(columns=["_id"]), use_container_width=True)

        with st.expander("✏️ Ficha de proyecto (editar / archivar / eliminar)"):
            opciones = (proj_df["nombre"] + " — " + proj_df["proyecto_id"]).tolist()
            elegido = st.selectbox("Elegí un proyecto", opciones, key="ficha_proyecto_selector")
            fila = proj_df.iloc[opciones.index(elegido)]
            with st.form("editar_proyecto"):
                nombre_e = st.text_input("Nombre", value=fila["nombre"])
                col1, col2 = st.columns(2)
                portafolio_e = col1.text_input("Portafolio", value=fila["portafolio"])
                sponsor_e = col2.text_input("Sponsor", value=fila["sponsor"] or "")
                dueno_id_e = _selector_usuario(
                    "Dueño", "editar_proy_dueno",
                    actual_id=equipo_df[equipo_df["nombre"] == fila["dueno"]]["id"].iloc[0]
                    if fila["dueno"] and (equipo_df["nombre"] == fila["dueno"]).any() else None,
                )
                segmento_e = st.selectbox("Segmento", ["Interno", "Cliente externo", "Regulatorio"],
                                           index=["Interno", "Cliente externo", "Regulatorio"].index(fila["segmento"])
                                           if fila["segmento"] in ["Interno", "Cliente externo", "Regulatorio"] else 0)
                col3, col4 = st.columns(2)
                presupuesto_e = col3.number_input("Presupuesto", min_value=0.0, step=100.0, value=float(fila["presupuesto"]))
                ejecutado_e = col4.number_input("Ejecutado", min_value=0.0, step=100.0, value=float(fila["ejecutado"]))
                criticidad_e = st.selectbox("Criticidad", ["Alta", "Media", "Baja"],
                                             index=["Alta", "Media", "Baja"].index(fila["criticidad"]))
                guardar = st.form_submit_button("💾 Guardar cambios")
                if guardar:
                    db.actualizar_proyecto(
                        int(fila["_id"]), nombre=nombre_e.strip(), portafolio=portafolio_e.strip(),
                        sponsor=sponsor_e.strip() or None, dueno_id=dueno_id_e, segmento=segmento_e,
                        presupuesto=presupuesto_e, ejecutado=ejecutado_e, criticidad=criticidad_e,
                    )
                    st.success("Cambios guardados.")
                    st.rerun()
            col_a, col_b = st.columns(2)
            if col_a.button("🗄️ Archivar proyecto", key="archivar_proy"):
                db.archivar_proyecto(int(fila["_id"]))
                st.success("Proyecto archivado.")
                st.rerun()
            if col_b.button("🗑️ Eliminar definitivamente", key="eliminar_proy"):
                db.eliminar_proyecto(int(fila["_id"]))
                st.success("Proyecto eliminado.")
                st.rerun()

        st.subheader("Por portafolio")
        st.bar_chart(catalog.por_portafolio(proj_df).set_index("portafolio")[["presupuesto", "ejecutado"]])

elif section == T("nav_tasks"):
    st.subheader(T("nav_tasks"))

    with st.expander("➕ Nueva tarea"):
        if proj_df.empty:
            st.warning("Creá un proyecto primero.")
        else:
            with st.form("nueva_tarea", clear_on_submit=True):
                proyecto_opciones = (proj_df["nombre"] + " — " + proj_df["proyecto_id"]).tolist()
                proyecto_elegido = st.selectbox("Proyecto", proyecto_opciones)
                proyecto_real_id = int(proj_df.iloc[proyecto_opciones.index(proyecto_elegido)]["_id"])
                titulo = st.text_input("Título de la tarea")
                responsable_id = _selector_usuario("Responsable", "nueva_tarea_resp")
                col1, col2 = st.columns(2)
                estado = col1.selectbox("Estado", ["todo", "in_progress", "blocked", "done"])
                prioridad = col2.selectbox("Prioridad", ["Alta", "Media", "Baja"], index=1)
                vencimiento = st.date_input("Vencimiento", value=date.today())
                dep_opciones = ["(ninguna)"] + (task_df["titulo"] + " — " + task_df["tarea_id"]).tolist()
                dependencia = st.selectbox("Depende de", dep_opciones)
                enviado = st.form_submit_button("Crear tarea")
                if enviado:
                    if not titulo.strip():
                        st.error("El título es obligatorio.")
                    else:
                        depende_de_id = None
                        if dependencia != "(ninguna)":
                            depende_de_id = int(task_df.iloc[dep_opciones.index(dependencia) - 1]["_id"])
                        db.crear_tarea(
                            proyecto_id=proyecto_real_id, titulo=titulo.strip(),
                            responsable_id=responsable_id, estado=estado,
                            vencimiento=str(vencimiento), prioridad=prioridad, depende_de=depende_de_id,
                        )
                        st.success(f"Tarea '{titulo}' creada.")
                        st.rerun()

    if not task_df.empty:
        st.dataframe(task_df.drop(columns=["_id"]), use_container_width=True)

        with st.expander("✏️ Ficha de tarea (editar / eliminar)"):
            t_opciones = (task_df["titulo"] + " — " + task_df["tarea_id"]).tolist()
            t_elegida = st.selectbox("Elegí una tarea", t_opciones, key="ficha_tarea_selector")
            t_fila = task_df.iloc[t_opciones.index(t_elegida)]
            with st.form("editar_tarea"):
                titulo_e = st.text_input("Título", value=t_fila["titulo"])
                responsable_actual = equipo_df[equipo_df["nombre"] == t_fila["responsable"]]["id"].iloc[0] \
                    if t_fila["responsable"] and (equipo_df["nombre"] == t_fila["responsable"]).any() else None
                responsable_id_e = _selector_usuario("Responsable", "editar_tarea_resp", actual_id=responsable_actual)
                col1, col2 = st.columns(2)
                estado_e = col1.selectbox("Estado", ["todo", "in_progress", "blocked", "done"],
                                           index=["todo", "in_progress", "blocked", "done"].index(t_fila["estado"]))
                prioridad_e = col2.selectbox("Prioridad", ["Alta", "Media", "Baja"],
                                              index=["Alta", "Media", "Baja"].index(t_fila["prioridad"]))
                guardar_t = st.form_submit_button("💾 Guardar cambios")
                if guardar_t:
                    db.actualizar_tarea(int(t_fila["_id"]), titulo=titulo_e.strip(),
                                         responsable_id=responsable_id_e, estado=estado_e, prioridad=prioridad_e)
                    st.success("Cambios guardados.")
                    st.rerun()
            if st.button("🗑️ Eliminar tarea", key="eliminar_tarea"):
                db.eliminar_tarea(int(t_fila["_id"]))
                st.success("Tarea eliminada.")
                st.rerun()

elif section == T("nav_health"):
    h = health.project_health(proj_df, task_df, team_df)
    st.subheader(f"{T('nav_health')} — índice global: {health.overall_index(proj_df, task_df, team_df)}/100")
    estado_color = {"saludable": "🟢", "observacion": "🟡", "riesgo": "🔴"}
    h_display = h.copy()
    h_display["estado"] = h_display["estado"].map(lambda e: f"{estado_color.get(e,'')} {e}")
    st.dataframe(h_display, use_container_width=True)
    st.subheader("Matriz por dimensión")
    matriz = health.matriz_por_dimension(proj_df, task_df, team_df).set_index("nombre")
    st.dataframe(matriz.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=100), use_container_width=True)

elif section == T("nav_dependencies"):
    st.subheader(T("nav_dependencies"))
    bloqueos = dep_mod.bloqueos_activos(task_df)
    if bloqueos.empty:
        st.success("No hay tareas bloqueadas activas.")
    else:
        st.dataframe(bloqueos[["tarea_id", "titulo", "proyecto_id", "tareas_impactadas"]], use_container_width=True)
    st.subheader("Dependencias inconsistentes")
    orphans = dep_mod.orphan_dependencies(task_df)
    if orphans.empty:
        st.success("Sin dependencias huérfanas.")
    else:
        st.warning(f"{len(orphans)} dependencia(s) apuntan a una tarea inexistente.")
        st.dataframe(orphans, use_container_width=True)

elif section == T("nav_backlog"):
    st.subheader(T("nav_backlog"))
    st.caption("Ordenado por valor esperado = criticidad × prioridad × urgencia × impacto en dependencias.")
    st.dataframe(
        prioritizer.prioritized_backlog(proj_df, task_df)[
            ["tarea_id", "titulo", "proyecto_id", "estado", "valor_esperado", "tareas_impactadas", "dias_restantes"]
        ],
        use_container_width=True,
    )

elif section == T("nav_copilot"):
    st.subheader(T("nav_copilot"))
    st.caption("El motor de reglas responde siempre. Si hay ANTHROPIC_API_KEY configurada y todavía hay cupo de IA en tu plan, Claude pule el lenguaje sin inventar cifras nuevas.")
    puede_ia, detalle_cupo = licensing.puede_usar_ia(LICENSE_TOKEN)
    st.caption(f"Cupo de IA: {detalle_cupo}")
    q = st.text_input("Preguntá sobre el portafolio", "¿Qué está bloqueando los proyectos?")
    if st.button("Preguntar"):
        result = copilot_mod.answer(q, proj_df, task_df, team_df, license_token=LICENSE_TOKEN)
        st.info(result["answer"])
        st.caption("Respuesta enriquecida con IA" if result["ai_enriched"] else "Respuesta del motor de reglas (sin IA)")

elif section == T("nav_advisor"):
    st.subheader(T("nav_advisor"))
    st.caption("El motor de reglas detecta los problemas siempre. La redacción de la sugerencia se "
               "puede pulir con el proveedor de IA que tengas configurado — nunca inventa el problema "
               "ni el número que lo sustenta, sólo redacta mejor la acción sugerida.")
    disponibles = advisor.proveedores_disponibles()
    etiquetas = {"claude": "Claude", "chatgpt": "ChatGPT", "gemini": "Gemini"}
    opciones_ia = ["Motor de reglas (sin IA)"] + [etiquetas[p] for p in disponibles]
    elegido = st.radio("Redacción de la sugerencia", opciones_ia, horizontal=True)
    proveedor = next((p for p in disponibles if etiquetas[p] == elegido), None)
    if not disponibles:
        st.caption("Sin proveedores de IA configurados — corriendo 100% con el motor de reglas. "
                   "Para sumar redacción con IA, configurá ANTHROPIC_API_KEY (Claude), o "
                   "OPENAI_API_KEY + OPENAI_MODEL (ChatGPT), o GEMINI_API_KEY + GEMINI_MODEL (Gemini).")

    problemas = advisor.detectar_problemas(proj_df, task_df, team_df)
    icon_severidad = {"alta": "🔴", "media": "🟡", "baja": "⚪"}
    if not problemas:
        st.success("El motor de reglas no detectó problemas activos en el portafolio ahora mismo.")
    for p in problemas:
        seg = db.obtener_seguimiento_por_problema(p["id"])
        with st.expander(f"{icon_severidad[p['severidad']]} {p['titulo']}"):
            resultado = advisor.sugerir(p, proveedor=proveedor)
            st.write(resultado["sugerencia"])
            st.caption(f"Redactado por {etiquetas[resultado['proveedor']]}" if resultado["ai_enriched"]
                       else "Motor de reglas (sin IA)")
            if seg:
                nuevo_estado = st.selectbox(
                    "Estado del seguimiento", ["abierto", "en_progreso", "resuelto"],
                    index=["abierto", "en_progreso", "resuelto"].index(seg["estado"]),
                    key=f"estado_{p['id']}",
                )
                if nuevo_estado != seg["estado"]:
                    db.actualizar_estado_seguimiento(seg["id"], nuevo_estado)
                    st.rerun()
            elif st.button("📌 Poner en seguimiento", key=f"seguir_{p['id']}"):
                db.crear_o_actualizar_seguimiento(p["id"], p["tipo"], p["titulo"],
                                                   resultado["sugerencia"], resultado["proveedor"])
                st.rerun()

    seguimientos_df = db.listar_seguimientos()
    if not seguimientos_df.empty:
        st.divider()
        st.subheader("Seguimientos")
        st.caption("Se mantienen acá aunque el problema original ya no se detecte — así queda el "
                   "historial de qué se resolvió y cuándo.")
        st.dataframe(seguimientos_df[["titulo", "tipo", "estado", "proveedor", "actualizado_en"]],
                     use_container_width=True)

elif section == T("nav_reports"):
    st.subheader(T("nav_reports"))
    st.code(reports.as_text(proj_df, task_df, team_df), language=None)
    st.download_button("Descargar JSON del portafolio", exporters.to_json_bundle(proj_df, task_df, team_df), file_name="portafolio_mvpm.json")
    st.download_button("Descargar Excel del portafolio", exporters.to_excel_bytes(proj_df, task_df, team_df), file_name="portafolio_mvpm.xlsx")

elif section == T("nav_reviews"):
    st.subheader(T("nav_reviews"))
    s = reviews.summary()
    if s["es_beta_sin_resenas"]:
        st.info(f"⭐ {T('reviews_empty_title')} — {T('reviews_empty_body')}")
    else:
        st.metric("Calificación promedio", f"{s['promedio']} / 5 ({s['total']} reseñas)")
        for r in reviews.list_reviews():
            st.markdown(f"**{'⭐' * r['calificacion']}** — *{r['autor']}, {r['rol']} en {r['empresa']}*")
            st.write(r["comentario"])
            st.divider()
    with st.expander("Dejar una reseña"):
        with st.form("nueva_resena"):
            autor = st.text_input("Tu nombre")
            empresa = st.text_input("Empresa")
            rol = st.text_input("Rol")
            calificacion = st.slider("Calificación", 1, 5, 5)
            comentario = st.text_area("Comentario")
            enviado = st.form_submit_button("Enviar reseña")
            if enviado and autor and comentario:
                reviews.add_review(autor, empresa, rol, calificacion, comentario, verificado=False)
                st.success("¡Gracias! Tu reseña queda pendiente de verificación antes de publicarse.")

elif section == T("nav_glossary"):
    st.subheader(T("nav_glossary"))
    st.dataframe(glossary.glossary(), use_container_width=True)

elif section == T("nav_policies"):
    st.subheader(T("nav_policies"))
    pol = policies.evaluate(proj_df, task_df, team_df)
    for _, row in pol.iterrows():
        icon = "✅" if row["estado"] == "cumple" else "⚠️"
        st.markdown(f"{icon} **{row['politica']}** — {row['evidencia']}")
    st.divider()
    st.subheader("Matriz de automatización y adopción")
    for row in help_center.automation_rows():
        nivel_icon = {"auto": "🟢 automático", "parcial": "🟡 parcial", "humano": "🔴 humano"}[row["nivel"]]
        st.markdown(f"**{row['area']}** — {nivel_icon}")
        st.caption(row["detalle"])

elif section == T("nav_pmbok"):
    st.subheader(T("nav_pmbok"))
    st.caption("Alineación con las 10 áreas de conocimiento del PMBOK (guía del PMI) — no es una "
               "certificación oficial, es una referencia honesta de qué cubre el producto y qué no.")
    r = pmbok.resumen()
    c1, c2, c3 = st.columns(3)
    c1.metric("Cobertura completa", r["completa"])
    c2.metric("Cobertura parcial", r["parcial"])
    c3.metric("No cubierta", r["no_cubierta"])
    st.divider()
    icon = {"completa": "✅", "parcial": "🟡", "no_cubierta": "⚪"}
    for a in pmbok.areas():
        st.markdown(f"{icon[a['cobertura']]} **{a['area']}** ({a['area_en']})")
        if a["como_lo_cubre"]:
            st.write(a["como_lo_cubre"])
        if a["lo_que_falta"]:
            st.caption(f"Lo que falta: {a['lo_que_falta']}")
        st.divider()

elif section == T("nav_import"):
    st.subheader(T("nav_import"))
    st.caption("Subí un archivo y elegí si son proyectos o tareas — se cargan de verdad a tu base, no es solo una vista previa.")
    tipo = st.radio("¿Qué estás importando?", ["Proyectos", "Tareas"], horizontal=True)
    uploaded = st.file_uploader("Subí un CSV/Excel", type=["csv", "xlsx"])
    if uploaded is not None:
        df_import = pd.read_csv(uploaded) if uploaded.name.endswith("csv") else pd.read_excel(uploaded)
        st.write(f"{len(df_import)} filas, {len(df_import.columns)} columnas detectadas.")
        st.dataframe(df_import.head(20), use_container_width=True)
        nulos = df_import.isna().sum()
        con_nulos = nulos[nulos > 0]
        if not con_nulos.empty:
            st.write("Columnas con datos faltantes:")
            st.dataframe(con_nulos.rename("valores_nulos"))

        def _col(df, *nombres):
            cols_lower = {c.lower().strip(): c for c in df.columns}
            for n in nombres:
                if n in cols_lower:
                    return cols_lower[n]
            return None

        if st.button(f"✅ Confirmar importación como {tipo.lower()}"):
            creadas = 0
            if tipo == "Proyectos":
                c_nombre = _col(df_import, "nombre", "proyecto", "titulo")
                if not c_nombre:
                    st.error("No encontré una columna 'nombre' (o 'proyecto'/'titulo') en el archivo.")
                else:
                    c_portafolio = _col(df_import, "portafolio")
                    c_sponsor = _col(df_import, "sponsor")
                    c_criticidad = _col(df_import, "criticidad", "prioridad")
                    c_presupuesto = _col(df_import, "presupuesto", "budget")
                    c_ejecutado = _col(df_import, "ejecutado", "spent")
                    for _, row in df_import.iterrows():
                        if pd.isna(row.get(c_nombre)):
                            continue
                        db.crear_proyecto(
                            nombre=str(row[c_nombre]),
                            portafolio=str(row[c_portafolio]) if c_portafolio and pd.notna(row.get(c_portafolio)) else "Importado",
                            sponsor=str(row[c_sponsor]) if c_sponsor and pd.notna(row.get(c_sponsor)) else None,
                            dueno_id=None, segmento="Interno",
                            fecha_inicio=None, fecha_fin=None,
                            presupuesto=float(row[c_presupuesto]) if c_presupuesto and pd.notna(row.get(c_presupuesto)) else 0,
                            ejecutado=float(row[c_ejecutado]) if c_ejecutado and pd.notna(row.get(c_ejecutado)) else 0,
                            criticidad=str(row[c_criticidad]) if c_criticidad and str(row.get(c_criticidad)) in ["Alta", "Media", "Baja"] else "Media",
                        )
                        creadas += 1
            else:
                c_titulo = _col(df_import, "titulo", "tarea", "nombre")
                if not c_titulo or proj_df.empty:
                    st.error("No encontré una columna 'titulo' (o 'tarea'/'nombre'), o todavía no hay proyectos para asociar las tareas.")
                else:
                    c_estado = _col(df_import, "estado", "status")
                    c_prioridad = _col(df_import, "prioridad", "priority")
                    proyecto_default_id = int(proj_df.iloc[0]["_id"])
                    for _, row in df_import.iterrows():
                        if pd.isna(row.get(c_titulo)):
                            continue
                        db.crear_tarea(
                            proyecto_id=proyecto_default_id, titulo=str(row[c_titulo]),
                            responsable_id=None,
                            estado=str(row[c_estado]) if c_estado and str(row.get(c_estado)) in ["todo", "in_progress", "blocked", "done"] else "todo",
                            vencimiento=None,
                            prioridad=str(row[c_prioridad]) if c_prioridad and str(row.get(c_prioridad)) in ["Alta", "Media", "Baja"] else "Media",
                            depende_de=None,
                        )
                        creadas += 1
                    if creadas:
                        st.caption(f"Todas las tareas importadas quedaron asociadas a '{proj_df.iloc[0]['nombre']}' — reasignalas desde la ficha de tarea si corresponde.")
            if creadas:
                st.success(f"Se importaron {creadas} fila(s).")
                st.rerun()

elif section == T("nav_users"):
    st.subheader(T("nav_users"))
    st.dataframe(equipo_df, use_container_width=True)
    st.caption("Para sumar gente al equipo, pedile que se registre desde la pantalla de login de este mismo servidor con 'Crear cuenta'.")
