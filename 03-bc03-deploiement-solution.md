# 03 - BC03 Deploiement de la solution

## Objectif

Le deploiement doit permettre de lancer la plateforme localement pour la soutenance et de decrire une trajectoire cloud vers Azure.

## Prerequis locaux

- Python 3.11 ou plus.
- Environnement virtuel `.venv`.
- PostgreSQL 16.
- Hadoop minimal Windows reference par `HADOOP_HOME` pour Spark local.
- Acces API Adzuna dans `.env`.
- Docker Desktop si la demo Docker est souhaitee.

## Variables d'environnement

Le fichier `.env.example` documente les variables attendues :

- identifiants Adzuna ;
- chemins locaux Bronze, Silver, Gold ;
- connexion PostgreSQL ;
- ports API et dashboard ;
- frequence Airflow via `JOBMARKET_AIRFLOW_SCHEDULE` ;
- parametres de backfill HTML ;
- parametres Grafana ;
- parametres SMTP optionnels pour les alertes mail.
- plan de collecte standard ou high volume via `EXTRACTION_PLAN_PATH`.

Le fichier `.env` contient les secrets et reste ignore par Git.

## Installation locale

```powershell
cd "<dossier_du_projet>"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[all,dev,windows]"
```

## Execution du pipeline

Pipeline complet :

```powershell
python scripts/run_local_pipeline.py --step all
```

Execution par etapes :

```powershell
python scripts/run_local_pipeline.py --step extract_adzuna
python scripts/run_local_pipeline.py --step bronze_to_silver
python scripts/run_local_pipeline.py --step silver_to_gold
python scripts/run_local_pipeline.py --step extract_skills
python scripts/run_local_pipeline.py --step build_recommendations
python scripts/run_local_pipeline.py --step quality_checks
python scripts/run_local_pipeline.py --step load_postgres
python scripts/run_local_pipeline.py --step backfill_adzuna_descriptions
```

## Lancement des services

API :

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Dashboard :

```powershell
python -m streamlit run dashboard\app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

URLs :

- API Swagger : http://127.0.0.1:8000/docs
- Dashboard : http://127.0.0.1:8501

## Deploiement Docker

Commande cible :

```powershell
docker compose up -d --build
```

Services definis :

- `postgres` : Data Warehouse.
- `api` : FastAPI.
- `dashboard` : Streamlit.
- `airflow` : orchestration du pipeline avec Java 17 embarque pour PySpark.
- `prometheus` : collecte des metriques.
- `grafana` : dashboards de monitoring.

Ports :

- PostgreSQL : 5432.
- API : 8000.
- Dashboard : 8501.
- Airflow : 8080.
- Prometheus : 9090.
- Grafana : 3000.

Monitoring local seul :

```powershell
docker compose -f docker-compose.monitoring.yml up -d prometheus grafana
```

Requetes Prometheus utiles pour verifier la demo :

```promql
jobmarket_api_up
jobmarket_postgres_up
jobmarket_jobs_total
jobmarket_quality_blocking_issues_total
```

Ces requetes confirment respectivement la disponibilite de l'API, la disponibilite PostgreSQL, le volume d'offres chargees et l'absence d'anomalies qualite bloquantes.

## Orchestration Airflow

DAG : `jobmarket_pipeline`

Frequence :

- quotidien par defaut avec `JOBMARKET_AIRFLOW_SCHEDULE=@daily` ;
- hebdomadaire possible avec `JOBMARKET_AIRFLOW_SCHEDULE=0 6 * * 1`.

Volume :

- plan standard : `EXTRACTION_PLAN_PATH=configs/extraction_plan.json` ;
- plan high volume pour un backfill 2000+ offres : `EXTRACTION_PLAN_PATH=configs/extraction_plan_high_volume.json`.

Le DAG utilise `catchup=False`, `max_active_runs=1` et un timeout de 3 heures afin d'eviter les rattrapages massifs et les executions concurrentes.

Ordre logique :

```text
extract_adzuna
extract_muse
extract_web_scraping
store_bronze
bronze_to_silver
silver_to_gold
extract_skills
build_recommendations
quality_checks
load_postgres
backfill_adzuna_descriptions
refresh_api
refresh_dashboard
```

## Cible Azure

Trajectoire cloud :

- Azure Data Lake Storage Gen2 pour Bronze, Silver, Gold.
- Azure Databricks ou Synapse Spark pour PySpark.
- Azure Database for PostgreSQL pour le Data Warehouse.
- Azure Container Apps ou App Service pour FastAPI et Streamlit.
- Azure Key Vault pour les secrets.
- Azure Monitor pour logs et supervision.

## Tests de validation

```powershell
python -m pytest
```

Resultat attendu :

```text
35 passed
```

## Plan de rollback

En cas de probleme :

- relancer une etape precise du pipeline ;
- conserver les fichiers Bronze pour rejouer les transformations ;
- verifier `.env` et la connexion PostgreSQL ;
- consulter `analytics.description_enrichment_log` pour les erreurs de scraping Adzuna.

## Conclusion BC03

La solution est demonstrable localement, conteneurisable avec Docker Compose et portable vers Azure avec une separation claire entre stockage, traitement, orchestration et exposition applicative.
