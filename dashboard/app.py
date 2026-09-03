from __future__ import annotations

import html
import os
import re
from typing import Any

import altair as alt
import httpx
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TECHNICAL_COLUMNS = {"job_id", "recommendation_id", "company_id", "location_id"}
NAV_ITEMS = [
    "Accueil",
    "Recherche d'offres",
    "Marche de l'emploi",
    "Salaires",
    "Salaire avance",
    "Monitoring",
    "Competences",
    "Entreprises",
    "Alertes mail",
    "Recommandations",
]
PAGE_HINTS = {
    "Accueil": "Vue globale de la plateforme data emploi",
    "Marche de l'emploi": "Ou sont concentrees les offres data en France",
    "Salaires": "Analyse des niveaux de remuneration disponibles",
    "Salaire avance": "Vues salaire optionnelles pour l'analyse",
    "Monitoring": "Suivi API, PostgreSQL, qualite et exposition Prometheus",
    "Competences": "Technos et competences les plus demandees",
    "Entreprises": "Acteurs qui recrutent le plus",
    "Recherche d'offres": "Moteur interactif branche sur PostgreSQL",
    "Alertes mail": "Generation et envoi d'alertes basees sur la recherche",
    "Recommandations": "Matching entre profil candidat et offres",
}
SALARY_QUALITY_LABELS = {
    "missing": "Manquant",
    "too_low": "Trop bas",
    "too_high": "Trop eleve",
    "usable": "Exploitable",
}
CHART_COLORS = ["#0f766e", "#2563eb", "#0891b2", "#16a34a", "#f97316", "#7c3aed", "#dc2626"]
SKILL_FAMILIES = {
    "BI / dataviz": {"power bi", "tableau", "looker", "excel"},
    "Cloud": {"azure", "aws", "gcp", "google cloud"},
    "Data engineering": {"pyspark", "spark", "airflow", "databricks", "dbt", "kafka", "docker", "kubernetes"},
    "Bases et SQL": {"sql", "postgresql", "mysql", "mongodb", "snowflake", "bigquery"},
    "Langages": {"python", "scala", "java", "r"},
}


