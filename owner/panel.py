"""Panel del OWNER — administración de licencias y cobros.

⚠️ ESTE ARCHIVO NO SE DISTRIBUYE AL CLIENTE.
`packaging/build_release.py` sólo empaqueta mvpm/, app/, api/ y tests/, así que
`owner/` queda fuera del ZIP y del instalador. Nunca lo agregues ahí: este panel
usa el secreto de firma de licencias (MVPM_LICENSE_SECRET) y el Access Token de
MercadoPago. Si viajan en el paquete del cliente, cualquiera se emite licencias.

Qué resuelve:
  - Emitir una licencia a mano (venta por transferencia, canje, cortesía, piloto).
  - Verificar / decodificar un token que te manda un cliente ("no me funciona").
  - Ver los cobros reales y las suscripciones activas contra la API de MercadoPago.

Correr:
    MVPM_LICENSE_SECRET=<tu-secreto> MP_ACCESS_TOKEN=<tu-token> \
        python -m streamlit run owner/panel.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mvpm import licensing  # noqa: E402

st.set_page_config(page_title="MV Project Management · Owner", page_icon="🔐", layout="wide")

MP_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
TIENE_SECRETO = bool(os.environ.get("MVPM_LICENSE_SECRET"))

st.title("🔐 Panel del owner")

if not TIENE_SECRETO:
    st.error(
        "Falta **MVPM_LICENSE_SECRET**. Sin el mismo secreto que usa la web, las "
        "licencias que emitas acá no van a validar en el programa del cliente. "
        "Exportá la variable con el mismo valor que cargaste en Vercel."
    )

tab_emitir, tab_verificar, tab_cobros = st.tabs(
    ["🎫 Emitir licencia", "🔍 Verificar token", "💳 Cobros y suscripciones"]
)

# ------------------------------------------------------------------ emitir
with tab_emitir:
    st.subheader("Emitir una licencia a mano")
    st.caption(
        "Para ventas fuera de MercadoPago (transferencia, factura, piloto, cortesía) "
        "o para reemitir la licencia de alguien que ya pagó y la perdió."
    )
    col1, col2 = st.columns(2)
    with col1:
        planes_pagos = [p for p in licensing.PLANES if p != "demo"]
        plan = st.selectbox("Plan", planes_pagos, index=0)
        email = st.text_input("Email del cliente", placeholder="cliente@empresa.com.uy")
    with col2:
        referencia = st.text_input(
            "Referencia (opcional)",
            placeholder="factura A-1234 / transferencia 15-07 / piloto",
            help="Queda dentro del token como payment_id, para rastrear de dónde salió.",
        )
        info = licensing.PLANES[plan]
        st.metric("Vigencia", f"{info['vigencia_dias']} días")
        cupo = info["cupo_mensual_ia"]
        st.caption(f"Cupo IA: {'ilimitado' if cupo is None else f'{cupo}/mes'}")

    if st.button("🎫 Emitir licencia", type="primary", disabled=not (email and TIENE_SECRETO)):
        try:
            token = licensing.issue_license(plan, email.strip(), referencia.strip() or None)
            vence = datetime.now() + timedelta(days=info["vigencia_dias"])
            st.success(f"Licencia emitida para **{email}** · vence el {vence:%d/%m/%Y}")
            st.code(token, language=None)
            st.caption(
                "Copiá el token y mandáselo al cliente. Se pega en la barra lateral "
                "del programa, campo «Token de licencia»."
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo emitir: {e}")

# --------------------------------------------------------------- verificar
with tab_verificar:
    st.subheader("Verificar un token")
    st.caption("Pegá el token que te pasó el cliente para ver si es válido y hasta cuándo vale.")
    token_in = st.text_area("Token", height=90, placeholder="MVPM1....")
    if st.button("🔍 Verificar", disabled=not token_in.strip()):
        payload = licensing.verify_license(token_in.strip())
        if not payload:
            st.error(
                "Token **inválido**: la firma no coincide. O está mal copiado, o fue "
                "emitido con otro secreto (¿cambiaste MVPM_LICENSE_SECRET?)."
            )
        else:
            vigente = licensing.licencia_vigente(payload)
            emitida = datetime.fromtimestamp(float(payload.get("iat", 0)))
            dias = licensing.PLANES.get(payload.get("plan"), {}).get("vigencia_dias")
            vence = emitida + timedelta(days=dias) if dias else None
            if vigente:
                st.success("Token válido y **vigente**")
            else:
                st.warning("Token válido pero **vencido** — hay que reemitir o renovar")
            st.json({
                "plan": payload.get("plan"),
                "email": payload.get("email"),
                "referencia_pago": payload.get("payment_id"),
                "emitida": emitida.strftime("%d/%m/%Y %H:%M"),
                "vence": vence.strftime("%d/%m/%Y") if vence else "sin vencimiento",
                "cupo_mensual_ia": payload.get("cupo_mensual_ia"),
            })

# ------------------------------------------------------------------ cobros
with tab_cobros:
    st.subheader("Cobros y suscripciones reales (MercadoPago)")
    if not MP_TOKEN:
        st.info(
            "Falta **MP_ACCESS_TOKEN** para consultar tu cuenta. Exportá la variable "
            "con el mismo token de producción que cargaste en Vercel."
        )
    else:
        dias = st.slider("Últimos N días", 7, 180, 60)
        if st.button("🔄 Traer de MercadoPago", type="primary"):
            headers = {"Authorization": f"Bearer {MP_TOKEN}"}
            desde = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%dT00:00:00.000-03:00")

            with st.spinner("Consultando pagos…"):
                try:
                    r = requests.get(
                        "https://api.mercadopago.com/v1/payments/search",
                        headers=headers,
                        params={"sort": "date_created", "criteria": "desc",
                                "range": "date_created", "begin_date": desde,
                                "end_date": "NOW", "limit": 100},
                        timeout=30,
                    )
                    if r.ok:
                        pagos = r.json().get("results", [])
                        if pagos:
                            df = pd.DataFrame([{
                                "fecha": p.get("date_created", "")[:10],
                                "estado": p.get("status"),
                                "monto": p.get("transaction_amount"),
                                "moneda": p.get("currency_id"),
                                "email": (p.get("payer") or {}).get("email"),
                                "plan": (p.get("metadata") or {}).get("plan"),
                                "payment_id": p.get("id"),
                            } for p in pagos])
                            aprobados = df[df["estado"] == "approved"]
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Pagos aprobados", len(aprobados))
                            c2.metric("Recaudado", f"${aprobados['monto'].sum():,.0f}".replace(",", "."))
                            c3.metric("Clientes únicos", aprobados["email"].nunique())
                            st.dataframe(df, width="stretch")
                            st.caption(
                                "Para emitir la licencia de un pago aprobado: copiá su "
                                "`payment_id` y su email, y usá la pestaña «Emitir licencia»."
                            )
                        else:
                            st.info("No hay pagos en el período elegido.")
                    else:
                        st.error(f"MercadoPago respondió {r.status_code} al pedir pagos.")
                except requests.RequestException as e:
                    st.error(f"No se pudo consultar pagos: {e}")

            with st.spinner("Consultando suscripciones…"):
                try:
                    r2 = requests.get(
                        "https://api.mercadopago.com/preapproval/search",
                        headers=headers, params={"limit": 100}, timeout=30,
                    )
                    if r2.ok:
                        subs = r2.json().get("results", [])
                        if subs:
                            dfs = pd.DataFrame([{
                                "estado": s.get("status"),
                                "email": s.get("payer_email"),
                                "monto": (s.get("auto_recurring") or {}).get("transaction_amount"),
                                "frecuencia": (s.get("auto_recurring") or {}).get("frequency_type"),
                                "alta": (s.get("date_created") or "")[:10],
                                "id": s.get("id"),
                            } for s in subs])
                            activas = dfs[dfs["estado"] == "authorized"]
                            c1, c2 = st.columns(2)
                            c1.metric("Suscripciones activas", len(activas))
                            c2.metric(
                                "Ingreso recurrente/mes",
                                f"${activas['monto'].sum():,.0f}".replace(",", "."),
                            )
                            st.dataframe(dfs, width="stretch")
                        else:
                            st.info(
                                "Todavía no hay suscripciones. Aparecen acá cuando alguien "
                                "compra el plan mensual desde la web."
                            )
                    else:
                        st.caption(
                            f"Suscripciones: MercadoPago respondió {r2.status_code} "
                            "(puede ser que la cuenta no las tenga habilitadas)."
                        )
                except requests.RequestException as e:
                    st.caption(f"No se pudieron consultar suscripciones: {e}")

st.divider()
st.caption(
    "Este panel es sólo para vos. No se incluye en el ZIP ni en el instalador del "
    "cliente porque usa el secreto de firma de licencias."
)
