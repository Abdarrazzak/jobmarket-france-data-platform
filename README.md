# JobMarket Data Platform

## Objectif

JobMarket Data Platform est un projet Data Engineering qui analyse le marche de l'emploi a partir de plusieurs sources d'offres.

Le projet doit demontrer :

- une ingestion multi-sources ;
- un Data Lake Azure en couches Bronze, Silver et Gold ;
- des transformations PySpark ;
- une orchestration avec Apache Airflow ;
- un Data Warehouse PostgreSQL ;
- une API FastAPI ;
- un dashboard Streamlit ;
- un moteur de recommandation simple et explicable ;
- un moteur de recherche interactif ;
- des vues salaire optionnelles, utiles pour une evolution analytique ;
- un monitoring Prometheus et Grafana ;
- une execution conteneurisee avec Docker ;
- une documentation professionnelle.

## Architecture cible

```text
Adzuna API + The Muse API
        |
        v
Apache Airflow
        |
        v
Azure Data Lake Storage Gen2
        |
        +--> Bronze: JSON brut historise
        |
        +--> Silver: Parquet nettoye et harmonise
        |
        +--> Gold: Parquet enrichi pour analytics
        |
        v
PostgreSQL Data Warehouse
        |
        +--> FastAPI
        |
        +--> Streamlit
        |
        +--> Prometheus + Grafana
```

## Structure du depot

```text
dags/                  DAG Airflow
src/jobmarket/         Code Python du pipeline
api/                   Application FastAPI
dashboard/             Application Streamlit
configs/               Fichiers de configuration
docs/                  Documentation projet
monitoring/            Prometheus, Grafana et dashboards
tests/                 Tests automatises
scripts/               Scripts utiles
data/local/            Donnees locales temporaires ignorees par Git
pyproject.toml         Packaging, dependances et configuration pytest
```

## Demarrage local

1. Creer un environnement Python.
2. Installer les dependances.
3. Copier `.env.example` vers `.env`.
4. Renseigner les identifiants API et Azure.
5. Lancer les tests.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[all,dev,windows]"
copy .env.example .env
pytest
```

Le projet utilise `pyproject.toml` comme source unique pour les dependances Python. Les extras permettent d'installer uniquement les composants necessaires : `.[api]`, `.[dashboard]`, `.[pipeline]`, `.[dev]` ou `.[windows]`.

Verifier qu'aucun secret local n'a ete copie dans les fichiers du projet :

```powershell
python scripts/check_no_secrets.py
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Modele de donnees](docs/DATA_MODEL.md)
- [API](docs/API.md)
- [PostgreSQL](docs/POSTGRESQL.md)
- [Hadoop Windows](docs/HADOOP_WINDOWS.md)
- [Deploiement](docs/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md)
- [Script de demonstration](docs/DEMO.md)
- [Rapport final consolide](07-rapport-final-consolide.md)

## Demo rapide

Tout relancer automatiquement :

```powershell
.\scripts\start_jobmarket_demo.ps1
```

La collecte est automatisee par Airflow avec le DAG `jobmarket_pipeline`. Par defaut, la frequence est quotidienne (`@daily`). Pour une collecte hebdomadaire, modifier `JOBMARKET_AIRFLOW_SCHEDULE` dans `.env`, par exemple `0 6 * * 1` pour chaque lundi a 06:00.

Pour viser plus de 2000 offres finales, utiliser le plan high volume dans `.env` :

```powershell
EXTRACTION_PLAN_PATH=configs/extraction_plan_high_volume.json
```

Ce plan augmente la pagination Adzuna et les mots-cles data. Il est conseille pour un backfill initial, puis le plan standard peut etre reutilise pour les actualisations quotidiennes plus legeres.

Sans Docker :

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\src"
python scripts/run_local_pipeline.py --step all --skip-postgres
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```

Avec Docker :

```powershell
docker compose up -d --build
```

Monitoring local uniquement :

```powershell
docker compose -f docker-compose.monitoring.yml up -d prometheus grafana
```

Requetes Prometheus utiles :

```promql
jobmarket_api_up
jobmarket_postgres_up
jobmarket_jobs_total
jobmarket_quality_blocking_issues_total
```

Arreter les services lances par le script :

```powershell
.\scripts\stop_jobmarket_demo.ps1 -StopMonitoring
```
