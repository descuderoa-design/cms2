"""
CMS Turístico de Cantabria
Guías turísticos · Recursos y Restaurantes
"""

import streamlit as st
import pandas as pd
from datetime import date
import textwrap
from urllib.parse import quote
import html

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="CMS Cantabria",
    page_icon="🏔️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SHEET_ID = "1J1T4vS736sotTVP9KgdSje0OxlBvFU_7alO4Mwap5YY"
EMAIL = "info@apitcantabria.com"

URLS = {
    "recursos": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=recursos",
    "contenidos_recursos": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=contenidos-recursos",
    "restaurantes": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=restaurantes",
    "experiencias_restaurantes": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=experiencias_restaurantes",
}

# ─────────────────────────────────────────────
# VALIDACIÓN ESQUEMA
# ─────────────────────────────────────────────

REQUIRED_SCHEMAS = {
    "recursos": ["recurso", "municipio", "tipo", "web_oficial", "activo"],
    "contenidos_recursos": ["recurso", "bloque", "subtipo", "contenido"],
    "restaurantes": ["restaurante", "municipio"],
    "experiencias_restaurantes": ["restaurante", "rating", "fecha"],
}

def validate_schema(df, key):
    missing = [c for c in REQUIRED_SCHEMAS.get(key, []) if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en {key}: {missing}")

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

def safe(x):
    return html.escape(str(x)) if x is not None else ""

def mailto(asunto: str, cuerpo: str) -> str:
    base = "https://mail.google.com/mail/?view=cm&fs=1"
    return (
        f"{base}"
        f"&to={quote(EMAIL)}"
        f"&su={quote(str(asunto))}"
        f"&body={quote(str(cuerpo))}"
    )

def normalize_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

# ─────────────────────────────────────────────
# CARGA DATOS
# ─────────────────────────────────────────────

@st.cache_data(ttl=600)
def load_data():
    date_cols = {
        "recursos": ["ultima_actualizacion"],
        "contenidos_recursos": ["actualizado", "fecha_inicio", "fecha_fin"],
        "experiencias_restaurantes": ["fecha"],
    }

    dfs = {}

    for key, url in URLS.items():
        df = pd.read_csv(url)

        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        validate_schema(df, key)
        df = normalize_dates(df, date_cols.get(key, []))

        dfs[key] = df

    return dfs

# ─────────────────────────────────────────────
# FECHAS
# ─────────────────────────────────────────────

DIAS_ES = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo",
}

# ─────────────────────────────────────────────
# FILTRADO (SIN APPLY)
# ─────────────────────────────────────────────

def filtrar_contenido(df, recurso, fecha):
    sub = df[df["recurso"] == recurso].copy()
    fecha = pd.Timestamp(fecha)

    sub["fecha_inicio"] = pd.to_datetime(sub.get("fecha_inicio"), errors="coerce")
    sub["fecha_fin"] = pd.to_datetime(sub.get("fecha_fin"), errors="coerce")

    mask = (
        (sub["fecha_inicio"].fillna(pd.Timestamp.min) <= fecha) &
        (sub["fecha_fin"].fillna(pd.Timestamp.max) >= fecha)
    )

    if "dias_semana" in sub.columns:
        dia = DIAS_ES[fecha.weekday()].lower()
        mask &= sub["dias_semana"].fillna("").str.lower().str.contains(dia)

    return sub[mask]

# ─────────────────────────────────────────────
# EMAIL (PLANTILLAS COHERENTES)
# ─────────────────────────────────────────────

def mail_nuevo_recurso():
    asunto = "[CMS Cantabria] Alta de nuevo recurso turístico"
    cuerpo = """
SOLICITUD DE ALTA DE RECURSO TURÍSTICO

Nombre:
Municipio:
Tipo:
Web oficial:
Descripción:

Fuente o motivo:
""".strip()
    return mailto(asunto, cuerpo)

def mail_nuevo_restaurante():
    asunto = "[CMS Cantabria] Alta de nuevo restaurante"
    cuerpo = """
SOLICITUD DE ALTA DE RESTAURANTE

Nombre:
Municipio:
Grupos (Sí/No):
Precio menú grupos:

Descripción:
""".strip()
    return mailto(asunto, cuerpo)

def mail_error_recurso(nombre):
    asunto = f"[CMS Cantabria] Error en recurso: {nombre}"
    cuerpo = f"""
REPORTE DE ERROR

Recurso: {nombre}

Error detectado:
Corrección propuesta:
Fuente:
""".strip()
    return mailto(asunto, cuerpo)

def mail_error_restaurante(nombre):
    asunto = f"[CMS Cantabria] Error en restaurante: {nombre}"
    cuerpo = f"""
REPORTE DE ERROR

Restaurante: {nombre}

Error detectado:
Corrección propuesta:
Fuente:
""".strip()
    return mailto(asunto, cuerpo)

# ─────────────────────────────────────────────
# BLOQUES HTML
# ─────────────────────────────────────────────

def build_bloque(tipo, subtipo, contenido, fuente):
    return f"""
    <div class="bloque">
        <b>{safe(tipo)}</b><br>
        <i>{safe(subtipo)}</i><br>
        {safe(contenido)}<br>
        <small>Fuente: {safe(fuente)}</small>
    </div>
    """

def build_disclaimer(web, ultima):
    fecha = ""
    if pd.notna(ultima):
        fecha = f" · Actualizado: {pd.to_datetime(ultima).strftime('%d/%m/%Y')}"

    web_link = f' · <a href="{web}" target="_blank">Web oficial</a>' if web else ""

    return f"""
    <div class="disclaimer">
        ⚠️ Información sujeta a cambios{web_link}{fecha}
    </div>
    """

def build_report_recurso(nombre):
    return f"""
    <a href="{mail_error_recurso(nombre)}">Reportar error</a>
    """

def build_report_restaurante(nombre):
    return f"""
    <a href="{mail_error_restaurante(nombre)}">Reportar error</a>
    """

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    .card {border:1px solid #ddd;padding:1rem;margin-bottom:1rem;border-radius:10px;}
    .bloque {margin-top:0.5rem;padding:0.5rem;background:#f4f8fc;}
    .disclaimer {font-size:0.8rem;color:#666;}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

def main():
    inject_css()

    st.title("CMS Cantabria")

    dfs = load_data()

    tab1, tab2 = st.tabs(["Recursos", "Restaurantes"])

    # ───── RECURSOS ─────
    with tab1:
        st.markdown(f'<a href="{mail_nuevo_recurso()}">➕ Añadir recurso</a>', unsafe_allow_html=True)

        for _, r in dfs["recursos"].iterrows():
            st.markdown(f"""
            <div class="card">
                <b>{safe(r["recurso"])}</b>
                {build_disclaimer(r.get("web_oficial"), r.get("ultima_actualizacion"))}
                {build_report_recurso(r["recurso"])}
            </div>
            """, unsafe_allow_html=True)

    # ───── RESTAURANTES ─────
    with tab2:
        st.markdown(f'<a href="{mail_nuevo_restaurante()}">➕ Añadir restaurante</a>', unsafe_allow_html=True)

        for _, r in dfs["restaurantes"].iterrows():
            st.markdown(f"""
            <div class="card">
                <b>{safe(r["restaurante"])}</b>
                {build_report_restaurante(r["restaurante"])}
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
