from __future__ import annotations

import os

import httpx
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="JobMarket Dashboard", page_icon=None, layout="wide")


@st.cache_data(ttl=60)
def api_get(path: str, params: dict | None = None):
    try:
        response = httpx.get(f"{API_BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return [] if path != "/statistics" else {}


def dataframe(data) -> pd.DataFrame:
    return pd.DataFrame(data or [])


page = st.sidebar.radio(
    "Navigation",
    [
        "Accueil",
        "Marche de l'emploi",
        "Salaires",
        "Competences",
        "Entreprises",
        "Recherche d'offres",
        "Recommandations",
    ],
)

st.title("JobMarket Data Platform")

stats = api_get("/statistics")
jobs_df = dataframe(api_get("/jobs", {"limit": 200}))

if page == "Accueil":
    col1, col2, col3 = st.columns(3)
    col1.metric("Offres", stats.get("job_count", 0))
    col2.metric("Entreprises", stats.get("company_count", 0))
    col3.metric("Salaire moyen", stats.get("average_salary", "N/A"))

    st.subheader("Architecture")
    st.code(
        "Sources API + Web scraping -> Airflow -> Bronze JSON -> PySpark Silver/Gold -> PostgreSQL -> FastAPI -> Streamlit",
        language="text",
    )
    st.dataframe(jobs_df.head(20), use_container_width=True)

elif page == "Marche de l'emploi":
    st.subheader("Offres par ville")
    cities_df = dataframe(stats.get("top_cities", []))
    if not cities_df.empty:
        st.bar_chart(cities_df.set_index("city")["job_count"])
    st.subheader("Dernieres offres")
    st.dataframe(jobs_df, use_container_width=True)

elif page == "Salaires":
    st.subheader("Analyse des salaires")
    salary_df = jobs_df.dropna(subset=["salary_avg"]) if "salary_avg" in jobs_df else pd.DataFrame()
    if not salary_df.empty:
        st.bar_chart(salary_df.set_index("title")["salary_avg"])
        st.dataframe(salary_df[["title", "company_name", "city", "salary_min", "salary_max", "salary_avg"]], use_container_width=True)
    else:
        st.info("Aucune donnee de salaire disponible pour le moment.")

elif page == "Competences":
    st.subheader("Top competences")
    skills_df = dataframe(api_get("/skills", {"limit": 30}))
    if not skills_df.empty:
        st.bar_chart(skills_df.set_index("skill_name")["job_count"])
    st.dataframe(skills_df, use_container_width=True)

elif page == "Entreprises":
    st.subheader("Entreprises qui recrutent")
    companies_df = dataframe(api_get("/companies", {"limit": 100}))
    st.dataframe(companies_df, use_container_width=True)

elif page == "Recherche d'offres":
    st.subheader("Recherche")
    query = st.text_input("Mot cle", value="data")
    city = st.text_input("Ville", value="")
    filtered = jobs_df.copy()
    if query and not filtered.empty:
        filtered = filtered[filtered["title"].str.contains(query, case=False, na=False)]
    if city and not filtered.empty:
        filtered = filtered[filtered["city"].str.contains(city, case=False, na=False)]
    st.dataframe(filtered, use_container_width=True)

elif page == "Recommandations":
    st.subheader("Moteur de recommandation")
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
    st.dataframe(dataframe(recommendations), use_container_width=True)

