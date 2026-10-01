# Architecture

## Objectif

Cette architecture separe clairement la collecte, le stockage, la transformation, la mise a disposition et la visualisation.

## Vue visuelle

![Architecture globale JobMarket](assets/jobmarket-architecture-globale.png)

## Flux du MVP local

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
Data Lake local (`data/local/`)
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

Dans le MVP, le Data Lake est constitue de fichiers locaux sous `data/local/`, organises en Bronze, Silver et Gold. Bronze conserve les donnees brutes, Silver contient les donnees nettoyees et Gold regroupe les jeux de donnees analytiques.

PySpark realise les transformations lourdes : nettoyage, harmonisation, enrichissement, extraction des competences, recommandations simples et aggregations.

PostgreSQL sert de Data Warehouse pour les tables structurees interrogees par l'API et le dashboard.

Azure Data Lake Storage Gen2 et Azure Database for PostgreSQL sont des options de deploiement cible, pas des services utilises par le MVP local.

Une etape complementaire enrichit les descriptions Adzuna apres le chargement PostgreSQL. Elle lit les URLs Adzuna stockees dans `analytics.fact_jobs`, scrape la page HTML de detail, remplace la description tronquee quand une version plus longue est disponible, puis rafraichit les competences et recommandations en base.

FastAPI expose les donnees via des endpoints REST documentes par Swagger.

Streamlit presente les KPI, les graphiques et les recommandations.

## Pourquoi le web scraping est optionnel

Les APIs restent les sources principales car elles sont plus stables et plus faciles a maintenir. Le web scraping est ajoute comme source complementaire pour montrer la capacite a integrer une source semi-structuree, mais il ne bloque pas le pipeline si le site change ou si l'acces est indisponible.

## Ordre technique du DAG

L'ordre retenu charge PostgreSQL apres la creation des competences et recommandations, afin que le Data Warehouse contienne toutes les tables finales :

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
