"""
CMS Turístico de Cantabria (versión mejorada)
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

REQUIRED_SCHEMAS = {
    "recursos": ["recurso", "municipio", "tipo", "web_oficial", "activo"],
    "contenidos_recursos": ["recurso", "bloque", "subtipo", "contenido"],
    "restaurantes": ["restaurante", "municipio"],
    "experiencias_restaurantes": ["restaurante", "rating", "fecha"]
}

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

def safe(x):
    return html.escape(str(x)) if x is not None else ""


def validate_schema(df, key):
    missing = [c for c in REQUIRED_SCHEMAS.get(key, []) if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en {key}: {missing}")


def normalize_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def mailto(asunto, cuerpo):
    return f"mailto:{EMAIL}?subject={quote(str(asunto))}&body={quote(str(cuerpo))}"


# ─────────────────────────────────────────────
# CARGA DE DATOS
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


def get_data():
    return load_data()


# ─────────────────────────────────────────────
# FECHAS
# ─────────────────────────────────────────────

DIAS_ES = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo",
}


# ─────────────────────────────────────────────
# FILTRADO OPTIMIZADO (SIN APPLY)
# ─────────────────────────────────────────────

def filtrar_contenido(df, recurso, fecha):
    sub = df[df["recurso"] == recurso].copy()

    fecha = pd.Timestamp(fecha)

    sub["fecha_inicio"] = pd.to_datetime(sub.get("fecha_inicio"))
    sub["fecha_fin"] = pd.to_datetime(sub.get("fecha_fin"))

    mask = (
        (sub["fecha_inicio"].fillna(pd.Timestamp.min) <= fecha) &
        (sub["fecha_fin"].fillna(pd.Timestamp.max) >= fecha)
    )

    if "dias_semana" in sub.columns:
        dia = DIAS_ES[fecha.weekday()].lower()
        mask &= sub["dias_semana"].fillna("").str.lower().str.contains(dia)

    return sub[mask]


# ─────────────────────────────────────────────
# HTML BUILDERS
# ─────────────────────────────────────────────

def build_bloque(tipo, subtipo, contenido, fuente):
    return f"""
    <div class="bloque">
        <div class="bloque-label">{safe(tipo)}</div>
        <div class="bloque-subtipo">{safe(subtipo)}</div>
        <div class="bloque-contenido">{safe(contenido)}</div>
        <small style="color:#9ca3af">Fuente: {safe(fuente)}</small>
    </div>
    """


def build_disclaimer(web, ultima):
    fecha = ""
    if pd.notna(ultima):
        fecha = f" · Última actualización: {pd.to_datetime(ultima).strftime('%d/%m/%Y')}"

    web_link = f' · <a href="{web}" target="_blank">Web oficial</a>' if web else ""

    return f"""
    <div class="disclaimer">
        ⚠️ Información sujeta a cambios.{web_link}{fecha}
    </div>
    """


def build_report(nombre):
    asunto = f"[CMS Cantabria] Error en {nombre}"
    cuerpo = f"Error detectado en: {nombre}\nDescripción:\n"

    return f"""
    <div class="report-row">
        <a class="report-btn" href="{mailto(asunto, cuerpo)}">
        Reportar error
        </a>
    </div>
    """


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    .card {padding:1rem;border:1px solid #ddd;border-radius:10px;margin-bottom:1rem;}
    .bloque {margin-top:0.5rem;padding:0.5rem;border-left:3px solid #0d7c9e;background:#f4f8fc;}
    .disclaimer {font-size:0.8rem;color:#666;margin-top:0.5rem;}
    .report-btn {font-size:0.75rem;color:#0d7c9e;}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO RECURSOS
# ─────────────────────────────────────────────

def modulo_recursos(dfs):
    recursos = dfs["recursos"]
    contenidos = dfs["contenidos_recursos"]

    fecha = st.date_input("Fecha", value=date.today())

    muni_list = ["Todos"] + sorted(recursos["municipio"].dropna().unique())
    muni = st.selectbox("Municipio", muni_list)

    df = recursos[recursos["activo"] == True]

    if muni != "Todos":
        df = df[df["municipio"] == muni]

    st.write(f"{len(df)} recursos")

    for _, r in df.iterrows():
        nombre = r["recurso"]

        contenido = filtrar_contenido(contenidos, nombre, fecha)

        bloques = ""
        for _, c in contenido.iterrows():
            bloques += build_bloque(
                c.get("bloque"),
                c.get("subtipo"),
                c.get("contenido"),
                c.get("fuente")
            )

        st.markdown(f"""
        <div class="card">
            <b>{safe(nombre)}</b>
            {bloques}
            {build_disclaimer(r.get("web_oficial"), r.get("ultima_actualizacion"))}
            {build_report(nombre)}
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO RESTAURANTES
# ─────────────────────────────────────────────

def modulo_restaurantes(dfs):
    rest = dfs["restaurantes"]
    exp = dfs["experiencias_restaurantes"]

    muni_list = ["Todos"] + sorted(rest["municipio"].dropna().unique())
    muni = st.selectbox("Municipio restaurantes", muni_list)

    df = rest.copy()

    if muni != "Todos":
        df = df[df["municipio"] == muni]

    for _, r in df.iterrows():
        nombre = r["restaurante"]

        reseñas = exp[exp["restaurante"] == nombre]

        st.markdown(f"""
        <div class="card">
            <b>{safe(nombre)}</b>
            <div>Reseñas: {len(reseñas)}</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

def main():
    inject_css()

    st.title("CMS Cantabria")

    dfs = get_data()

    tab1, tab2 = st.tabs(["Recursos", "Restaurantes"])

    with tab1:
        modulo_recursos(dfs)

    with tab2:
        modulo_restaurantes(dfs)


if __name__ == "__main__":
    main()
