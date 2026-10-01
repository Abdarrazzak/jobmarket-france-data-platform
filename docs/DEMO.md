# Guide de demonstration locale

## Objectif

Cette page decrit le lancement local de la plateforme et les controles a effectuer apres execution du pipeline.

## Demo complete avec Docker

Prerequis : Docker Desktop lance.

```powershell
cd "<dossier_du_projet>"
copy .env.example .env
docker compose up -d --build
```

Puis ouvrir :

- Airflow : http://localhost:8080
- API Swagger : http://localhost:8000/docs
- Dashboard Streamlit : http://localhost:8501

Dans Airflow, declencher le DAG `jobmarket_pipeline`.

Le DAG est aussi planifie automatiquement. Par defaut, il tourne en quotidien avec `JOBMARKET_AIRFLOW_SCHEDULE=@daily`. Pour une collecte hebdomadaire, utiliser `JOBMARKET_AIRFLOW_SCHEDULE=0 6 * * 1`.

Pour suivre le nombre d'offres traitees dans Airflow :

- ouvrir le DAG `jobmarket_pipeline` ;
- aller dans l'onglet **Grid** ou **Graph** ;
- cliquer sur une tache ;
- ouvrir **Logs** ;
- regarder le JSON affiche en fin de log.

Les compteurs utiles sont :

- `extract_adzuna.row_count` : offres ecrites en Bronze depuis Adzuna ;
- `bronze_to_silver` : lignes nettoyees en Silver ;
- `silver_to_gold.fact_jobs` : offres finales dans la couche Gold ;
- `load_postgres.fact_jobs` : offres chargees dans PostgreSQL ;
- `jobmarket_jobs_total` dans Prometheus : volume visible par l'API.

Pour charger un stock initial superieur a 2000 offres finales, activer le plan high volume dans `.env` :

```powershell
EXTRACTION_PLAN_PATH=configs/extraction_plan_high_volume.json
```

Ce mode collecte davantage de pages Adzuna et plus de variantes de mots-cles data. Il sert surtout au backfill initial ; pour l'actualisation quotidienne, le plan standard limite mieux la duree d'execution et la consommation de quota API.

## Demo locale sans Docker

Cette option est utile si Docker n'est pas disponible.

Pour relancer automatiquement PostgreSQL, l'API, Streamlit et le monitoring :

```powershell
cd "<dossier_du_projet>"
.\scripts\start_jobmarket_demo.ps1
```

Pour arreter l'API, Streamlit et le monitoring lances par ce script :

```powershell
.\scripts\stop_jobmarket_demo.ps1 -StopMonitoring
```

Execution manuelle du pipeline :

```powershell
cd "<dossier_du_projet>"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\src"
python scripts/run_local_pipeline.py --step all --skip-postgres
```

Puis charger PostgreSQL :

```powershell
python scripts/run_local_pipeline.py --step load_postgres
```

Puis enrichir les descriptions Adzuna tronquees :

```powershell
python scripts/run_local_pipeline.py --step backfill_adzuna_descriptions
```

Si PySpark affiche une erreur Java, installer le JDK local embarque :

```powershell
pip install -e ".[windows]"
python scripts/run_local_pipeline.py --step all --skip-postgres
```

Si Spark affiche une erreur Hadoop/Windows du type `winutils.exe` ou `HADOOP_HOME`, installer le correctif Windows minimal :

```powershell
mkdir "<chemin_hadoop_local>\bin"
# Copier winutils.exe et hadoop.dll dans "<chemin_hadoop_local>\bin"
setx HADOOP_HOME "<chemin_hadoop_local>"
```

Cette commande genere :

- Bronze : JSON brut historise, sans donnees d'exemple en chargement final ;
- Silver : Parquet nettoye avec PySpark ;
- Gold : tables analytiques avec PySpark ;
- fact_skills : competences detectees ;
- job_recommendations : recommandations scorees ;
- quality_report.json : rapport qualite.
- description_enrichment_log : audit des descriptions Adzuna enrichies depuis HTML.

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

Verifier Prometheus :

```promql
jobmarket_api_up
jobmarket_postgres_up
jobmarket_jobs_total
jobmarket_quality_blocking_issues_total
```

Les indicateurs ci-dessus permettent de verifier la disponibilite de l'API et de PostgreSQL, le volume charge et l'absence d'anomalie qualite bloquante.

## Resultats attendus

Le sprint local valide :

- 2 028 vraies offres Adzuna France/data dans `analytics.fact_jobs` ;
- 793 entreprises dans `analytics.dim_company` ;
- 266 localisations dans `analytics.dim_location` ;
- 773 lignes de competences dans `analytics.fact_skills` apres enrichissement Adzuna ;
- 10 recommandations dans `analytics.job_recommendations` ;
- 2 028 lignes de features salaire, dont 380 exploitables pour entrainement ;
- rapport qualite `PASS`.

## Extraction internet ciblee France/data

Le fichier `configs/extraction_plan.json` pilote le volume d'extraction :

- focus : mots-cles data et termes de localisation France ;
- Adzuna : metiers data, recherche France entiere, nombre de pages, delai entre appels ;
- The Muse : categorie Data Science et localisations France ;
- web scraping Python.org Jobs : module optionnel, desactive par defaut dans la demo France car la source retourne surtout des offres remote internationales.

Pour augmenter le volume, augmenter progressivement `max_pages_per_search`. Le plan actuel utilise peu de localisations et plus de pages par metier, afin de limiter les doublons et de rester dans les quotas Adzuna.

Le fichier `configs/extraction_plan_high_volume.json` est le preset conseille pour viser 2000+ offres : `16 requetes x 15 pages x 50 resultats`, soit jusqu'a 12000 resultats bruts avant dedoublonnage et filtres qualite.
