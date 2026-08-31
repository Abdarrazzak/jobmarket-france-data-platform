# Script de demonstration

## Objectif

Cette page sert de guide de soutenance rapide. Elle explique quoi montrer si tu as peu de temps.

## Demo complete avec Docker

Prerequis : Docker Desktop lance.

```powershell
cd "C:\Users\abdho\Documents\Projet Fil Rouge"
copy .env.example .env
docker compose up -d --build
```

Puis ouvrir :

- Airflow : http://localhost:8080
- API Swagger : http://localhost:8000/docs
- Dashboard Streamlit : http://localhost:8501

Dans Airflow, declencher le DAG `jobmarket_pipeline`.

## Demo locale sans Docker

Cette option est utile si Docker n'est pas disponible.

```powershell
cd "C:\Users\abdho\Documents\Projet Fil Rouge"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="C:\Users\abdho\Documents\Projet Fil Rouge\src"
python scripts/run_local_pipeline.py --step all --skip-postgres
```

Puis charger PostgreSQL :

```powershell
python scripts/run_local_pipeline.py --step load_postgres
```

Si PySpark affiche une erreur Java, installer le JDK local embarque :

```powershell
pip install -r requirements-local-windows.txt
python scripts/run_local_pipeline.py --step all --skip-postgres
```

Cette commande genere :

- Bronze : JSON brut historise ;
- Silver : Parquet nettoye avec PySpark ;
- Gold : tables analytiques avec PySpark ;
- fact_skills : competences detectees ;
- job_recommendations : recommandations scorees ;
- quality_report.json : rapport qualite.

Ensuite lancer l'API :

```powershell
uvicorn api.main:app --reload
```

Puis lancer le dashboard dans un second terminal :

```powershell
streamlit run dashboard/app.py
```

En mode Windows sans prompt Streamlit :

```powershell
streamlit run dashboard/app.py --server.headless true --browser.gatherUsageStats false
```

## Resultats attendus

Le sprint local valide :

- 58 offres dans `analytics.fact_jobs` ;
- 47 entreprises dans `analytics.dim_company` ;
- 29 localisations dans `analytics.dim_location` ;
- 57 competences extraites dans `analytics.fact_skills` ;
- 10 recommandations dans `analytics.job_recommendations` ;
- rapport qualite `PASS`.

## Discours court pour le jury

Le projet collecte des offres depuis Adzuna, The Muse et une source web scraping optionnelle. Les donnees brutes sont conservees en Bronze au format JSON avec une historisation par date et par run. PySpark lit ensuite la couche Bronze, nettoie et harmonise les colonnes dans Silver, puis cree les tables Gold pour l'analyse metier. Les competences sont extraites automatiquement par expressions regulieres Spark sans UDF. Le moteur de recommandation applique un score explicable base sur les competences, la localisation, le contrat et le niveau. Les donnees Gold sont chargees dans PostgreSQL, puis exposees par FastAPI et visualisees dans Streamlit. Airflow orchestre les etapes, Docker Compose lance les composants.
