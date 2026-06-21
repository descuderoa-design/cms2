"""
CMS Turístico de Cantabria
Guías turísticos · Recursos y Restaurantes
"""

import streamlit as st
import pandas as pd
from datetime import date
import textwrap
from urllib.parse import quote

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CMS Cantabria",
    page_icon="🏔️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SHEET_ID  = "1J1T4vS736sotTVP9KgdSje0OxlBvFU_7alO4Mwap5YY"
EMAIL     = "info@apitcantabria.com"

URLS = {
    "recursos":                  f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=recursos",
    "contenidos_recursos":       f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=contenidos-recursos",
    "restaurantes":              f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=restaurantes",
    "experiencias_restaurantes": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=experiencias_restaurantes",
}

# ─────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_data() -> dict:
    date_cols = {
        "recursos":                  ["ultima_actualizacion"],
        "contenidos_recursos":       ["actualizado", "fecha_inicio", "fecha_fin"],
        "restaurantes":              [],
        "experiencias_restaurantes": ["fecha"],
    }
    dfs = {}
    for key, url in URLS.items():
        df = pd.read_csv(url, parse_dates=date_cols[key])
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        dfs[key] = df
    return dfs


def load_local_data() -> dict:
    xl = pd.read_excel("recursos_y_restaurantes.xlsx", sheet_name=None)
    mapping = {
        "recursos":                  "recursos",
        "contenidos-recursos":       "contenidos_recursos",
        "restaurantes":              "restaurantes",
        "experiencias_restaurantes": "experiencias_restaurantes",
    }
    dfs = {}
    for sheet, key in mapping.items():
        df = xl[sheet].copy()
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        dfs[key] = df
    return dfs


@st.cache_data(ttl=600)
def get_data() -> dict:
    try:
        if SHEET_ID == "TU_GOOGLE_SHEET_ID":
            raise ValueError("Sheet ID no configurado")
        return load_data()
    except Exception:
        return load_local_data()


# ─────────────────────────────────────────────
# HELPERS FECHA
# ─────────────────────────────────────────────
DIAS_ES = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo",
}


def fila_es_fecha(row: pd.Series, fecha: date) -> bool:
    try:
        inicio = pd.to_datetime(row.get("fecha_inicio")).date() if pd.notna(row.get("fecha_inicio")) else date.min
        fin    = pd.to_datetime(row.get("fecha_fin")).date()    if pd.notna(row.get("fecha_fin"))    else date.max
        if not (inicio <= fecha <= fin):
            return False
    except Exception:
        pass
    dias_str = str(row.get("dias_semana", "") or "")
    if dias_str.strip():
        dia = DIAS_ES[fecha.weekday()]
        dias = [d.strip().lower() for d in dias_str.split("-")]
        if dia not in dias:
            return False
    return True


def filtrar_contenido(df: pd.DataFrame, recurso: str, fecha: date) -> pd.DataFrame:
    sub = df[df["recurso"] == recurso].copy()
    mask = sub.apply(lambda r: fila_es_fecha(r, fecha), axis=1)
    return sub[mask]


def html(s: str) -> str:
    return textwrap.dedent(s).strip()


def gmail_compose_url(asunto: str, cuerpo: str, destinatario: str = EMAIL) -> str:
    """URL que abre un borrador de Gmail (web) con destinatario, asunto y cuerpo prerellenados."""
    return (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={quote(destinatario)}"
        f"&su={quote(asunto)}"
        f"&body={quote(cuerpo)}"
    )


# ─────────────────────────────────────────────
# PLANTILLAS DE CORREO
# ─────────────────────────────────────────────
NOTA_OPCIONALES = (
    "(*) Solo los campos marcados con (*) son obligatorios. "
    "El resto son opcionales: rellena los que conozcas y deja en blanco los demás.\n"
)


def plantilla_nuevo_recurso() -> tuple[str, str]:
    """Asunto y cuerpo para proponer un nuevo recurso turístico."""
    asunto = "[CMS Cantabria] Propuesta de nuevo recurso turístico"
    cuerpo = (
        "Hola,\n\n"
        "Quiero proponer la incorporación de un nuevo recurso turístico al CMS de Cantabria.\n\n"
        "── DATOS DEL RECURSO ───────────────────────\n"
        f"{NOTA_OPCIONALES}\n"
        "Nombre del recurso (*):\n"
        "Municipio (*):\n"
        "Tipo (museo, iglesia, cueva, playa…):\n"
        "Web oficial:\n"
        "Horario / días de apertura:\n"
        "Descripción breve:\n\n"
        "Gracias por ayudarnos a mantener la base de datos actualizada."
    )
    return asunto, cuerpo