st.set_page_config(page_title="JobMarket France", page_icon=None, layout="wide")


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --jm-ink: #102027;
            --jm-muted: #52616b;
            --jm-line: #d8e5e3;
            --jm-bg: #f7fbfa;
            --jm-teal: #0f766e;
            --jm-blue: #2563eb;
            --jm-green: #16a34a;
            --jm-card: #ffffff;
        }
        .stApp {
            background:
                radial-gradient(circle at 18% 12%, rgba(15, 118, 110, 0.12), transparent 28%),
                radial-gradient(circle at 88% 18%, rgba(37, 99, 235, 0.10), transparent 26%),
                linear-gradient(180deg, #f8fbfb 0%, #eef8f6 48%, #f8fbfb 100%);
            color: var(--jm-ink);
        }
        .main .block-container {
            max-width: 1280px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }
        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.92);
            border-right: 1px solid var(--jm-line);
        }
        section[data-testid="stSidebar"] * {
            color: var(--jm-ink);
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            padding: 1rem 1rem 0.8rem;
            box-shadow: 0 12px 28px rgba(16, 32, 39, 0.07);
        }
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricLabel"] *,
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] label * {
            color: var(--jm-muted) !important;
            opacity: 1 !important;
            font-weight: 700;
        }
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] * {
            color: var(--jm-ink) !important;
            opacity: 1 !important;
            font-weight: 800;
        }
        div[data-testid="stMetricDelta"],
        div[data-testid="stMetricDelta"] * {
            color: var(--jm-muted) !important;
            opacity: 1 !important;
        }
        .jm-metric-grid {
            display: grid;
            gap: 1rem;
            margin-bottom: 1.1rem;
        }
        .jm-metric-card {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 12px 28px rgba(16, 32, 39, 0.07);
            min-width: 0;
        }
        .jm-metric-label {
            color: var(--jm-muted);
            font-size: 0.9rem;
            font-weight: 850;
            margin-bottom: 0.45rem;
        }
        .jm-metric-value {
            color: var(--jm-ink);
            font-size: 1.75rem;
            line-height: 1.15;
            font-weight: 900;
            overflow-wrap: anywhere;
        }
        .jm-metric-help {
            color: var(--jm-muted);
            font-size: 0.78rem;
            margin-top: 0.35rem;
        }
        div[data-testid="stVegaLiteChart"] {
            background: #ffffff;
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            padding: 0;
            box-sizing: border-box;
            overflow: hidden;
            width: 100%;
            box-shadow: 0 10px 24px rgba(16, 32, 39, 0.06);
        }
        div[data-testid="stVegaLiteChart"] > div {
            max-width: 100%;
        }
        .jm-brand {
            border-radius: 8px;
            border: 1px solid var(--jm-line);
            padding: 1rem;
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.10), rgba(37, 99, 235, 0.10));
            margin-bottom: 1rem;
        }
        .jm-brand h2 {
            margin: 0;
            font-size: 1.1rem;
            line-height: 1.2;
        }
        .jm-brand p {
            margin: 0.35rem 0 0;
            color: var(--jm-muted);
            font-size: 0.86rem;
        }
        .jm-hero {
            border-radius: 8px;
            padding: 1.55rem 1.7rem;
            margin-bottom: 1.15rem;
            color: #ffffff;
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.98), rgba(37, 99, 235, 0.94));
            box-shadow: 0 18px 42px rgba(16, 32, 39, 0.16);
        }
        .jm-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 800;
            opacity: 0.9;
            margin-bottom: 0.35rem;
        }
        .jm-hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.14;
        }
        .jm-hero p {
            margin: 0.55rem 0 0;
            max-width: 840px;
            opacity: 0.94;
            font-size: 1rem;
        }
        .jm-section-title {
            margin: 1.15rem 0 0.55rem;
            font-size: 1.05rem;
            font-weight: 850;
            color: var(--jm-ink);
        }
        .jm-section-title-centered {
            text-align: center;
        }
        .jm-contract-overview-card {
            display: grid;
            grid-template-columns: minmax(180px, 0.95fr) minmax(220px, 1.05fr);
            align-items: center;
            gap: 1rem;
            min-height: 300px;
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            background: #ffffff;
            padding: 1rem 1rem 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(16, 32, 39, 0.06);
        }
        .jm-contract-summary {
            min-width: 0;
        }
        .jm-contract-summary-title {
            color: var(--jm-ink);
            font-size: 0.92rem;
            font-weight: 850;
            margin-bottom: 0.55rem;
        }
        .jm-contract-row {
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 0.4rem;
            color: var(--jm-ink);
            font-size: 0.86rem;
            margin: 0.35rem 0;
        }
        .jm-contract-dot {
            width: 0.65rem;
            height: 0.65rem;
            border-radius: 999px;
        }
        .jm-contract-label {
            font-weight: 800;
        }
        .jm-contract-value {
            color: var(--jm-muted);
            font-weight: 800;
            white-space: nowrap;
        }
        .jm-contract-reading {
            margin-top: 0.8rem;
            color: var(--jm-muted);
            font-size: 0.82rem;
            line-height: 1.45;
        }
        .jm-contract-reading strong {
            color: var(--jm-ink);
        }
        .jm-contract-chart {
            display: flex;
            justify-content: flex-end;
            align-items: center;
        }
        .jm-contract-chart svg {
            width: min(100%, 230px);
            height: auto;
            display: block;
        }
        @media (max-width: 900px) {
            .jm-contract-overview-card {
                grid-template-columns: 1fr;
            }
            .jm-contract-chart {
                justify-content: center;
            }
        }
        .jm-pipeline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
            gap: 0.65rem;
            margin-top: 0.6rem;
        }
        .jm-step {
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            background: #ffffff;
            padding: 0.85rem;
        }
        .jm-step strong {
            display: block;
            font-size: 0.92rem;
        }
        .jm-step span {
            display: block;
            color: var(--jm-muted);
            font-size: 0.8rem;
            margin-top: 0.2rem;
        }
        .jm-job-card {
            border: 1px solid var(--jm-line);
            border-left: 4px solid var(--jm-teal);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.96);
            padding: 1rem 1rem 0.85rem;
            margin: 0.7rem 0;
            box-shadow: 0 10px 24px rgba(16, 32, 39, 0.06);
        }
        .jm-job-card h3 {
            margin: 0 0 0.35rem;
            font-size: 1.02rem;
            line-height: 1.28;
        }
        .jm-job-meta {
            color: var(--jm-muted);
            font-size: 0.88rem;
            margin-bottom: 0.55rem;
        }
        .jm-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin: 0.45rem 0;
        }
        .jm-tag {
            border-radius: 999px;
            background: #e7f7f4;
            color: #0f5f59;
            padding: 0.18rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .jm-job-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.5rem;
            font-size: 0.86rem;
        }
        .jm-score {
            color: var(--jm-blue);
            font-weight: 800;
        }
        .jm-link {
            color: var(--jm-teal) !important;
            font-weight: 800;
            text-decoration: none;
        }
        .jm-empty {
            border: 1px dashed var(--jm-line);
            border-radius: 8px;
            padding: 1rem;
            color: var(--jm-muted);
            background: rgba(255, 255, 255, 0.7);
        }
        .jm-note {
            border: 1px solid var(--jm-line);
            border-left: 4px solid var(--jm-teal);
            border-radius: 8px;
            background: #ffffff;
            color: var(--jm-ink);
            padding: 0.8rem 1rem;
            margin-top: 1rem;
            font-weight: 750;
        }
        .jm-email-subject {
            border: 1px solid var(--jm-line);
            border-radius: 8px;
            background: #ffffff;
            color: var(--jm-ink);
            padding: 0.75rem 1rem;
            margin: 0.75rem 0;
        }
        .jm-email-subject span {
            display: block;
            color: var(--jm-muted);
            font-size: 0.78rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }
        .jm-email-subject strong {
            color: var(--jm-ink);
            font-size: 1rem;
            line-height: 1.35;
        }
        div[data-testid="stWidgetLabel"],
        div[data-testid="stWidgetLabel"] *,
        .stTextInput label,
        .stTextInput label *,
        .stTextArea label,
        .stTextArea label *,
        .stNumberInput label,
        .stNumberInput label *,
        .stSelectbox label,
        .stSelectbox label *,
        .stMultiSelect label,
        .stMultiSelect label *,
        .stSlider label,
        .stSlider label * {
            color: var(--jm-ink) !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        input,
        textarea,
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            background: #ffffff !important;
            color: var(--jm-ink) !important;
            border-color: var(--jm-line) !important;
        }
        input::placeholder,
        textarea::placeholder {
            color: #70828c !important;
            opacity: 1 !important;
        }
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] * {
            color: var(--jm-ink) !important;
        }
        div.stButton > button,
        div.stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stLinkButton"] a {
            border-radius: 8px;
            border: 1px solid var(--jm-teal);
            background: var(--jm-teal) !important;
            color: #ffffff !important;
            font-weight: 800;
        }
        div.stButton > button *,
        div.stDownloadButton > button *,
        div[data-testid="stFormSubmitButton"] button *,
        div[data-testid="stLinkButton"] a * {
            color: #ffffff !important;
        }
        div.stButton > button:hover,
        div.stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stLinkButton"] a:hover {
            border-color: var(--jm-blue);
            background: var(--jm-blue) !important;
            color: #ffffff !important;
        }
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] {
            background: #ffffff !important;
            border-color: var(--jm-line) !important;
            color: var(--jm-ink) !important;
        }
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary *,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span {
            color: var(--jm-ink) !important;
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid #f59e0b;
            background: #fff7d6 !important;
        }
        div[data-testid="stAlert"],
        div[data-testid="stAlert"] *,
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {
            color: var(--jm-ink) !important;
            opacity: 1 !important;
            font-weight: 700;
        }
        @media (max-width: 900px) {
            .jm-pipeline {
                grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            }
            .jm-hero h1 {
                font-size: 1.55rem;
            }
            .jm-job-footer {
                display: block;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60)
def api_get(path: str, params: dict | None = None):
    try:
        response = httpx.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.session_state["api_error"] = str(exc)
        dict_paths = {"/statistics", "/search/options", "/ml/salary/metadata", "/monitoring/warehouse"}
        return {} if path in dict_paths else []


def api_post(path: str, payload: dict) -> dict:
    try:
        response = httpx.post(f"{API_BASE_URL}{path}", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        return {"error": detail}
    except Exception as exc:
        return {"error": str(exc)}


def dataframe(data) -> pd.DataFrame:
    return pd.DataFrame(data or [])


def option_values(options: dict, key: str, label: str) -> list[str]:
    values = []
    for item in options.get(key, []):
        value = item.get(label) if isinstance(item, dict) else item
        if value and value not in values:
            values.append(value)
    return values


def format_number(value: Any) -> str:
    if is_missing(value):
        return "N/A"
    try:
        return f"{int(float(value)):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def format_salary(value: Any) -> str:
    if is_missing(value):
        return "N/A"
    try:
        return f"{float(value):,.0f} €".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def html_text(value: Any) -> str:
    return html.escape(str("" if is_missing(value) else value), quote=True)


def list_text(value: Any) -> str:
    if is_missing(value):
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if not is_missing(item))
    return str(value or "")


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict, set)):
        return False
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def row_value(row: pd.Series, column: str, fallback: str = "") -> Any:
    value = row.get(column)
    return fallback if is_missing(value) else value


