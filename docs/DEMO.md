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

Puis enrichir les descriptions Adzuna tronquees :

```powershell
python scripts/run_local_pipeline.py --step backfill_adzuna_descriptions
```

Si PySpark affiche une erreur Java, installer le JDK local embarque :

```powershell
pip install -r requirements-local-windows.txt
python scripts/run_local_pipeline.py --step all --skip-postgres
```

Si Spark affiche une erreur Hadoop/Windows du type `winutils.exe` ou `HADOOP_HOME`, installer le correctif Windows minimal :

```powershell
mkdir C:\hadoop\bin
# Copier winutils.exe et hadoop.dll dans C:\hadoop\bin
setx HADOOP_HOME C:\hadoop
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

## Resultats attendus

Le sprint local valide :

- 797 vraies offres Adzuna France dans `analytics.fact_jobs` ;
- 397 entreprises dans `analytics.dim_company` ;
- 141 localisations dans `analytics.dim_location` ;
- 350 competences extraites dans `analytics.fact_skills` apres enrichissement Adzuna ;
- 10 recommandations dans `analytics.job_recommendations` ;
- rapport qualite `PASS`.

## Extraction internet ciblee France/data

Le fichier `configs/extraction_plan.json` pilote le volume d'extraction :

- focus : mots-cles data et termes de localisation France ;
- Adzuna : metiers data, recherche France entiere, nombre de pages, delai entre appels ;
- The Muse : categorie Data Science et localisations France ;
- web scraping Python.org Jobs : module optionnel, desactive par defaut dans la demo France car la source retourne surtout des offres remote internationales.

Pour augmenter le volume, augmenter progressivement `max_pages_per_search`. Le plan actuel utilise peu de localisations et plus de pages par metier, afin de limiter les doublons et de rester dans les quotas Adzuna.

## Discours court pour le jury

Le projet interroge Adzuna et The Muse, avec un module web scraping optionnel. Le dataset final valide contient uniquement de vraies offres Adzuna France, car les sources hors perimetre France/data sont filtrees ou desactivees. Le plan de collecte cible les metiers data comme Data Engineer, Data Analyst, Data Scientist, Analytics Engineer, BI Analyst et Machine Learning Engineer. Les donnees brutes sont conservees en Bronze au format JSON avec une historisation par date et par run. PySpark lit ensuite la couche Bronze, nettoie et harmonise les colonnes dans Silver, puis cree les tables Gold pour l'analyse metier. Les competences sont extraites automatiquement par expressions regulieres Spark sans UDF. Le moteur de recommandation applique un score explicable base sur les competences, la localisation, le contrat et le niveau. Les donnees Gold sont chargees dans PostgreSQL, puis exposees par FastAPI et visualisees dans Streamlit. Airflow orchestre les etapes, Docker Compose lance les composants.

Point important sur Adzuna : l'API peut renvoyer une description courte. Pour ameliorer l'extraction des competences, une etape lit les URLs Adzuna stockees dans PostgreSQL, recupere la page HTML de detail, extrait une description plus longue quand elle existe, puis rafraichit `fact_skills` et `job_recommendations`. Le dernier test local a enrichi 14 descriptions Adzuna et pousse la plus longue description a 4 785 caracteres.