def plantilla_nuevo_restaurante() -> tuple[str, str]:
    """Asunto y cuerpo para proponer un nuevo restaurante, con primera reseña opcional."""
    asunto = "[CMS Cantabria] Propuesta de nuevo restaurante"
    cuerpo = (
        "Hola,\n\n"
        "Quiero proponer la incorporación de un nuevo restaurante al CMS de Cantabria.\n\n"
        "── DATOS DEL RESTAURANTE ───────────────────\n"
        f"{NOTA_OPCIONALES}\n"
        "Nombre (*):\n"
        "Municipio (*):\n"
        "Admite grupos (Sí/No):\n"
        "Precio menú grupos (€/persona):\n\n"
        "── PRIMERA RESEÑA (opcional) ───────────────\n"
        "Si ya has visitado el restaurante, cuéntanos qué tal; si no, deja esta sección en blanco.\n\n"
        "Fecha de la visita (dd/mm/aaaa):\n"
        "Nombre del guía:\n"
        "Número de personas:\n"
        "Precio por persona (€):\n"
        "Valoración (1-5 estrellas):\n"
        "Comentario:\n\n"
        "Gracias por ayudarnos a mantener la base de datos actualizada."
    )
    return asunto, cuerpo


def plantilla_denuncia(tipo: str, nombre: str) -> tuple[str, str]:
    """Asunto y cuerpo para denunciar un dato incorrecto. tipo: 'recurso' o 'restaurante'."""
    asunto = f"[CMS Cantabria] Corrección de datos: {nombre}"
    cuerpo = (
        "Hola,\n\n"
        f"He detectado un dato incorrecto o desactualizado en el {tipo} «{nombre}».\n\n"
        "── DESCRIPCIÓN DEL ERROR ───────────────────\n"
        "Dato incorrecto (*):\n"
        "Valor correcto (si lo conoces):\n"
        "Fuente de referencia (opcional):\n\n"
        "Gracias por ayudarnos a mantener la base de datos actualizada."
    )
    return asunto, cuerpo


# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────
def inject_css():
    st.markdown(html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { max-width: 680px; padding: 1rem 1rem 4rem; }
    .section-header {
        background: linear-gradient(135deg, #1a4a6b 0%, #0d7c9e 100%);
        color: white; padding: 0.75rem 1.1rem; border-radius: 10px;
        margin-bottom: 1rem; font-weight: 600; font-size: 1.05rem; letter-spacing: 0.02em;
    }
    .card {
        background: #ffffff; border: 1px solid #e5e9ef; border-radius: 12px;
        padding: 1rem 1.1rem; margin-bottom: 0.85rem; box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }
    .card-title { font-weight: 700; font-size: 1rem; color: #1a2e40; margin-bottom: 0.25rem; }
    .card-meta { font-size: 0.78rem; color: #6b7a8d; margin-bottom: 0.5rem; }
    .bloque {
        background: #f4f8fc; border-left: 3px solid #0d7c9e;
        border-radius: 0 8px 8px 0; padding: 0.55rem 0.8rem; margin-bottom: 0.45rem;
    }
    .bloque-label {
        font-size: 0.7rem; font-weight: 600; color: #0d7c9e;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    .bloque-subtipo { font-weight: 600; color: #1a2e40; font-size: 0.87rem; }
    .bloque-contenido { color: #374151; font-size: 0.87rem; }
    .disclaimer {
        background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px;
        padding: 0.55rem 0.8rem; margin-top: 0.6rem; margin-bottom: 0;
        font-size: 0.78rem; color: #78350f; line-height: 1.5;
    }
    .disclaimer strong { color: #92400e; }
    .stars { color: #f59e0b; font-size: 1rem; }
    .rating-num { font-weight: 700; color: #1a2e40; font-size: 0.9rem; }
    .badge {
        display: inline-block; background: #e0f2fe; color: #0369a1;
        border-radius: 20px; padding: 0.15rem 0.65rem;
        font-size: 0.72rem; font-weight: 600; margin-right: 0.3rem; margin-bottom: 0.2rem;
    }
    .badge-green { background: #dcfce7; color: #15803d; }
    .badge-amber { background: #fef9c3; color: #92400e; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0; padding: 0.45rem 1.1rem;
        font-weight: 600; font-size: 0.88rem;
    }
    label { font-weight: 600 !important; font-size: 0.83rem !important; color: #374151 !important; }
    a { color: #0d7c9e !important; }
    .no-results { text-align: center; color: #9ca3af; padding: 2rem 1rem; font-size: 0.9rem; }
    .report-btn {
        display: inline-block; font-size: 0.75rem; color: #6b7a8d !important;
        text-decoration: none; margin-right: 0.75rem;
        border-bottom: 1px dashed #d1d5db; padding-bottom: 1px;
    }
    .report-btn:hover { color: #0d7c9e !important; border-bottom-color: #0d7c9e; }
    .report-row { margin-top: 0.65rem; padding-top: 0.55rem; border-top: 1px solid #f3f4f6; }
    </style>
    """), unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS HTML
# ─────────────────────────────────────────────
def build_bloque(bloque_tipo, subtipo, contenido, fuente):
    fuente_html = f'<br><small style="color:#9ca3af">Fuente: {fuente}</small>' if fuente else ""
    return (
        '<div class="bloque">'
        f'<div class="bloque-label">{bloque_tipo}</div>'
        f'<div class="bloque-subtipo">{subtipo}</div>'
        f'<div class="bloque-contenido">{contenido}{fuente_html}</div>'
        '</div>'
    )


def build_resena(r_stars, guia, fecha_str, n_p, comentario):
    return (
        '<div style="border-top:1px solid #e5e9ef;padding-top:0.5rem;margin-top:0.5rem;">'
        f'<div style="font-size:0.78rem;color:#6b7a8d;">{r_stars} · {guia} · {fecha_str} · {n_p} pax</div>'
        f'<div style="font-size:0.85rem;color:#374151;margin-top:0.2rem;">{comentario}</div>'
        '</div>'
    )


def build_disclaimer(web, ultima_act):
    """Franja de aviso + enlace web + fecha de actualización."""
    web_link = f' · <a href="{web}" target="_blank" style="color:#92400e;font-weight:600;">🔗 Web oficial</a>' if web else ""
    if pd.notna(ultima_act) and ultima_act:
        try:
            fecha_act = pd.to_datetime(ultima_act).strftime("%d/%m/%Y")
            act_str = f' · <span>Última actualización: <strong>{fecha_act}</strong></span>'
        except Exception:
            act_str = ""
    else:
        act_str = ""
    return (
        '<div class="disclaimer">'
        '⚠️ <strong>Aviso:</strong> Esta información puede estar desactualizada. '
        'Contrástala con la fuente oficial antes de usarla.'
        f'{web_link}{act_str}'
        '</div>'
    )


def build_report_links_recurso(nombre):
    """Enlaces a Gmail para reportar un dato incorrecto o proponer un nuevo recurso."""
    asunto_error, cuerpo_error = plantilla_denuncia("recurso", nombre)
    asunto_nuevo, cuerpo_nuevo = plantilla_nuevo_recurso()
    return (
        '<div class="report-row">'
        f'<a class="report-btn" href="{gmail_compose_url(asunto_error, cuerpo_error)}" target="_blank">✏️ Reportar dato incorrecto</a>'
        f'<a class="report-btn" href="{gmail_compose_url(asunto_nuevo, cuerpo_nuevo)}" target="_blank">➕ Proponer nuevo recurso</a>'
        '</div>'
    )


def build_report_links_restaurante(nombre):
    """Enlace a Gmail para reportar un dato incorrecto en un restaurante."""
    asunto, cuerpo = plantilla_denuncia("restaurante", nombre)
    return (
        '<div class="report-row">'
        f'<a class="report-btn" href="{gmail_compose_url(asunto, cuerpo)}" target="_blank">✏️ Reportar dato incorrecto</a>'
        '</div>'
    )


# ─────────────────────────────────────────────
# MÓDULO RECURSOS
# ─────────────────────────────────────────────
def modulo_recursos(dfs: dict):
    recursos_df   = dfs["recursos"]
    contenidos_df = dfs["contenidos_recursos"]

    hoy       = date.today()
    fecha_max = date(hoy.year + 2, hoy.month, hoy.day)

    col_fecha, col_muni = st.columns([1, 1])
    with col_fecha:
        fecha_sel = st.date_input(
            "📅 Consultar fecha",
            value=hoy,
            min_value=hoy,
            max_value=fecha_max,
            format="DD/MM/YYYY",
            key="rec_fecha",
        )
        dia_label = DIAS_ES[fecha_sel.weekday()].capitalize()
        st.markdown(
            f'<small style="color:#6b7a8d">{dia_label}, {fecha_sel.strftime("%d/%m/%Y")}</small>',
            unsafe_allow_html=True,
        )
    with col_muni:
        municipios = ["Todos"] + sorted(recursos_df["municipio"].dropna().unique())
        muni = st.selectbox("Municipio", municipios, key="rec_muni")

    df_fil = recursos_df[recursos_df["activo"] == True].copy()
    if muni != "Todos":
        df_fil = df_fil[df_fil["municipio"] == muni]
    df_fil = df_fil.sort_values(["prioridad", "recurso"])

    if df_fil.empty:
        st.markdown('<div class="no-results">No hay recursos para los filtros seleccionados.</div>', unsafe_allow_html=True)
        return

    # Enlace global "proponer nuevo recurso" antes de las cards
    asunto_nuevo, cuerpo_nuevo = plantilla_nuevo_recurso()
    st.markdown(
        f'<div style="margin-bottom:0.75rem;font-size:0.8rem;">'
        f'¿Falta algún recurso? '
        f'<a href="{gmail_compose_url(asunto_nuevo, cuerpo_nuevo)}" target="_blank" style="color:#0d7c9e;font-weight:600;">'
        f'➕ Proponer nuevo recurso turístico</a></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{len(df_fil)} recurso(s) encontrado(s)**")

    for _, rec in df_fil.iterrows():
        nombre      = rec["recurso"]
        municipio   = rec.get("municipio", "")
        tipo_rec    = rec.get("tipo", "")
        web         = rec.get("web_oficial", "")
        ultima_act  = rec.get("ultima_actualizacion", None)

        contenido_fecha = filtrar_contenido(contenidos_df, nombre, fecha_sel)

        if not contenido_fecha.empty:
            bloques_html = ""
            for bloque_tipo, grupo in contenido_fecha.groupby("bloque"):
                for _, fila in grupo.iterrows():
                    bloques_html += build_bloque(
                        bloque_tipo,
                        fila.get("subtipo", "") or "",
                        fila.get("contenido", "") or "",
                        fila.get("fuente", "") or "",
                    )
        else:
            bloques_html = '<small style="color:#9ca3af">Sin datos disponibles para la fecha seleccionada.</small>'

        web_str = str(web) if pd.notna(web) else ""

        card = (
            '<div class="card">'
            f'<div class="card-title">🏛️ {nombre}</div>'
            '<div class="card-meta">'
            f'<span class="badge">{municipio}</span>'
            f'<span class="badge badge-amber">{tipo_rec}</span>'
            '</div>'
            f'{bloques_html}'
            f'{build_disclaimer(web_str, ultima_act)}'
            f'{build_report_links_recurso(nombre)}'
            '</div>'
        )
        st.markdown(card, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO RESTAURANTES
# ─────────────────────────────────────────────
def panel_nuevo_restaurante():
    """Expander con enlace a Gmail para proponer nuevo restaurante + primera reseña."""
    asunto, cuerpo = plantilla_nuevo_restaurante()
    with st.expander("➕ Proponer nuevo restaurante", expanded=False):
        st.markdown(
            '<p style="font-size:0.85rem;color:#374151;margin-bottom:0.6rem;">'
            '¿Conoces un restaurante que debería estar en esta lista? '
            'Envíanos los datos y, si quieres, añade también tu primera reseña. '
            'Revisaremos la propuesta y la incorporaremos a la base de datos.</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<a href="{gmail_compose_url(asunto, cuerpo)}" target="_blank" style="display:inline-block;'
            'background:#0d7c9e;color:white!important;padding:0.45rem 1.1rem;'
            'border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">'
            '📧 Abrir borrador en Gmail</a>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="font-size:0.72rem;color:#9ca3af;margin-top:0.5rem;">'
            f'Se abrirá Gmail en una pestaña nueva con destinatario y plantilla ya preparados ({EMAIL}).</p>',
            unsafe_allow_html=True,
        )


def modulo_restaurantes(dfs: dict):
    rest_df = dfs["restaurantes"]
    exp_df  = dfs["experiencias_restaurantes"]

    rating_medio = (
        exp_df.groupby("restaurante")["rating"]
        .agg(rating_medio="mean", n_resenas="count")
        .reset_index()
    )
    rest_df = rest_df.merge(rating_medio, on="restaurante", how="left")

    municipios = ["Todos"] + sorted(rest_df["municipio"].dropna().unique())
    muni = st.selectbox("Municipio", municipios, key="rest_muni")

    df_fil = rest_df.copy()
    if muni != "Todos":
        df_fil = df_fil[df_fil["municipio"] == muni]
    df_fil = df_fil.sort_values("rating_medio", ascending=False, na_position="last")

    if df_fil.empty:
        st.markdown('<div class="no-results">No hay restaurantes para los filtros seleccionados.</div>', unsafe_allow_html=True)
        panel_nuevo_restaurante()
        return

    st.markdown(f"**{len(df_fil)} restaurante(s) encontrado(s)**")

    for _, row in df_fil.iterrows():
        nombre    = row["restaurante"]
        municipio = row.get("municipio", "")
        grupos    = row.get("admite_grupos", "")
        precio    = row.get("precio_menu_grupos", None)
        rating    = row.get("rating_medio", None)
        n_res     = int(row.get("n_resenas", 0)) if pd.notna(row.get("n_resenas")) else 0

        if pd.notna(rating):
            estrellas   = int(round(rating))
            stars_str   = "⭐" * estrellas + "☆" * (5 - estrellas)
            sufijo      = "s" if n_res != 1 else ""
            rating_html = (
                f'<span class="stars">{stars_str}</span>'
                f'<span class="rating-num"> {rating:.1f}/5</span>'
                f'<small style="color:#9ca3af"> ({n_res} reseña{sufijo})</small>'
            )
        else:
            rating_html = '<small style="color:#9ca3af">Sin reseñas aún</small>'

        precio_html  = f'<span class="badge badge-green">Menú grupo: {int(precio)}€/p.</span>' if pd.notna(precio) else ""
        grupos_badge = '<span class="badge badge-green">✓ Grupos</span>' if str(grupos).upper() in ["SÍ", "SI", "YES"] else ""

        resenas = exp_df[exp_df["restaurante"] == nombre].sort_values("fecha", ascending=False)
        resenas_html = ""
        for _, res in resenas.head(3).iterrows():
            fecha_str = pd.to_datetime(res["fecha"]).strftime("%d/%m/%Y") if pd.notna(res.get("fecha")) else ""
            r_stars   = "⭐" * int(res.get("rating", 0))
            resenas_html += build_resena(
                r_stars,
                res.get("guia", ""),
                fecha_str,
                res.get("num_personas", ""),
                res.get("comentario", ""),
            )

        sin_resenas = '<small style="color:#9ca3af">Sin reseñas registradas.</small>'

        card = (
            '<div class="card">'
            f'<div class="card-title">🍽️ {nombre}</div>'
            '<div class="card-meta">'
            f'<span class="badge">{municipio}</span>'
            f'{grupos_badge}{precio_html}'
            '</div>'
            f'<div style="margin-bottom:0.5rem;">{rating_html}</div>'
            f'{resenas_html if resenas_html else sin_resenas}'
            f'{build_report_links_restaurante(nombre)}'
            '</div>'
        )
        st.markdown(card, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)
    panel_nuevo_restaurante()


# ─────────────────────────────────────────────
# APP PRINCIPAL
# ─────────────────────────────────────────────
def main():
    inject_css()

    st.markdown(html("""
    <div style="text-align:center;padding:1.2rem 0 0.5rem;">
    <div style="font-size:2rem;">🏔️</div>
    <div style="font-weight:700;font-size:1.35rem;color:#1a2e40;letter-spacing:-0.01em;">CMS Cantabria</div>
    <div style="color:#6b7a8d;font-size:0.82rem;margin-top:0.2rem;">Panel de Guías Turísticos</div>
    </div>
    """), unsafe_allow_html=True)

    with st.spinner("Cargando datos…"):
        dfs = get_data()

    col_ref, _ = st.columns([1, 3])
    with col_ref:
        if st.button("🔄 Actualizar datos"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    tab_rec, tab_rest = st.tabs(["🏛️ Recursos", "🍽️ Restaurantes"])

    with tab_rec:
        st.markdown('<div class="section-header">🏛️ Recursos Turísticos</div>', unsafe_allow_html=True)
        modulo_recursos(dfs)

    with tab_rest:
        st.markdown('<div class="section-header">🍽️ Restaurantes</div>', unsafe_allow_html=True)
        modulo_restaurantes(dfs)

    st.markdown(
        '<div style="text-align:center;color:#9ca3af;font-size:0.72rem;margin-top:2rem;padding-bottom:1rem;">'
        'CMS Cantabria · Datos actualizados desde Google Sheets'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