def translate_salary_quality(value: Any) -> str:
    text = list_text(value)
    return SALARY_QUALITY_LABELS.get(text, text)


def clean_description(value: Any, max_chars: int = 240) -> str:
    text = list_text(value)
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    return text[:max_chars].rstrip() + ("..." if len(text) > max_chars else "")


def short_label(value: Any, max_chars: int = 44) -> str:
    text = list_text(value).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def clean_frame(data, columns: list[str] | None = None) -> pd.DataFrame:
    frame = data.copy() if isinstance(data, pd.DataFrame) else dataframe(data)
    if frame.empty:
        return frame
    frame = frame.drop(columns=[column for column in TECHNICAL_COLUMNS if column in frame.columns])
    if columns:
        frame = frame[[column for column in columns if column in frame.columns]]
    for column in ["matched_skills", "detected_skills", "input_skills"]:
        if column in frame.columns:
            frame[column] = frame[column].apply(list_text)
    return frame


def display_dataframe(data, columns: list[str] | None = None, height: int | None = None) -> None:
    frame = clean_frame(data, columns)
    column_config = {}
    if "source_url" in frame.columns:
        column_config["source_url"] = st.column_config.LinkColumn("Lien source")
    for column in ["salary_min", "salary_max", "salary_avg", "target_salary_avg"]:
        if column in frame.columns:
            column_config[column] = st.column_config.NumberColumn(column, format="%.0f EUR")
    dataframe_kwargs = {
        "use_container_width": True,
        "hide_index": True,
        "column_config": column_config,
    }
    if height is not None:
        dataframe_kwargs["height"] = height
    st.dataframe(frame, **dataframe_kwargs)


