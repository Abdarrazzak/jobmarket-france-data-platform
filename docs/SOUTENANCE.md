# Fiche de soutenance

## Pitch en 45 secondes

JobMarket Data Platform est une plateforme Data Engineering qui collecte des offres d'emploi depuis plusieurs sources, dont Adzuna, The Muse et une source web scraping optionnelle. Les donnees brutes sont historisees dans une couche Bronze, puis nettoyees en Silver et enrichies en Gold avec PySpark. Les tables Gold alimentent un Data Warehouse PostgreSQL. FastAPI expose les donnees et Streamlit permet d'explorer les KPI, les competences, les entreprises et les recommandations.

## Ce que je montre dans la demo

1. Le dossier projet structure : `src`, `dags`, `api`, `dashboard`, `docs`, `tests`.
2. Le pipeline local :

```powershell
python scripts/run_local_pipeline.py --step all --skip-postgres
```

3. Le chargement PostgreSQL :

```powershell
python scripts/run_local_pipeline.py --step load_postgres
```

4. L'API Swagger :

```text
http://127.0.0.1:8000/docs
```

5. Le dashboard :

```text
http://127.0.0.1:8501
```

## Resultats valides localement

- Offres chargees en Silver/Gold : 58
- Entreprises : 47
- Localisations : 29
- Competences extraites : 57
- Recommandations generees : 10
- Rapport qualite : PASS

## Tables PostgreSQL

- `analytics.fact_jobs`
- `analytics.dim_company`
- `analytics.dim_location`
- `analytics.fact_skills`
- `analytics.job_recommendations`

## Top competences observees

- SQL
- Python
- Azure
- Docker
- PostgreSQL
- Databricks
- Airflow
- GCP
- DBT
- PySpark

## Recommandation principale observee

Pour un profil `Python, SQL, PySpark, Azure`, localise a Paris, niveau junior, contrat CDI :

```text
Junior Data Engineer - DataNova - score 46
```

Le score est explicable :

```text
skills=4 | location_bonus=3 | contract_bonus=2 | experience_bonus=1
```

## Points techniques a expliquer

Bronze conserve les donnees brutes JSON et l'historique des executions. Cette couche n'est jamais modifiee.

Silver nettoie et harmonise les sources : identifiant unique, colonnes standard, types corrects, suppression des doublons.

Gold prepare les donnees metier : tables de faits, dimensions, competences, statistiques et recommandations.

PySpark est utilise pour les transformations, les aggregations et l'extraction des competences avec des fonctions natives Spark.

PostgreSQL sert de Data Warehouse, pas de Data Lake.

Airflow orchestre les etapes, mais ne contient pas la logique metier.

FastAPI expose les donnees via une API REST documentee automatiquement par Swagger.

Streamlit sert d'interface de restitution pour le jury et les utilisateurs.

## Compromis assumes

Azure Data Lake Storage Gen2 est documente comme architecture cible. En demonstration locale rapide, les chemins `data/local/bronze`, `data/local/silver` et `data/local/gold` simulent les containers Azure.

Le web scraping est optionnel pour eviter de rendre la soutenance dependante d'une page web externe instable.

Le moteur de recommandation est volontairement simple et explicable : pas de Deep Learning, pas de LLM.

