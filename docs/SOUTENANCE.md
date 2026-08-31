# Fiche de soutenance

## Pitch en 45 secondes

JobMarket Data Platform est une plateforme Data Engineering specialisee sur les offres data en France. Elle interroge Adzuna et The Muse, avec un module web scraping optionnel, puis conserve uniquement les vraies offres qui respectent le perimetre France/data. Les donnees brutes sont historisees dans une couche Bronze, puis nettoyees en Silver et enrichies en Gold avec PySpark. Les tables Gold alimentent un Data Warehouse PostgreSQL. FastAPI expose les donnees et Streamlit permet d'explorer les KPI, les competences, les entreprises et les recommandations.

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

- Offres chargees en Silver/Gold : 797 vraies offres Adzuna France
- Entreprises : 397
- Localisations : 141
- Competences extraites : 350 apres enrichissement Adzuna
- Recommandations generees : 10
- Rapport qualite : PASS
- Hadoop Windows installe pour permettre l'ecriture Parquet native Spark en local
- Descriptions Adzuna enrichissables depuis les URLs stockees en base

## Tables PostgreSQL

- `analytics.fact_jobs`
- `analytics.dim_company`
- `analytics.dim_location`
- `analytics.fact_skills`
- `analytics.job_recommendations`

## Top competences observees

- Power BI
- Databricks
- SQL
- GCP
- Azure
- DBT
- Python
- Snowflake
- AWS
- Spark

## Recommandation principale observee

Pour un profil `Python, SQL, PySpark, Azure`, localise a Paris, niveau junior, contrat CDI :

```text
Data Engineer F/H - Datatorii - Paris - score 43
```

Le score est explicable :

```text
skills=4 | location_bonus=3 | contract_bonus=0 | experience_bonus=0
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

Sous Windows, Hadoop minimal est installe dans `C:\hadoop` pour permettre a Spark d'ecrire les fichiers Parquet localement.

Le web scraping est optionnel pour eviter de rendre la soutenance dependante d'une page web externe instable.

Le moteur de recommandation est volontairement simple et explicable : pas de Deep Learning, pas de LLM.

## Sources internet

Adzuna est interroge avec pagination par metier data sur le marche France, en respectant un delai entre les appels et en normalisant les localisations pour remonter des villes plutot que des arrondissements.

The Muse est interroge via son API publique paginee, sur la categorie Data Science et les localisations France.

Le scraping optionnel lit Python.org Jobs pour demontrer l'integration d'une page HTML publique, mais il est desactive dans la demo finale car cette source retourne surtout des offres remote internationales, hors perimetre France.

Un filtre de focus conserve uniquement les offres qui contiennent des mots-cles data et une localisation francaise. Cela evite que des requetes larges comme `python` ou `sql` melangent des offres de developpement general avec le marche data.

Les donnees d'exemple ne sont pas chargees dans la base finale. Si une API echoue, le pipeline ne remplace pas les resultats par de fausses URLs.

Limite Adzuna assumee : la description retournee par API peut etre tronquee. Le projet ajoute donc une etape `backfill_adzuna_descriptions` qui lit les liens Adzuna dans PostgreSQL, scrape la page HTML de detail, remplace la description si elle est plus longue, puis recalcule les competences et les recommandations.

Dernier test local : 14 descriptions Adzuna enrichies, description maximale passee a 4 785 caracteres, et table `analytics.fact_skills` rafraichie a 350 lignes.