def render_horizontal_bar_chart(
    frame: pd.DataFrame,
    label_column: str,
    value_column: str,
    label_title: str,
    value_title: str,
    height: int = 360,
) -> None:
    if frame.empty:
        st.info("Aucune donnee disponible pour le moment.")
        return

    chart_frame = frame[[label_column, value_column]].copy()
    chart_frame[value_column] = pd.to_numeric(chart_frame[value_column], errors="coerce")
    chart_frame = chart_frame.dropna(subset=[value_column]).sort_values(value_column, ascending=False)
    if chart_frame.empty:
        st.info("Aucune donnee exploitable pour ce graphique.")
        return
    max_value = chart_frame[value_column].max()
    x_scale = alt.Scale(domain=[0, float(max_value) * 1.12]) if pd.notna(max_value) and max_value > 0 else alt.Scale()
    chart = (
        alt.Chart(chart_frame)
        .mark_bar(color="#0f766e", cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                f"{value_column}:Q",
                title=value_title,
                scale=x_scale,
                axis=alt.Axis(
                    labelColor="#102027",
                    titleColor="#102027",
                    labelFontSize=13,
                    titleFontSize=17,
                    titleFontWeight=800,
                ),
            ),
            y=alt.Y(
                f"{label_column}:N",
                sort="-x",
                title=label_title,
                axis=alt.Axis(
                    labelColor="#102027",
                    titleColor="#102027",
                    labelFontSize=13,
                    titleFontSize=17,
                    titleFontWeight=800,
                    labelLimit=190,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{label_column}:N", title=label_title),
                alt.Tooltip(f"{value_column}:Q", title=value_title, format=",.0f"),
            ],
        )
        .properties(width="container", height=height, background="#ffffff")
        .configure_axis(
            labelColor="#102027",
            titleColor="#102027",
            gridColor="#d8e5e3",
            domainColor="#9fb6b2",
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_vertical_bar_chart(
    frame: pd.DataFrame,
    label_column: str,
    value_column: str,
    label_title: str,
    value_title: str,
    height: int = 320,
    sort: str | list[str] = "-y",
) -> None:
    if frame.empty:
        st.info("Aucune donnee disponible pour le moment.")
        return

    chart_frame = frame[[label_column, value_column]].copy()
    chart_frame[value_column] = pd.to_numeric(chart_frame[value_column], errors="coerce")
    chart_frame = chart_frame.dropna(subset=[value_column])
    if chart_frame.empty:
        st.info("Aucune donnee exploitable pour ce graphique.")
        return
    chart = (
        alt.Chart(chart_frame)
        .mark_bar(color="#2563eb", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                f"{label_column}:N",
                sort=sort,
                title=label_title,
                axis=alt.Axis(
                    labelColor="#102027",
                    titleColor="#102027",
                    labelFontSize=13,
                    titleFontSize=17,
                    titleFontWeight=800,
                    labelAngle=-25,
                    labelLimit=130,
                ),
            ),
            y=alt.Y(
                f"{value_column}:Q",
                title=value_title,
                axis=alt.Axis(
                    labelColor="#102027",
                    titleColor="#102027",
                    labelFontSize=13,
                    titleFontSize=17,
                    titleFontWeight=800,
                    gridColor="#d8e5e3",
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{label_column}:N", title=label_title),
                alt.Tooltip(f"{value_column}:Q", title=value_title, format=",.0f"),
            ],
        )
        .properties(width="container", height=height, background="#ffffff")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_donut_chart(
    frame: pd.DataFrame,
    label_column: str,
    value_column: str,
    label_title: str,
    value_title: str,
    height: int = 320,
    centered: bool = False,
    chart_width: int = 320,
    inner_radius: int = 70,
    outer_radius: int = 120,
    show_legend_title: bool = True,
) -> None:
    if frame.empty:
        st.info("Aucune donnee disponible pour le moment.")
        return

    chart_frame = frame[[label_column, value_column]].copy()
    chart_frame[value_column] = pd.to_numeric(chart_frame[value_column], errors="coerce")
    chart_frame = chart_frame.dropna(subset=[value_column])
    if chart_frame.empty:
        st.info("Aucune donnee exploitable pour ce graphique.")
        return
    chart = (
        alt.Chart(chart_frame)
        .mark_arc(innerRadius=inner_radius, outerRadius=outer_radius)
        .encode(
            theta=alt.Theta(f"{value_column}:Q"),
            color=alt.Color(
                f"{label_column}:N",
                title=label_title if show_legend_title else None,
                scale=alt.Scale(range=CHART_COLORS),
                legend=alt.Legend(
                    orient="bottom",
                    title=label_title if show_legend_title else None,
                    labelColor="#102027",
                    titleColor="#102027",
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{label_column}:N", title=label_title),
                alt.Tooltip(f"{value_column}:Q", title=value_title, format=",.0f"),
            ],
        )
        .properties(width=chart_width if centered else "container", height=height, background="#ffffff")
        .configure_view(strokeWidth=0)
    )
    if centered:
        left, middle, right = st.columns([1, 8, 1])
        with left:
            st.empty()
        with middle:
            st.altair_chart(chart, use_container_width=False)
        with right:
            st.empty()
    else:
        st.altair_chart(chart, use_container_width=True)


def render_contract_overview(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("Aucune donnee disponible pour le moment.")
        return

    chart_frame = frame[["contract_type", "job_count"]].copy()
    chart_frame["contract_type"] = chart_frame["contract_type"].apply(lambda value: list_text(value) or "Non renseigne")
    chart_frame["job_count"] = pd.to_numeric(chart_frame["job_count"], errors="coerce")
    chart_frame = chart_frame.dropna(subset=["job_count"])
    chart_frame = chart_frame[chart_frame["job_count"] > 0]
    if chart_frame.empty:
        st.info("Aucune donnee exploitable pour ce graphique.")
        return

    total = float(chart_frame["job_count"].sum())
    dominant = chart_frame.sort_values("job_count", ascending=False).iloc[0]
    dominant_label = list_text(dominant["contract_type"])
    dominant_percent = (float(dominant["job_count"]) / total) * 100 if total else 0

    circles = [
        '<circle cx="50" cy="50" r="33" fill="none" stroke="#e7f0ef" stroke-width="18" />'
    ]
    rows = []
    offset = 0.0
    for index, row in enumerate(chart_frame.to_dict("records")):
        label = html_text(row.get("contract_type", "Non renseigne"))
        value = float(row.get("job_count") or 0)
        percent = (value / total) * 100 if total else 0
        color = CHART_COLORS[index % len(CHART_COLORS)]
        circles.append(
            '<circle cx="50" cy="50" r="33" fill="none" '
            f'stroke="{color}" stroke-width="18" pathLength="100" '
            f'stroke-dasharray="{percent:.4f} {100 - percent:.4f}" '
            f'stroke-dashoffset="{-offset:.4f}" transform="rotate(-90 50 50)" />'
        )
        rows.append(
            '<div class="jm-contract-row">'
            f'<span class="jm-contract-dot" style="background:{color}"></span>'
            f'<span class="jm-contract-label">{label}</span>'
            f'<span class="jm-contract-value">{format_number(value)} ({percent:.0f}%)</span>'
            "</div>"
        )
        offset += percent

    st.markdown(
        '<div class="jm-contract-overview-card">'
        '<div class="jm-contract-summary">'
        '<div class="jm-contract-summary-title">Contrats observes</div>'
        + "".join(rows)
        + '<div class="jm-contract-reading">'
        f'<strong>Interpretation :</strong> le type dominant est {html_text(dominant_label)} '
        f'avec {dominant_percent:.0f}% des offres. Les contrats non renseignes restent visibles '
        "pour signaler la qualite incomplete de certaines sources."
        "</div></div>"
        '<div class="jm-contract-chart">'
        '<svg viewBox="0 0 100 100" role="img" aria-label="Repartition des contrats">'
        + "".join(circles)
        + '<circle cx="50" cy="50" r="20" fill="#ffffff" />'
        + "</svg></div></div>",
        unsafe_allow_html=True,
    )


def render_line_chart(
    frame: pd.DataFrame,
    date_column: str,
    value_column: str,
    date_title: str,
    value_title: str,
    height: int = 320,
) -> None:
    if frame.empty:
        st.info("Aucune donnee disponible pour le moment.")
        return

    chart_frame = frame[[date_column, value_column]].copy()
    chart_frame[date_column] = pd.to_datetime(chart_frame[date_column], errors="coerce")
    chart_frame[value_column] = pd.to_numeric(chart_frame[value_column], errors="coerce")
    chart_frame = chart_frame.dropna(subset=[date_column, value_column]).sort_values(date_column)
    if chart_frame.empty:
        st.info("Aucune donnee exploitable pour ce graphique.")
        return
    chart = (
        alt.Chart(chart_frame)
        .mark_line(point=True, color="#0f766e", strokeWidth=3)
        .encode(
            x=alt.X(
                f"{date_column}:T",
                title=date_title,
                axis=alt.Axis(labelColor="#102027", titleColor="#102027", labelFontSize=12, titleFontSize=17, titleFontWeight=800),
            ),
            y=alt.Y(
                f"{value_column}:Q",
                title=value_title,
                axis=alt.Axis(labelColor="#102027", titleColor="#102027", labelFontSize=13, titleFontSize=17, titleFontWeight=800, gridColor="#d8e5e3"),
            ),
            tooltip=[
                alt.Tooltip(f"{date_column}:T", title=date_title),
                alt.Tooltip(f"{value_column}:Q", title=value_title, format=",.0f"),
            ],
        )
        .properties(width="container", height=height, background="#ffffff")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def skill_family(skill: Any) -> str:
    normalized = list_text(skill).strip().lower()
    for family, values in SKILL_FAMILIES.items():
        if normalized in values:
            return family
    return "Autres"


def build_skill_family_frame(skills_df: pd.DataFrame) -> pd.DataFrame:
    if skills_df.empty or "skill_name" not in skills_df or "job_count" not in skills_df:
        return pd.DataFrame()
    family_df = skills_df.copy()
    family_df["family"] = family_df["skill_name"].apply(skill_family)
    family_df["job_count"] = pd.to_numeric(family_df["job_count"], errors="coerce").fillna(0)
    return family_df.groupby("family", as_index=False)["job_count"].sum().sort_values("job_count", ascending=False)


def metric_row(cards: list[tuple[str, Any, str]]) -> None:
    grid_columns = "repeat(auto-fit, minmax(180px, 1fr))"
    cards_html = "\n".join(
        (
            '<div class="jm-metric-card">'
            f'<div class="jm-metric-label">{html_text(label)}</div>'
            f'<div class="jm-metric-value">{html_text(value)}</div>'
            f'<div class="jm-metric-help">{html_text(help_text)}</div>'
            "</div>"
        )
        for label, value, help_text in cards
    )
    st.markdown(
        f'<div class="jm-metric-grid" style="grid-template-columns: {grid_columns};">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def render_hero(page: str) -> None:
    st.markdown(
        f"""
        <div class="jm-hero">
            <div class="jm-kicker">Projet Fil Rouge Data Engineering</div>
            <h1>JobMarket France</h1>
            <p>{html_text(PAGE_HINTS.get(page, ""))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, centered: bool = False) -> None:
    class_name = "jm-section-title jm-section-title-centered" if centered else "jm-section-title"
    st.markdown(f'<div class="{class_name}">{html_text(title)}</div>', unsafe_allow_html=True)


def render_pipeline() -> None:
    steps = [
        ("Sources", "Adzuna API, The Muse API, scraping"),
        ("Orchestration", "Airflow"),
        ("Transform", "PySpark Silver/Gold"),
        ("Warehouse", "PostgreSQL"),
        ("Services", "FastAPI"),
        ("Usage", "Streamlit, Prometheus, Grafana"),
    ]
    cards = "\n".join(
        f'<div class="jm-step"><strong>{html_text(title)}</strong><span>{html_text(text)}</span></div>'
        for title, text in steps
    )
    st.markdown(f'<div class="jm-pipeline">{cards}</div>', unsafe_allow_html=True)


def render_job_cards(data, limit: int = 6, columns_per_row: int = 1) -> None:
    frame = data.copy() if isinstance(data, pd.DataFrame) else dataframe(data)
    if frame.empty:
        st.markdown('<div class="jm-empty">Aucune offre trouvee avec ces criteres.</div>', unsafe_allow_html=True)
        return

    rows = list(frame.head(limit).iterrows())
    if columns_per_row <= 1:
        for _, row in rows:
            render_job_card(row)
        return

    for start in range(0, len(rows), columns_per_row):
        row_group = rows[start : start + columns_per_row]
        containers = st.columns(columns_per_row)
        for container, (_, row) in zip(containers, row_group):
            with container:
                render_job_card(row)


def render_job_card(row: pd.Series) -> None:
    title = list_text(row_value(row, "title", "Titre non renseigne"))
    company = list_text(row_value(row, "company_name", "Entreprise non renseignee"))
    city = list_text(row_value(row, "city", "Ville non renseignee"))
    contract = list_text(row_value(row, "contract_type", "Contrat non renseigne"))
    experience = list_text(row_value(row, "experience_level", "Niveau non renseigne"))
    source = list_text(row_value(row, "source", "Source non renseignee"))
    salary = format_salary(row_value(row, "salary_avg"))
    score = row_value(row, "search_score") if "search_score" in row else row_value(row, "score")
    description = clean_description(row_value(row, "description_extract"))
    skills = row_value(row, "matched_skills") or row_value(row, "detected_skills") or []
    if isinstance(skills, str):
        skills = [skill.strip() for skill in skills.split(",") if skill.strip()]
    source_url = str(row_value(row, "source_url"))

    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(f"{company} | {city} | {contract} | {experience} | {salary} | {source}")
        if skills:
            st.markdown(" ".join(f"`{skill}`" for skill in list(skills)[:8]))
        if description:
            st.write(description)

        footer_left, footer_right = st.columns([1, 1])
        if score:
            footer_left.caption(f"Score de pertinence: {score}")
        if source_url:
            footer_right.link_button("Voir l'offre", source_url)


def search_controls(options: dict, prefix: str, default_limit: int, max_limit: int) -> dict:
    city_values = option_values(options, "cities", "city")
    skill_values = option_values(options, "skills", "skill_name")
    contract_values = options.get("contract_types", [])
    experience_values = options.get("experience_levels", [])
    source_values = options.get("sources", [])

    col1, col2, col3 = st.columns([2.0, 1.1, 1.1])
    query = col1.text_input(
        "Mot cle",
        value="data",
        placeholder="data engineer, analyst, cloud...",
        key=f"{prefix}_query",
    )
    city = col2.selectbox("Ville", ["Toutes"] + city_values, key=f"{prefix}_city")
    source = col3.selectbox("Source", ["Toutes"] + source_values, key=f"{prefix}_source")

    col1, col2, col3, col4 = st.columns(4)
    selected_skills = col1.multiselect("Competences", skill_values, default=[], key=f"{prefix}_skills")
    contract_type = col2.selectbox("Contrat", ["Tous"] + contract_values, key=f"{prefix}_contract")
    experience_level = col3.selectbox("Niveau", ["Tous"] + experience_values, key=f"{prefix}_experience")
    min_salary = col4.number_input(
        "Salaire minimum",
        min_value=0,
        value=0,
        step=5000,
        key=f"{prefix}_salary",
    )
    limit = st.slider(
        "Nombre maximum de resultats",
        min_value=5,
        max_value=max_limit,
        value=default_limit,
        step=5,
        key=f"{prefix}_limit",
    )

    params = {
        "query": query,
        "city": "" if city == "Toutes" else city,
        "skills": ",".join(selected_skills),
        "contract_type": "" if contract_type == "Tous" else contract_type,
        "experience_level": "" if experience_level == "Tous" else experience_level,
        "source": "" if source == "Toutes" else source,
        "min_salary": min_salary if min_salary > 0 else None,
        "limit": limit,
    }
    return {key: value for key, value in params.items() if value not in (None, "")}


def render_home(stats: dict, jobs_df: pd.DataFrame) -> None:
    top_cities = stats.get("top_cities", [])
    salary_summary = stats.get("salary_summary", {})
    metric_row(
        [
            ("Offres", format_number(stats.get("job_count", 0)), "Nombre d'offres chargees en warehouse"),
            ("Entreprises", format_number(stats.get("company_count", 0)), "Entreprises detectees"),
            ("Salaire moyen", format_salary(salary_summary.get("average_salary") or stats.get("average_salary")), "Salaire moyen disponible"),
            ("Top villes", format_number(len(top_cities)), "Villes visibles dans le dashboard"),
        ]
    )

    col1, col2 = st.columns([1.05, 0.95])
    with col1:
        section_title("Pipeline de donnees")
        render_pipeline()
    with col2:
        section_title("Repartition des contrats")
        render_contract_overview(dataframe(stats.get("contract_distribution", [])).head(5))

    col1, col2 = st.columns(2)
    with col1:
        section_title("Top villes")
        render_horizontal_bar_chart(
            dataframe(top_cities).head(6),
            label_column="city",
            value_column="job_count",
            label_title="Ville",
            value_title="Offres",
            height=280,
        )
    with col2:
        section_title("Top competences")
        render_horizontal_bar_chart(
            dataframe(stats.get("top_skills", [])).head(6),
            label_column="skill_name",
            value_column="job_count",
            label_title="Competence",
            value_title="Offres",
            height=280,
        )

    section_title("Dernieres offres")
    render_job_cards(jobs_df, limit=3, columns_per_row=1)


def render_market(stats: dict, jobs_df: pd.DataFrame) -> None:
    cities_df = dataframe(stats.get("top_cities", []))
    regions_df = dataframe(stats.get("top_regions", []))
    sources_df = dataframe(stats.get("source_distribution", []))
    trend_df = dataframe(stats.get("publication_trend", []))
    if not cities_df.empty:
        cities_df = cities_df.sort_values("job_count", ascending=False).head(10)
    if not regions_df.empty:
        regions_df = regions_df.sort_values("job_count", ascending=False).head(10)

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        section_title("Offres par ville - decroissant")
        render_horizontal_bar_chart(
            cities_df,
            label_column="city",
            value_column="job_count",
            label_title="Ville",
            value_title="Nombre d'offres",
            height=390,
        )
    with col2:
        section_title("Top villes")
        display_dataframe(cities_df, ["city", "region", "job_count"], height=390)

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        section_title("Offres par region")
        render_horizontal_bar_chart(
            regions_df,
            label_column="region",
            value_column="job_count",
            label_title="Region",
            value_title="Nombre d'offres",
            height=340,
        )
    with col2:
        section_title("Sources")
        render_donut_chart(
            sources_df,
            label_column="source",
            value_column="job_count",
            label_title="Source",
            value_title="Offres",
            height=340,
        )

    section_title("Publications dans le temps")
    render_line_chart(
        trend_df,
        date_column="publication_day",
        value_column="job_count",
        date_title="Date de publication",
        value_title="Offres",
        height=300,
    )

    section_title("Dernieres offres chargees")
    display_dataframe(jobs_df, height=420)


def render_salaries(stats: dict, jobs_df: pd.DataFrame) -> None:
    section_title("Analyse des salaires")
    salary_df = jobs_df.dropna(subset=["salary_avg"]) if "salary_avg" in jobs_df else pd.DataFrame()
    if salary_df.empty:
        st.info("Aucune donnee de salaire disponible pour le moment.")
        return

    salary_df = salary_df.copy()
    salary_df["salary_avg"] = pd.to_numeric(salary_df["salary_avg"], errors="coerce")
    salary_df = salary_df.dropna(subset=["salary_avg"])
    salary_summary = stats.get("salary_summary", {})
    metric_row(
        [
            ("Offres avec salaire", format_number(salary_summary.get("salary_job_count") or len(salary_df)), "Offres exploitables pour l'analyse salaire"),
            ("Salaire moyen", format_salary(salary_summary.get("average_salary") or salary_df["salary_avg"].mean()), "Moyenne des salaires disponibles"),
            ("Salaire median", format_salary(salary_summary.get("median_salary") or salary_df["salary_avg"].median()), "Mediane des salaires disponibles"),
        ]
    )
    col1, col2 = st.columns([1.15, 0.85])
    with col1:
        section_title("Distribution des salaires")
        render_vertical_bar_chart(
            dataframe(stats.get("salary_buckets", [])),
            label_column="salary_bucket",
            value_column="job_count",
            label_title="Tranche salaire",
            value_title="Nombre d'offres",
            height=320,
            sort=["< 30k", "30k - 40k", "40k - 50k", "50k - 60k", "60k - 80k", "80k+"],
        )
    with col2:
        section_title("Salaire moyen par contrat")
        render_horizontal_bar_chart(
            dataframe(stats.get("salary_by_contract", [])).head(8),
            label_column="contract_type",
            value_column="average_salary",
            label_title="Contrat",
            value_title="Salaire moyen EUR",
            height=320,
        )

    top_salary_df = salary_df.sort_values("salary_avg", ascending=False).head(10)
    top_salary_df["title_short"] = top_salary_df["title"].apply(short_label)
    section_title("Top 10 salaires disponibles")
    render_horizontal_bar_chart(
        top_salary_df,
        label_column="title_short",
        value_column="salary_avg",
        label_title="Intitule de poste",
        value_title="Salaire moyen EUR",
        height=420,
    )
    display_dataframe(
        top_salary_df,
        ["title", "company_name", "city", "salary_min", "salary_max", "salary_avg"],
        height=360,
    )


def render_ml_salary() -> None:
    metadata = api_get("/ml/salary/metadata")
    features_df = dataframe(api_get("/ml/salary/features", {"limit": 300}))
    training_df = dataframe(api_get("/ml/salary/training", {"limit": 300}))
    if not features_df.empty and "salary_quality_flag" in features_df.columns:
        features_df = features_df.copy()
        features_df["salary_quality_flag"] = features_df["salary_quality_flag"].apply(translate_salary_quality)

    metric_row(
        [
            ("Features", format_number(metadata.get("feature_rows", 0)), "Lignes disponibles pour l'analyse salaire"),
            ("Training", format_number(metadata.get("training_rows", 0)), "Lignes avec salaire utilisable"),
            ("A predire", format_number(metadata.get("inference_rows", 0)), "Lignes sans cible salaire"),
            ("Moyenne training", format_salary(metadata.get("avg_training_salary")), "Salaire moyen du dataset salaire"),
        ]
    )

    col1, col2 = st.columns([0.9, 1.1])
    with col1:
        section_title("Qualite de la cible")
        if not features_df.empty and "salary_quality_flag" in features_df.columns:
            quality_df = features_df.groupby("salary_quality_flag").size().reset_index(name="job_count")
            render_horizontal_bar_chart(
                quality_df,
                label_column="salary_quality_flag",
                value_column="job_count",
                label_title="Qualite salaire",
                value_title="Nombre d'offres",
                height=260,
            )
        else:
            st.info("Pas encore de features salaire disponibles.")
    with col2:
        section_title("Bornes retenues")
        metric_row(
            [
                ("Min", format_salary(metadata.get("min_training_salary")), "Salaire minimum retenu"),
                ("Max", format_salary(metadata.get("max_training_salary")), "Salaire maximum retenu"),
                ("Exclus", format_number(metadata.get("excluded_too_low_salary_rows", 0)), "Salaires trop bas retires"),
            ]
        )

    section_title("Exemples de features salaire")
    feature_columns = [
        "title",
        "company_name",
        "city",
        "contract_type",
        "experience_level",
        "experience_level_encoded",
        "target_salary_avg",
        "salary_quality_flag",
        "skill_count",
        "detected_skills",
        "has_python",
        "has_sql",
        "has_pyspark",
        "has_spark",
        "has_airflow",
        "has_databricks",
        "has_azure",
        "has_aws",
        "has_power_bi",
        "description_length",
    ]
    display_dataframe(features_df, feature_columns, height=420)

    with st.expander("Dataset d'entrainement salaire"):
        display_dataframe(
            training_df,
            [
                "title",
                "company_name",
                "city",
                "contract_type",
                "experience_level",
                "target_salary_avg",
                "skill_count",
                "detected_skills",
            ],
            height=360,
        )


def render_monitoring() -> None:
    monitoring = api_get("/monitoring/warehouse")
    counts = monitoring.get("warehouse_counts", {}) if isinstance(monitoring, dict) else {}
    checks = monitoring.get("checks", {}) if isinstance(monitoring, dict) else {}
    enrichment = monitoring.get("description_enrichment", []) if isinstance(monitoring, dict) else []
    quality_status = monitoring.get("status", "UNKNOWN") if isinstance(monitoring, dict) else "UNKNOWN"
    database_status = monitoring.get("database_status", "unknown") if isinstance(monitoring, dict) else "unknown"

    metric_row(
        [
            ("API", "UP", "FastAPI expose les endpoints applicatifs et /metrics"),
            ("PostgreSQL", "UP" if database_status == "available" else "DOWN", "Disponibilite du warehouse"),
            ("Qualite", quality_status, "Controles bloquants sample/example/hors France"),
            ("Prometheus", "ACTIF", "Scrape des metriques exposees par FastAPI"),
        ]
    )

    col1, col2 = st.columns([0.75, 1.25])
    with col1:
        section_title("Acces monitoring")
        st.link_button("Ouvrir Grafana", "http://localhost:3000")
        st.link_button("Ouvrir Prometheus", "http://localhost:9090")
        st.caption("Flux: FastAPI /metrics -> Prometheus -> Grafana.")

    with col2:
        section_title("Volumetrie warehouse")
        count_rows = [
            {"table": key, "rows": value}
            for key, value in counts.items()
            if key in {
                "fact_jobs",
                "dim_company",
                "dim_location",
                "fact_skills",
                "job_recommendations",
                "ml_salary_feature_rows",
                "ml_salary_training_rows",
                "ml_salary_inference_rows",
            }
        ]
        count_df = dataframe(count_rows).sort_values("rows", ascending=False) if count_rows else pd.DataFrame()
        render_horizontal_bar_chart(
            count_df,
            label_column="table",
            value_column="rows",
            label_title="Objet",
            value_title="Nombre de lignes",
            height=320,
        )

    section_title("Controles qualite")
    quality_df = dataframe(
        [
            {"controle": "Sources sample", "valeur": checks.get("sample_source_rows", 0)},
            {"controle": "URL example.com", "valeur": checks.get("example_url_rows", 0)},
            {"controle": "Localisations hors France", "valeur": checks.get("non_france_location_rows", 0)},
        ]
    )
    display_dataframe(quality_df, height=160)

    if enrichment:
        section_title("Enrichissement descriptions Adzuna")
        display_dataframe(dataframe(enrichment), height=220)


def render_skills() -> None:
    skills_df = dataframe(api_get("/skills", {"limit": 30}))
    family_df = build_skill_family_frame(skills_df)
    col1, col2 = st.columns([1.15, 0.85])
    with col1:
        section_title("Competences les plus demandees")
        if not skills_df.empty:
            render_horizontal_bar_chart(
                skills_df.head(15),
                label_column="skill_name",
                value_column="job_count",
                label_title="Competence",
                value_title="Nombre d'offres",
                height=420,
            )
    with col2:
        section_title("Familles de competences")
        render_donut_chart(
            family_df,
            label_column="family",
            value_column="job_count",
            label_title="Famille",
            value_title="Occurrences",
            height=420,
        )
    display_dataframe(skills_df)


def render_companies() -> None:
    companies_df = dataframe(api_get("/companies", {"limit": 100}))
    section_title("Entreprises qui recrutent")
    if not companies_df.empty:
        render_horizontal_bar_chart(
            companies_df.head(15),
            label_column="company_name",
            value_column="job_count",
            label_title="Entreprise",
            value_title="Nombre d'offres",
            height=440,
        )
    display_dataframe(companies_df, height=520)


def render_search() -> None:
    options = api_get("/search/options")
    section_title("Filtres de recherche")
    params = search_controls(options, "search", default_limit=100, max_limit=500)
    results_df = dataframe(api_get("/jobs/search", params))

    salary_series = pd.to_numeric(results_df.get("salary_avg", pd.Series(dtype=float)), errors="coerce").dropna()
    metric_row(
        [
            ("Resultats", format_number(len(results_df)), "Offres trouvees"),
            ("Avec salaire", format_number(len(salary_series)), "Offres avec salaire moyen renseigne"),
            (
                "Salaire moyen",
                format_salary(salary_series.mean()) if not salary_series.empty else "N/A",
                "Moyenne sur les resultats filtres",
            ),
        ]
    )

    section_title("Offres les plus pertinentes")
    render_job_cards(results_df, limit=8)

    result_columns = [
        "title",
        "company_name",
        "city",
        "contract_type",
        "experience_level",
        "salary_avg",
        "matched_skills",
        "detected_skills",
        "skill_count",
        "search_score",
        "publication_date",
        "source",
        "source_url",
        "description_extract",
    ]
    with st.expander("Voir le tableau complet"):
        display_dataframe(results_df, result_columns, height=520)
        if not results_df.empty:
            st.download_button(
                "Telecharger les resultats CSV",
                clean_frame(results_df, result_columns).to_csv(index=False).encode("utf-8"),
                file_name="jobmarket_recherche_offres.csv",
                mime="text/csv",
            )


def render_email_alerts() -> None:
    options = api_get("/search/options")
    section_title("Configurer une alerte")
    with st.form("email_alert_form"):
        col1, col2 = st.columns([1.3, 0.9])
        recipient_email = col1.text_input("Email destinataire", placeholder="prenom.nom@email.com")
        recipient_name = col2.text_input("Nom destinataire", placeholder="Optionnel")
        params = search_controls(options, "alert_v2", default_limit=15, max_limit=50)
        payload = {
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            **params,
        }
        col1, col2 = st.columns([1, 1])
        preview_submit = col1.form_submit_button("Previsualiser l'alerte")
        send_submit = col2.form_submit_button("Envoyer par mail")

    if preview_submit or send_submit:
        if not recipient_email.strip():
            st.error("Renseigne d'abord un email destinataire.")
        else:
            endpoint = "/alerts/email/send" if send_submit else "/alerts/email/preview"
            st.session_state["alert_response"] = api_post(endpoint, payload)

    response = st.session_state.get("alert_response")
    if response:
        if response.get("error"):
            st.error(response["error"])
        elif response.get("sent"):
            st.success("Alerte envoyee.")
        elif response.get("configured") is False:
            st.warning("Mode previsualisation: le SMTP n'est pas encore configure pour l'envoi reel.")
        else:
            st.info("Apercu de l'alerte pret.")

        metric_row(
            [
                ("Offres dans l'alerte", format_number(response.get("job_count", 0)), "Top 15 offres incluses par defaut"),
                ("SMTP", "Configure" if response.get("configured") else "Demo", "Statut envoi mail"),
            ]
        )
        st.markdown(
            f"""
            <div class="jm-email-subject">
                <span>Objet</span>
                <strong>{html_text(response.get("subject", ""))}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.text_area("Message", value=response.get("body", ""), height=340)
        render_job_cards(dataframe(response.get("jobs", [])), limit=5)

    st.markdown(
        """
        <div class="jm-note">
            A renseigner uniquement dans le fichier .env. Pour Gmail, utiliser un mot de passe d'application Google.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendations() -> None:
    section_title("Moteur de recommandation")
    col1, col2 = st.columns(2)
    skills = col1.text_input("Competences", value="Python,SQL,PySpark,Azure")
    location = col2.text_input("Localisation", value="Paris")
    contract_type = col1.text_input("Type de contrat", value="CDI")
    experience_level = col2.text_input("Niveau", value="junior")

    recommendations = api_get(
        "/recommendations",
        {
            "skills": skills,
            "location": location,
            "contract_type": contract_type,
            "experience_level": experience_level,
            "limit": 10,
        },
    )
    recommendations_df = dataframe(recommendations)
    render_job_cards(recommendations_df, limit=6)
    with st.expander("Tableau de scoring"):
        display_dataframe(recommendations_df)


inject_theme()

with st.sidebar:
    st.markdown(
        """
        <div class="jm-brand">
            <h2>JobMarket</h2>
            <p>Data jobs France, de la collecte a l'analyse.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio("Navigation", NAV_ITEMS, label_visibility="collapsed")
    st.caption(f"API: {API_BASE_URL}")
    if st.button("Actualiser les donnees"):
        st.cache_data.clear()
        st.rerun()

render_hero(page)

stats = api_get("/statistics")
jobs_df = dataframe(api_get("/jobs", {"limit": 200}))

if "api_error" in st.session_state and not stats:
    st.warning("API indisponible ou en cours de redemarrage. Relance FastAPI puis actualise la page.")

if page == "Accueil":
    render_home(stats, jobs_df)
elif page == "Marche de l'emploi":
    render_market(stats, jobs_df)
elif page == "Salaires":
    render_salaries(stats, jobs_df)
elif page == "Salaire avance":
    render_ml_salary()
elif page == "Monitoring":
    render_monitoring()
elif page == "Competences":
    render_skills()
elif page == "Entreprises":
    render_companies()
elif page == "Recherche d'offres":
    render_search()
elif page == "Alertes mail":
    render_email_alerts()
elif page == "Recommandations":
    render_recommendations()
