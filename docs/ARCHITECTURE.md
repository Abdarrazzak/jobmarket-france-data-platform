# Architecture

## Objectif

Cette architecture separe clairement la collecte, le stockage, la transformation, la mise a disposition et la visualisation.

## Flux cible

```text
Sources API
  - Adzuna
  - The Muse
  - Web scraping optionnel
        |
        v
Airflow orchestre les etapes
        |
        v
Azure Data Lake Storage Gen2
  - bronze: donnees brutes JSON, jamais modifiees
  - silver: donnees nettoyees au format Parquet
  - gold: donnees enrichies au format Parquet
        |
        v
PostgreSQL
  - schema analytics
  - schema serving
        |
        v
FastAPI + Streamlit
```

## Roles des composants

Airflow ne contient pas la logique metier. Il lance les taches dans le bon ordre, surveille les echecs et rend le pipeline lisible.

Azure Data Lake Storage Gen2 conserve les fichiers. Il garde l'historique complet en Bronze et les datasets propres en Silver et Gold.

PySpark realise les transformations lourdes : nettoyage, harmonisation, enrichissement, extraction des competences, recommandations simples et aggregations.

PostgreSQL sert de Data Warehouse pour les tables structurees interrogees par l'API et le dashboard.

FastAPI expose les donnees via des endpoints REST documentes par Swagger.

Streamlit presente les KPI, les graphiques et les recommandations.

## Pourquoi le web scraping est optionnel

Les APIs restent les sources principales car elles sont plus stables et plus faciles a maintenir. Le web scraping est ajoute comme source complementaire pour montrer la capacite a integrer une source semi-structuree, mais il ne bloque pas le pipeline si le site change ou si l'acces est indisponible.

## Ordre technique du DAG

L'ordre retenu charge PostgreSQL apres la creation des competences et recommandations, afin que le Data Warehouse contienne toutes les tables finales :

```text
extract_adzuna
extract_muse
extract_scraping_sample
store_bronze
bronze_to_silver
silver_to_gold
extract_skills
build_recommendations
quality_checks
load_postgres
refresh_api
refresh_dashboard
```
